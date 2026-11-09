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
- Every new quote brings one new unknown that can be solved with no arbitrage.
- But this is what causes sudden jumps in the forward curve. DF remains continuous.

### Q: What exactly does bootstrapping get right, and what is an assumption?

- **Gets right:** the discount factor for all input contracts.
- **Assumed:** the forward rates connecting two contracts, along with any extrapolation.

### Note: Swap mechanism

- Swaps settle on T+2. The settlement date is called the spot date.
- We downloaded data on Oct 15 (Thu). Settlement is Oct 19 (Mon).
- We assume a constant discount rate between Oct 15 and 19.
- Day count convention used is ACT/360.
- We use modified following to calculate the payment dates (useful when the date falls on a weekend, a weekend that is also the last 1–2 days of the month).

### Note: Less than a year

- When bootstrapping, we don't bootstrap less than a year because there is no coupon provided.
- Those are considered as individual discount factors.
- The PV of \$1 invested in SOFR remains \$1. Coupons are provided so as to maintain its invested value.
- If we don't add less than a year to bootstrap, then there are no nodes there and cashflows there are a guess. This matters for CVA as well, since early exposures use the short end of the curve.
- We assume annual bootstrapping dates are consecutive (1Y, 2Y, ..., 10Y). The 1W–11M quotes are added on top. 18M and anything past 10Y are not used yet.

### Note: Bloomberg rounding

- Bloomberg rounds its DF to 6 decimals. Since we are using \$100M notional, no implementation can beat $10^{-6} \times$ \$100M = \$100 rounding error.

## Swaps

- Assume that start and end are the same date and month; only the year changes.
- Although payment dates run from 2027, we store dates from 2026 because we need it to calculate the forward rate.
- In interest rate swaps the floating leg (when constructed off the SOFR curve) is a telescoping sum and cancels out. So Floating leg = $1 - DF(0, T_n)$ (per unit notional, for a swap starting at spot). For the Oracle swap starting 10/15 it is $DF_c(s_0) - DF_c(s_n)$. But in our code we consider the fact that payment date and accrual date are different. So they don't cancel out.
- Compared to Bloomberg SWPM, year 2 and 3 values are off; this is because we didn't bootstrap the 18M values. Despite this, NPV comes out right (thanks to the telescoping property). The wrong DF at 2028-10-16 pushes the year 2 and year 3 forwards in opposite directions, so they nearly cancel. Not exactly, because of the pay delay.

### 2 ways to see DV01 of a bond

- From a derivatives perspective we write it as $PV_{bumped} - PV$. But since DV01 is sensitivity to rate changes, in order to maintain duration conventions (i.e. -ve value change) we will use $PV - PV_{bumped}$
- DV01 of payer and receiver are the same magnitude, opposite in sign.
- If payment was made on accrual date, the positive position becomes more positive and negative position becomes more negative (i.e. both increase in magnitude)
- At par, receiver DV01 can be estimated as $N A \frac{dS}{dr}$. If it is not at par we need to add adjustment of $-N (K-S) \frac{dA}{dr}$, i.e. for off-market swaps a rate shift moves the annuity too.
- A receiver swap has approx the same DV01 as a long term bond cuz a receiver swap can be thought of as longing a bond and shorting a floater. A floater has no rate risk so almost all of rate risk comes from the bond.

## Hull–White

- Short rates are not observable. Limit of forward rate is the short rate.
- Taking $E^Q[r_T]$ doesn't give the forward rate $f(0, T)$, but it does under the T-forward measure: $f(0, T) = E^{Q_T}[r_T]$. Under $Q$ they differ by a convexity term.
- The problem with HW1F is that it models all rates as perfectly correlated (one factor), which is unrealistic.
- We use Hull–White instead of Vasicek because the reverting mean level can vary with time. This degree of freedom lets us model the whole curve.
- We use convention ACT/365 here (compared to ACT/360 for bootstrapping and schedule build).
- Hull–White can be decomposed as $\alpha(t) + x(t)$. $x(t)$ is a mean 0, mean-reverting random process. $\alpha(t)$ = forward + convexity correction.

### Q: Why does $\theta_t$ blow up? Do the numbers, then say whether $\theta_t$ is even defined for this curve.

- $\theta_t$ depends on the derivative $\partial f/\partial t$ and this blows up at the nodes for a bootstrapped curve. So $\theta_t$ isn't properly defined at the nodes but is an ordinary function elsewhere (and $\partial f/\partial t = 0$).
- Note that the size of the spike is just an artifact. The width of time step $h$ determines the spike.

### Q: Why is there only one spike when the curve has about 20 nodes? What would that mean if you simulated with $\theta_t$?

- It's pure coincidence. It depends on where the nodes land. If the node is part of the pts used to calculate $\partial f/\partial t$ then we will see a spike at those points.
- If we simulated with $\theta_t$, each jump is hit or missed depending on where the grid points land, so the model won't reprice the curve.

### Q: Why is $\alpha(t)$ above $f(0,t)$, with the gap growing over time?

- It is due to Jensen's inequality. $E[e^{-\int_0^t r_s ds}] \ge e^{-E[\int_0^t r_s ds]}$ and the gap keeps growing with $t$. $\alpha(t)$ has to sit above $f(0,t)$ to make up for the gap, so the model still reprices $DF(0, t)$.

### Q: Why simulate with $x_t + \alpha(t)$ rather than $\theta_t$?

- It's because as we saw $\theta_t$ needs calculation of $\partial f/\partial t$, which isn't defined at the nodes for a piecewise-flat forward curve. $\alpha(t)$ only needs $f$ itself. $x_t$ also doesn't contain discretization error (if we use the exact OU step) but if we use $\theta_t$ we get discretization error as well.

### Q: Why Hull–White rather than Vasicek for pricing?

- Vasicek has only 3 parameters. It won't be able to fit the entire forward curve. HW1F has time-varying $\theta$ as a param and hence can fit the entire curve.

### Q: Rates can go negative in Hull–White. Does that matter for CVA on a swap?

- Rates can go negative (e.g. EUR and JPY), so HW1F makes sense. For a receiver swap, value increases when rates fall, so ignoring negative rates makes us underestimate expected exposure. At the same time using HW1F causes the short rates to be a Gaussian around $\alpha(t)$ and this can put more weight on very negative rates than the real world does. We will know which model is true representation only when we consider deep receiver swaps. Since we use only ATM this can't be inferred.
