# Cheatsheet

## Bootstrapping

### Q: Intermixing Treasuries and swaps for bootstrapping

- We can set up a swap that exchanges SOFR for the Treasury yield, and it is similar to borrowing at SOFR and investing in Treasuries.
- But we cannot mix them:
  - A Treasury is premium collateral with higher liquidity.
  - Synthetic instruments don't need an upfront payment like Treasuries do.
- So there is a swap spread: $S_{swap} - y_{treasury}$.

### Q: A piecewise-constant forward rate between nodes means $\log DF$ is linear between nodes. Why does that matter?

- It makes bootstrapping piecewise and locally solvable.
- Every new quote brings one forward quote that can be solved with no arbitrage.
- But this is what causes sudden jumps in the forward curve. DF remains continuous.

### Q: What exactly does bootstrapping get right, and what is an assumption?

- **Gets right:** the discount factor for all input contracts.
- **Assumed:** the forward rates connecting two contracts, along with any extrapolation.

### Note: Swap mechanism

- Swaps settle on T+2. The settlement date is called the swap date.
- We downloaded data on Oct 15 (Thu). Settlement is Oct 19 (Mon).
- We assume a constant discount rate between Oct 15 and 19.
- Day count convention used is ACT/360.
- We use modified following to calculate the payment dates (useful when the date falls on a weekend, a weekend that is also the last 1–2 days of the month).

