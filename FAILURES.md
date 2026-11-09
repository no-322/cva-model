# Failures log

| symptom | cause | fix | lesson |
|---------|-------|-----|--------|
| Swap float rows 1–2 off ~$3,400 vs SWPM | No curve nodes before 1Y; the first period ends before the first node | Add 1WK–12M quotes | Anything before the first node is extrapolation |
| Swap float rows 2–3 off ~$160–230 vs SWPM. Effect on NPV < $100 | No 18M node. Interpolated between year 1 and 2 | Not fixed yet (add 18M later) | |
