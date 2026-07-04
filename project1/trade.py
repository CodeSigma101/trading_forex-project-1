import numpy as np
import pandas as pd
import yfinance as yf


# ==========================================
# LAYER 1: DATA INGESTION & TECHNICAL CALCULATIONS
# ==========================================
def fetch_market_data(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Fetches clean historical candle records via yfinance API."""
    # group_by="column" and multi_level_index=False configures a clean flat column index
    df = yf.download(
        ticker,
        start=start_date,
        end=end_date,
        multi_level_index=False,
        progress=False,
    )
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df


def engineer_technical_features(df: pd.DataFrame) -> pd.DataFrame:
    """Calculates absolute price rejection (R_wb), EMAs, and RSI tracking."""
    df = df.copy()

    # 1. Calculate Wick-to-Body Ratio (R_wb)
    high_max_oc = df["High"] - df[["Open", "Close"]].max(axis=1)
    min_oc_low = df[["Open", "Close"]].min(axis=1) - df["Low"]
    body_abs = (df["Open"] - df["Close"]).abs()

    df["R_wb"] = (high_max_oc + min_oc_low) / body_abs.replace(0, np.nan)
    df["R_wb"] = df["R_wb"].fillna(0)

    # 2. Structural Trend Filters (Slate Blue 50 EMA & Amber 200 EMA)
    df["EMA_50"] = df["Close"].ewm(span=50, adjust=False).mean()
    df["EMA_200"] = df["Close"].ewm(span=200, adjust=False).mean()

    # 3. Momentum Confirmation (14-Period RSI Filter)
    delta = df["Close"].diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1 / 14, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1 / 14, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    df["RSI"] = 100 - (100 / (1 + rs))
    df["RSI"] = df["RSI"].fillna(50)

    return df


# ==========================================
# LAYER 2: RISK ENGINE & MANAGEMENT PATTERNS
# ==========================================
class BacktestRiskManager:

    def __init__(self, initial_capital: float, max_daily_loss: float):
        """Initializes account health bars and positioning metrics."""
        self.initial_capital = initial_capital
        self.current_balance = initial_capital
        self.max_daily_loss = max_daily_loss

        self.consecutive_losses = 0
        self.peak_balance = initial_capital
        self.max_drawdown = 0.0
        self.size_multiplier = 1.0
        self.is_locked = False

    def check_preflight_risk(self) -> str:
        """Determines if the account state is cleared for execution."""
        current_drawdown = self.peak_balance - self.current_balance
        if current_drawdown >= (self.max_daily_loss * 0.70):
            self.is_locked = True
            return "LOCKED"
        if current_drawdown >= (self.max_daily_loss * 0.50):
            return "HALTED"
        if self.is_locked:
            return "LOCKED"
        return "OPERATIONAL"

    def update_account_metrics(self, trade_pnl: float):
        """Updates internal equity curves, counters, and sizing constraints."""
        self.current_balance += trade_pnl
        if self.current_balance > self.peak_balance:
            self.peak_balance = self.current_balance

        # Track absolute trailing portfolio strategy drawdown
        current_drawdown = self.peak_balance - self.current_balance
        if current_drawdown > self.max_drawdown:
            self.max_drawdown = current_drawdown

        # Half-Size Position Scaling Rule Matrix
        if trade_pnl < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0

        if self.consecutive_losses >= 2:
            self.size_multiplier = 0.50
        else:
            self.size_multiplier = 1.0


# ==========================================
# LAYER 3: QUANTITATIVE HISTORICAL BACKTESTER
# ==========================================
def run_system_backtest(
    df: pd.DataFrame, risk_engine: BacktestRiskManager
) -> dict:
    """Executes a chronological event-driven strategy simulation loop."""
    trade_ledger = []
    in_position = False
    entry_price = 0.0
    take_profit = 0.0
    stop_loss = 0.0
    allocated_units = 0.0

    # Strict baseline risk constants for standard single-trade parameters
    RISK_PER_TRADE_USD = 200.0
    TARGET_REWARD_RATIO = 2.0  # 1:2 Risk-to-Reward distribution blueprint

    for idx, row in df.iterrows():
        # A. If already in an active position, evaluate exit coordinates
        if in_position:
            current_low = row["Low"]
            current_high = row["High"]

            # 1. Evaluate Stop-Loss breach
            if current_low <= stop_loss:
                pnl = (stop_loss - entry_price) * allocated_units
                risk_engine.update_account_metrics(pnl)
                trade_ledger.append(
                    {
                        "Date": idx,
                        "Type": "EXIT_SL",
                        "Price": stop_loss,
                        "PnL": pnl,
                        "Balance": risk_engine.current_balance,
                    }
                )
                in_position = False
                continue

            # 2. Evaluate Take-Profit reach
            elif current_high >= take_profit:
                pnl = (take_profit - entry_price) * allocated_units
                risk_engine.update_account_metrics(pnl)
                trade_ledger.append(
                    {
                        "Date": idx,
                        "Type": "EXIT_TP",
                        "Price": take_profit,
                        "PnL": pnl,
                        "Balance": risk_engine.current_balance,
                    }
                )
                in_position = False
                continue

        # B. If looking for a trade, run entry confluence validation rules
        else:
            risk_state = risk_engine.check_preflight_risk()
            if risk_state != "OPERATIONAL":
                continue  # Skip entries if the safety circuit breaker is triggered

            # Validate technical entry rules
            gate_a_rejection = row["R_wb"] > 1.2
            gate_b_trend = row["EMA_50"] > row["EMA_200"]
            gate_c_momentum = row["RSI"] > 50

            if gate_a_rejection and gate_b_trend and gate_c_momentum:
                in_position = True
                entry_price = row["Close"]

                # Structure bracket parameters: 2% risk threshold
                sl_distance = entry_price * 0.02
                stop_loss = entry_price - sl_distance
                take_profit = entry_price + (sl_distance * TARGET_REWARD_RATIO)

                # Factor in position sizing scaling from the risk manager
                active_risk = RISK_PER_TRADE_USD * risk_engine.size_multiplier
                allocated_units = active_risk / sl_distance

                trade_ledger.append(
                    {
                        "Date": idx,
                        "Type": "ENTRY_BUY",
                        "Price": entry_price,
                        "PnL": 0.0,
                        "Balance": risk_engine.current_balance,
                    }
                )

    # Compute descriptive performance analytics metrics
    ledger_df = pd.DataFrame(trade_ledger) if trade_ledger else pd.DataFrame()
    summary_stats = {}

    if not ledger_df.empty:
        exits = ledger_df[ledger_df["Type"].str.startswith("EXIT")]
        total_trades = len(exits)
        winning_trades = len(exits[exits["PnL"] > 0])

        summary_stats = {
            "Total_Executed_Trades": total_trades,
            "Win_Rate_Pct": (
                (winning_trades / total_trades) * 100 if total_trades else 0
            ),
            "Terminal_Balance_USD": risk_engine.current_balance,
            "Maximum_Equity_Drawdown_USD": risk_engine.max_drawdown,
        }

    return {"summary": summary_stats, "ledger": ledger_df}


# ==========================================
# MASTER PRODUCTION PIPELINE RUNNER
# ==========================================
if __name__ == "__main__":
    # 1. Extract historical market asset arrays
    raw_candles = fetch_market_data(
        ticker="AAPL", start_date="2022-01-01", end_date="2026-01-01"
    )
    processed_signals = engineer_technical_features(raw_candles)

    # 2. Establish starting system capital states
    trading_desk_risk = BacktestRiskManager(
        initial_capital=10000.0, max_daily_loss=1500.0
    )

    # 3. Process simulations through the system pipeline layers
    backtest_results = run_system_backtest(processed_signals, trading_desk_risk)

    print("\n==================================================")
    print("      DECODELABS SYSTEM STRATEGY METRICS          ")
    print("==================================================")
    for metric, val in backtest_results["summary"].items():
        print(f"🔹 {metric.replace('_', ' ')}: {val:.2f}")

    if not backtest_results["ledger"].empty:
        print("\n📥 Sample Extract From Order Execution Ledger:")
        print(backtest_results["ledger"].tail(6).to_string(index=False))
        import matplotlib.pyplot as plt


def plot_market_architecture(df: pd.DataFrame, ticker: str):
    """Generates the visual architecture charts for the strategy report."""
    # Slice the last 150 days to keep the candlestick structural lines scannable
    plot_df = df.tail(150).copy()

    plt.figure(figsize=(14, 8))
    plt.style.use("dark_background")

    # 1. Map dynamic support and resistance floor-to-ceiling boundaries
    support_floor = plot_df["Low"].min()
    resistance_ceiling = plot_df["High"].max()

    plt.axhline(
        y=resistance_ceiling,
        color="#8B2500",
        linestyle="--",
        alpha=0.8,
        label=f"Resistance Ceiling (${resistance_ceiling:.2f})",
    )
    plt.axhline(
        y=support_floor,
        color="#2E8B57",
        linestyle="--",
        alpha=0.8,
        label=f"Support Floor (${support_floor:.2f})",
    )

    # 2. Overlay smoothing trend constants
    plt.plot(
        plot_df.index,
        plot_df["EMA_50"],
        color="#4682B4",
        linewidth=2,
        label="Slate Blue: 50-Day EMA (Responsive)",
    )
    plt.plot(
        plot_df.index,
        plot_df["EMA_200"],
        color="#FFBF00",
        linewidth=2,
        label="Amber: 200-Day EMA (Rigid)",
    )

    # 3. Plot closing price action sequence
    plt.plot(
        plot_df.index,
        plot_df["Close"],
        color="#FFFFFF",
        alpha=0.4,
        label="Raw Price Action",
    )

    # Label styling rules mapping directly to industrial kit standards
    plt.title(
        f"DecodeLabs Architecture Suite - {ticker} Visual Balance Profile",
        fontsize=14,
        pad=15,
    )
    plt.xlabel("Timeline Date Coordinate", fontsize=11)
    plt.ylabel("Asset Valuation Price ($)", fontsize=11)
    plt.legend(loc="upper left", frameon=True, facecolor="#111111")
    plt.grid(color="#222222", linestyle="-", linewidth=0.5)

    plt.tight_layout()
    plt.show()


# Place this trigger line at the very bottom inside your `__main__` entrypoint:
# plot_market_architecture(processed_signals, "AAPL")

