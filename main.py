# -*- coding: utf-8 -*-
"""
Created on Wed Jun  5 08:20:08 2024

@author: evan_
"""
import yfinance_api as yf_api

if __name__=="__main__":
    tickers = ["BIL", "AGG", "TIP", "MUB", "PFF", "IVV", "IWM", "EFA", "EEM", "IYR"]
    start: str = "2023-05-30"
    end: str = "2024-05-30"
    
    err, names = yf_api.get_investment_names(tickers)
    if err != "":
        print(err)
    else:
        adj_daily_close = yf_api.get_adj_daily_close(tickers, start, end)
