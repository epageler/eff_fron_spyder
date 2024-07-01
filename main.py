from typing import Tuple

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import pandas as pd
import yfinance_api as yf_api
import streamlit as st
import port_stats as ps
import efrontier as ef
import plotly.express as px
import plotly.graph_objects as go

if "init" not in st.session_state:
    st.session_state["init"] = True
    st.session_state["xlsx_selected"] = False
    st.session_state["dates_and_rf_rate_selected"] = False


def configure_page() -> None:
    st.set_page_config(page_title="Efficient Frontier", layout="wide")


def overview() -> None:
    # st.write(st.session_state)
    st.markdown("## Overview")
    st.markdown(
        "#### This app determines the Efficient Frontier for a specified list of investments and timeframe."
    )
    st.markdown(
        "The objective is to determine the optimum diversification of an investment portfolio."
    )
    st.divider()


def sidebar() -> tuple[pd.DataFrame, pd.DataFrame, datetime, datetime, float]:

    def excel_file_selected() -> None:
        st.session_state["xlsx_selected"] = True

    def dates_and_rf_rate_selected() -> None:
        st.session_state["dates_and_rf_rate_selected"] = True

    def reset_all() -> Tuple:
        tickers_and_constraints = pd.DataFrame()
        names = pd.DataFrame()
        start_date = None
        end_date = None
        rf_rate = None
        return tickers_and_constraints, names, start_date, end_date, rf_rate

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
            st.session_state["dates_and_rf_rate_selected"] = False
        elif opt == options[1]:
            tickers_and_constraints = pd.read_excel("./data/industry_sectors.xlsx")
            st.session_state["dates_and_rf_rate_selected"] = False
        elif opt == options[2]:
            st.session_state["xlsx_selected"] = False
            tickers_and_constraints, names, start_date, end_date, rf_rate = reset_all()
            f = st.file_uploader("Select Excel File")
            if f:
                tickers_and_constraints = pd.read_excel(f)
                st.session_state["xlsx_selected"] = True
        else:
            tickers_and_constraints, names, start_date, end_date, rf_rate = reset_all()
            st.session_state["xlsx_selected"] = False
            st.session_state["dates_and_rf_rate_selected"] = False
        # Check if all tickers are valid
        if st.session_state["xlsx_selected"]:
            names = pd.DataFrame()
            err, names = yf_api.get_investment_names(
                tickers=tickers_and_constraints["Ticker"].tolist()
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
                    # value=datetime.today() - timedelta(1) - relativedelta(years=5),
                    value=datetime(year=2007, month=5, day=29),
                )
                end_date = st.date_input(
                    "Select End Date",
                    format="MM/DD/YYYY",
                    # value=datetime.today() - timedelta(1),
                    value=datetime(year=2023, month=5, day=20),
                )
                # rf_rate = st.number_input("Specify Risk-Free Rate", min_value=0.00)
                rf_rate = st.number_input(
                    "Specify Risk-Free Rate", min_value=0.00, value=3.70
                )
                calc_ef_button = st.form_submit_button(
                    "Calculate Efficient Frontier", on_click=dates_and_rf_rate_selected
                )
            if calc_ef_button:
                st.session_state["dates_and_rf_rate_selected"] = True
                if end_date < start_date:
                    st.error("Error! Start Date must be less than End Date.")
                    start_date, end_date, rf_rate = reset_start_end_and_rf_rate()
                    st.session_state["dates_and_rf_rate_entered"] = False

        return tickers_and_constraints, names, start_date, end_date, rf_rate


@st.cache_data
def get_data_from_yf(tickers, start, end):
    adj_daily_close = yf_api.get_adj_daily_close(tickers, start, end)
    return adj_daily_close


