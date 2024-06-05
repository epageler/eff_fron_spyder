# -*- coding: utf-8 -*-
"""
Created on Wed Jun  5 11:26:12 2024

@author: evan_
"""
import pandas as pd


def get_growth_10000(adj_close: pd.DataFrame) -> pd.DataFrame:
    print("\n calculating get_growth_10000 df")
    g = adj_close.div(adj_close.iloc[0])*10000
    return g


def get_daily_ln_return(adj_close: pd.DataFrame) -> pd.DataFrame:
    print("\n calculating daily_ln_return df")
    return adj_close


def get_total_return(adj_close: pd.DataFrame) -> pd.DataFrame:
    print("\n calculating total_return df")
    return adj_close


def get_correlation_matrix(adj_close: pd.DataFrame) -> pd.DataFrame:
    print("\n calculating correlation_matrix df")


def get_expected_returns(adj_close: pd.DataFrame) -> pd.DataFrame:
    print("\n calculating expected_returns df")


def get_std_deviations(adj_close: pd.DataFrame) -> pd.DataFrame:
    print("\n calculating std_deviations df")


def get_covariance_matrix(adj_close: pd.DataFrame) -> pd.DataFrame:
    print("\n calculating covariance_matrix df")


def get_inv_covariance_matrix(adj_close: pd.DataFrame) -> pd.DataFrame:
    print("\n calculating inv_covariance_matrix df")
