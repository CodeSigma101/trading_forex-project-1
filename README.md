# Decode Labs Master Portfolio Suite
####Link : https://tradingforex-project-1-nvqobaxwkkhlrug5gglevx.streamlit.app/
### Comprehensive 4-Project Quantitative Internship Workspace Profile

This interactive suite wraps four individual algorithmic and fundamental financial engines into a unified web application dashboard.

---

## 📊 Project 1: Price Action Engine
*   **Microstructure Extraction:** Quantifies raw candlestick wick-to-body ratios ($R_{wb}$) at key structural zones without relying on lagging indicators.
*   **Capital Protection:** Enforces automated risk circuit breakers, utilizing the Half-Size Rule to scale order risk down by 50% after consecutive losing outcomes.

## 🔬 Project 2: Fundamental DCF Core
*   **Financial Statement Ingestion:** Extracts raw financial metrics directly from official corporate 10-K and 10-Q regulatory filings.
*   **Multi-Scenario Discounting:** Implements an iterative 5-year outlook using a rigid 9.9% Weighted Average Cost of Capital (WACC) discount hurdle rate.
*   **Gatekeeper Margin of Safety:** Enforces a strict 30% safety discount to isolate true capital entry targets, outputting a defensive `STRONG SELL` verdict under market premiums.

## ⚡ Project 3: Algorithmic Backtester
*   **Time-Series Conditioning:** Employs a strict forward-filling (`ffill`) data imputation filter to resolve NaN intervals without creating lookahead validation leakage.
*   **Asymmetric Bracket Management:** Coordinates automated entry setups using responsive moving average crossovers paired with a fixed 3:1 Reward-to-Risk bracket layout.

## 🛡️ Project 4: MPT Risk Allocator
*   **Covariance Variance Core:** Applies Modern Portfolio Theory linear algebra across uncorrelated sectors to lower unsystematic portfolio variance.
*   **Systemic Volatility Cap:** Measures individual asset market betas relative to the S&P 500 index to constrain the weighted portfolio beta strictly under 1.0 ($\beta_p < 1.0$).
*   **Aggregate Heat Protection:** Limits cumulative capital exposure to a maximum 8.0% loss threshold, ensuring 92.45% of core equity is structurally insulated against market shocks.
