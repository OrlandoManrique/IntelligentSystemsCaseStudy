import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

unallocated_path = BASE_DIR / "unallocated_skus.csv"                 # comma-separated
parts_path = BASE_DIR / "synthetic_parts_generated_dummy.csv"         # semicolon-separated
output_path = BASE_DIR / "synthetic_parts_generated_dummy_clean.csv"

unallocated = pd.read_csv(unallocated_path)
parts = pd.read_csv(parts_path, sep=";")

# strip header whitespace just in case
unallocated.columns = unallocated.columns.str.strip()
parts.columns = parts.columns.str.strip()

bad_ids = set(unallocated["ITEM_ID"].astype(str))

before = len(parts)
parts_clean = parts[~parts["ITEM_ID"].astype(str).isin(bad_ids)]
parts_clean.to_csv(output_path, sep=";", index=False)  # keep same delimiter style

print(f"Removed {before - len(parts_clean)} rows.")
print(f"Saved: {output_path}")
