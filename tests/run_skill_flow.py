#!/usr/bin/env python3
import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = [
    "example_input.json",
    "bbas3_example_input.json",
    "vale3_example_input.json",
    "lren3_example_input.json",
    "no_profit_example_input.json",
    "high_extraordinary_yield_example_input.json",
]


def run(command):
    return subprocess.check_output(command, text=True)


def main():
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        for example in EXAMPLES:
            input_path = ROOT / "examples" / example
            valuation_path = tmpdir / f"{example}.valuation.json"
            sensitivity_path = tmpdir / f"{example}.sensitivity.json"
            report_path = tmpdir / f"{example}.report.json"
            valuation = run([sys.executable, "-B", str(ROOT / "scripts" / "calculate_valuation.py"), str(input_path)])
            valuation_path.write_text(valuation, encoding="utf-8")
            sensitivity = run([sys.executable, "-B", str(ROOT / "scripts" / "calculate_sensitivity.py"), str(valuation_path)])
            sensitivity_path.write_text(sensitivity, encoding="utf-8")
            report = run([sys.executable, "-B", str(ROOT / "scripts" / "generate_report.py"), str(valuation_path), str(sensitivity_path)])
            report_path.write_text(report, encoding="utf-8")
            validation = json.loads(run([sys.executable, "-B", str(ROOT / "scripts" / "validate_output.py"), str(report_path)]))
            if not validation["ok"]:
                raise SystemExit(f"{example} failed validation: {validation}")
    print("ok")


if __name__ == "__main__":
    main()
