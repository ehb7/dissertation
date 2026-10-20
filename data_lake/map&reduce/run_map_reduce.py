"""
Map and Reduce using python.
Additional arguments
    Args:
        raw_csv_path: path to the raw source CSV (e.g. today's POS export).
        output_dir: directory where the resulting CSV should be written (RAW_CSV_DIR).
"""

import subprocess
import pandas as pd
import sys
from pathlib import Path


def run_map_reduce(raw_csv_path: str, output_dir: str) -> str:

    with open(raw_csv_path, "rb") as f:
        raw_bytes = f.read()

    print(f"Running mapper on {raw_csv_path}...")
    mapper_result = subprocess.run(
        [sys.executable, "mapper.py"],
        input=raw_bytes,
        capture_output=True,
        check=True,
    )

    print("Sorting mapper output...")
    sorted_lines = sorted(mapper_result.stdout.decode().splitlines())
    sorted_input = ("\n".join(sorted_lines) + "\n").encode()

    print("Running reducer...")
    reducer_result = subprocess.run(
        [sys.executable, "reducer.py"],
        input=sorted_input,
        capture_output=True,
        check=True,
    )

    print("Building output CSV...")
    rows = [line.split("\t") for line in reducer_result.stdout.decode().splitlines()]
    df = pd.DataFrame(rows, columns=["pizza_id", "quantity"])

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    output_path = Path(output_dir) / f"daily_orders.csv"
    df.to_csv(output_path, index=False)

    print(f"Done: {len(df)} products, written to {output_path}")
    return str(output_path)


if __name__ == "__main__":
    run_map_reduce(
        raw_csv_path="test_daily_orders.csv",
        output_dir="output/",
    )
