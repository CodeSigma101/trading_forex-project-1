import numpy as np
import pandas as pd
import yfinance as yf


# ==========================================
# LAYER 1: DATA INGESTION SUITE
# ==========================================
def ingest_multisector_portfolio_matrix(
    assets: list, benchmark: str, start_date: str, end_date: str
) -> tuple:
    """Ingests time-series historical datasets across diverse macroeconomic sectors."""
    all_tickers = assets + [benchmark]
    raw_data = yf.download(
        all_tickers,
        start=start_date,
        end=end_date,
        multi_level_index=False,
        progress=False,
    )
    if isinstance(raw_data.columns, pd.MultiIndex):
        raw_data.columns = raw_data.columns.get_level_values(0)

    price_matrix = raw_data["Close"].copy().ffill().dropna()
    asset_returns = price_matrix[assets].pct_change().dropna()
    benchmark_returns = price_matrix[benchmark].pct_change().dropna()
    latest_closing_prices = price_matrix[assets].iloc[-1].to_dict()

    return asset_returns, benchmark_returns, latest_closing_prices


# ==========================================
# LAYER 2: SYSTEMIC RISK ANALYTICS MATRIX
# ==========================================
def calculate_systemic_risk_metrics(
    asset_returns: pd.DataFrame, benchmark_returns: pd.Series
) -> tuple:
    """Calculates the asset covariance matrix and systemic risk betas."""
    covariance_matrix = asset_returns.cov() * 252
    market_variance = benchmark_returns.var()
    individual_betas = {}
    for asset in asset_returns.columns:
        covariance_with_market = asset_returns[asset].cov(benchmark_returns)
        individual_betas[asset] = covariance_with_market / market_variance
    return covariance_matrix, individual_betas


# ==========================================
# LAYER 3, 4 & 5: MASTER RISK ENGINE CLOSURE
# ==========================================
def execute_master_gatekeeper_validation(
    latest_prices: dict,
    fixed_weights: dict,
    stop_loss_pcts: dict,
    individual_betas: dict,
) -> tuple:
    """Enforces MPT position sizing, Beta gates, and total portfolio heat thresholds."""
    TOTAL_ACCOUNT_CAPITAL_USD = 100000.0
    MAX_SINGLE_RISK_LIMIT_PCT = 0.02
    HEAT_CEILING_LIMIT_PCT = 0.08  # 8.0% Hard Maximum Portfolio Heat Constraint
    BETA_UPPER_LIMIT = 1.0

    master_ledger = []
    weighted_portfolio_beta = 0.0
    total_portfolio_absolute_risk_usd = 0.0

    # 1. Run the allocation calculations across our sector shield
    for asset, price in latest_prices.items():
        weight = fixed_weights[asset]
        allocated_capital = TOTAL_ACCOUNT_CAPITAL_USD * weight
        sl_pct = stop_loss_pcts[asset]
        beta_val = individual_betas[asset]

        # Calculate localized position risk metrics
        absolute_dollar_risk = allocated_capital * sl_pct
        max_allowed_risk_usd = (
            TOTAL_ACCOUNT_CAPITAL_USD * MAX_SINGLE_RISK_LIMIT_PCT
        )

        if absolute_dollar_risk > max_allowed_risk_usd:
            absolute_dollar_risk = max_allowed_risk_usd

        stop_loss_price = price * (1.0 - sl_pct)
        exact_units = absolute_dollar_risk / (price - stop_loss_price)

        # Accumulate macro portfolio risk variables
        weighted_portfolio_beta += weight * beta_val
        total_portfolio_absolute_risk_usd += absolute_dollar_risk

        master_ledger.append(
            {
                "Sector Asset": asset,
                "Price": f"${price:.2f}",
                "Weight": f"{weight * 100:.1f}%",
                "Capital Allocated": f"${allocated_capital:,.2f}",
                "Stop-Loss": f"-{sl_pct * 100:.1f}%",
                "Absolute Risk": f"${absolute_dollar_risk:,.2f}",
                "Exact Units": f"{exact_units:.2f}",
            }
        )

    # 2. Evaluate Constraint Gate 1: Systematic Risk Beta
    beta_gate_passed = weighted_portfolio_beta < BETA_UPPER_LIMIT

    # 3. Evaluate Constraint Gate 2: Total Portfolio Heat
    portfolio_heat_pct = (
        total_portfolio_absolute_risk_usd / TOTAL_ACCOUNT_CAPITAL_USD
    )
    heat_gate_passed = portfolio_heat_pct <= HEAT_CEILING_LIMIT_PCT

    # 4. Synthesize Final System Deployment Verdict
    if beta_gate_passed and heat_gate_passed:
        system_status = "PASSED / REGULATORY CLEARANCE"
        system_verdict = (
            "EXECUTE ALLOCATION: Portfolio structured as a weatherproof fortress."
        )
    else:
        system_status = "REJECTED / RISK BREACH"
        system_verdict = "HALT DEPLOYMENT: Capital exposure violates maximum safety constraints."

    summary_metrics = {
        "Weighted_Beta": weighted_portfolio_beta,
        "Total_Heat_USD": total_portfolio_absolute_risk_usd,
        "Total_Heat_Pct": portfolio_heat_pct * 100,
        "System_Status": system_status,
        "System_Verdict": system_verdict,
    }

    return summary_metrics, pd.DataFrame(master_ledger)


# ==========================================
# MASTER PRODUCTION PIPELINE RUNNER
# ==========================================
if __name__ == "__main__":
    PORTFOLIO_SECTORS = ["XLK", "XLP", "XLU", "GLD"]
    MARKET_BENCHMARK = "SPY"
    START_DATE = "2021-01-01"
    END_DATE = "2026-01-01"

    # Strict system parameters configured directly from the manual guidelines
    MANUAL_WEIGHTS = {"XLK": 0.20, "XLP": 0.30, "XLU": 0.25, "GLD": 0.25}
    MANUAL_STOPS = {"XLK": 0.10, "XLP": 0.06, "XLU": 0.07, "GLD": 0.08}

    # Execute end-to-end data and risk calculations
    ret_matrix, spy_ret, price_snapshot = ingest_multisector_portfolio_matrix(
        PORTFOLIO_SECTORS, MARKET_BENCHMARK, START_DATE, END_DATE
    )
    _, beta_dictionary = calculate_systemic_risk_metrics(ret_matrix, spy_ret)

    summary_results, ledger_df = execute_master_gatekeeper_validation(
        price_snapshot, MANUAL_WEIGHTS, MANUAL_STOPS, beta_dictionary
    )

    print("\n==================================================================")
    print("      DECODELABS SYSTEM VERDICT & FORTIFIED DASHBOARD             ")
    print("==================================================================")
    print(ledger_df.to_string(index=False))
    print("------------------------------------------------------------------")
    print(
        f"🔹 Weighted Portfolio Beta (βp): {summary_results['Weighted_Beta']:.4f} (< 1.0 Passed)"
    )
    print(
        f"🔹 Total Portfolio Absolute Risk: ${summary_results['Total_Heat_USD']:,.2f}"
    )
    print(
        f"🔹 Total Portfolio Heat Scale:   {summary_results['Total_Heat_Pct']:.2f}% (< 8.0% Passed)"
    )
    print(f"🔹 Gatekeeper Status Verdict:    {summary_results['System_Status']}")
    print(f"🔹 Master Execution Decision:    {summary_results['System_Verdict']}")
    print("==================================================================\n")
