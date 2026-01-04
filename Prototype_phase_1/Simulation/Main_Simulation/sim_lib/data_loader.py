# sim_lib/data_loader.py
import pandas as pd
from pathlib import Path


def load_data():
    """
    Loads parts and locations.
    ALL DIMENSIONS AND POSITIONS ARE IN MILLIMETERS.
    Volume is stored in mm³.

    Returns:
      parts: list[dict]
      part_meta: dict[item_id -> pandas.Series-like row]
      locations: list[dict]
      total_capacity: float (mm³)
      locations_index: dict[loc_id -> location dict]   (for O(1) lookup by loc_inst_code)
    """

    BASE_PATH = Path(__file__).parent.parent

    # Be tolerant to folder name casing differences
    data_path_candidates = [
        BASE_PATH / "Synthetic_data",
        BASE_PATH / "synthetic_data",
    ]
    DATA_PATH = next((p for p in data_path_candidates if p.exists()), data_path_candidates[0])

    # =====================================================
    # LOAD PARTS
    # =====================================================
    parts_df = pd.read_csv(DATA_PATH / "synthetic_parts_generated_dummy.csv", sep=";")

    # --- ABC classification based on demand ---
    parts_df = parts_df.sort_values("DEMAND", ascending=False).reset_index(drop=True)
    n_items = len(parts_df)

    nA = max(1, int(0.2 * n_items))
    nB = max(1, int(0.3 * n_items))

    parts_df.loc[:nA - 1, "ABC_CLASS"] = "A"
    parts_df.loc[nA:nA + nB - 1, "ABC_CLASS"] = "B"
    parts_df.loc[nA + nB:, "ABC_CLASS"] = "C"

    # SKU volume (in mm³)
    parts_df["VOLUME_MM3"] = (
        parts_df["LEN_MM"] *
        parts_df["DEP_MM"] *
        parts_df["WID_MM"]
    )

    parts = parts_df.to_dict(orient="records")

    part_meta = {
        row["ITEM_ID"]: row
        for _, row in parts_df.iterrows()
    }

    # =====================================================
    # LOAD LOCATIONS (MM)
    # =====================================================
    locations_df = pd.read_csv(DATA_PATH / "locations_dummy.csv", sep=",")

    locations = []

    for _, row in locations_df.iterrows():

        width_mm  = int(row["width"])
        depth_mm  = int(row["depth"])
        height_mm = int(row["height"])

        volume_mm3 = width_mm * depth_mm * height_mm

        locations.append({
            "LOCATION_ID": row["loc_inst_code"],
            "TYPE": row["loc_type"],

            # Slot geometry (mm)
            "DIMS_MM": [width_mm, depth_mm, height_mm],
            "VOLUME_MM3": float(volume_mm3),

            # Slot position in warehouse (mm)
            "POS_X_MM": int(row["x"]),
            "POS_Y_MM": int(row["y"]),
            "POS_Z_MM": int(row["z"]),

            # Allocation state
            "ASSIGNED_SKU": None,
            "MAX_UNITS": 0,
            "INIT_UNITS": 0,
            "CURRENT_STOCK": 0,
            "ORIENTATION": None,
            "GRID": None,
            "FULL_LAYERS": 0,
            "PARTIAL_UNITS": 0,
            "UNITS_PER_LAYER": 0,
            "FULL_LAYERS_MTX": None,
            "PARTIAL_LAYER_MTX": None,

            # Helpful for scoring/RL
            "STORED_VOLUME_MM3": 0.0,
        })

    total_capacity = float(sum(loc["VOLUME_MM3"] for loc in locations))
    locations_index = {loc["LOCATION_ID"]: loc for loc in locations}

    return parts, part_meta, locations, total_capacity, locations_index
