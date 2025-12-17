# sim_lib/reporting.py
from .geometry import print_ascii_layer
import pandas as pd
from pathlib import Path


def report_initial_state(locations, total_capacity, used_volume, max_print=50):
    print("\n--- WAREHOUSE INITIALIZATION ---\n")

    allocated = [loc for loc in locations if loc["ASSIGNED_SKU"]]

    for i, loc in enumerate(allocated[:max_print], 1):
        nX, nY, nZ = loc["GRID"]

        layout_desc = f"{nX}x{nY}x{loc['FULL_LAYERS']}"
        if loc["PARTIAL_UNITS"] > 0:
            layout_desc += f" + {loc['PARTIAL_UNITS']} units on last layer"

        ox, oy, oz = loc["ORIENTATION"]

        print(
            f"{i}. Location: {loc['LOCATION_ID']} | Type: {loc['TYPE']} | "
            f"SKU: {loc['ASSIGNED_SKU']}\n"
            f"   Initial allocation: {loc['INIT_UNITS']}/{loc['MAX_UNITS']} units\n"
            f"   Grid capacity: {nX}x{nY}x{nZ}\n"
            f"   Allocation layout: {layout_desc}\n"
            f"   Orientation: (X={ox:.3f}, Y={oy:.3f}, Z={oz:.3f})"
        )

        if loc["PARTIAL_LAYER_MTX"] is not None:
            partial_index = loc["FULL_LAYERS"] + 1
            print(f"   Partial layer (Z = {partial_index}) in ASCII:")
            print_ascii_layer(loc["PARTIAL_LAYER_MTX"])
            print()
        else:
            print("All layers full.")
            print()

    util_pct = (used_volume / total_capacity) * 100 if total_capacity > 0 else 0.0

    print("\n--- INITIAL SUMMARY ---")
    print(f"Total rack volume: {total_capacity:.3f} m^3")
    print(f"Used volume: {used_volume:.3f} m^3")
    print(f"Utilization: {util_pct:.2f}%")
    print(f"Allocated locations: {len(allocated)}/{len(locations)}")

def export_allocations_csv(locations, filename="initial_allocation.csv"):
    """
    Exports one row per location with allocation + geometry info.
    """
    rows = []

    for loc in locations:
        if loc["ASSIGNED_SKU"] is None:
            continue

        nX, nY, nZ = loc["GRID"]
        ox, oy, oz = loc["ORIENTATION"]

        rows.append({
            "LOCATION_ID": loc["LOCATION_ID"],
            "LOCATION_TYPE": loc["TYPE"],
            "SKU": loc["ASSIGNED_SKU"],
            "INIT_UNITS": loc["INIT_UNITS"],
            "MAX_UNITS": loc["MAX_UNITS"],
            "CURRENT_STOCK": loc["CURRENT_STOCK"],
            "GRID_X": nX,
            "GRID_Y": nY,
            "GRID_Z": nZ,
            "FULL_LAYERS": loc["FULL_LAYERS"],
            "PARTIAL_UNITS": loc["PARTIAL_UNITS"],
            "ORIENT_X_M": ox,
            "ORIENT_Y_M": oy,
            "ORIENT_Z_M": oz,
            "LOCATION_VOL_M3": loc["VOLUME_M3"],
        })

    df = pd.DataFrame(rows)

    # Save to project root / outputs
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
