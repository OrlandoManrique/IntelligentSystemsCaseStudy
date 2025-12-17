# sim_lib/geometry.py
import math
from itertools import permutations


def compute_layered_capacity(loc_dims, sku_dims):
    """
    loc_dims = [LX, LY, LZ]
    sku_dims = [sx, sy, sz]
    Returns:
      max_units, best_orientation, (nX, nY, nZ)
    """
    LX, LY, LZ = loc_dims

    max_units = 0
    best_orientation = None
    best_grid = (0, 0, 0)

    for sx, sy, sz in permutations(sku_dims):
        nX = int(LX // sx)
        nY = int(LY // sy)
        base_units = nX * nY
        if base_units == 0:
            continue

        nZ = int(LZ // sz)
        if nZ == 0:
            continue

        total_units = base_units * nZ
        if total_units > max_units:
            max_units = total_units
            best_orientation = (sx, sy, sz)
            best_grid = (nX, nY, nZ)

    return max_units, best_orientation, best_grid


def compute_actual_layout(init_units, max_grid):
    nX, nY, nZ = max_grid
    units_per_layer = nX * nY

    if units_per_layer == 0:
        return 0, units_per_layer, init_units

    full_layers = init_units // units_per_layer
    partial_units = init_units % units_per_layer

    return full_layers, units_per_layer, partial_units


def build_actual_matrix(init_units, max_grid):
    """
    Returns full_layers (list of layers) and one partial_layer matrix.
    Each layer is a nY x nX grid with 1 = filled, 0 = empty.
    """
    nX, nY, nZ = max_grid
    units_per_layer = nX * nY

    full_layers_count = 0
    remaining = init_units

    if units_per_layer > 0:
        full_layers_count = init_units // units_per_layer
        remaining = init_units % units_per_layer

    full_layers = []
    for _ in range(full_layers_count):
        layer = [[1] * nX for _ in range(nY)]
        full_layers.append(layer)

    partial_layer = None
    if remaining > 0:
        partial_layer = []
        units_left = remaining
        for row in range(nY):
            row_vals = []
            for col in range(nX):
                if units_left > 0:
                    row_vals.append(1)
                    units_left -= 1
                else:
                    row_vals.append(0)
            partial_layer.append(row_vals)

    return full_layers, partial_layer


def print_ascii_layer(layer):
    if not layer:
        return
    for row in layer:
        print("      " + "".join("[X]" if cell == 1 else "[ ]" for cell in row))
