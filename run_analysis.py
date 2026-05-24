"""Run full ML pipeline (same logic as main.ipynb). Usage: python run_analysis.py"""
import matplotlib

matplotlib.use("Agg")

import json
from pathlib import Path

nb = json.loads(Path("main.ipynb").read_text(encoding="utf-8"))
code = []
for cell in nb["cells"]:
    if cell["cell_type"] == "code":
        code.append("".join(cell["source"]).replace("display(", "print("))
exec(compile("\n".join(code), "main.ipynb", "exec"), {"__name__": "__main__"})
