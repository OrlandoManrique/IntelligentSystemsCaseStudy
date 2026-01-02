# sim_lib/allocation.py
import random
import pandas as pd
from .geometry import (
    compute_layered_capacity,
    compute_actual_layout,
    build_actual_matrix,
)


def _cached_capacity(loc, sku, fit_cache):
    """
    Cache key: (LOCATION_ID, ITEM_ID)
    Cache value: (max_units, best_orientation, best_grid)
    """
    key = (loc["LOCATION_ID"], sku["ITEM_ID"])
    if key in fit_cache:
        return fit_cache[key]

    sku_dims_mm = [sku["LEN_MM"], sku["DEP_MM"], sku["WID_MM"]]
    result = compute_layered_capacity(loc["DIMS_MM"], sku_dims_mm)
    fit_cache[key] = result
    return result


def _compute_allocation_score(locations, total_capacity, used_volume_mm3, unallocated_df):
    MM3_TO_M3 = 1e-9

    allocated = [loc for loc in locations if loc["ASSIGNED_SKU"] is not None]
    n_alloc = len(allocated)
    n_total = len(locations)

    fill_ratios = []
    wastes_mm3 = []

    for loc in allocated:
        slot_vol = float(loc["VOLUME_MM3"])
        stored_vol = float(loc.get("STORED_VOLUME_MM3", 0.0))

        if slot_vol > 0:
            fill_ratios.append(stored_vol / slot_vol)
            wastes_mm3.append(slot_vol - stored_vol)

    avg_fill_ratio = sum(fill_ratios) / len(fill_ratios) if fill_ratios else 0.0
    total_waste_mm3 = sum(wastes_mm3) if wastes_mm3 else 0.0

    util_pct = (used_volume_mm3 / total_capacity) * 100.0 if total_capacity > 0 else 0.0

    return {
        # Volumes (converted and rounded)
        "total_capacity_m3": round(total_capacity * MM3_TO_M3, 3),
        "used_volume_m3": round(used_volume_mm3 * MM3_TO_M3, 3),
        "total_waste_m3": round(total_waste_mm3 * MM3_TO_M3, 3),

        # Utilization
        "utilization_pct": round(util_pct, 3),
        "avg_fill_ratio_per_location": round(avg_fill_ratio, 3),

        # Counts
        "n_locations_total": n_total,
        "n_locations_allocated": n_alloc,
        "n_unallocated_skus": 0 if unallocated_df is None else len(unallocated_df),
    }


