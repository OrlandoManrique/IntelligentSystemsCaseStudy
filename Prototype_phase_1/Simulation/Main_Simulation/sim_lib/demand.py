import numpy as np


def sample_demand(mean, abc_class):
    if mean <= 0:
        return 0

    if abc_class == "A":
        std = 0.2 * mean if mean > 0 else 1.0
        val = np.random.normal(loc=mean, scale=std)
    elif abc_class == "B":
        shape = 2.0
        scale = mean / shape if mean > 0 else 1.0
        val = np.random.gamma(shape, scale)
    else:
        val = np.random.exponential(scale=mean)

    qty = int(max(0, round(val)))
    return qty


def get_reorder_params(abc_class, max_capacity):
    if max_capacity <= 0:
        return 0, 0
    if abc_class == "A":
        rp = int(0.5 * max_capacity)
        target = int(0.9 * max_capacity)
    elif abc_class == "B":
        rp = int(0.4 * max_capacity)
        target = int(0.8 * max_capacity)
    else:
        rp = int(0.3 * max_capacity)
        target = int(0.7 * max_capacity)
    return rp, target


def sample_lead_time(abc_class):
    if abc_class == "A":
        return 2
    lt = int(max(1, round(np.random.normal(5.0, 3.5))))
    return lt

