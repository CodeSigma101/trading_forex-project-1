import numpy as np
import pandas as pd
import yfinance as yf


# ==========================================
# LAYER 1: DATA INGESTION SUITE
# ==========================================
def ingest_clean_timeseries_data(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Ingests daily time-series historical data and handles null structures."""
    df = yf.download(ticker, start=start_date, end=end_date, multi_level_index=False, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df.copy().ffill().fillna(0)


# ==========================================
# LAYER 2 & 3: THE STRATEGY MATRIX CORE
# ==========================================
def run_bracket_strategy(df: pd.DataFrame, fast_window: int, slow_window: int) -> pd.DataFrame:
    """Processes crossovers on customized moving average parameters."""
    df = df.copy()
    df["Fast_MA"] = df["Close"].rolling(window=fast_window).mean()
    df["Slow_MA"] = df["Close"].rolling(window=slow_window).mean()

    df["Signal"] = "IDLE"
    df["Stance"] = 0

    is_long_active = False
    tp_target, sl_target = 0.0, 0.0
    RISK_THRESHOLD_PCT, REWARD_RATIO_SCALE = 0.02, 3.0

    for i in range(1, len(df)):
        idx, prev_idx = df.index[i], df.index[i - 1]
        if pd.isna(df.at[idx, "Slow_MA"]) or pd.isna(df.at[prev_idx, "Slow_MA"]):
            continue

        if is_long_active:
            if df.at[idx, "Low"] <= sl_target:
                df.at[idx, "Signal"], df.at[idx, "Stance"], is_long_active = "EXIT_SL", 0, False
            elif df.at[idx, "High"] >= tp_target:
                df.at[idx, "Signal"], df.at[idx, "Stance"], is_long_active = "EXIT_TP", 0, False
            else:
                df.at[idx, "Stance"] = 1
        else:
            if (df.at[prev_idx, "Fast_MA"] <= df.at[prev_idx, "Slow_MA"]) and (df.at[idx, "Fast_MA"] > df.at[idx, "Slow_MA"]):
                is_long_active = True
                entry = df.at[idx, "Close"]
                sl_distance = entry * RISK_THRESHOLD_PCT
                sl_target, tp_target = entry - sl_distance, entry + (sl_distance * REWARD_RATIO_SCALE)
                df.at[idx, "Signal"], df.at[idx, "Stance"] = "ENTRY_BUY", 1
    return df


# ==========================================
# LAYER 4: PERFORMANCE METRIC PARSER
# ==========================================
def evaluate_performance_kpis(df: pd.DataFrame) -> float:
    """Isolates Sharpe Ratio performance from the strategy execution path."""
    df = df.copy()
    df["Market_Returns"] = np.log(df["Close"] / df["Close"].shift(1))
    df["Strategy_Returns"] = df["Market_Returns"] * df["Stance"].shift(1).fillna(0)
    
    daily_vol = df["Strategy_Returns"].std()
    if daily_vol == 0 or np.isnan(daily_vol):
        return -1.0
    return float((df["Strategy_Returns"].mean() / daily_vol) * np.sqrt(252))


# ==========================================
# LAYER 5: WALK-FORWARD OPTIMIZATION ENGINE
# ==========================================
def execute_walk_forward_optimization(df: pd.DataFrame):
    """Executes a chronological rolling validation split to prevent overfitting."""
    # Convert timestamps into unique localized year arrays
    df["Year"] = df.index.year
    unique_years = sorted(df["Year"].unique())
    
    print("==================================================================")
    print("      DECODELABS LAYER 5: WALK-FORWARD OPTIMIZATION LOGS          ")
    print("==================================================================")

    # Parameter combination search grid options
    parameter_grid = [(5, 20), (10, 50), (20, 100)]
    compiled_oos_returns = []

    # Run rolling validation iterations (Minimum 3 years history needed to optimize)
    for cycle in range(len(unique_years) - 3):
        # 1. Map precise chronological slice boundaries
        in_sample_years = unique_years[cycle : cycle + 3]
        out_of_sample_year = unique_years[cycle + 3]

        is_data = df[df["Year"].isin(in_sample_years)]
        oos_data = df[df["Year"] == out_of_sample_year]

        best_sharpe = -99.0
        best_params = (10, 50)

        # 2. In-Sample Phase: Find the optimal parameters
        for fast, slow in parameter_grid:
            is_run = run_bracket_strategy(is_data, fast, slow)
            sharpe = evaluate_performance_kpis(is_run)
            if sharpe > best_sharpe:
                best_sharpe = sharpe
                best_params = (fast, slow)

        # 3. Out-of-Sample Phase: Freeze parameters and test blindly
        optimal_fast, optimal_slow = best_params
        oos_run = run_bracket_strategy(oos_data, optimal_fast, optimal_slow)
        oos_sharpe = evaluate_performance_kpis(oos_run)

        print(f"🔹 Cycle {cycle + 1} | IS Train: {in_sample_years} -> Selected Optima: MAs({optimal_fast}, {optimal_slow})")
        print(f"        | OOS Test Blind Validation Year: [{out_of_sample_year}] -> Verified OOS Sharpe: {oos_sharpe:.2f}")


# ==========================================
# SYSTEM PIPELINE EXECUTION
# ==========================================
if __name__ == "__main__":
    raw_history = ingest_clean_timeseries_data("SPY", "2021-01-01", "2026-01-01")
    execute_walk_forward_optimization(raw_history)
