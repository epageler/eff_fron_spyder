# -*- coding: utf-8 -*-
"""
Created on Wed Jun  5 08:20:08 2024

@author: evan_
"""
from typing import Tuple

# from datetime import datetime
import pandas as pd
import yfinance_api as yf_api
import port_stats as ps
import efrontier as ef


def get_investments_and_constraints(excel_file: str, sheet: str) -> pd.DataFrame:
    df = pd.read_excel(excel_file)
    return df


def get_start_end_risk_free_rate(excel_file: str, sheet: str) -> Tuple[str, str, float]:
    df = pd.read_excel(excel_file, sheet_name="Dates & Risk Free Rate")
    start: str = df.loc[0, "Start Date"].strftime("%Y-%m-%d")
    end: str = df.loc[0, "End Date"].strftime("%Y-%m-%d")
    risk_free_rate: float = df.loc[0, "Risk Free Rate"]
    return start, end, risk_free_rate


if __name__ == "__main__":
    excel_file: str = "asset_classes.xlsx"
    inv_and_constraints: pd.DataFrame = get_investments_and_constraints(
        excel_file, sheet="Investments"
    )
    tickers: list[str] = inv_and_constraints["Ticker"].tolist()

    start, end, risk_free_rate = get_start_end_risk_free_rate(
        excel_file, sheet="Dates & Risk Free Rate"
    )

    inv_constraints: pd.DataFrame = inv_and_constraints.set_index("Ticker")

    err, names = yf_api.get_investment_names(tickers)
    if err != "":
        print(err)
    else:
        adj_daily_close = yf_api.get_adj_daily_close(tickers, start, end)
        growth_of_10000 = ps.get_growth_10000(adj_daily_close)
        daily_returns = ps.get_daily_returns(adj_daily_close)
        daily_ln_returns = ps.get_daily_ln_returns(adj_daily_close)
        correlation_matrix = ps.get_correlation_matrix(daily_ln_returns)
        expected_returns = ps.get_expected_returns(daily_ln_returns)
        std_deviations = ps.get_std_deviations(daily_ln_returns)
        cov_matrix = ps.get_cov_matrix(daily_ln_returns)
        inv_cov_matrix = ps.get_inv_cov_matrix(cov_matrix)
        efficient_frontier = ef.get_efficient_frontier(
            inv_and_constraints, risk_free_rate, adj_daily_close
        )
