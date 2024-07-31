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


def init_session_state() -> None:
    st.session_state.tickers_and_constraints = pd.DataFrame()
    st.session_state.names_and_inceptions = pd.DataFrame()
    st.session_state.start_date = None
    st.session_state.end_date = None
    st.session_state.rf_rate = None
    st.session_state.adj_daily_close=pd.DataFrame()
    st.session_state.growth_of_10000 = pd.DataFrame()
    st.session_state.expected_returns = pd.DataFrame()
    st.session_state.std_deviations = pd.DataFrame()
    st.session_state.correlation_matrix = pd.DataFrame()
    st.session_state.efficient_frontier = pd.DataFrame()
    st.session_state.selected_port = None


def configure_page() -> None:
    st.set_page_config(page_title="Efficient Frontier", layout="wide")


def overview() -> None:
    st.markdown("## Overview")
    st.markdown(
        "#### This app determines the Efficient Frontier for a specified list of investments and timeframe."
    )
    st.markdown(
        "The objective is to determine the optimum diversification of an investment portfolio."
    )
    st.divider()


def sidebar():
    def reset_all() -> None:
        st.session_state.tickers_and_constraints = pd.DataFrame()
        st.session_state.names_and_inceptions = pd.DataFrame()
        st.session_state.start_date = None
        st.session_state.end_date = None
        st.session_state.rf_rate = None
        st.session_state.adj_daily_close=pd.DataFrame()
        st.session_state.growth_of_10000 = pd.DataFrame()
        st.session_state.expected_returns = pd.DataFrame()
        st.session_state.std_deviations = pd.DataFrame()
        st.session_state.correlation_matrix = pd.DataFrame()
        st.session_state.efficient_frontier = pd.DataFrame()
        st.session_state.selected_port = None

    def reset_start_end_and_rf_rate():
        st.session_state.start_date = None
        st.session_state.end_date = None
        st.session_state.rf_rate = None

    with st.sidebar:
        st.markdown("# Configure Analysis")
        st.markdown("### Step 1: Select Excel File with Tickers & Constraints")
        options: list[str] = ["Major Asset Classes", "Industry Sectors", "Custom"]
        opt = st.selectbox("Select Scenario", options, index=None)
        if opt == options[0]:
            st.session_state.tickers_and_constraints = pd.read_excel(
                "./data/asset_classes.xlsx"
            )
        elif opt == options[1]:
            st.session_state.tickers_and_constraints = pd.read_excel(
                "./data/industry_sectors.xlsx"
            )
        elif opt == options[2]:
            reset_all()
            f = st.file_uploader("Select Excel File")
            if f:
                st.session_state.tickers_and_constraints = pd.read_excel(f)
        else:
            reset_all()

        # Once Excel File has been selected
        if not st.session_state.tickers_and_constraints.equals(pd.DataFrame()):
            # Check if all tickers are valid
            err, names_and_inceptions = yf_api.get_names_and_inceptions(
                tickers=st.session_state.tickers_and_constraints["Ticker"].tolist()
            )
            if err != "":
                st.error(f"Error! {err}")
                reset_all()
            else:
                st.session_state.names_and_inceptions = names_and_inceptions
                st.markdown("### Step 2: Select Start Date, End Date, & Risk Free Rate")
                with st.form("config_dates_rf_rate"):
                    start_date = st.date_input(
                        "Select Start Date",
                        format="MM/DD/YYYY",
                        value=datetime.today() - timedelta(1) - relativedelta(years=5),
                        # value=datetime(year=2007, month=5, day=29),  # for testing youtube
                    )
                    end_date = st.date_input(
                        "Select End Date",
                        format="MM/DD/YYYY",
                        value=datetime.today() - timedelta(1),
                        # value=datetime(year=2023, month=5, day=20),   # for testing youtube
                    )
                    # rf_rate = st.number_input("Specify Risk-Free Rate", min_value=0.00)
                    rf_rate = st.number_input(
                        "Specify Risk-Free Rate", min_value=0.00, value=3.70
                    )
                    calc_ef_button = st.form_submit_button(
                        "Calculate Efficient Frontier"
                    )
                if calc_ef_button:
                    if end_date < start_date:
                        st.error("Error! Start Date must be less than End Date.")
                        reset_start_end_and_rf_rate()
                    else:
                        st.session_state.start_date = start_date
                        st.session_state.end_date = end_date
                        st.session_state.rf_rate = rf_rate


@st.cache_data
def get_data_from_yf(tickers:list,start,end):
    return yf_api.get_adj_daily_close(tickers, start, end)



@st.cache_data
def calc_port_stats(adj_daily_close):
    growth_of_10000 = ps.get_growth_10000(adj_daily_close)
    # daily_returns = ps.get_daily_returns(adj_daily_close)
    daily_ln_returns = ps.get_daily_ln_returns(adj_daily_close)
    correlation_matrix = ps.get_correlation_matrix(daily_ln_returns)
    expected_returns = ps.get_expected_returns(daily_ln_returns)
    std_deviations = ps.get_std_deviations(daily_ln_returns)
    cov_matrix = ps.get_cov_matrix(daily_ln_returns)
    # inv_cov_matrix = ps.get_inv_cov_matrix(cov_matrix)
    efficient_frontier = ef.get_efficient_frontier(
        st.session_state.tickers_and_constraints,
        st.session_state.rf_rate / 100,
        adj_daily_close,
    )
    efficient_frontier.rename(columns={"Risk": "Std Dev"}, inplace=True)
    return (
        growth_of_10000,
        expected_returns,
        std_deviations,
        correlation_matrix,
        efficient_frontier,
    )


