TEST 03: VOLUMETRIC UTILIZATION (Scoring Logic)

SCENARIO:
- Item TINY_1 (Volume 1,000) is sitting in L-HUGE-1 (Volume 1,000,000). Utilization score is near 0.
- Location L-SMALL-1 (Volume 8,000) is currently empty.
- Items HUGE_1 and HUGE_2 are in the parts list but currently unallocated.

SUCCESS CRITERIA:
- The engine should move TINY_1 from L-HUGE-1 to L-SMALL-1.
- Why? Because (1000/8000 * 800) >> (1000/1000000 * 800).
- This frees up L-HUGE-1 for the larger items (HUGE_1).
- If TINY_1 remains in L-HUGE-1, the utilization logic is weak.
