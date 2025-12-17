# sim_lib/warehouse.py
from .data_loader import load_data
from .allocation import assign_initial_stock
from .simulation import build_sku_state, run_simulation
from .reporting import report_initial_state, report_simulation_results, export_allocations_csv



def main():
    # 1) Load data
    parts, part_meta, locations, total_capacity = load_data()

    # 2) Allocate initial stock
    locations, used_volume, unallocated_df = assign_initial_stock(parts, locations, total_capacity, target_utilization=0.5)

    if not unallocated_df.empty:
        from pathlib import Path

        base_path = Path(__file__).parent.parent
        out_path = base_path / "outputs"
        out_path.mkdir(exist_ok=True)

        csv_path = out_path / "unallocated_skus.csv"
        unallocated_df.to_csv(csv_path, index=False)

        print(f"\nUnallocated SKUs written to: {csv_path.resolve()}\n")
    else:
        print("\nAll SKUs were successfully allocated.\n")


    # 3) Report initial layout
    report_initial_state(locations, total_capacity, used_volume, max_print=50)
    export_allocations_csv(locations, filename="initial_allocations.csv")

    # 4) Build SKU state
    sku_state = build_sku_state(part_meta, locations)

    # 5) Run simulation (36 months)
    #print("\n--- START MONTHLY SIMULATION (36 MONTHS) ---\n")
   # kpi = run_simulation(sku_state, months=36)

    # 6) Report simulation results
    #report_simulation_results(kpi)


if __name__ == "__main__":
    main()
