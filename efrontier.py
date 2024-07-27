# -*- coding: utf-8 -*-
"""
Created on Sat Jun  8 14:22:21 2024

@author: evan_
"""
import pandas as pd
import numpy as np
import port_stats as ps
from scipy.optimize import minimize  # type: ignore


def get_max_sharpe_portfolio(
    inv_and_constraints: pd.DataFrame,
    risk_free_rate: float,
    expected_returns: pd.Series,
    cov: pd.DataFrame,
) -> list[float]:

    def neg_sharpe_ratio(guess, expected_returns, cov, risk_free_rate):
        er = sum(guess * expected_returns)
        sd = np.sqrt(np.dot(np.dot(guess, cov), guess.T) * 252)
        return -((er - risk_free_rate) / sd)

    # ---------- Configure optimization ------------
    num_tickers = len(inv_and_constraints)
    # Initial guess
    guess=[1/len(inv_and_constraints)]*len(inv_and_constraints)
    # args
    args = (expected_returns, cov, risk_free_rate)

    # Constraint #1
    def weights_total_one_hundred_pct(guess):
        return sum(guess) - 1

    # Constraints
    cons = {"type": "eq", "fun": weights_total_one_hundred_pct}
    # Bounds
    bnds = []
    for i in range(0, num_tickers):
        bnds.append(
            (
                inv_and_constraints.loc[i]["Min Weight"],
                inv_and_constraints.loc[i]["Max Weight"],
            )
        )
    solution = minimize(
        neg_sharpe_ratio,
        guess,
        args=args,
        method="SLSQP",
        constraints=cons,
        bounds=bnds,
        tol=1e-10,
    )
    max_sharpe_ratio = -solution.fun
    max_sharpe_portfolio = solution.x
    max_sharpe_sd = np.sqrt(
        np.dot(np.dot(max_sharpe_portfolio, cov), max_sharpe_portfolio.T) * 252
    )
    max_sharpe_return = np.inner(max_sharpe_portfolio, expected_returns)
    eff_fron_point = [max_sharpe_sd, max_sharpe_return, max_sharpe_ratio]
    for i in max_sharpe_portfolio:
        eff_fron_point.append(i)
    return eff_fron_point


def get_min_risk_portfolio(
    inv_and_constraints: pd.DataFrame,
    risk_free_rate: float,
    expected_returns: pd.Series,
    cov: pd.DataFrame,
) -> list[float]:

    # ---------- Configure optimization ------------
    # Objective function
    def portfolio_risk(guess, expected_returns, cov, risk_free_rate):
        sd = np.sqrt(np.dot(np.dot(guess, cov), guess.T) * 252)
        return sd

    # Initial guess
    num_tickers = len(inv_and_constraints)
    guess = [1 / len(inv_and_constraints)] * len(inv_and_constraints)
    # args
    args = (expected_returns, cov, risk_free_rate)

    # Constraint #1
    def weights_total_one_hundred_pct(guess):
        return sum(guess) - 1

    cons = {"type": "eq", "fun": weights_total_one_hundred_pct}

    # Bounds
    bnds = []
    for i in range(0, num_tickers):
        bnds.append(
            (
                inv_and_constraints.loc[i]["Min Weight"],
                inv_and_constraints.loc[i]["Max Weight"],
            )
        )
    # Perform Optimization
    solution = minimize(
        portfolio_risk,
        guess,
        args=args,
        method="SLSQP",
        constraints=cons,
        bounds=bnds,
        tol=1e-10,
    )
    # Retrieve results of optimization
    risk = solution.fun
    portfolio = solution.x
    p_ret = np.inner(portfolio, expected_returns)
    sharpe = (p_ret - risk_free_rate) / risk

    # Construct entry for Efficient Portfolio df
    eff_fron_point = [risk, p_ret, sharpe]
    for i in portfolio:
        eff_fron_point.append(i)
    return eff_fron_point


