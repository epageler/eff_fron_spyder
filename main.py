# -*- coding: utf-8 -*-
"""
Created on Wed Jun  5 08:20:08 2024

@author: evan_
"""
import pandas as pd
import yfinance_api as yf_api
import port_stats as ps


def get_investments_and_constraints(excel_file: str) -> pd.DataFrame:
    df = pd.read_excel(excel_file)
    return df


if __name__ == "__main__":
    inv_and_constraints: pd.DataFrame = get_investments_and_constraints("investments.xlsx")
    tickers: list[str] = inv_and_constraints["Ticker"].tolist()
    start: str = "2023-05-30"
    end: str = "2024-05-30"
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
        expected_returns=ps.get_expected_returns(daily_ln_returns)
        std_deviations=ps.get_std_deviations(daily_ln_returns)
        cov_matrix=ps.get_cov_matrix(daily_ln_returns)
        inv_cov_matrix=ps.get_inv_cov_matrix(cov_matrix)
