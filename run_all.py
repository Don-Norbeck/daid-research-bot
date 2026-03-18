import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

STEPS = [
    ("Capture RSS items", ["python", "capture_local.py"]),
    ("Analyze recent items", ["python", "analyze_local.py"]),
    ("Rank signals", ["python", "rank_signals.py"]),
    ("Generate pitch ideas", ["python", "pitch_bot.py"]),
]


def run_step(label: str, cmd: list[str]) -> None:
    print(f"\n=== {label} ===")
    print("Running:", " ".join(cmd))

    result = subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        text=True,
    )

    if result.returncode != 0:
        print(f"[ERROR] Step failed: {label}")
        sys.exit(result.returncode)

    print(f"[OK] Completed: {label}")


def main() -> None:
    print("Starting DAID Research Bot pipeline...")

    for label, cmd in STEPS:
        run_step(label, cmd)

    print("\n[OK] Full pipeline complete.")
    print("Next:")
    print(" - Review data/outputs/weekly_summary_*.json")
    print(" - Review data/outputs/pitch_ideas_*.json")
    print(" - Launch UI with: python -m streamlit run app.py")


if __name__ == "__main__":
    main()