def get_max_return_portfolio(
    inv_and_constraints: pd.DataFrame,
    risk_free_rate: float,
    expected_returns: pd.Series,
    cov: pd.DataFrame,
) -> list[float]:

    # ---------- Configure optimization ------------
    # Objective function
    def neg_portfolio_return(guess, expected_returns) -> float:
        p_ret = np.inner(guess, expected_returns)
        return -p_ret

    # Initial guess
    num_tickers = len(inv_and_constraints)
    guess = [1 / len(inv_and_constraints)] * len(inv_and_constraints)
    # args
    args = (expected_returns,)

    # Constraint #1
    def weights_total_one_hundred_pct(guess):
        return sum(guess) - 1

    cons = {"type": "eq", "fun": weights_total_one_hundred_pct}

    # Bounds
    bnds = []
    for i in range(0, num_tickers):
        bnds.append(
            (
                inv_and_constraints.loc[i]["Min Weight"],
                inv_and_constraints.loc[i]["Max Weight"],
            )
        )
    # Perform Optimization
    solution = minimize(
        neg_portfolio_return,
        guess,
        args=args,
        method="SLSQP",
        constraints=cons,
        bounds=bnds,
        tol=1e-10,
    )
    # Retrieve results of optimization
    p_ret = -solution.fun
    portfolio = solution.x
    risk = np.sqrt(np.dot(np.dot(portfolio, cov), portfolio.T) * 252)
    p_ret = np.inner(portfolio, expected_returns)
    sharpe = (p_ret - risk_free_rate) / risk

    # Construct entry to be added to Efficient Portfolio df
    eff_fron_point = [risk, p_ret, sharpe]
    for i in portfolio:
        eff_fron_point.append(i)
    return eff_fron_point


def get_target_return_portfolio(
    inv_and_constraints: pd.DataFrame,
    risk_free_rate: float,
    expected_returns: pd.Series,
    cov: pd.DataFrame,
    tgt_ret: float,
) -> list[float]:

    # ---------- Configure optimization ------------
    # Objective function
    def std_deviation(guess, expected_returns, cov, risk_free_rate):
        sd = np.sqrt(np.dot(np.dot(guess, cov), guess.T) * 252)
        return sd

    # Initial guess
    num_tickers = len(inv_and_constraints)
    guess = [1 / len(inv_and_constraints)] * len(inv_and_constraints)
    # args
    args = (expected_returns, cov, risk_free_rate)

    # Set constraints
    # Constraint #1
    def weights_total_one_hundred_pct(guess):
        return sum(guess) - 1

    # Constraint #2
    def return_equals_target(guess: float) -> float:
        p_ret = np.inner(guess, expected_returns)
        return p_ret - tgt_ret

    cons = (
        {"type": "eq", "fun": weights_total_one_hundred_pct},
        {"type": "eq", "fun": return_equals_target},
    )

    # Bounds
    bnds = []
    for i in range(0, num_tickers):
        bnds.append(
            (
                inv_and_constraints.loc[i]["Min Weight"],
                inv_and_constraints.loc[i]["Max Weight"],
            )
        )
    # Perform Optimization
    solution = minimize(
        std_deviation,
        guess,
        args=args,
        method="SLSQP",
        constraints=cons,
        bounds=bnds,
        tol=1e-10,
    )
    # Retrieve results of optimization
    p_ret = -solution.fun
    portfolio = solution.x
    risk = np.sqrt(np.dot(np.dot(portfolio, cov), portfolio.T) * 252)
    p_ret = np.inner(portfolio, expected_returns)
    sharpe = (p_ret - risk_free_rate) / risk

    # Construct entry to be added to Efficient Portfolio df
    eff_fron_point = [risk, p_ret, sharpe]
    for i in portfolio:
        eff_fron_point.append(i)
    return eff_fron_point


