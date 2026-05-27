"""Run 02_methodological_innovation.ipynb"""
import json, matplotlib
matplotlib.use("Agg")
from pathlib import Path
nb = json.loads(Path("02_methodological_innovation.ipynb").read_text(encoding="utf-8"))
code = "\n".join("".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code")
exec(compile(code, "02_methodological_innovation.ipynb", "exec"), {"__name__": "__main__"})
