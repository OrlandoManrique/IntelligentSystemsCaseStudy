import random
from .geometry import (
    compute_layered_capacity,
    compute_actual_layout,
    build_actual_matrix,
)


def assign_initial_stock(parts, locations, total_capacity, target_utilization=0.5):
    """
    2-pass allocation:
      Pass 1: ensure every SKU has at least one location.
      Pass 2: fill remaining locations randomly until target utilization.
    """
    TARGET_UTILIZATION = target_utilization * total_capacity
    used_volume = 0.0

    # Sort locations by volume so big SKUs get a chance
    locations_sorted = sorted(locations, key=lambda x: x["VOLUME_M3"], reverse=True)

    # ---- PASS 1: one slot per SKU ----
    for sku in parts:
        sku_id = sku["ITEM_ID"]
        sku_dims_m = [
            sku["LEN_MM"] / 1000,
            sku["DEP_MM"] / 1000,
            sku["WID_MM"] / 1000,
        ]

        placed = False
        for loc in locations_sorted:
            if loc["ASSIGNED_SKU"] is not None:
                continue

            max_units, orientation, grid = compute_layered_capacity(loc["DIMS_M"], sku_dims_m)
            if max_units <= 0:
                continue

            # 25% fill for the first assignment
            init_units = max(1, int(max_units * 0.25))
            stored_volume = init_units * sku["VOLUME_M3"]

            if used_volume + stored_volume > TARGET_UTILIZATION:
                remaining = TARGET_UTILIZATION - used_volume
                init_units = int(remaining // sku["VOLUME_M3"])
                if init_units <= 0:
                    continue
                stored_volume = init_units * sku["VOLUME_M3"]

            full_layers, units_per_layer, partial_units = compute_actual_layout(init_units, grid)
            full_mtx, partial_mtx = build_actual_matrix(init_units, grid)

            loc["ASSIGNED_SKU"] = sku_id
            loc["MAX_UNITS"] = max_units
            loc["INIT_UNITS"] = init_units
            loc["CURRENT_STOCK"] = init_units
            loc["ORIENTATION"] = orientation
            loc["GRID"] = grid
            loc["FULL_LAYERS"] = full_layers
            loc["PARTIAL_UNITS"] = partial_units
            loc["UNITS_PER_LAYER"] = units_per_layer
            loc["FULL_LAYERS_MTX"] = full_mtx
            loc["PARTIAL_LAYER_MTX"] = partial_mtx

            used_volume += stored_volume
            placed = True
            break

        if not placed:
            print(f"WARNING: SKU {sku_id} could not fit in ANY location!")

    # ---- PASS 2: random fill remaining locations ----
    remaining_locations = [loc for loc in locations_sorted if loc["ASSIGNED_SKU"] is None]
    random.shuffle(remaining_locations)

    for loc in remaining_locations:
        for _ in range(40):
            sku = random.choice(parts)
            sku_dims_m = [
                sku["LEN_MM"] / 1000,
                sku["DEP_MM"] / 1000,
                sku["WID_MM"] / 1000,
            ]

            max_units, orientation, grid = compute_layered_capacity(loc["DIMS_M"], sku_dims_m)
            if max_units <= 0:
                continue

            init_units = max(1, int(max_units * 0.5))
            stored_volume = init_units * sku["VOLUME_M3"]

            if used_volume + stored_volume > TARGET_UTILIZATION:
                remaining = TARGET_UTILIZATION - used_volume
                init_units = int(remaining // sku["VOLUME_M3"])
                if init_units <= 0:
                    break
                stored_volume = init_units * sku["VOLUME_M3"]

            full_layers, units_per_layer, partial_units = compute_actual_layout(init_units, grid)
            full_mtx, partial_mtx = build_actual_matrix(init_units, grid)

            loc["ASSIGNED_SKU"] = sku["ITEM_ID"]
            loc["MAX_UNITS"] = max_units
            loc["INIT_UNITS"] = init_units
            loc["CURRENT_STOCK"] = init_units
            loc["ORIENTATION"] = orientation
            loc["GRID"] = grid
            loc["FULL_LAYERS"] = full_layers
            loc["PARTIAL_UNITS"] = partial_units
            loc["UNITS_PER_LAYER"] = units_per_layer
            loc["FULL_LAYERS_MTX"] = full_mtx
            loc["PARTIAL_LAYER_MTX"] = partial_mtx

            used_volume += stored_volume
            break

        if used_volume >= TARGET_UTILIZATION:
            break

    return locations, used_volume
