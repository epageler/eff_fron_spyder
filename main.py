from typing import Tuple

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import numpy as np
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
    st.session_state.curr_rf_rate = yf_api.get_previous_close('^TNX')/100
    st.session_state.rf_rate = None
    st.session_state.adj_daily_close = pd.DataFrame()
    st.session_state.growth_of_10000 = pd.DataFrame()
    st.session_state.expected_returns = pd.DataFrame()
    st.session_state.std_deviations = pd.DataFrame()
    st.session_state.correlation_matrix = pd.DataFrame()
    st.session_state.efficient_frontier = pd.DataFrame()
    st.session_state.selected_port = None
    st.session_state.current_portfolio_return = None
    st.session_state.current_portfolio_sd = None
    st.session_state.current_portfolio_sharpe = None


def configure_page() -> None:
    st.set_page_config(page_title="Efficient Frontier", layout="wide")


def overview() -> None:
    st.markdown("### Overview:")
    st.markdown(
        "##### This app determines the Efficient Frontier for a specified list of investments."
    )
    st.markdown(
        "The objective is to determine the optimum diversification of an investment portfolio. The optimum portfolio is defined as one that maximizes return for a give level of risk, as measured by Standard Deviation.")
    st.markdown("It also allows you to compare the current diversification of your portfolio to a selected portfolio on the Efficient Frontier.")

    st.markdown("### Instructions:")
    with st.expander("Instructions to Use Application. (Click to Hide/Show)", expanded=False):
        st.markdown(
            "To get started, follow the Steps listed in the sidebar on the left.")
        st.markdown("If you want to determine the Efficient Frontier for your own list of investments, select \"Custom\" scenario and drag & drop an Excel file from your computer.")
        st.markdown(
            "The Excel file must have the following format: (Be sure to spell the column headings exactly as shown.)")
        st.image("./data/custom_excel_format.png")
        st.markdown(
            "If you would like to compare your current portfolio to the Efficient Frontier, enter the current investment weights of your portfolio in the \"Curr Weight\" column.")

    st.markdown("### Additional Resources:")
    with st.expander("Additional Resources on Efficient Frontier (Click to Show/Hide)", expanded=False):
        st.markdown("##### Some useful resources:")
        st.markdown(
            "1. Article: Efficient Frontier: What It Is and How Investors Use It by Akhilesh Ganti  \nlink: www.investopedia.com/terms/e/efficientfrontier.asp")
        st.markdown("2. Article: Markowitz Efficient Set: Meaning, Implementation, Diversification by Will Kenton  \nlink: www.investopedia.com/terms/m/markowitzefficientset.asp")
        st.markdown("3. Video: Efficient Frontier and Portfolio Optimization Explained | The Ultimate Guide by Ryan O'Connell, CFA, FRM  \n link: www.youtube.com/watch?v=pwyR9uAM0iU&list=PLPe-_ytPHqygIlNok8a3pm1xwHXwVsYmv&index=1&t=44s")
        st.markdown(
            "4. Video: Portfolio Optimization in Excel: Step by Step Tutorial by Ryan O'Connell, CFA, FRM  \nlink: www.youtube.com/watch?v=XQS17YrZvEs&list=LL&index=2")


