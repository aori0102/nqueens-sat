import subprocess
import sys
from pathlib import Path

WORKING_DIR = Path(r"D:\Uni\Modern Problem in CS\N-Queens")
SCRIPT = WORKING_DIR / "experiments.py"

ARGS = [
    "--sat-binary",
    "--sat-commander",
    "--sat-sequential",
    "--sat-product",
    "--cplex-cp",
    "--cplex-mip",
    "--cpsat",
    "--gurobi-mip",
    "--combine-reports",
]


def main():
    for arg in ARGS:
        print(f"\n{'=' * 60}")
        print(f"Running: python experiments.py {arg}")
        print(f"{'=' * 60}", flush=True)

        result = subprocess.run(
            [sys.executable, str(SCRIPT), arg],
            cwd=WORKING_DIR,
            check=False,
        )

        if result.returncode != 0:
            print(
                f"Process failed with exit code {result.returncode}: {arg}",
                flush=True,
            )
            sys.exit(result.returncode)

        print(f"Completed: {arg}", flush=True)

    print("\nAll experiments completed successfully!")


if __name__ == "__main__":
    main()