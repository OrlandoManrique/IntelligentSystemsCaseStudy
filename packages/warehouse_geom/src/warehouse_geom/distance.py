# sim_lib/distance.py
def manhattan_distance(loc_a_id, loc_b_id, locations_index):
    """
    Manhattan distance between two locations, using their millimeter coordinates.

    Args:
      loc_a_id (str): loc_inst_code of location A
      loc_b_id (str): loc_inst_code of location B
      locations_index (dict): {loc_id: location_dict}, where location_dict contains: POS_X_MM, POS_Y_MM, POS_Z_MM

    Returns:
      float: Manhattan distance in millimeters.

    Raises:
      KeyError: if a location ID is not found in locations_index
    """
    if loc_a_id not in locations_index:
        raise KeyError(f"Location '{loc_a_id}' not found in locations_index.")
    if loc_b_id not in locations_index:
        raise KeyError(f"Location '{loc_b_id}' not found in locations_index.")

    a = locations_index[loc_a_id]
    b = locations_index[loc_b_id]

    dx = abs(int(a["POS_X_MM"]) - int(b["POS_X_MM"]))
    dy = abs(int(a["POS_Y_MM"]) - int(b["POS_Y_MM"]))
    dz = abs(int(a["POS_Z_MM"]) - int(b["POS_Z_MM"]))

    return float(dx + dy + dz)
