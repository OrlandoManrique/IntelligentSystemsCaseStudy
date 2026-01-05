# sim_lib/reporting.py
from .geometry import print_ascii_layer
import pandas as pd
from pathlib import Path

MM3_TO_M3 = 1e-9

def report_initial_state(locations, total_capacity, used_volume, max_print=10):
    print("\n--- WAREHOUSE INITIALIZATION (first 10 SKUs)---\n")

    allocated = [loc for loc in locations if loc["ASSIGNED_SKU"]]

    for i, loc in enumerate(allocated[:max_print], 1):
        nX, nY, nZ = loc["GRID"]
        ox, oy, oz = loc["ORIENTATION"]

        layout_desc = f"{nX} x {nY} x {loc['FULL_LAYERS']}"
        if loc["PARTIAL_UNITS"] > 0:
            layout_desc += f" + {loc['PARTIAL_UNITS']} units on last layer"

        print(
            f"{i}. Location: {loc['LOCATION_ID']} | Type: {loc['TYPE']} | "
            f"SKU: {loc['ASSIGNED_SKU']}\n"
            f"   Slot position (mm): "
            f"X={loc['POS_X_MM']}, Y={loc['POS_Y_MM']}, Z={loc['POS_Z_MM']}\n"
            f"   Initial allocation: {loc['INIT_UNITS']} / {loc['MAX_UNITS']} units\n"
            f"   Grid capacity (X x Y x Z): {nX} x {nY} x {nZ}\n"
            f"   Allocation layout: {layout_desc}\n"
            f"   Product orientation (mm): "
            f"(X={int(ox)}, Y={int(oy)}, Z={int(oz)})"
        )

        if loc["PARTIAL_LAYER_MTX"] is not None:
            partial_index = loc["FULL_LAYERS"] + 1
            print(f"   Partial layer (Z = {partial_index}) in ASCII:")
            print_ascii_layer(loc["PARTIAL_LAYER_MTX"])
            print()
        else:
            print("   All layers full.\n")

    util_pct = (used_volume / total_capacity) * 100 if total_capacity > 0 else 0.0

    #print("\n--- INITIAL SUMMARY ---")
    #print(f"Total rack volume: {round(total_capacity * MM3_TO_M3, 3)} m³")
    #print(f"Used volume:       {round(used_volume * MM3_TO_M3, 3)} m³")
    #print(f"Utilization:       {round(util_pct, 3)} %")
    #print(f"Allocated locations: {len(allocated)} / {len(locations)}")


def export_allocations_csv(locations, filename="allocation.csv"):
    """
    Exports one row per location with allocation + geometry info.
    """
    rows = []

    for loc in locations:
        if loc["ASSIGNED_SKU"] is None:
            continue

        nX, nY, nZ = loc["GRID"]
        ox, oy, oz = loc["ORIENTATION"]

        # Precompute per-slot volume utilization
        location_vol_mm3 = float(loc["VOLUME_MM3"])
        stored_vol_mm3 = float(loc.get("STORED_VOLUME_MM3", 0.0))
        util_ratio = (stored_vol_mm3 / location_vol_mm3) if location_vol_mm3 > 0 else 0.0
        util_pct = util_ratio * 100.0

        rows.append({
            "loc_inst_code": loc["LOCATION_ID"],
            "LOCATION_TYPE": loc["TYPE"],
            "ITEM_ID": loc["ASSIGNED_SKU"],

            # Position
            #"POS_X_MM": loc["POS_X_MM"],
            #"POS_Y_MM": loc["POS_Y_MM"],
            #"POS_Z_MM": loc["POS_Z_MM"],

            # Stock
            "QTY_ALLOCATED": loc["INIT_UNITS"],
            #"CURRENT_STOCK": loc["CURRENT_STOCK"],
            "MAX_UNITS": loc["MAX_UNITS"],

            # Geometry
            "GRID_X": nX,
            "GRID_Y": nY,
            "GRID_Z": nZ,
            "FULL_LAYERS": loc["FULL_LAYERS"],
            "PARTIAL_UNITS": loc["PARTIAL_UNITS"],

            # Orientation
            "ORIENT_X_MM": ox,
            "ORIENT_Y_MM": oy,
            "ORIENT_Z_MM": oz,

            # Volume
            "LOCATION_VOL_MM3": round(loc["VOLUME_MM3"],1),
            "LOCATION_VOL_M3": round(loc["VOLUME_MM3"] * MM3_TO_M3, 1),
            "STORED_VOL_M3": round(loc.get("STORED_VOLUME_MM3", 0.0) * MM3_TO_M3, 1),
            "UTILIZATION_PCT": round(util_pct, 1),
        })

    df = pd.DataFrame(rows)

    base_path = Path(__file__).parent.parent
    out_path = base_path / "outputs"
    out_path.mkdir(exist_ok=True)

    csv_path = out_path / filename
    df.to_csv(csv_path, index=False)

    print(f"\nAllocation CSV written to: {csv_path.resolve()}\n")


def report_simulation_results(kpi):
    print("\n--- SIMULATION SUMMARY ---")

    total_demand = sum(v["demand"] for v in kpi.values())
    total_shipped = sum(v["shipped"] for v in kpi.values())
    total_lost = sum(v["lost"] for v in kpi.values())

    print(f"SKUs simulated: {len(kpi)}")
    print(f"Total demand:   {total_demand}")
    print(f"Total shipped:  {total_shipped}")
    print(f"Total lost:     {total_lost}")

    if total_demand > 0:
        service_level = 100.0 * total_shipped / total_demand
        print(f"Fill rate (service level): {service_level:.2f}%")
    else:
        print("No demand generated.")