def sidebar():
    def reset_all() -> None:
        st.session_state.tickers_and_constraints = pd.DataFrame()
        st.session_state.names_and_inceptions = pd.DataFrame()
        st.session_state.start_date = None
        st.session_state.end_date = None
        st.session_state.rf_rate = None
        st.session_state.adj_daily_close = pd.DataFrame()
        st.session_state.growth_of_10000 = pd.DataFrame()
        st.session_state.expected_returns = pd.DataFrame()
        st.session_state.std_deviations = pd.DataFrame()
        st.session_state.correlation_matrix = pd.DataFrame()
        st.session_state.efficient_frontier = pd.DataFrame()
        st.session_state.selected_port = None
        st.session_state.current_portfolio_return = None
        st.session_state.current_portfolio_sd = None
        st.session_state.current_portfolio_sharpe = None

    def reset_start_end_and_rf_rate():
        st.session_state.start_date = None
        st.session_state.end_date = None
        st.session_state.rf_rate = None
        st.session_state.selected_port = None

    with st.sidebar:
        st.markdown("# Configure Analysis:")
        st.markdown(
            "#### Step 1: Select Pre-Configured Scenario or Select Custom Excel File")
        old_tickers_and_constraints = st.session_state.tickers_and_constraints
        options: list[str] = ["Major Asset Classes, Constrained",
                              "Major Asset Classes, Unconstrained",
                              "S&P Industry Sectors, Constrained",
                              "S&P Industry Sectors, Unconstrained",
                              "Custom"]
        opt = st.selectbox("Select Scenario", options, index=None,
                           help='Select from list of pre-configured scenario. Or, choose \"Custom\" & drag & drop Excel file from your computer.')
        if opt == options[0]:
            st.session_state.tickers_and_constraints = pd.read_excel(
                "./data/asset_classes_constrained.xlsx"
            )
        elif opt == options[1]:
            st.session_state.tickers_and_constraints = pd.read_excel(
                "./data/asset_classes_unconstrained.xlsx"
            )
        elif opt == options[2]:
            st.session_state.tickers_and_constraints = pd.read_excel(
                "./data/industry_sectors_constrained.xlsx"
            )
        elif opt == options[3]:
            st.session_state.tickers_and_constraints = pd.read_excel(
                "./data/industry_sectors_unconstrained.xlsx"
            )
        elif opt == options[4]:
            f = st.file_uploader("Select Excel File")
            if f:
                st.session_state.tickers_and_constraints = pd.read_excel(f)
        else:
            reset_all()
        if not st.session_state.tickers_and_constraints.equals(old_tickers_and_constraints):
            reset_start_end_and_rf_rate()

        # Once Excel File has been selected
        if not st.session_state.tickers_and_constraints.equals(pd.DataFrame()):
            # Check if all tickers are valid
            err, names_and_inceptions = yf_api.get_names_and_inceptions(
                tickers=st.session_state.tickers_and_constraints["Ticker"].tolist(
                )
            )
            if err != "":
                st.error(f"Error! {err}")
                reset_all()
            else:
                st.session_state.names_and_inceptions = names_and_inceptions
                st.markdown(
                    "#### Step 2: Select History Start Date &End Date and Risk Free Rate")
                # Find latest inception date
                df = names_and_inceptions
                max_inception_date: datetime = df.loc[df.loc[:, 'Inception'].idxmax(
                ), "Inception"].date()
                df = st.session_state.tickers_and_constraints
                min_weight: float = df.loc[df.loc[:,
                                                  'Min Weight'].idxmin(), 'Min Weight']
                max_weight: float = df.loc[df.loc[:,
                                                  'Max Weight'].idxmax(), 'Max Weight']
                min_less_than_max_weights = df['Min Weight'] <= df['Max Weight']
                sum_of_max_weights: float = df["Max Weight"].sum()
                sum_of_curr_weights: float = df["Curr Weight"].sum()
                with st.form("config_dates_rf_rate"):
                    start_date = st.date_input(
                        "Select Start Date (MM-DD-YYYY)",
                        format="MM-DD-YYYY",
                        value=max_inception_date,
                        # value=datetime.today() - timedelta(1) - relativedelta(years=3),
                        # for testing youtube
                        # value=datetime(year=2007, month=5, day=29),
                        min_value=max_inception_date,
                        help='Defaults to latest Inception Date of selected investments.'
                    )
                    end_date = st.date_input(
                        "Select End Date (MM-DD-YYYY)",
                        format="MM-DD-YYYY",
                        value=datetime.today() - timedelta(1),
                        # for testing youtube
                        # value=datetime(year=2023, month=5, day=20),
                        help='Defaults to yesterday'
                    )
                    # rf_rate = st.number_input("Specify Risk-Free Rate", min_value=0.00)
                    rf_rate = st.number_input(
                        "Specify Risk-Free Rate", min_value=0.00, value=st.session_state.curr_rf_rate*100,
                        help='Defaults to current yield on 10-year Treasury bond.'
                    )
                    calc_ef_button = st.form_submit_button(
                        "Calculate Efficient Frontier"
                    )
                if calc_ef_button:
                    if end_date < start_date:
                        st.error(
                            "Invalid! Start Date must be less than End Date.")
                        reset_start_end_and_rf_rate()
                    elif start_date < max_inception_date:
                        st.error(f"Invalid! Start Date cannot be precede latest inception date of {
                                 max_inception_date}.")
                        reset_start_end_and_rf_rate()
                    elif min_weight < 0:
                        st.error(
                            f"Invalid! Minimum investment weights must be greater than or equal to 0%.")
                        reset_start_end_and_rf_rate()
                    elif max_weight > 1.0:
                        st.error(
                            f"Invalid! Maximum investment weights must be less than or equal to 100%.")
                        reset_start_end_and_rf_rate()
                    elif not min_less_than_max_weights.all():
                        st.error(
                            f"Invalid! Minimum Investment weights must be less than or equal to Maximum Investment Weights.")
                        reset_start_end_and_rf_rate()
                    elif sum_of_max_weights < 1:
                        st.error(
                            'Invalid! Sum of Maximum Weights of investments must be greater than or equal to 100%')
                        reset_start_end_and_rf_rate()
                    elif sum_of_curr_weights > 1.00:
                        st.error(
                            'Invalid! Sum of Current Weights of investments must be less than or equal to 100%')
                        reset_start_end_and_rf_rate()
                    else:
                        st.session_state.start_date = start_date
                        st.session_state.end_date = end_date
                        st.session_state.rf_rate = rf_rate
                        st.session_state.selected_port = None


