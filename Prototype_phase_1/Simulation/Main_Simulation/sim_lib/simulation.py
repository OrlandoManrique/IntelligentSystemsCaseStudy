from .demand import sample_demand, get_reorder_params, sample_lead_time


def build_sku_state(part_meta, locations):
    """
    Creates sku_state from part_meta and allocated locations.
    """
    sku_state = {}

    for loc in locations:
        sku_id = loc["ASSIGNED_SKU"]
        if sku_id is None:
            continue

        meta = part_meta.get(sku_id)
        if meta is None:
            continue

        if sku_id not in sku_state:
            sku_state[sku_id] = {
                "ABC": meta["ABC_CLASS"],
                "mean_demand": float(meta["DEMAND"]),
                "locations": [],
                "total_stock": 0,
                "max_capacity": 0,
                "open_orders": [],
            }

        state = sku_state[sku_id]
        state["locations"].append(loc)
        state["total_stock"] += loc["CURRENT_STOCK"]
        state["max_capacity"] += loc["MAX_UNITS"]

    return sku_state


def consume_stock(item_id, qty, sku_state):
    if qty <= 0 or item_id not in sku_state:
        return 0, qty

    state = sku_state[item_id]
    remaining = qty
    shipped = 0

    for loc in state["locations"]:
        if remaining <= 0:
            break
        available = loc["CURRENT_STOCK"]
        if available <= 0:
            continue
        take = min(available, remaining)
        loc["CURRENT_STOCK"] -= take
        state["total_stock"] -= take
        shipped += take
        remaining -= take

    lost = remaining
    return shipped, lost


def add_stock(item_id, qty, sku_state):
    if qty <= 0 or item_id not in sku_state:
        return 0

    state = sku_state[item_id]
    remaining = qty
    added = 0

    for loc in state["locations"]:
        if remaining <= 0:
            break
        cap = loc["MAX_UNITS"]
        cur = loc["CURRENT_STOCK"]
        free = cap - cur
        if free <= 0:
            continue
        put = min(free, remaining)
        loc["CURRENT_STOCK"] += put
        state["total_stock"] += put
        remaining -= put
        added += put

    return added


def run_simulation(sku_state, months=36):
    """
    Monthly simulation with demand + replenishment.
    Returns KPI dict per SKU.
    """
    kpi = {
        item_id: {"demand": 0, "shipped": 0, "lost": 0}
        for item_id in sku_state.keys()
    }

    for month in range(1, months + 1):

        # 1) Process arriving orders
        for item_id, state in sku_state.items():
            if not state["open_orders"]:
                continue

            arriving = [o for o in state["open_orders"] if o["arrival"] == month]
            still_open = [o for o in state["open_orders"] if o["arrival"] > month]

            for order in arriving:
                add_stock(item_id, order["qty"], sku_state)

            state["open_orders"] = still_open

        # 2) Demand & shipment
        for item_id, state in sku_state.items():
            mean_d = state["mean_demand"]
            abc = state["ABC"]

            demand = sample_demand(mean_d, abc)
            shipped, lost = consume_stock(item_id, demand, sku_state)

            kpi[item_id]["demand"] += demand
            kpi[item_id]["shipped"] += shipped
            kpi[item_id]["lost"] += lost

        # 3) Replenishment decisions
        for item_id, state in sku_state.items():
            max_cap = state["max_capacity"]
            if max_cap <= 0:
                continue

            rp, target = get_reorder_params(state["ABC"], max_cap)

            if state["total_stock"] <= rp and len(state["open_orders"]) == 0:
                order_qty = max(0, target - state["total_stock"])
                if order_qty > 0:
                    lt = sample_lead_time(state["ABC"])
                    arrival = month + lt
                    state["open_orders"].append({"qty": order_qty, "arrival": arrival})

    return kpi
