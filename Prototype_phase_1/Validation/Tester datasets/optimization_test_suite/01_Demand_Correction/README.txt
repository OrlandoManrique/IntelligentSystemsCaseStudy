TEST 01: DEMAND CORRECTION (Efficiency Check)

SCENARIO:
- 5 "Class A" items (High Demand) are currently stored at the back of the warehouse (X=2000).
- 5 "Class C" items (Low Demand) are currently stored at the entrance (X=0).
- All items fit in all bins. All weights are safe.

SUCCESS CRITERIA:
- In final_allocations.csv, Items 1001-1005 (Class A) should be in locations L-FAST-1 to L-FAST-5.
- Items 2001-2005 (Class C) should be moved to L-SLOW-1 to L-SLOW-5.
- This proves the engine prioritizes Pick Velocity logic.