def display_configuration() -> None:
    if st.session_state.start_date != None:
        with st.expander(
            "Analysis Configuration (Click to Hide / Show)",
            expanded=True,
        ):
            st.markdown("#### Analysis Configuration:")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"###### History Start Date: {st.session_state.start_date.strftime("%Y-%m-%d")}")
            with col2:
                st.markdown(f"###### History End Date: {st.session_state.end_date.strftime("%Y-%m-%d")}")
            with col3:
                st.markdown(f"###### Risk-Free Rate: {st.session_state.rf_rate:.2f}%")
            st.markdown("###### Investments & Constraints:")
            df2: pd.DataFrame = st.session_state.names_and_inceptions
            df2["Inception"] = df2["Inception"].dt.strftime("%Y-%m-%d")
            df2["Ticker"] = df2.index
            df = pd.merge(st.session_state.tickers_and_constraints, df2)
            df = df[["Ticker", "Name", "Min Weight", "Max Weight", "Inception"]]
            st.dataframe(
                df.style.format(
                    {
                        "Min Weight": "{:.2%}",
                        "Max Weight": "{:.2%}",
                    },
                )
            )


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
    names_and_inceptions, expected_returns, std_deviations
) -> None:
    with st.expander(
        "Expected Return & Standard Deviation (Click to Hide / Show)", expanded=True
    ):
        df = pd.DataFrame(
            {
                "Investment": names_and_inceptions["Investment"],
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
                yaxis_title="Annual Return",
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

    def set_portfolio(abs_value, inc_value):
        if abs_value == None:
            st.session_state["selected_portfolio"] += inc_value
            if st.session_state["selected_portfolio"] < 0:
                st.session_state["selected_portfolio"] = 0
            if st.session_state["selected_portfolio"] > len(ef.index):
                st.session_state["selected_portfolio"] = len(ef.index)
        else:
            st.session_state["selected_portfolio"] = abs_value
        print(
            st.session_state[
                "FormSubmitter:config_dates_rf_rate-Calculate Efficient Frontier"
            ]
        )

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.button(
            "Min Risk Portfolio", on_click=set_portfolio, args=(0, None), type="primary"
        )
    with col2:
        st.button(
            "Reduce Risk & Return",
            on_click=set_portfolio,
            args=(None, -1),
            type="primary",
        )
    with col3:
        st.button(
            "Max Sharpe Portfolio",
            on_click=set_portfolio,
            args=(ef["Sharpe"].idxmax(), None),
            type="primary",
        )
    with col4:
        st.button(
            "Increase Risk & Return",
            on_click=set_portfolio,
            args=(None, 1),
            type="primary",
        )
    with col5:
        st.button(
            "Max Risk & Return",
            on_click=set_portfolio,
            args=(len(ef.index), None),
            type="primary",
        )

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
        # fig.add_trace(
        #     go.Scatter(
        #         x=[portfolio_with_max_sharpe["Std Dev"]],
        #         y=[portfolio_with_max_sharpe["Return"]],
        #         name="Max Sharpe Ratio",
        #         marker=dict(color="red", size=10),
        #         mode="markers",
        #     )
        # )
        # fig.add_trace(
        #     go.Scatter(
        #         x=[selected_portfolio["Std Dev"]],
        #         y=[selected_portfolio["Return"]],
        #         name="Selected Portfolio",
        #         marker=dict(
        #             size=25,
        #             symbol="diamond",
        #             line=dict(width=2, color="green"),
        #             opacity=0.5,
        #         ),
        #     )
        # )

        fig.update_xaxes(rangemode="tozero")
        fig.update_yaxes(rangemode="tozero")
        fig.update_layout(height=600, width=600, title=dict(text="Efficient Frontier"))
        fig.update_layout(
            xaxis_title="Annual Standard Deviation (Risk)",
            yaxis_title="Annual Return",
            xaxis=dict(tickformat=".2%"),
            yaxis=dict(tickformat=".2%"),
        )
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.write("Display Portfolio for Selected Point on Efficient Frontier")
    st.divider()
    format_dict: dict[str, str] = {}
    for c in ef.columns:
        format_dict[c] = "{:.2%}"
    st.dataframe(ef.style.format(formatter=format_dict))


if __name__ == "__main__":
    configure_page()

    # Init session_state if not done so already
    if len(st.session_state) == 0:
        init_session_state()

    # st.write(st.session_state)
    overview()
    sidebar()
    display_configuration()
    
    # Once Analysis is Configured (Indicated by History End Date being specified)
    if st.session_state.end_date!=None:
        # Get Adjust Daily Close Prices
        st.session_state.adj_daily_close=get_data_from_yf(st.session_state.tickers_and_constraints["Ticker"].tolist(),st.session_state.start_date,st.session_state.end_date)
        
       # Calculate Portfolio Statistics based on Adjust Daily Closing Prices
        (
            st.session_state.growth_of_10000,
            st.session_state.expected_returns,
            st.session_state.std_deviations,
            st.session_state.correlation_matrix,
            st.session_state.efficient_frontier,
        ) = calc_port_stats(st.session_state.adj_daily_close)
        
        display_growth_of_10000_table(st.session_state.tickers_and_constraints, st.session_state.growth_of_10000)
        # display_growth_of_10000_graph(tickers_and_constraints, growth_of_10000)
        # display_return_and_sd_table_and_graph(names_and_inceptions, expected_returns, std_deviations)
        # display_correlation_matrix(correlation_matrix)
        # display_efficient_frontier(efficient_frontier)

st.write(st.session_state)
