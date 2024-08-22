# -*- coding: utf-8 -*-
"""
Created on Wed Jun  5 11:26:12 2024

@author: evan_
"""
from typing import Any
from numpy.typing import NDArray

# from typing import TypeVar
import pandas as pd
import numpy as np


def get_growth_10000(adj_close: pd.DataFrame) -> pd.DataFrame:
    df = adj_close.div(adj_close.iloc[0]) * 10000
    return df


def get_daily_returns(adj_close: pd.DataFrame) -> pd.DataFrame:
    df = (adj_close / adj_close.shift(1)) - 1
    df = df.dropna()
    return df


def get_daily_ln_returns(adj_close: Any) -> Any:
    df = np.log((adj_close / adj_close.shift(1)))
    df = df.dropna()
    return df


# def get_total_return(adj_close: pd.DataFrame) -> pd.DataFrame:
#     return pd.DataFrame()


def get_correlation_matrix(daily_ln_returns: pd.DataFrame) -> pd.DataFrame:
    df = daily_ln_returns.corr()
    return df


def get_expected_returns(daily_ln_returns: pd.DataFrame) -> pd.Series:
    """
    Calculates the annual return (CAGR)of the specified investments.

    Args:
        daily_ln_returns (pd.DataFrame):
            column headings: investment tickers
            row headings: dates
            table content: log normal return of investment vs previous day close

    Returns:
        df (pd.Series):
            row headings: investment tickers
            table content: annual expected return of investment
    """
    # line below calculates annual expected returns based on 252 trading days per year
    # df = np.exp(daily_ln_returns.mean() * 252) - 1

    # lines below calculates annual expected returns based on 365 calendar days per year
    trading_days: int = len(daily_ln_returns)
    start_date = daily_ln_returns.index[0]
    end_date = daily_ln_returns.index[-1]
    calendar_days: int = (end_date-start_date).days
    years: float = (calendar_days/365)
    df = np.exp(daily_ln_returns.mean() * trading_days/years) - 1
    return df


def get_std_deviations(daily_ln_returns: pd.DataFrame) -> pd.Series:
    """
    Calculates the covariance of the specified investments.

    Args:
        daily_ln_returns (pd.DataFrame):
            column headings: investment tickers
            row headings: dates
            table content: log normal return of investment vs previous day close

    Returns:
        df (pd.Series):
            row headings: investment tickers
            table content: standard deviation of investment
    """
    df = daily_ln_returns.std() * np.sqrt(252)
    return df


def get_cov_matrix(daily_ln_returns: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates the covariance of the specified investments.

    Args:
        daily_ln_returns (pd.DataFrame):
            column headings: investment tickers
            row headings: dates
            table content: log normal return of investment vs previous day close

    Returns:
        df (pd.DataFrame):
            column headings: investment tickers
            row headings: investment tickers
            table content: covariances
    """
    df = daily_ln_returns.cov()
    return df


def get_inv_cov_matrix(cov_matrix: Any) -> Any:
    df = np.linalg.inv(cov_matrix)
    return df

def get_portfolio_return(weights:pd.DataFrame, expected_returns:pd.Series)-> float:
    p_ret = np.inner(weights, expected_returns)
    return p_ret

def get_portfolio_sd(weights:pd.DataFrame,cov:pd.DataFrame)-> float:
    # Equation:
    # Std Dev = sqrt ( (Investment_Weights)*(Covariance_Matrix) * (Inverse of Investment_Weights) *252 )
    sd:float = np.sqrt(np.dot(np.dot(weights, cov), weights.T) * 252)
    return sd