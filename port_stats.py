# -*- coding: utf-8 -*-
"""
Created on Wed Jun  5 11:26:12 2024

@author: evan_
"""
import pandas as pd
import numpy as np
from numpy.typing import NDArray
# from typing import TypeVar
from typing import Any


def get_growth_10000(adj_close: pd.DataFrame) -> pd.DataFrame:
    df = adj_close.div(adj_close.iloc[0])*10000
    return df


def get_daily_returns(adj_close: pd.DataFrame) -> pd.DataFrame:
    df = (adj_close/adj_close.shift(1)-1)
    df = df.dropna()
    return df


def get_daily_ln_returns(adj_close: Any) -> Any:
    # print(type(adj_close))
    df = np.log((adj_close/adj_close.shift(1)))
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


def get_expected_returns(daily_ln_returns: pd.DataFrame) -> pd.DataFrame:
    df = np.exp(daily_ln_returns.mean()*252)-1
    return df


def get_std_deviations(daily_ln_returns: pd.DataFrame) -> pd.DataFrame:
    df = daily_ln_returns.std()*np.sqrt(252)
    return df


def get_cov_matrix(daily_ln_returns: pd.DataFrame) -> pd.DataFrame:
    df = daily_ln_returns.cov()
    return df


def get_inv_cov_matrix(cov_matrix: Any) -> Any:
    df = np.linalg.inv(cov_matrix)
    return df