def assign_initial_stock(
    parts,
    locations,
    total_capacity,
    max_random_tries_per_location=200,
    seed=None,
):
    """
    Random (chaotic) allocation at t=0, with caching.

    Goal:
      - Fill the warehouse as much as possible (assign as many locations as feasible).
      - Each location holds exactly one SKU type.
      - A SKU may appear in multiple locations.
      - If a SKU is assigned to a location, fill that location to MAX_UNITS for that SKU.

    Returns:
      locations, used_volume_mm3, unallocated_df, allocation_score
    """
    if seed is not None:
        random.seed(seed)

    used_volume_mm3 = 0.0
    fit_cache = {}

    # Sort locations by volume (largest first) – helps feasibility in Pass 1.
    locations_sorted = sorted(locations, key=lambda x: x["VOLUME_MM3"], reverse=True)

    # Sort SKUs by "difficulty" (largest dimension first) – helps coverage in Pass 1.
    parts_sorted = sorted(
        parts,
        key=lambda s: max(s["LEN_MM"], s["DEP_MM"], s["WID_MM"]),
        reverse=True,
    )

    unallocated_skus = []

    # ======================================================
    # PASS 1: ensure every SKU has at least one location (if possible)
    # ======================================================
    for sku in parts_sorted:
        sku_id = sku["ITEM_ID"]

        feasible_locs = []
        for loc in locations_sorted:
            if loc["ASSIGNED_SKU"] is not None:
                continue

            max_units, orientation, grid = _cached_capacity(loc, sku, fit_cache)
            if max_units > 0:
                feasible_locs.append((loc, max_units, orientation, grid))

        if not feasible_locs:
            unallocated_skus.append({
                "ITEM_ID": sku_id,
                "LEN_MM": sku["LEN_MM"],
                "DEP_MM": sku["DEP_MM"],
                "WID_MM": sku["WID_MM"],
                "VOLUME_MM3": sku["VOLUME_MM3"],
            })
            continue

        # chaotic: pick one feasible location at random
        loc, max_units, orientation, grid = random.choice(feasible_locs)

        init_units = int(max_units)
        stored_volume = init_units * float(sku["VOLUME_MM3"])

        full_layers, units_per_layer, partial_units = compute_actual_layout(init_units, grid)
        full_mtx, partial_mtx = build_actual_matrix(init_units, grid)

        loc.update({
            "ASSIGNED_SKU": sku_id,
            "MAX_UNITS": int(max_units),
            "INIT_UNITS": int(init_units),
            "CURRENT_STOCK": int(init_units),
            "ORIENTATION": orientation,
            "GRID": grid,
            "FULL_LAYERS": int(full_layers),
            "PARTIAL_UNITS": int(partial_units),
            "UNITS_PER_LAYER": int(units_per_layer),
            "FULL_LAYERS_MTX": full_mtx,
            "PARTIAL_LAYER_MTX": partial_mtx,
            "STORED_VOLUME_MM3": float(stored_volume),
        })

        used_volume_mm3 += stored_volume

    # ======================================================
    # PASS 2: fill remaining locations randomly as much as possible
    # ======================================================
    remaining_locations = [loc for loc in locations_sorted if loc["ASSIGNED_SKU"] is None]
    random.shuffle(remaining_locations)

    for loc in remaining_locations:
        placed = False

        # 1) Random tries (fast, chaotic)
        for _ in range(int(max_random_tries_per_location)):
            sku = random.choice(parts)

            max_units, orientation, grid = _cached_capacity(loc, sku, fit_cache)
            if max_units <= 0:
                continue

            init_units = int(max_units)
            stored_volume = init_units * float(sku["VOLUME_MM3"])

            full_layers, units_per_layer, partial_units = compute_actual_layout(init_units, grid)
            full_mtx, partial_mtx = build_actual_matrix(init_units, grid)

            loc.update({
                "ASSIGNED_SKU": sku["ITEM_ID"],
                "MAX_UNITS": int(max_units),
                "INIT_UNITS": int(init_units),
                "CURRENT_STOCK": int(init_units),
                "ORIENTATION": orientation,
                "GRID": grid,
                "FULL_LAYERS": int(full_layers),
                "PARTIAL_UNITS": int(partial_units),
                "UNITS_PER_LAYER": int(units_per_layer),
                "FULL_LAYERS_MTX": full_mtx,
                "PARTIAL_LAYER_MTX": partial_mtx,
                "STORED_VOLUME_MM3": float(stored_volume),
            })

            used_volume_mm3 += stored_volume
            placed = True
            break

        # 2) Deterministic fallback fill as much as possible with random allocations
        if not placed:
            shuffled_parts = parts[:] 
            random.shuffle(shuffled_parts)

            for sku in shuffled_parts:
                max_units, orientation, grid = _cached_capacity(loc, sku, fit_cache)
                if max_units <= 0:
                    continue

                init_units = int(max_units)
                stored_volume = init_units * float(sku["VOLUME_MM3"])

                full_layers, units_per_layer, partial_units = compute_actual_layout(init_units, grid)
                full_mtx, partial_mtx = build_actual_matrix(init_units, grid)

                loc.update({
                    "ASSIGNED_SKU": sku["ITEM_ID"],
                    "MAX_UNITS": int(max_units),
                    "INIT_UNITS": int(init_units),
                    "CURRENT_STOCK": int(init_units),
                    "ORIENTATION": orientation,
                    "GRID": grid,
                    "FULL_LAYERS": int(full_layers),
                    "PARTIAL_UNITS": int(partial_units),
                    "UNITS_PER_LAYER": int(units_per_layer),
                    "FULL_LAYERS_MTX": full_mtx,
                    "PARTIAL_LAYER_MTX": partial_mtx,
                    "STORED_VOLUME_MM3": float(stored_volume),
                })

                used_volume_mm3 += stored_volume
                placed = True
                break

        # if still not placed: that location is genuinely not feasible for any SKU

    unallocated_df = pd.DataFrame(unallocated_skus)

    allocation_score = _compute_allocation_score(
        locations=locations,
        total_capacity=total_capacity,
        used_volume_mm3=used_volume_mm3,
        unallocated_df=unallocated_df,
    )

    return locations, used_volume_mm3, unallocated_df, allocation_score