@st.cache_data
def get_data_from_yf(tickers: list, start, end):
    return yf_api.get_adj_daily_close(tickers, start, end)


@st.cache_data
def calc_port_stats(inv_and_constraints, risk_free_rate, adj_daily_close):
    growth_of_10000 = ps.get_growth_10000(adj_daily_close)
    daily_returns = ps.get_daily_returns(adj_daily_close)
    daily_ln_returns = ps.get_daily_ln_returns(adj_daily_close)
    correlation_matrix = ps.get_correlation_matrix(daily_ln_returns)
    expected_returns = ps.get_expected_returns(daily_ln_returns)
    std_deviations = ps.get_std_deviations(daily_ln_returns)
    cov_matrix = ps.get_cov_matrix(daily_ln_returns)
    inv_cov_matrix = ps.get_inv_cov_matrix(cov_matrix)
    efficient_frontier = ef.get_efficient_frontier(
        inv_and_constraints,
        risk_free_rate / 100,
        adj_daily_close,
    )
    efficient_frontier.rename(columns={"Risk": "Std Dev"}, inplace=True)
    if not (inv_and_constraints['Curr Weight'] == 0).all():
        current_portfolio_return = ps.get_portfolio_return(
            inv_and_constraints['Curr Weight'],
            expected_returns)
        current_portfolio_sd: float = ps.get_portfolio_sd(
            inv_and_constraints['Curr Weight'], cov_matrix)
        current_portfolio_sharpe: float = (
            current_portfolio_return-st.session_state.rf_rate/100)/current_portfolio_sd
    else:
        current_portfolio_return, current_portfolio_sd, current_portfolio_sharpe = None, None, None
    return (
        growth_of_10000,
        expected_returns,
        std_deviations,
        cov_matrix,
        correlation_matrix,
        efficient_frontier,
        current_portfolio_return,
        current_portfolio_sd,
        current_portfolio_sharpe
    )


def display_configuration() -> None:
    with st.expander("Analysis Configuration (Click to Hide / Show)", expanded=True,):
        if not st.session_state.names_and_inceptions.equals(pd.DataFrame()):
            st.markdown("#### Analysis Configuration:")
            st.markdown("###### Investments & Constraints:")
            df2: pd.DataFrame = st.session_state.names_and_inceptions
            df2["Inception"] = df2["Inception"].dt.strftime("%Y-%m-%d")
            df2["Ticker"] = df2.index
            df = pd.merge(st.session_state.tickers_and_constraints, df2)
            df = df[["Ticker", "Name", "Min Weight",
                     "Max Weight", "Curr Weight", "Inception"]]
            st.dataframe(
                df.style.format(
                    {
                        "Min Weight": "{:.2%}",
                        "Max Weight": "{:.2%}",
                        "Curr Weight": "{:.2%}",
                    },
                )
            )
        if st.session_state.start_date != None:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"###### History Start Date: {
                            st.session_state.start_date.strftime('%Y-%m-%d')}")
            with col2:
                st.markdown(f"###### History End Date: {
                            st.session_state.end_date.strftime("%Y-%m-%d")}")
            with col3:
                st.markdown(  # The above code is using f-string formatting in Python to display the
                    # value of `st.session_state.rf_rate` with two decimal places followed by
                    # a percentage sign. The text "Risk-Free Rate: " is also included in the
                    # output.

                    f"###### Risk-Free Rate: {st.session_state.rf_rate:.2f}%")


