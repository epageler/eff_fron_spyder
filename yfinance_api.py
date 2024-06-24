# -*- coding: utf-8 -*-
"""
Created on Tue Jun  4 15:50:42 2024

@author: evan_
"""
from typing import Tuple
import pandas as pd
import yfinance as yf  # type: ignore
import streamlit as st


# ---------------------------------------------------------------------------- #
def get_investment_names(tickers: list[str]) -> Tuple[str, pd.DataFrame]:
    """
    Retrieve investment names for list of tickers.

    If invalid ticker is in list, err contains an error message with the invalid ticker and the returned df is empty.

    Args:
        tickers (list[str]): list of tickers

    Returns:
        str:
            If an invalid ticker is included in list, message specify
            invalid ticker. Empty string if no errors.
        pd.DataFrame:
            Column Heading(s): shortName,
            Index: ticker
            df Contents: Short Name for each investment. Empty df if errors.
    """
    err = ""
    investment_names = pd.DataFrame()
    for t in tickers:
        try:
            investment_names.loc[t, "longName"] = yf.Ticker(t).info["longName"]
        except:
            err = f"Invalid Ticker: {t}"
            investment_names = pd.DataFrame()  # return empty df if error
            return err, investment_names  # return immediately if error
    return err, investment_names


# ---------------------------------------------------------------------------- #
def get_adj_daily_close(tickers: list[str], start_date: str, end_date: str) -> pd.DataFrame:
    """
    Retrieve adjusted daily closing prices for a list of tickers over a specified
    date range. Order of columns in returned df is same as order in tickers argument.

    Note: Assumes that the tickers are valid. So, recommendation is call the get_investment_names
    function first. That function includes an error if any entry in tickers is invalid.

    Args:
        tickers (list[str]): List of tickers to be retrieved
        start_date (str): Start date in format YYYY-MM-DD
        end_date (str): End date in format YYYY-MM-DD

    Returns:
        pd.DataFrame:
            Column Heading(s): tickers
            Index: Date
            df Contents: Adjusted daily closing prices
    """
    # Retrieve daily
    adj_close = yf.download(tickers, start=start_date, end=end_date, interval="1d")["Adj Close"][
        tickers
    ]
    return adj_close


# ---------------------------------------------------------------------------- #
if __name__ == "__main__":
    tickers = ["BIL", "AGG", "TIP", "MUB", "PFF", "IVV", "IWM", "EFA", "EEM", "IYR"]
    start: str = "2023-05-30"
    end: str = "2024-05-30"

    err, names = get_investment_names(tickers)
    if err != "":
        print(err)
    else:
        adj_daily_close = get_adj_daily_close(tickers, start, end)