@st.cache_data
def calc_port_stats(adj_daily_close):
    growth_of_10000 = ps.get_growth_10000(adj_daily_close)
    daily_returns = ps.get_daily_returns(adj_daily_close)
    daily_ln_returns = ps.get_daily_ln_returns(adj_daily_close)
    correlation_matrix = ps.get_correlation_matrix(daily_ln_returns)
    expected_returns = ps.get_expected_returns(daily_ln_returns)
    std_deviations = ps.get_std_deviations(daily_ln_returns)
    cov_matrix = ps.get_cov_matrix(daily_ln_returns)
    # inv_cov_matrix = ps.get_inv_cov_matrix(cov_matrix)
    print(risk_free_rate)
    efficient_frontier = ef.get_efficient_frontier(
        tickers_and_constraints, risk_free_rate/100, adj_daily_close
    )
    efficient_frontier.rename(columns={"Risk": "Std Dev"}, inplace=True)
    return (
        growth_of_10000,
        expected_returns,
        std_deviations,
        correlation_matrix,
        efficient_frontier,
    )


def display_configuration(tickers_and_constraints, names) -> None:
    with st.expander(
        "Tickers, Investment Names, & Constraints (Click to Hide / Show)", expanded=True
    ):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"###### History Start Date: {start}")
        with col2:
            st.markdown(f"###### History Enc Date: {end}")
        with col3:
            st.markdown(f"###### Risk-Free Rate: {risk_free_rate:.2f}%")
        st.markdown("#### Investments & Constraints:")
        df2: pd.DataFrame = names
        df2["Ticker"] = names.index
        df2.rename(columns={"longName": "Investment"}, inplace=True)
        df = pd.merge(tickers_and_constraints, df2)
        df = df[["Ticker", "Investment", "Min Weight", "Max Weight"]]
        st.dataframe(df.style.format({"Min Weight": "{:.2%}", "Max Weight": "{:.2%}"}))


def display_growth_of_10000_table(tickers_and_constraints, growth_of_10000) -> None:
    with st.expander("Growth of $10,000 Table (Click to Hide / Show)", expanded=True):
        tickers: list[str] = tickers_and_constraints["Ticker"].tolist()
        # adj_daily_close = yf_api.get_adj_daily_close(tickers, start, end)
        # growth_of_10000 = ps.get_growth_10000(adj_daily_close)
        columns = growth_of_10000.columns
        format_dict: dict[str, str] = {}
        for c in columns:
            format_dict[c] = "${:,.2f}"
        st.dataframe(growth_of_10000.style.format(formatter=format_dict))


def display_growth_of_10000_graph(
    tickers_and_constraints, growth_of_10000: pd.DataFrame
) -> None:
    with st.expander("Growth of $10,000 Graph (Click to Hide / Show)", expanded=True):
        tickers: list[str] = tickers_and_constraints["Ticker"].tolist()
        # adj_daily_close = yf_api.get_adj_daily_close(tickers, start, end)
        # growth_of_10000 = ps.get_growth_10000(adj_daily_close)
        columns = growth_of_10000.columns
        format_dict: dict[str, str] = {}
        for c in columns:
            format_dict[c] = "${:,.2f}"
        fig = px.line(
            growth_of_10000,
            x=growth_of_10000.index,
            y=growth_of_10000.columns[0 : len(growth_of_10000.columns)],
            title="Growth of $10,000",
            # color="Ticker"
        )
        fig.update_layout(
            title="Growth of $10,000",
            title_font_size=24,
            # title_x=0.5,
            legend_title="Investment",
            autosize=True,
            height=800,
            yaxis_tickprefix="$",
            yaxis_tickformat=",",
        )
        st.plotly_chart(fig, use_container_width=True)


