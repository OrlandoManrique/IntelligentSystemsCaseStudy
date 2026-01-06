* warehouse_geom
    │   pyproject.toml
    │   README.md
    │
    └───src
        ├───warehouse_geom
        │   │   allocation.py
        │   │   api.py
        │   │   data_loader.py
        │   │   distance.py
        │   │   geometry.py
        │   │   __init__.py
        │   │
        │   └───__pycache__
        │           __init__.cpython-313.pyc
        │
        └───warehouse_geom.egg-info
                dependency_links.txt
                PKG-INFO
                SOURCES.txt
                top_level.txt

* Modules and Functions

1) Module data_loader

* Function load_data()

Loads parts (SKUs) and locations from CSV files and prepares in-memory data structures.

Returns

parts, part_meta, locations, total_capacity, locations_index


parts – list of SKU dictionaries

part_meta – lookup dict {ITEM_ID → pandas row}

locations – list of slot dictionaries

total_capacity – total warehouse volume (mm³)

locations_index – {LOCATION_ID → location_dict} for O(1) access

Notes

Enforces presence of BOXES_ON_HAND

Computes SKU volume

Adds ABC classification based on demand


2) Module geometry.py

* Function compute_layered_capacity(loc_dims, sku_dims)

Computes the maximum number of units of a SKU that fit in a location.

Inputs

loc_dims: [LX, LY, LZ] (mm)

sku_dims: [sx, sy, sz] (mm)

Outputs

max_units, best_orientation, (nX, nY, nZ)


max_units – maximum number of units that fit

best_orientation – SKU orientation (sx, sy, sz)

(nX, nY, nZ) – grid dimensions

Returns (0, None, (0,0,0)) if the SKU cannot fit in any orientation.



* Function compute_actual_layout(init_units, max_grid)

Converts a number of units into full layers and a partial layer.

Outputs

full_layers, units_per_layer, partial_units


* Function build_actual_matrix(init_units, max_grid)

Builds explicit 2D matrices representing filled layers.

Outputs

full_layers, partial_layer


Used mainly for debugging and visualization.

print_ascii_layer(layer)

Pretty-prints a single layer as ASCII.


3) Module distance.py

* Function manhattan_distance(loc_a_id, loc_b_id, locations_index)

Computes Manhattan distance between two locations.

Inputs

loc_a_id, loc_b_id

locations_index from load_data()

Output

Distance in mm

4) Module allocation.py

* Function assign_initial_stock(...)

Performs a geometry-constrained initial allocation of inventory at t = 0.

Purpose
Allocate available stock (BOXES_ON_HAND) into feasible locations until:

stock is exhausted, or

no feasible/free locations remain.

Inputs

assign_initial_stock(
    parts,
    locations,
    total_capacity,
    max_random_tries_per_location=200,
    seed=None
)


Outputs

locations, used_volume_mm3, unallocated_df, allocation_score


locations – updated location list (mutated)

used_volume_mm3 – total allocated volume

unallocated_df – DataFrame of SKUs with remaining stock

allocation_score – KPI summary dict

Behavior

SKUs are processed largest-dimension first

Allocation spills across multiple locations if needed

Strictly respects geometry and stock availability

Detects infeasible SKUs

Finds reasons for Unallocated SKUs

Unallocated SKUs are classified explicitly:

NO_FEASIBLE_FIT_ANYWHERE
SKU cannot fit in any warehouse location.

NO_FREE_LOCATIONS
Warehouse is full (no empty slots left).

NO_FEASIBLE_FIT_IN_AVAILABLE_SLOTS
SKU could fit in the warehouse, but not in the remaining free slots.
