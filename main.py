from typing import Tuple

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import pandas as pd
import yfinance_api as yf_api
import streamlit as st
import port_stats as ps
import efrontier as ef

if "init" not in st.session_state:
    st.session_state["init"] = True
    st.session_state["xlsx_selected"] = False
    st.session_state["dates_and_rf_rate_selected"] = False


def configure_page() -> None:
    st.set_page_config(page_title="Efficient Frontier", layout="wide")


def overview() -> None:
    st.write(st.session_state)
    st.markdown("## Overview")
    st.markdown(
        "### This app determines the Efficient Frontier for a specified list of investments and timeframe."
    )
    st.markdown(
        "The objective is to determine the optimum diversification of an investment portfolio."
    )


def sidebar() -> Tuple:

    def excel_file_selected() -> None:
        st.session_state["xlsx_selected"] = True

    def dates_and_rf_rate_selected() -> None:
        st.session_state["dates_and_rf_rate_selected"] = True

    def reset_all() -> Tuple:
        tickers_and_constraints = pd.DataFrame()
        start_date = None
        end_date = None
        rf_rate = None
        return tickers_and_constraints, start_date, end_date, rf_rate

    def reset_start_end_and_rf_rate():
        start_date = None
        end_date = None
        rf_rate = None
        return start_date, end_date, rf_rate

    with st.sidebar:
        st.markdown("# Configure Analysis")
        st.markdown("### Step 1: Select Excel File with Tickers & Constraints")
        options: list[str] = ["Major Asset Classes", "Industry Sectors", "Custom"]
        opt = st.selectbox(
            "Select Scenario", options, index=None, on_change=excel_file_selected
        )
        if opt == options[0]:
            tickers_and_constraints = pd.read_excel("./data/asset_classes.xlsx")
        elif opt == options[1]:
            tickers_and_constraints = pd.read_excel("./data/industry_sectors.xlsx")
        elif opt == options[2]:
            st.session_state["xlsx_selected"] = False
            tickers_and_constraints, start_date, end_date, rf_rate = reset_all()
            f = st.file_uploader("Select Excel File")
            if f:
                tickers_and_constraints = pd.read_excel(f)
                st.session_state["xlsx_selected"] = True
        else:
            tickers_and_constraints, start_date, end_date, rf_rate = reset_all()
            st.session_state["xlsx_selected"] = False
            st.session_state["dates_and_rf_rate_selected"] = False
        # Check if all tickers are valid
        if st.session_state["xlsx_selected"]:
            err, dft = yf_api.get_investment_names(
                tickers_and_constraints["Ticker"].to_list()
            )
            if err != "":
                st.error(f"Error! {err}")
                reset_all()
                st.session_state["xlsx_selected"] = False
                st.session_state["dates_and_rf_rate_selected"] = False

        if st.session_state["xlsx_selected"]:
            st.markdown("### Step 2: Select Start Date, End Date, & Risk Free Rate")
            with st.form("config_dates_rf_rate"):
                start_date = st.date_input(
                    "Select Start Date",
                    format="MM/DD/YYYY",
                    value=datetime.today() - timedelta(1) - relativedelta(years=3),
                )
                end_date = st.date_input(
                    "Select End Date",
                    format="MM/DD/YYYY",
                    value=datetime.today() - timedelta(1),
                )
                rf_rate = st.number_input("Specify Risk-Free Rate", min_value=0.00)
                calc_ef_button = st.form_submit_button(
                    "Calculate Efficient Frontier", on_click=dates_and_rf_rate_selected
                )
            if calc_ef_button:
                if end_date < start_date:
                    st.error("Error! Start Date must be less than End Date.")
                    start_date, end_date, rf_rate = reset_start_end_and_rf_rate()
                    st.session_state["dates_and_rf_rate_entered"] = False

        return tickers_and_constraints, start_date, end_date, rf_rate


# def get_start_end_risk_free_rate(excel_file: str, sheet: str) -> Tuple[str, str, float]:
#     df = pd.read_excel(excel_file, sheet_name="Dates & Risk Free Rate")
#     start: str = df.loc[0, "Start Date"].strftime("%Y-%m-%d")
#     end: str = df.loc[0, "End Date"].strftime("%Y-%m-%d")
#     risk_free_rate: float = df.loc[0, "Risk Free Rate"]
#     return start, end, risk_free_rate


if __name__ == "__main__":
    configure_page()
    overview()
    tickers_and_constraints, start, end, risk_free_rate = sidebar()

    if st.session_state["xlsx_selected"]:
        tickers: list[str] = tickers_and_constraints["Ticker"].tolist()
        st.write(tickers)

    if st.session_state["dates_and_rf_rate_selected"]:
        pass

        # err, names = yf_api.get_investment_names(tickers)
        # if err != "":
        #     print(err)
        # else:
        #     adj_daily_close = yf_api.get_adj_daily_close(tickers, start, end)
        #     growth_of_10000 = ps.get_growth_10000(adj_daily_close)
        #     daily_returns = ps.get_daily_returns(adj_daily_close)
        #     daily_ln_returns = ps.get_daily_ln_returns(adj_daily_close)
        #     correlation_matrix = ps.get_correlation_matrix(daily_ln_returns)
        #     expected_returns = ps.get_expected_returns(daily_ln_returns)
        #     std_deviations = ps.get_std_deviations(daily_ln_returns)
        #     cov_matrix = ps.get_cov_matrix(daily_ln_returns)
        #     inv_cov_matrix = ps.get_inv_cov_matrix(cov_matrix)
        #     efficient_frontier = ef.get_efficient_frontier(
        #         inv_and_constraints, risk_free_rate, adj_daily_close
        #     )
        #     st.dataframe(growth_of_10000)
        #     st.dataframe(correlation_matrix)
st.write(st.session_state)