def display_return_and_sd_table_and_graph(
    names, expected_returns, std_deviations
) -> None:
    with st.expander(
        "Expected Return & Standard Deviation (Click to Hide / Show)", expanded=True
    ):
        df = pd.DataFrame(
            {
                "Investment": names["Investment"],
                "Return": expected_returns,
                "Std Dev": std_deviations,
            }
        )
        df = df.reset_index()
        df = df.rename(columns={"index": "Ticker"})
        col1, col2 = st.columns([6, 6])
        with col1:
            st.markdown("##### Annual Return vs Standard Deviation")
            st.dataframe(df.style.format({"Return": "{:.2%}", "Std Dev": "{:.2%}"}))
        with col2:
            fig = go.Figure(
                go.Scatter(
                    x=df["Std Dev"],
                    y=df["Return"],
                    name="",
                    text=pd.Series(expected_returns).index,
                    mode="markers+text",
                    showlegend=False,
                )
            )
            fig.update_traces(
                textposition="middle right",
                marker=dict(size=7, color="red"),
                hovertemplate="<br>Std Dev: %{x}<br>Return: %{y}",
            )
            fig.update_xaxes(showgrid=True)
            fig.update_yaxes(showgrid=True)
            fig.update_layout(
                # title="Standard Deviation vs Return",
                # title_x=0.25,
                xaxis_title="Annual Std Deviation (Risk)",
                yaxis_title="Annual Return (%)",
                xaxis=dict(tickformat=".2%"),
                yaxis=dict(tickformat=".2%"),
                autosize=False,
                # width=600,
                height=500,
            )
            # st.plotly_chart(fig, use_container_width=True)
            st.plotly_chart(fig)


def display_correlation_matrix(cm: pd.DataFrame) -> None:
    with st.expander(
        "Investment Correlation Matrix (Click to Hide / Show)", expanded=True
    ):
        # st.markdown("##### Investment Correlation Matrix")
        # st.dataframe(cm)
        cm = cm.round(decimals=2)
        cm = cm[::-1]  # Reverse the df  Why does this work?
        fig = go.FigureWidget(
            data=go.Heatmap(
                z=cm,
                x=cm.index[::-1],  # Reverse the x-axis labels. Why does this work?
                y=cm.index,
                colorscale="RdBu_r",
                texttemplate="%{z}",
                zmin=-1,
                zmax=1,
            )
        )

        fig.update_traces()

        fig.update_layout(
            title="Investment Correlation Matrix",
            title_font_size=24,
            # title_x=0.5,
            autosize=False,
            width=800,
            height=800,
            font=dict(size=18),
        )
        st.plotly_chart(fig)


def display_efficient_frontier(ef: pd.DataFrame):
    st.markdown("##### Efficient Frontier")
    st.dataframe(ef)
    col1, col2 = st.columns(2)
    with col1:
        fig = go.Figure(
            go.Scatter(
                x=ef["Std Dev"],
                y=ef["Return"],
                name="Efficient Frontier",
                mode="lines+markers",
            )
        )
        fig.update_xaxes(rangemode='tozero')
        fig.update_yaxes(rangemode='tozero')
        fig.update_layout(height=600, width=600, title=dict(text="Efficient Frontier"))
        fig.update_layout(
            xaxis_title="Risk: Annual Standard Deviation (%)",
            yaxis_title="Annual Return (%)",
            xaxis=dict(tickformat=".2%"),
            yaxis=dict(tickformat=".2%"),
        )
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.write("Display Portfolio for Selected Point on Efficient Frontier")


if __name__ == "__main__":
    configure_page()
    overview()
    # TODO in sidebar, change start, end, & risk free rate back 
    tickers_and_constraints, names, start, end, risk_free_rate = sidebar()
    if (
        st.session_state["xlsx_selected"]
        and st.session_state["dates_and_rf_rate_selected"]
    ):
        display_configuration(tickers_and_constraints, names)
        adj_daily_close = get_data_from_yf(
            tickers_and_constraints["Ticker"].tolist(), start, end
        )
        (
            growth_of_10000,
            expected_returns,
            std_deviations,
            correlation_matrix,
            efficient_frontier,
        ) = calc_port_stats(adj_daily_close)
        display_growth_of_10000_table(tickers_and_constraints, growth_of_10000)
        display_growth_of_10000_graph(tickers_and_constraints, growth_of_10000)
        display_return_and_sd_table_and_graph(names, expected_returns, std_deviations)
        display_correlation_matrix(correlation_matrix)
        display_efficient_frontier(efficient_frontier)
    # err, names = yf_api.get_investment_names(tickers)
    # if err != "":
    #     print(err)
    # else:
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
# st.write(st.session_state)
