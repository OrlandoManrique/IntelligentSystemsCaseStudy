TEST 02: SAFETY PROTOCOL (Hard Constraint Check)

SCENARIO:
- 3 Heavy Items (25kg) are currently located at Z=2000mm (Above the 1500mm safety limit).
- 3 Light Items (1kg) are located at Z=500mm.
- The Spec defines Weight > 15kg above 1500mm as a Hard Constraint violation (-10,000 pts).

SUCCESS CRITERIA:
- In final_allocations.csv, Items 9001-9003 (Heavy) MUST be in locations L-LOW-1 to L-LOW-3.
- If the heavy items remain in L-HIGH, the test fails (Constraint Logic Failure).
