import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

for fname in ["unallocated_skus.csv", "synthetic_parts_generated_dummy.csv"]:
    path = BASE_DIR / fname

    # Try comma then semicolon
    df = pd.read_csv(path)
    if df.shape[1] == 1:
        df = pd.read_csv(path, sep=";")

    print("\n===", fname, "===")
    print("n_cols:", df.shape[1])
    print("raw columns repr:")
    for c in df.columns:
        print(repr(c))
