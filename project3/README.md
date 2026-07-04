---

## Project 3: Algorithmic Trading Strategy & Backtesting Engine
**Status:** Validated / Production Ready

### 📊 System Operations & Risk Design
*   **Time-Series Imputation Pipeline:** Implements a strict Forward-Filling (`ffill`) data conditioning layer to repair NaN intervals without creating look-ahead verification bias.
*   **State Machine Crossover Core:** Codes a responsive 10-day and 50-day moving average entry engine conditioned to reject entry signals unless active inventory states are completely flat (`Position == 0`).
*   **Asymmetric Bracket Architecture:** Hardcodes an institutional 3:1 Reward-to-Risk bracket engine designed to automatically log Take-Profit and Stop-Loss boundaries upon entry execution.
*   **Dynamic Volatility Validation:** Bypasses destructive random cross-validation shuffling by applying an event-driven rolling Walk-Forward Optimization (WFO) processing split across a 5-year chronological window.
