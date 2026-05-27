# BitnBolt Hydroponics ML — Presentation README

This README is the **quick briefing document** for presenting your changes today.
It explains:
- what was changed,
- why it was changed,
- what each notebook proves,
- what to claim (and what not to claim) in the paper.

---

## 1) Reviewer problems

1. **Insufficient Statistical Validation**
   - Missing RMSE/error metrics
   - Missing confidence intervals
   - Missing calibration analysis

2. **Limited Scientific Novelty**
   - Looked like system integration only
   - No formal modelling
   - No advanced control / ML decision making

---

## 2) Critical hardware truth

### EC and TDS are not independent sensors

In this setup, **TDS is derived from EC** (same conductivity probe + firmware formula).
So:
- Do **not** claim EC–TDS as dual-sensor validation.
- Do **not** use TDS to predict EC in ML (circular).
- Use TDS only for **formula audit**.

This correction is already applied in the notebooks.

---

## 3) Main files

### Notebooks
- `01_statistical_validation.ipynb`
  - Reviewer #1
  - RMSE, MAE, R2, bootstrap CI, calibration, Bland–Altman

- `02_methodological_innovation.ipynb`
  - Reviewer #2
  - Fault models, FDD, state-space, ML policy, predictive-control preview

### Outputs
- `results/validation_metrics.csv`
- `results/water_temp_validation.csv`
- `results/ec_tds_formula_audit.csv`
- `results/innovation_metrics.csv`
- `figures/validation/*`
- `figures/innovation/*`

### Data
- `test.nfads.csv`
- `test.ems.csv`
- `test.lms.csv`

---

## 4) Intuition — Notebook 1 (Statistical Validation)

Goal: prove sensor behavior statistically, not only visually.

Flow:
1. Merge NFADS + EMS (+ LMS where available) into hourly data.
2. Build **virtual EC model** using independent features only.
3. Validate with **time-series CV**.
4. Report RMSE/MAE/R2 + 95% bootstrap CI.
5. Add calibration and Bland–Altman plots.
6. Add ±3% tolerance analysis.
7. Audit EC→TDS formula separately.
8. Validate waterTemp with independent context.

Why this matters: directly satisfies reviewer demand for **error metrics + CI + calibration**.

---

## 5) Intuition — Notebook 2 (Methodological Innovation)

Goal: show real method contribution beyond IoT integration.

Flow:
1. Define formal fault families (normal, bias, drift, precision, spike, stuck).
2. Inject faults on real EC windows.
3. Train FDD classifiers + confusion matrices.
4. Build state-space model:
   - state = [EC, waterTemp]
   - input = [pump duty, air temp, humidity]
5. Build ML dosing policy.
6. Add predictive-control preview.
7. Add field anomaly flags from virtual EC residuals.

Why this matters: addresses **formal modelling + ML decision-making + control strategy preview**.

---

## 6) How to present today (10 min)

1. Reviewer comments (slide)
2. What changed (2 notebooks + corrected EC/TDS logic)
3. Statistical validation pipeline + key figures
4. Methodological innovation pipeline + key figures
5. Honest results: strengths and limitations
6. Next data plan (more overlap, pH recovery, longer LMS)

---

## 7) Claims to use vs avoid

### Use
- “Sensor-independent EC validation with RMSE, CI, calibration.”
- “Formal state-space and ML decision layer added.”
- “Predictive control presented as feasibility preview.”

### Avoid
- “Dual-probe EC/TDS validation.”
- “Production-ready MPC.”
- Overclaiming FDD class-wise performance.

---

## 8) Run

```bash
pip install -r requirements.txt
python run_notebook1.py
python run_notebook2.py
```

For full manuscript writing template and section-by-section text, see:
`README_NOTEBOOKS.md`