def get_efficient_frontier(
    inv_and_constraints: pd.DataFrame,
    risk_free_rate: float,
    adj_daily_close: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calculates the efficient frontier

    Args:
        inv_and_constraints (pd.DataFrame):
            column labels:
                Ticker,
                Min Weight,
                Max Weight
            row labels:
                Ticker
            df contents:
                ticker [str],
                min portfolio weight [float],
                max portfolio weight [float]
        risk_free_rate (float): rate that can earned on a risk-free investment
        adj_daily_close (pd.DataFrame):
            column labels:
                Date
                list of tickers
            row labels:
                dates
            df contents:
                date [date],
                adjusted daily close for each ticker [float]

    Returns:
        df (pd.DataFrame):
            column labels: risk, return, sharpe, investment weights,

            row labels: 0..number of points in efficient frontier,

            df contents:
                risk (std dev),
                annual expected return of portfolio,
                sharpe ratio of portfolio,
                weight of each investment in the portfolio
    """

    daily_ln_returns = ps.get_daily_ln_returns(adj_daily_close)
    expected_returns = ps.get_expected_returns(daily_ln_returns)
    cov_matrix = ps.get_cov_matrix(daily_ln_returns)

    # Get Portfolio with Minimum Risk
    min_risk_portfolio = get_min_risk_portfolio(
        inv_and_constraints, risk_free_rate, expected_returns, cov_matrix
    )

    # Get Portfolio with Maximum Sharpe Ratio
    max_sharpe_port = get_max_sharpe_portfolio(
        inv_and_constraints, risk_free_rate, expected_returns, cov_matrix
    )
    # Get Portfolio with Maximum Return
    max_return_port = get_max_return_portfolio(
        inv_and_constraints, risk_free_rate, expected_returns, cov_matrix
    )

    # Save returns calculated above
    min_risk_return = min_risk_portfolio[1]
    max_sharpe_return = max_sharpe_port[1]
    max_return = max_return_port[1]

    # Create Empty Efficient Frontier df
    cols = ["Risk", "Return", "Sharpe"]
    for ticker in inv_and_constraints["Ticker"]:
        cols.append(ticker)
    eff_fron = pd.DataFrame(columns=cols)

    # Add Min Risk Portfolio to Efficient Frontier
    eff_fron.loc[len(eff_fron.index)] = min_risk_portfolio

    INCR: float = 0.005  # Incr in Return between portfolios in the Efficient Frontier

    # Add portfolios between min risk portfolio & max sharpe portfolio to efficient frontier
    tgt_ret = (int(min_risk_return / INCR) + 1) * INCR
    while tgt_ret <= (max_sharpe_return - INCR / 5):
        tgt_ret_port = get_target_return_portfolio(
            inv_and_constraints,
            risk_free_rate,
            expected_returns,
            cov_matrix,
            tgt_ret,
        )
        eff_fron.loc[len(eff_fron)] = tgt_ret_port  # Add to Efficient Frontier
        tgt_ret += INCR

    # Add Maximum Sharpe Portfolio to Efficient Frontier
    eff_fron.loc[len(eff_fron.index)] = max_sharpe_port

    # Add portfolios between max sharpe portfolio & max return portfolio to efficient frontier
    tgt_ret = (int(max_sharpe_return / INCR) + 1) * INCR
    while tgt_ret <= (max_return - INCR / 5):
        tgt_ret_port = get_target_return_portfolio(
            inv_and_constraints,
            risk_free_rate,
            expected_returns,
            cov_matrix,
            tgt_ret,
        )
        eff_fron.loc[len(eff_fron)] = tgt_ret_port  # Add to Efficient Frontier
        tgt_ret += INCR

    # Add Portfolio with Maximum Return Efficient Frontier if it is not equal to max_sharpe_portfolio
    if round(max_sharpe_return, 5) != round(max_return, 5):
        eff_fron.loc[len(eff_fron)] = max_return_port

    return eff_fron
