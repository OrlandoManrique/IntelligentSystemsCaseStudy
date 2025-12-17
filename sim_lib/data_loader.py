import pandas as pd
from pathlib import Path


def load_data():
    """
    Loads parts, location types and locations.
    Returns:
        parts (list[dict])
        part_meta (dict ITEM_ID -> row)
        locations (list[dict])
        total_capacity (float, m^3)
    """
    BASE_PATH = Path(__file__).parent.parent  # project root
    DATA_PATH = BASE_PATH / "Synthetic_data"

    parts_df = pd.read_csv(DATA_PATH / "synthetic_parts_generated.csv", sep=";")
    location_types_df = pd.read_csv(DATA_PATH / "location_types.csv", sep=";")
    locations_df = pd.read_csv(DATA_PATH / "locations.csv", sep=";")

    # --- ABC classification based on DEMAND ---
    parts_df = parts_df.sort_values("DEMAND", ascending=False).reset_index(drop=True)
    n_items = len(parts_df)
    nA = max(1, int(0.2 * n_items))
    nB = max(1, int(0.3 * n_items))
    cut_A = nA
    cut_B = min(nA + nB, n_items)

    parts_df.loc[:cut_A - 1, "ABC_CLASS"] = "A"
    parts_df.loc[cut_A:cut_B - 1, "ABC_CLASS"] = "B"
    parts_df.loc[cut_B:, "ABC_CLASS"] = "C"

    # Volume of SKU (X = length, Y = depth, Z = height)
    parts_df["VOLUME_M3"] = (
        parts_df["LEN_MM"] *
        parts_df["DEP_MM"] *
        parts_df["WID_MM"] / 1e9
    )

    parts = parts_df.to_dict(orient="records")

    part_meta = {
        row["ITEM_ID"]: row
        for _, row in parts_df.iterrows()
    }

    # ---- Location types ----
    location_types_df["VOLUME_M3"] = (
        location_types_df["WID_MM"] *
        location_types_df["DEP_MM"] *
        location_types_df["HT_MM"] / 1e9
    )

    location_types = {
        row["LOCATION_ID"]: row
        for _, row in location_types_df.iterrows()
    }

    # ---- Build location instances ----
    locations = []

    for _, row in locations_df.iterrows():
        loc_type = row["LOCATION_TYPE"]
        type_data = location_types[loc_type]

        dims_m = [
            type_data["WID_MM"] / 1000,  # X
            type_data["DEP_MM"] / 1000,  # Y
            type_data["HT_MM"] / 1000    # Z
        ]

        locations.append({
            "LOCATION_ID": row["LOCATION_ID"],
            "TYPE": loc_type,
            "DIMS_M": dims_m,
            "VOLUME_M3": type_data["VOLUME_M3"],
            "ASSIGNED_SKU": None,
            "MAX_UNITS": 0,
            "INIT_UNITS": 0,
            "ORIENTATION": None,
            "GRID": None,
            "FULL_LAYERS": 0,
            "PARTIAL_UNITS": 0,
            "UNITS_PER_LAYER": 0,
            "FULL_LAYERS_MTX": None,
            "PARTIAL_LAYER_MTX": None,
            "CURRENT_STOCK": 0,
        })

    total_capacity = sum(loc["VOLUME_M3"] for loc in locations)

    return parts, part_meta, locations, total_capacity
