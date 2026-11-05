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
- But this is what causes sudden jumps in it.

### Q: What exactly does bootstrapping get right, and what is an assumption?

- **Gets right:** the discount factor for all existing contracts.
- **Assumed:** the forward rates connecting two contracts, along with any extrapolation.
