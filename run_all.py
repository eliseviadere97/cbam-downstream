"""Run every step in order, exactly as if typed one by one. From the repository root:  python run_all.py"""
import subprocess
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent / "src"

for script in sorted(SRC.glob("[0-9][0-9]_*.py")):
    print(f"\n=== {script.name} ===", flush=True)
    subprocess.run([sys.executable, str(script)], check=True)
