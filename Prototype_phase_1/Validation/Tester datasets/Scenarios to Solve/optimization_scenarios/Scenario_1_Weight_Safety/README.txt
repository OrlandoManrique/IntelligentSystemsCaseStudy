SCENARIO 1: WEIGHT SAFETY PROTOCOL
----------------------------------
OBJECTIVE:
Verify Hard Constraint: Items > 15kg must not be stored above Z = 1500mm.

INPUT STATE:
1. '99-HEAVY' (20kg) is at A1-00016 (Z=1950mm). VIOLATION.
2. '11-LIGHT' (0.5kg) is at A1-00001 (Z=0mm). Safe.

EXPECTED OUTPUT:
- 99-HEAVY moves down.
