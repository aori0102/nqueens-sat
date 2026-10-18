from pathlib import Path
from typing import List
import pandas as pd
import csv
from utils import SolveReport

TEXT_COLS = ["Method Name", "Result"]
INT_COLS = ["Board Size", "Num Clauses", "Num Variables"]

def export_reports_to_csv(reports: List[SolveReport], file_path: str = "benchmark_results.csv"):
    if not reports:
        return

    fieldnames = list(reports[0].to_dict().keys())

    with open(file_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        
        writer.writeheader()
        
        for report in reports:
            writer.writerow(report.to_dict())
            
    print(f"Successfully written {len(reports)} data lines into file: {file_path}")

def combine_csv_reports(
    directories: List[str],
    file_names: List[str],
    output_path: str = "benchmark_results.csv",
    key_column: str = "Board Size",
):
    frames = []
    columns = None

    for name in file_names:
        runs = []
        for d in directories:
            path = Path(d) / name
            if path.exists():
                runs.append(pd.read_csv(path))
            else:
                print(f"Skipping missing file: {path}")

        if not runs:
            continue

        df = pd.concat(runs, ignore_index=True)
        if columns is None:
            columns = list(df.columns)

        agg = {}
        for col in df.columns:
            if col == key_column:
                continue
            if col in TEXT_COLS:
                agg[col] = lambda s: s.mode().iloc[0]  # most common value across runs
            else:
                agg[col] = "mean"

        avg = df.groupby(key_column, as_index=False).agg(agg)

        for col in INT_COLS:
            if col in avg.columns:
                avg[col] = avg[col].round().astype(int)  # kills the .0

        frames.append(avg[columns].sort_values(key_column))

    if not frames:
        return

    # file_names order = method order, Board Size ascending within each
    pd.concat(frames, ignore_index=True).to_csv(output_path, index=False)

    print(f"Combined {len(frames)} methods across {len(directories)} dirs into: {output_path}")