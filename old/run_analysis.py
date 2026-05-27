"""Run all cells in main.ipynb (batch). Usage: python run_analysis.py"""
import json
import matplotlib

matplotlib.use("Agg")

from pathlib import Path

nb = json.loads(Path("main.ipynb").read_text(encoding="utf-8"))
code = []
for cell in nb["cells"]:
    if cell["cell_type"] == "code":
        code.append("".join(cell["source"]))
exec(compile("\n".join(code), "main.ipynb", "exec"), {"__name__": "__main__"})
