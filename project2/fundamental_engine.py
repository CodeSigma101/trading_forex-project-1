import pandas as pd


# ==========================================
# LAYER 1: DATA INGESTION & CORE METRICS
# ==========================================
def get_fundamental_database() -> dict:
    """Isolates raw fundamental metrics from primary regulatory filings.

    Establishes core data for AAPL and its structural operating peers.
    """
    return {
        "AAPL": {
            "Ticker": "AAPL",
            "Reference_Period": "Q2 2026 10-Q",
            "Total_Net_Sales_USD_Billion": 111.18,
            "Strategic_Net_Cash_USD_Billion": 61.88,
            "Diluted_Shares_Outstanding_Billion": 14.725873,
            "Current_Market_Price_USD": 308.82,
            "EPS_TTM": 8.27,
            "PE_Multiple": 37.36,
            "DE_Ratio_Pct": 79.55,
        },
        "MSFT": {
            "Ticker": "MSFT",
            "Current_Market_Price_USD": 418.57,
            "EPS_TTM": 16.79,
            "PE_Multiple": 24.93,
            "DE_Ratio_Pct": 30.30,
        },
        "GOOGL": {
            "Ticker": "GOOGL",
            "Current_Market_Price_USD": 379.38,
            "EPS_TTM": 13.00,
            "PE_Multiple": 29.21,
            "DE_Ratio_Pct": 18.90,
        },
    }


# ==========================================
# LAYER 2: THE DISCOUNTED CASH FLOW ENGINE
# ==========================================
def calculate_dcf_intrinsic_value(data: dict, scenario: str) -> float:
    """Projects future free cash flows and discounts them to present value.

    Applies the fixed 9.9% WACC discount rate to evaluate intrinsic value.
    """
    if scenario == "conservative_baseline":
        cagr, operating_margin, exit_pe = 0.0639, 0.320, 23.2
    elif scenario == "optimistic_bull":
        cagr, operating_margin, exit_pe = 0.1000, 0.330, 30.0
    else:
        raise ValueError("Invalid scenario specified.")

    WACC, TAX_RATE, CAPEX_USD_BILLION, FORECAST_YEARS = 0.099, 0.15, 2.0, 5
    current_annual_revenue = data["Total_Net_Sales_USD_Billion"] * 4
    projected_revenue = current_annual_revenue
    discounted_fcf_sum = 0.0

    for year in range(1, FORECAST_YEARS + 1):
        projected_revenue *= 1 + cagr
        projected_ebit = projected_revenue * operating_margin
        projected_taxes = projected_ebit * TAX_RATE
        free_cash_flow = projected_ebit - projected_taxes - CAPEX_USD_BILLION
        discounted_fcf_sum += free_cash_flow / ((1 + WACC) ** year)

    terminal_net_income = projected_revenue * (operating_margin - TAX_RATE)
    terminal_value = terminal_net_income * exit_pe
    discounted_terminal_value = terminal_value / ((1 + WACC) ** FORECAST_YEARS)

    total_enterprise_value = discounted_fcf_sum + discounted_terminal_value
    intrinsic_equity_value = (
        total_enterprise_value + data["Strategic_Net_Cash_USD_Billion"]
    )

    return (
        intrinsic_equity_value / data["Diluted_Shares_Outstanding_Billion"]
    )


# ==========================================
# LAYER 3: RELATIVE COMPARISON & EXECUTION LOGIC
# ==========================================
def run_execution_gatekeeper(
    db: dict, intrinsic_baseline_val: float
) -> pd.DataFrame:
    """Generates the peer comparison matrix and fires the final trade verdict."""
    # 1. Compile relative valuation tracking table
    peer_summary = {
        "Ticker Asset": [db["AAPL"]["Ticker"], db["MSFT"]["Ticker"], db["GOOGL"]["Ticker"]],
        "Stock Price": [
            f"${db['AAPL']['Current_Market_Price_USD']:.2f}",
            f"${db['MSFT']['Current_Market_Price_USD']:.2f}",
            f"${db['GOOGL']['Current_Market_Price_USD']:.2f}",
        ],
        "EPS (TTM)": [
            f"${db['AAPL']['EPS_TTM']:.2f}",
            f"${db['MSFT']['EPS_TTM']:.2f}",
            f"${db['GOOGL']['EPS_TTM']:.2f}",
        ],
        "P/E Multiple": [
            f"{db['AAPL']['PE_Multiple']:.2f}x",
            f"{db['MSFT']['PE_Multiple']:.2f}x",
            f"{db['GOOGL']['PE_Multiple']:.2f}x",
        ],
        "D/E Leverage Ratio": [
            f"{db['AAPL']['DE_Ratio_Pct']:.2f}%",
            f"{db['MSFT']['DE_Ratio_Pct']:.2f}%",
            f"{db['GOOGL']['DE_Ratio_Pct']:.2f}%",
        ],
    }

    # 2. Enforce the Gatekeeper Buffer Rule (30% Margin of Safety)
    margin_of_safety = 0.30
    max_purchase_price = intrinsic_baseline_val * (1.0 - margin_of_safety)
    current_market_price = db["AAPL"]["Current_Market_Price_USD"]

    print("\n==================================================================")
    print("           DECODELABS SYSTEM VERDICT & GATEKEEPER LOG            ")
    print("==================================================================")
    print(f"🔹 Baseline Intrinsic Value:            ${intrinsic_baseline_val:.2f}")
    print(f"🔹 Max Entry Target (30% MoS Buffer):  ${max_purchase_price:.2f}")
    print(f"🔹 Active Live Market Valuation Price:  ${current_market_price:.2f}")

    premium_pct = ((current_market_price - max_purchase_price) / max_purchase_price) * 100
    print(f"⚠️ Current market pricing sits at a +{premium_pct:.2f}% premium over target.")

    print("------------------------------------------------------------------")
    if current_market_price <= max_purchase_price:
        print(" FINAL SYSTEM DECISION: EXECUTE UNDERVALUED BUY-SIDE POSITION")
    else:
        print(" FINAL SYSTEM DECISION: STRONG SELL (PRESERVE CAPITAL & AWAIT CONTRACTION)")
    print("==================================================================\n")

    return pd.DataFrame(peer_summary)


# --- Production Pipeline Entrypoint ---
if __name__ == "__main__":
    system_db = get_fundamental_database()

    # Process pricing vectors through engine layers
    aapl_baseline = calculate_dcf_intrinsic_value(system_db["AAPL"], "conservative_baseline")
    peer_matrix_df = run_execution_gatekeeper(system_db, aapl_baseline)

    print("📥 The Structural Peer Comparison Analysis Matrix:")
    print(peer_matrix_df.to_string(index=False))