def display_growth_of_10000_table(tickers_and_constraints: pd.DataFrame, growth_of_10000: pd.DataFrame) -> None:
    df = growth_of_10000
    df.index = pd.to_datetime(df.index).strftime('%Y-%m-%d')
    with st.expander("Growth of $10,000 Table (Click to Hide / Show)", expanded=True):
        st.markdown("#### Growth of $10,000")
        tickers: list[str] = tickers_and_constraints["Ticker"]
        # adj_daily_close = yf_api.get_adj_daily_close(tickers, start, end)
        # growth_of_10000 = ps.get_growth_10000(adj_daily_close)
        columns = df.columns
        format_dict: dict[str, str] = {}
        for c in columns:
            format_dict[c] = "${:,.2f}"
        st.dataframe(
            df.iloc[[-1]].style.format(formatter=format_dict))


def display_growth_of_10000_graph(tickers_and_constraints: pd.DataFrame, growth_of_10000: pd.DataFrame) -> None:
    with st.expander("Growth of $10,000 Graph (Click to Hide / Show)", expanded=True):
        # Display Graph
        customdata_set: list = list(
            tickers_and_constraints[['Ticker']].to_numpy())
        columns = growth_of_10000.columns
        fig = px.line(
            growth_of_10000,
            x=growth_of_10000.index,  # date column
            y=growth_of_10000.columns[0: len(
                growth_of_10000.columns)],   # Value on date
            title="Growth of $10,000",
        )
        fig.update_traces(
            customdata=customdata_set,
            hovertemplate="Date: %{x}<br>Value: $%{y:,.0f}",
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

        # Display ending value of $10,000 investment
        df = growth_of_10000
        columns = df .columns
        format_dict: dict[str, str] = {}
        for c in columns:
            format_dict[c] = "${:,.2f}"
        # Convert Timestamp index to string
        df.index = df.index.astype(str)
        st.markdown('Ending value of $10,000 Investment:')
        st.dataframe(
            df.iloc[[-1]].style.format(formatter=format_dict))


def display_return_and_sd_table_and_graph(
    names_and_inceptions, expected_returns, std_deviations
) -> None:
    with st.expander(
        "Annual Return, Standard Deviation, & Sharpe Ratio for Each Investment (Click to Hide / Show)", expanded=True
    ):
        df = pd.DataFrame(
            {
                "Investment": names_and_inceptions["Name"],
                "Return": expected_returns,
                "Std Dev": std_deviations,
            }
        )
        df['Sharpe'] = (
            df['Return']-st.session_state.rf_rate/100)/df['Std Dev']
        df = df.reset_index()
        df = df.rename(columns={"index": "Ticker"})
        col1, col2 = st.columns([6, 6])
        with col1:
            st.markdown("##### Annual Return, Standard Deviation, & Sharpe")
            st.dataframe(df.style.format(
                {"Return": "{:.2%}", "Std Dev": "{:.2%}", "Sharpe": "{:.2f}"}))
        with col2:
            customdata_set = list(df[['Investment']].to_numpy())
            fig = go.Figure(
                go.Scatter(
                    x=df["Std Dev"],
                    y=df["Return"],
                    customdata=customdata_set,
                    name="",
                    text=pd.Series(expected_returns).index,
                    mode="markers+text",
                    showlegend=False,
                )
            )
            fig.update_traces(
                textposition="middle right",
                marker=dict(size=7, color="red"),
                hovertemplate='<b>%{customdata[0]}</b><br>' + 'Return: %{y}<br>' +
                'Std Dev: %{x}',
            )
            fig.update_xaxes(showgrid=True)
            fig.update_yaxes(showgrid=True)
            fig.update_layout(
                title="Standard Deviation vs Return",
                # title_x=0.25,
                xaxis_title="Annual Std Deviation (Risk)",
                yaxis_title="Annual Return",
                xaxis=dict(tickformat=".2%"),
                yaxis=dict(tickformat=".2%"),
                autosize=True,
                # width=600,
                # height=500,
            )
            # st.plotly_chart(fig, use_container_width=True)
            st.plotly_chart(fig)


def display_correlation_matrix(cm: pd.DataFrame, names_and_inceptions: pd.DataFrame) -> None:
    with st.expander(
        "Investment Correlation Matrix (Click to Hide / Show)", expanded=True
    ):
        # Create hover text
        hover_text = list()
        for y_index, y_name in enumerate(cm.index):
            hover_text.append(list())
            for x_index, x_name in enumerate(cm.index):
                hover_text[-1].append(f"{names_and_inceptions.loc[x_name, 'Name']} ({x_name})<br>vs {
                                      names_and_inceptions.loc[y_name, 'Name']} ({y_name})<br>Correlation: {cm.loc[x_name, y_name]:.2f}")

        cm = cm.round(decimals=2)
        fig = go.Figure(
            data=go.Heatmap(
                z=cm,
                x=cm.index,
                y=cm.index,
                colorscale="RdBu_r",
                texttemplate="%{z}",
                zmin=-1,
                zmax=1,
                hoverinfo='text',
                text=hover_text
            )
        )

        fig.update_traces()

        fig.update_layout(
            title="Investment Correlation Matrix",
            title_font_size=24,
            # title_x=0.5,
            autosize=False,
            width=900,
            height=900,
            font=dict(size=18),
            hoverlabel_align='right',
            hoverlabel=dict(font=dict(size=16))
        )
        st.plotly_chart(fig)


def display_efficient_frontier(ef: pd.DataFrame):
    st.markdown("##### Efficient Frontier")

    if st.session_state.selected_port == None:
        st.session_state.selected_port = ef['Sharpe'].idxmax()

    def set_portfolio(abs_value, inc_value):
        if abs_value == None:
            st.session_state.selected_port += inc_value
            if st.session_state.selected_port < 0:
                st.session_state.selected_port = 0
            if st.session_state.selected_port > (len(ef)-1):
                st.session_state.selected_port = len(ef)-1
        else:
            st.session_state.selected_port = abs_value

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
            args=(len(ef.index)-1, None),
            type="primary",
        )

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"#### Efficient Frontier:")
        st.markdown('---')
        selected_portfolio = ef.iloc[st.session_state.selected_port]

        fig = go.Figure(
            go.Scatter(
                x=ef["Std Dev"],
                y=ef["Return"],
                name="Efficient Frontier",
                mode="lines+markers",
                customdata=ef[['Std Dev', 'Return', 'Sharpe']],
                hovertemplate='Return: %{customdata[1]:.2%}<br>' +
                'Std Dev: %{customdata[0]:.2%}<br>' +
                'Sharpe: %{customdata[2]:.2f}',
            )
        )
        fig.add_trace(
            go.Scatter(
                x=[ef.iloc[ef['Sharpe'].idxmax()]['Std Dev']],
                y=[ef.iloc[ef['Sharpe'].idxmax()]['Return']],
                name="Max Sharpe Ratio",
                customdata=[ef.iloc[ef['Sharpe'].idxmax()]['Sharpe']],
                hovertemplate='Return: %{y:.2%}<br>' +
                'Std Dev: %{x:.2%}<br>' +
                'Sharpe: %{customdata:.2f}',
                marker=dict(color="red", size=10),
                mode="markers",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=[selected_portfolio["Std Dev"]],
                y=[selected_portfolio["Return"]],
                name="Selected Portfolio",
                customdata=selected_portfolio[['Sharpe']],
                hovertemplate='Return: %{y:.2%}<br>' +
                'Std Dev: %{x:.2%}<br>' +
                'Sharpe: %{customdata:.2f}',
                marker=dict(
                    size=25,
                    symbol="diamond",
                    line=dict(width=2, color="green"),
                    opacity=0.5,
                ),
            )
        )
        fig.add_trace(
            go.Scatter(
                x=[st.session_state.current_portfolio_sd],
                y=[st.session_state.current_portfolio_return],
                name="Current Portfolio",
                customdata=[st.session_state.current_portfolio_sharpe],
                hovertemplate='Return: %{y:.2%}<br>' +
                'Std Dev: %{x:.2%}<br>' +
                'Sharpe: %{customdata:.2f}',
                marker=dict(color="green", size=10),)
        )
        fig.update_xaxes(rangemode="tozero")
        fig.update_yaxes(rangemode="tozero")
        fig.update_layout(height=500, width=500,
                          title=dict(text=""))
        fig.update_layout(
            xaxis_title="Annual Standard Deviation (Risk)",
            yaxis_title="Annual Return",
            xaxis=dict(tickformat=".2%"),
            yaxis=dict(tickformat=".2%"),
        )
        fig.update_traces(
            textposition="middle right",
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown(f"#### Portfolio Diversification:")
        st.markdown('---')
        df = ef.iloc[st.session_state.selected_port]
        selected_port_tickers = df.index.tolist()[3:]
        selected_port_diversification = df.iloc[3:len(df)]
        customdata_set = st.session_state.names_and_inceptions[[
            'Name']]
        values = selected_port_diversification.tolist()
        labels = selected_port_tickers
        fig = go.Figure(data=[go.Pie(
                        values=values,
                        labels=labels,
                        customdata=customdata_set,
                        name="",
                        sort=False, direction='clockwise',
                        showlegend=True,
                        automargin=False
                        ),
        ]
        )
        fig.update_traces(textinfo='label+percent', textfont_size=14)
        fig.update_traces(
            hovertemplate='<b>%{customdata[0]}</b><br>'+'%{label}<br>'+'%{percent:.1%}',)
        fig.update_layout(height=500,
                          autosize=True,
                          # title='Portfolio Diversification'
                          )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown('##### Statistics of Selected Portfolio:')
    st.text(f"Annual Return: {selected_portfolio['Return']:.2%}   Std Dev: {
            selected_portfolio['Std Dev']:.2%}   Sharpe Ratio: {selected_portfolio['Sharpe']:.2f}")

    # Display Selected Portfolio (+/-) 1 & 2 Std Dev's
    data: dict = {'Probability': ['68% Probability (+/- 1 Std Dev)', '95% Probability (+/- 2 Std Dev\'s'],
                  'Lowest Annual Return': [selected_portfolio['Return']-selected_portfolio['Std Dev'], selected_portfolio['Return']-selected_portfolio['Std Dev']*2],
                  'Highest Annual Return': [selected_portfolio['Return']+selected_portfolio['Std Dev'], selected_portfolio['Return']+selected_portfolio['Std Dev']*2],
                  }
    df: pd.DataFrame = pd.DataFrame(data)
    st.markdown(f"##### Probability of Returns for Selected Portfolio:")
    st.dataframe(df.style.format(
        {"Lowest Annual Return": "{:.2%}", "Highest Annual Return": "{:.2%}"}), hide_index=True)

    with st.expander("Efficient Frontier Table (Click to Hide / Show)", expanded=False):
        format_dict: dict[str, str] = {}
        for c in ef.columns:
            format_dict[c] = "{:.2%}"
        st.dataframe(ef.style.format(formatter=format_dict))


def display_current_vs_selected_portfolio(tickers_and_constraints: pd.DataFrame,
                                          curr_port_sd: float,
                                          curr_port_return: float,
                                          curr_port_sharpe: float,
                                          selected_port: pd.DataFrame) -> None:

    # Check that "Curr Weights" do not violate "Min Weight" / "Max Weight"
    curr_weights = tickers_and_constraints["Curr Weight"]
    min_weights = tickers_and_constraints["Min Weight"]
    max_weights = tickers_and_constraints["Max Weight"]
    tickers = tickers_and_constraints["Ticker"]
    e = []
    for i in range(len(curr_weights)):
        if (curr_weights[i] < min_weights[i] or curr_weights[i] > max_weights[i]):
            e.append(tickers[i])
    if len(e) != 0:
        st.error(
            f"Note! The following investments violate your Minimum / Maximum investment weights: {e}")

    # Check if sum of current investment weights are less than 100%
    s = curr_weights.sum()
    if s < 1:
        st.error(f"Note! The sum of the current weights in your portfolio is {
                 s:.2%}, which is less than 100.00%.")

    with st.expander('Compare Current Portfolio to Selected Portfolio (Click to Hide/Show)', expanded=True):
        st.markdown(f"### Compare Current Portfolio to Selected Portfolio")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"##### Current Portfolio:")
            st.markdown('---')
            df = selected_port
            selected_port_tickers = df.index.tolist()[3:]
            selected_port_diversification = df.iloc[3:len(df)]
            customdata_set = st.session_state.names_and_inceptions[[
                'Name']]
            values = curr_weights.tolist()
            labels = selected_port_tickers
            fig = go.Figure(data=[go.Pie(
                            values=values,
                            labels=labels,
                            customdata=customdata_set,
                            name="",
                            sort=False, direction='clockwise',
                            showlegend=True,
                            automargin=False
                            ),
            ]
            )
            fig.update_traces(textinfo='label+percent', textfont_size=14)
            fig.update_traces(
                hovertemplate='<b>%{customdata[0]}</b><br>'+'%{label}<br>'+'%{percent:.1%}',)
            fig.update_layout(autosize=True,
                              height=500,
                              # title='Selected Portfolio Diversification'
                              )
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            st.markdown(f"##### Selected Portfolio:")
            st.markdown('---')
            df = selected_port
            selected_port_tickers = df.index.tolist()[3:]
            selected_port_diversification = df.iloc[3:len(df)]
            customdata_set = st.session_state.names_and_inceptions[[
                'Name']]
            values = selected_port_diversification.tolist()
            labels = selected_port_tickers
            fig = go.Figure(data=[go.Pie(
                            values=values,
                            labels=labels,
                            customdata=customdata_set,
                            name="",
                            sort=False, direction='clockwise',
                            showlegend=True,
                            automargin=False
                            ),
            ]
            )
            fig.update_traces(textinfo='label+percent', textfont_size=14)
            fig.update_traces(
                hovertemplate='<b>%{customdata[0]}</b><br>'+'%{label}<br>'+'%{percent:.1%}',)
            fig.update_layout(
                # title='Selected Portfolio Diversification',
                height=500, autosize=True)
            st.plotly_chart(fig, use_container_width=True)

        # Display Stats of Current Portfolio vs Selected Portfolio
        data = {'Portfolio': ['Current', 'Selected'],
                'Return': [curr_port_return, selected_port['Return']],
                'Std Dev': [curr_port_sd, selected_port['Std Dev']],
                'Sharpe': [curr_port_sharpe, selected_port['Sharpe']]}
        df: pd.DataFrame = pd.DataFrame(data)
        co11, col2, col3 = st.columns([4, 4, 4])
        with col2:
            st.markdown(f"##### Current Portfolio vs Selected Portfolio")
            st.dataframe(df.style.format(
                {"Return": "{:.2%}", "Std Dev": "{:.2%}", "Sharpe": "{:.2f}"}), hide_index=True)
            # st.dataframe(df,hide_index=True)


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
    if st.session_state.end_date != None:
        # Get Adjust Daily Close Prices
        st.session_state.adj_daily_close = get_data_from_yf(
            st.session_state.tickers_and_constraints["Ticker"].tolist(),
            st.session_state.start_date,
            st.session_state.end_date)

       # Calculate Portfolio Statistics based on Adjust Daily Closing Prices
        (
            st.session_state.growth_of_10000,
            st.session_state.expected_returns,
            st.session_state.std_deviations,
            st.session_state.cov_matrix,
            st.session_state.correlation_matrix,
            st.session_state.efficient_frontier,
            st.session_state.current_portfolio_return,
            st.session_state.current_portfolio_sd,
            st.session_state.current_portfolio_sharpe
        ) = calc_port_stats(st.session_state.tickers_and_constraints,
                            st.session_state.rf_rate,
                            st.session_state.adj_daily_close)

        display_growth_of_10000_graph(
            st.session_state.tickers_and_constraints,
            st.session_state.growth_of_10000)
        # display_growth_of_10000_table(
        #     st.session_state.tickers_and_constraints,
        #     st.session_state.growth_of_10000)
        display_return_and_sd_table_and_graph(
            st.session_state.names_and_inceptions,
            st.session_state.expected_returns,
            st.session_state.std_deviations)
        display_correlation_matrix(
            st.session_state.correlation_matrix, st.session_state.names_and_inceptions)
        display_efficient_frontier(st.session_state.efficient_frontier)
        if not np.isnan(st.session_state.current_portfolio_return):
            display_current_vs_selected_portfolio(
                st.session_state.tickers_and_constraints,
                st.session_state.current_portfolio_sd,
                st.session_state.current_portfolio_return,
                st.session_state.current_portfolio_sharpe,
                st.session_state.efficient_frontier.iloc[
                    st.session_state.selected_port])

        # Inspect Session_State
        # with st.expander('Inspect session_state (Click to Show/Hide)', expanded=False):
        #     pass
        #     st.write(st.session_state)
