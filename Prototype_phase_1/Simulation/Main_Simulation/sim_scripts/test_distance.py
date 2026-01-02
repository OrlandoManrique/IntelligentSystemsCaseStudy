# sim_scripts/test_distance.py
from sim_lib.data_loader import load_data
from sim_lib.distance import manhattan_distance


def main():
    # Load locations + index (O(1) lookup by loc_inst_code)
    parts, part_meta, locations, total_capacity, locations_index = load_data()

    # ---- MANUAL TEST PAIRS (edit these) ----
    loc_a = "A1-00001"
    loc_b = "A2-00092"

    # Example: uncomment and set a second test if you want
    # loc_c = "PUT_LOC_ID_HERE_3"
    # loc_d = "PUT_LOC_ID_HERE_4"

    # Compute & print Manhattan distance
    d_ab = manhattan_distance(loc_a, loc_b, locations_index)
    d_ab_m = round(d_ab / 1000.0,3)  # convert to meters
    print(f"Manhattan distance between '{loc_a}' and '{loc_b}': {d_ab_m:.3f} m")



if __name__ == "__main__":
    main()
