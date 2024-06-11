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
    # print(type(adj_close))
    df = np.log((adj_close / adj_close.shift(1)))
    # print(type(df))
    df = df.dropna()
    # print(type(df))
    return df


def get_total_return(adj_close: pd.DataFrame) -> pd.DataFrame:
    print("\n calculating total_return df")
    return pd.DataFrame()


def get_correlation_matrix(daily_ln_returns: pd.DataFrame) -> pd.DataFrame:
    df = daily_ln_returns.corr()
    return df


def get_expected_returns(daily_ln_returns: pd.DataFrame) -> pd.Series:
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
            table content: annual expected return of investment
    """
    df = np.exp(daily_ln_returns.mean() * 252) - 1
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
