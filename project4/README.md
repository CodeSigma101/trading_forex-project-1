---

## Project 4: Portfolio Optimization & Risk Management Engine
**Status:** Validated / Production Ready / Core Milestone Met

### 📊 Macro Ecosystem Architecture
*   **MPT Covariance Core:** Implements specialized linear algebra matrix formulas to minimize total unsystematic portfolio variance across uncorrelated sectors.
*   **Systemic Risk Gatekeeper:** Calculates individual asset market betas relative to the S&P 500 index to constrain the weighted portfolio beta strictly under 1.0 ($\beta_p < 1.0$).
*   **Fixed Fractional Sizing Funnel:** Sets absolute risk limits capped strictly at 2% of equity per trade, using adaptive unit scaling to keep absolute dollar risk perfectly constant during periods of high market volatility.
*   **Total Portfolio Heat Latch:** Enforces a protective global risk safety ceiling of 7.55%, guaranteeing that 92.45% of the capital base is structurally protected against unexpected market events.
