import random
import pandas as pd
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
    ALL VOLUMES ARE IN MM³
    """

    TARGET_UTILIZATION = target_utilization * total_capacity
    used_volume_mm3 = 0.0

    # Sort locations by volume (largest first)
    locations_sorted = sorted(
        locations, key=lambda x: x["VOLUME_MM3"], reverse=True
    )

    unallocated_skus = []

    # ======================================================
    # PASS 1: ensure every SKU has at least one location
    # ======================================================
    # Sort SKUs by placement difficulty (largest & most awkward first)
    parts_sorted = sorted(parts, key=lambda s: max(s["LEN_MM"], s["DEP_MM"], s["WID_MM"]),reverse=True)

    
    for sku in parts_sorted:
        sku_id = sku["ITEM_ID"]

        # SKU dimensions IN MM (NO CONVERSION)
        sku_dims_mm = [
            sku["LEN_MM"],
            sku["DEP_MM"],
            sku["WID_MM"],
        ]

        placed = False

        for loc in locations_sorted:
            if loc["ASSIGNED_SKU"] is not None:
                continue

            max_units, orientation, grid = compute_layered_capacity(
                loc["DIMS_MM"], sku_dims_mm
            )

            if max_units <= 0:
                continue

            # 25% fill for first assignment
            init_units = max(1, int(max_units * 0.25))
            stored_volume = init_units * sku["VOLUME_MM3"]

            if used_volume_mm3 + stored_volume > TARGET_UTILIZATION:
                remaining = TARGET_UTILIZATION - used_volume_mm3
                init_units = int(remaining // sku["VOLUME_MM3"])
                if init_units <= 0:
                    continue
                stored_volume = init_units * sku["VOLUME_MM3"]

            full_layers, units_per_layer, partial_units = compute_actual_layout(
                init_units, grid
            )
            full_mtx, partial_mtx = build_actual_matrix(init_units, grid)

            loc.update({
                "ASSIGNED_SKU": sku_id,
                "MAX_UNITS": max_units,
                "INIT_UNITS": init_units,
                "CURRENT_STOCK": init_units,
                "ORIENTATION": orientation,
                "GRID": grid,
                "FULL_LAYERS": full_layers,
                "PARTIAL_UNITS": partial_units,
                "UNITS_PER_LAYER": units_per_layer,
                "FULL_LAYERS_MTX": full_mtx,
                "PARTIAL_LAYER_MTX": partial_mtx,
            })

            used_volume_mm3 += stored_volume
            placed = True
            break

        if not placed:
            print(f"WARNING: SKU {sku_id} could not fit in ANY location!")

            unallocated_skus.append({
                "ITEM_ID": sku_id,
                "LEN_MM": sku["LEN_MM"],
                "DEP_MM": sku["DEP_MM"],
                "WID_MM": sku["WID_MM"],
                "VOLUME_MM3": sku["VOLUME_MM3"],
    })


    # ======================================================
    # PASS 2: fill remaining locations randomly
    # ======================================================
    remaining_locations = [
        loc for loc in locations_sorted if loc["ASSIGNED_SKU"] is None
    ]
    random.shuffle(remaining_locations)

    for loc in remaining_locations:
        for _ in range(40):
            sku = random.choice(parts)

            sku_dims_mm = [
                sku["LEN_MM"],
                sku["DEP_MM"],
                sku["WID_MM"],
            ]

            max_units, orientation, grid = compute_layered_capacity(
                loc["DIMS_MM"], sku_dims_mm
            )

            if max_units <= 0:
                continue

            init_units = max(1, int(max_units * 0.5))
            stored_volume = init_units * sku["VOLUME_MM3"]

            if used_volume_mm3 + stored_volume > TARGET_UTILIZATION:
                remaining = TARGET_UTILIZATION - used_volume_mm3
                init_units = int(remaining // sku["VOLUME_MM3"])
                if init_units <= 0:
                    break
                stored_volume = init_units * sku["VOLUME_MM3"]

            full_layers, units_per_layer, partial_units = compute_actual_layout(
                init_units, grid
            )
            full_mtx, partial_mtx = build_actual_matrix(init_units, grid)

            loc.update({
                "ASSIGNED_SKU": sku["ITEM_ID"],
                "MAX_UNITS": max_units,
                "INIT_UNITS": init_units,
                "CURRENT_STOCK": init_units,
                "ORIENTATION": orientation,
                "GRID": grid,
                "FULL_LAYERS": full_layers,
                "PARTIAL_UNITS": partial_units,
                "UNITS_PER_LAYER": units_per_layer,
                "FULL_LAYERS_MTX": full_mtx,
                "PARTIAL_LAYER_MTX": partial_mtx,
            })

            used_volume_mm3 += stored_volume
            break

        if used_volume_mm3 >= TARGET_UTILIZATION:
            break

    unallocated_df = pd.DataFrame(unallocated_skus)

    return locations, used_volume_mm3, unallocated_df
