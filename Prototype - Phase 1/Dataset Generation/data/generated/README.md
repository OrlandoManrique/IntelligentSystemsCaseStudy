# Warehouse Dataset – First Version

This folder contains a **first-version dataset** for warehouse storage allocations. The dataset includes item details, warehouse location types, instantiated locations, and preliminary allocations. It is intended for team members to explore and use the data.

---

## **1. parts.csv**

**Description:** Details of warehouse items.
**Columns:**

| Column        | Description                          |
| ------------- | ------------------------------------ |
| ITEM_ID       | Unique identifier for the item       |
| ITEM_DESC     | Item description                     |
| WT_KG         | Weight of a single unit in kilograms |
| QTY_PER_BOX   | Number of units per box              |
| BOXES_ON_HAND | Number of boxes currently in stock   |
| DEMAND        | Customer demand for this item        |
| LEN_MM        | Item length in millimeters           |
| WID_MM        | Item width in millimeters            |
| DEP_MM        | Item depth in millimeters            |

**Notes:**

* Item dimensions are used to determine suitable storage locations.

---

## **2. location_types.csv**

**Description:** Warehouse location types and their dimensions.
**Columns:**

| Column   | Description                           |
| -------- | ------------------------------------- |
| LOC_CODE | Location type identifier              |
| WID_MM   | Width of the location in millimeters  |
| HT_MM    | Height of the location in millimeters |
| DEP_MM   | Depth of the location in millimeters  |

**Notes:**

* Locations are fixed-size storage slots.
* Items are allocated only to locations that can fit them.

---

## **3. locations.csv**

**Description:** Instantiated storage locations in the warehouse.
**Columns:**

| Column        | Description                                            |
| ------------- | ------------------------------------------------------ |
| LOC_INST_CODE | Unique instance code for this location (e.g., 001-001) |
| LOC_TYPE      | Type of location (from `location_types.csv`)           |

**Notes:**

* Each location instance holds only **one item type**.
* Multiple instances of the same type may exist to accommodate all units of an item.

---

## **4. allocations.csv**

**Description:** Preliminary allocations of items to locations.
**Columns:**

| Column                 | Description                                             |
| ---------------------- | ------------------------------------------------------- |
| ITEM_ID                | ID of the item being stored                             |
| LOC_CODE               | Location instance where item is stored                  |
| UNITS_ALLOCATED        | Number of units allocated to this location              |
| VOLUME_UTILIZATION (%) | Percentage of the location volume occupied by this item |

**Notes:**

* Allocations are based on volume-fitting rules.
* Each location holds only one item type.
* Items may occupy multiple locations if needed.

---

**Additional Notes:**

* All CSV files use **semicolon (`;`) delimiters** for Excel compatibility.
* This dataset is a **first-version dataset**; allocations are preliminary and may need refinement.

**End of README**
