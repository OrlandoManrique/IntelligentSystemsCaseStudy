# sim_lib/warehouse.py
import json
import pandas as pd
from pathlib import Path

from .data_loader import load_data
from .allocation import assign_initial_stock
from .simulation import build_sku_state  # run_simulation
from .reporting import report_initial_state, export_allocations_csv
from sim_lib.geometry import compute_layered_capacity


def export_allocation_score_json(allocation_score, filename="allocation_score.json"):
    base_path = Path(__file__).parent.parent
    out_path = base_path / "outputs"
    out_path.mkdir(exist_ok=True)
    out_file = out_path / filename

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(allocation_score, f, indent=2)

    #print(f"\nAllocation score JSON written to: {out_file.resolve()}\n")


def main():
    # 1) Load data
    parts, part_meta, locations, total_capacity, locations_index = load_data()

    # 2) Allocate initial stock
    locations, used_volume, unallocated_df, allocation_score = assign_initial_stock(
        parts,
        locations,
        total_capacity,
        max_random_tries_per_location=200,
        seed=None,
    )

    if unallocated_df is not None and not unallocated_df.empty:
        print("\n--- GEOMETRY FEASIBILITY CHECK (ignoring occupancy) ---")
    else:
        print("\n--- GEOMETRY FEASIBILITY CHECK not possible---")

    for _, sku in unallocated_df.iterrows():
        sku_dims = [sku["LEN_MM"], sku["DEP_MM"], sku["WID_MM"]]
        fits_anywhere = False

        for loc in locations:
            max_units, _, _ = compute_layered_capacity(loc["DIMS_MM"], sku_dims)
            if max_units > 0:
                fits_anywhere = True
                break

        print(
            f"SKU {sku['ITEM_ID']} | "
            f"fits anywhere in warehouse: {fits_anywhere}"
        )

    print("--- END GEOMETRY CHECK ---\n")

    # 3) Report initial layout
    report_initial_state(locations, total_capacity, used_volume, max_print=10)
    export_allocations_csv(locations, filename="allocations.csv")

    # 4) Export allocation score
    unallocated_ids = []
    if unallocated_df is not None and not unallocated_df.empty and "ITEM_ID" in unallocated_df.columns:
        unallocated_ids = unallocated_df["ITEM_ID"].tolist()

    allocation_score["unallocated_item_ids"] = unallocated_ids

    print("\n--- ALLOCATION SCORE ---")
    for k, v in allocation_score.items():
        print(f"{k}: {v}")
    export_allocation_score_json(allocation_score)

    # 5) Export unallocated SKUs
    base_path = Path(__file__).parent.parent
    out_path = base_path / "outputs"
    out_path.mkdir(exist_ok=True)

    csv_path = out_path / "unallocated_skus.csv"

    EXPECTED_COLS = ["ITEM_ID", "LEN_MM", "DEP_MM", "WID_MM", "VOLUME_MM3", "REASON"]

    if unallocated_df is None or unallocated_df.empty:
        unallocated_df = pd.DataFrame(columns=EXPECTED_COLS)
    else:
        unallocated_df = unallocated_df[EXPECTED_COLS].copy()

    unallocated_df.to_csv(csv_path, index=False)
    print(f"\nUnallocated SKUs written to: {csv_path.resolve()}\n")

    if unallocated_df.empty:
        print("\nAll SKUs were successfully allocated.\n")


    # 6) Build SKU state (RL / inventory simulation uses this)
    sku_state = build_sku_state(part_meta, locations)

    # 6) Run monthly simulation
    # from .simulation import run_simulation
    # from .reporting import report_simulation_results
    # kpi = run_simulation(sku_state, months=36)
    # report_simulation_results(kpi)


if __name__ == "__main__":
    main()
