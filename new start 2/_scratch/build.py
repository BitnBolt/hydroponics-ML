import nbformat, shutil
from pathlib import Path
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parent.parent
nb = nbformat.read(ROOT / 'main.ipynb', as_version=4)

# remove any previously appended review cells (idempotent rebuild)
cut = next((i for i, c in enumerate(nb.cells) if c.metadata.get('review_response')), None)
if cut is not None:
    nb.cells = nb.cells[:cut]

# ---- targeted fixes to the existing narrative cell (index 8) -------------------------------------------------
c8 = nb.cells[8]
# always patch from the pristine original so the rebuild is idempotent
src = nbformat.read(ROOT / '_scratch' / 'main_backup.ipynb', as_version=4).cells[8].source
src = src.replace("        window_override='12-hour daytime',\n", "")
PATCH_ANCHOR = "    raw, cal = ols['raw'], ols['calibrated']\n"
src = src.replace(
    PATCH_ANCHOR,
    PATCH_ANCHOR +
    "    if df['meter'].nunique() == 1:  # constant reference: R2 undefined, OLS not identifiable\n"
    "        diff = df['sensor'] - df['meter']\n"
    "        return (\n"
    "            f\"{meta['quantity'].capitalize()} were measured over a {window} window \"\n"
    "            f\"using {meta['sensor_name']} as the onboard sensor and {meta['meter_name']} as the reference meter \"\n"
    "            f\"in the {meta['node']}, as seen in {meta['figure_data']}. The reference meter stayed constant at \"\n"
    "            f\"{df['meter'].iloc[0]:.1f} {unit} for the whole test, so R² is undefined and an OLS calibration is not identifiable. \"\n"
    "            f\"The sensor is therefore reported only through its fixed offset of {diff.mean():+.2f} {unit} \"\n"
    "            f\"(MAE = {diff.abs().mean():.2f} {unit}, sensor SD = {df['sensor'].std():.3f} {unit}); \"\n"
    "            f\"see {meta['figure_timeline']}.\"\n"
    "        )\n", 1)
src = src.replace(
    "out_md.write_text('\\n'.join(md_lines), encoding='utf-8')",
    "tail = ''\n"
    "if out_md.exists():  # keep the hand-assembled summary tables that follow the paragraphs\n"
    "    _old = out_md.read_text(encoding='utf-8')\n"
    "    if '## Accuracy %' in _old:\n"
    "        tail = '\\n---\\n\\n' + _old[_old.index('## Accuracy %'):]\n"
    "out_md.write_text('\\n'.join(md_lines) + tail, encoding='utf-8')")
assert 'window_override=' not in src and 'not identifiable' in src and 'tail' in src
c8.source = src

# ---- new cells ---------------------------------------------------------------------------------------------------
def code(name):
    c = nbformat.v4.new_code_cell((ROOT / '_scratch' / 'cells' / f'{name}.py').read_text(encoding='utf-8').rstrip() + '\n')
    c.metadata['review_response'] = name
    return c


def md(text):
    c = nbformat.v4.new_markdown_cell(text)
    c.metadata['review_response'] = 'md'
    return c


H1 = """---
# Reviewer response - Part 1: data collection, train/test procedure, confidence intervals and accuracy %

**What the reviewer asked:** how the data were collected, how train/test was done, and how the reported confidence intervals and accuracy percentages were calculated.

**What this section does**
1. Summarises the four experiments directly from the raw logs (Table R1-A).
2. States honestly that the first analysis fitted and scored OLS on the *same* data (in-sample), and re-evaluates with **time-ordered** validation: blocked 5-fold CV (primary), chronological 70/30 hold-out, plus leave-one-out as a *leaky* contrast (Table R1-B, Figure R1).
3. Explains the intervals: classical t-based slope/intercept CIs vs. autocorrelation-aware **moving-block bootstrap** CIs, and what the +/-1.96 x RMSE band is (Table R1-C, Figure R2).
4. Re-computes accuracy % (in-sample vs out-of-fold, with 95% CI) and handles the constant-reference nutrient-temperature test (Table R1-D).
5. Prints paper-ready text with every number computed from the data (Tables 1-4 in the text)."""

H2 = """---
# Reviewer response - Part 2: why is the pre-calibration air-temperature R^2 negative?

**Short answer.** R^2 = 1 - SSE/SST measures the sensor against a baseline that always predicts the *mean of the reference*. In the EMS test the reference spread is tiny (SD = 0.075 C, span 0.2 C) while the raw sensor sits 0.177 C below the reference, so the squared error is ~6x the reference variance and R^2 = -5.18. Exact identity:

$$R^2 = r^2 - \\left(r - \\frac{s_{sensor}}{s_{ref}}\\right)^2 - \\left(\\frac{\\text{bias}}{s_{ref}}\\right)^2$$

The cells below compute this decomposition for every sensor, quantify the effect of the 0.1 C logging resolution, and plot Figure R3."""

nb.cells += [md(H1), code('q1_a'), code('q1_b'), code('q1_c'), code('q1_d'), code('q1_text'), md(H2), code('q2_a'), code('q2_text')]

client = NotebookClient(nb, timeout=1200, kernel_name='python3', resources={'metadata': {'path': str(ROOT)}})
import re
from nbclient.exceptions import CellExecutionError
try:
    client.execute()
except CellExecutionError as exc:
    print(re.sub(r'\x1b\[[0-9;]*m', '', str(exc))[:2500])
    raise SystemExit(1)
nbformat.write(nb, ROOT / 'main.ipynb')
print('main.ipynb updated; cells =', len(nb.cells))
