import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
from datetime import datetime

# Streamlit app setup
st.title("YieldMax Funds Dashboard")
st.write("This application fetches data for all YieldMax funds from inception, plots their value since inception, and displays a table of all dividends paid.")

# Define YieldMax fund ticker symbols (from YieldMax ETFs website)
yieldmax_tickers = [
    "TSLY", "OARK", "APLY", "NVDY", "AMZY", "FBY", "GOOY", "CONY", "NFLY", "DISO", 
    "MSFO", "XOMO", "JPMO", "AMDY", "PYPY", "SQY", "MRNY", "AIYY", "YMAX", "YMAG", 
    "MSTY", "ULTY", "YBIT", "CRSH", "GDXY", "SNOY", "ABNY", "FIAT", "DIPS", "BABO", 
    "YQQQ", "TSMY", "SMCY", "PLTY", "BIGY", "SOXY", "MARO"
]

# Sidebar for selecting indices to display
st.sidebar.title("Select YieldMax Funds")
st.sidebar.write("Choose which YieldMax funds to display in the analysis.")
selected_tickers = st.sidebar.multiselect("Select Funds", yieldmax_tickers, default=["YMAX", "YMAG"])

# Function to fetch data from Yahoo Finance
def fetch_yieldmax_data(tickers):
    data = {}
    dividends = {}
    for ticker in tickers:
        stock_data = yf.Ticker(ticker)
        hist = stock_data.history(period="max")
        divs = stock_data.history(period="max")[["Dividends"]].reset_index()
        divs.columns = ["Date", "Dividends"]
        divs["Dividends"] = divs["Dividends"].fillna(0)  # Fill missing dividends with 0
        divs["Date"] = pd.to_datetime(divs["Date"]).dt.tz_localize(None)  # Remove timezone info
        data[ticker] = hist
        dividends[ticker] = divs
    return data, dividends

# Create session state to avoid page reload
if "fund_data" not in st.session_state:
    st.session_state.fund_data = {}
if "fund_dividends" not in st.session_state:
    st.session_state.fund_dividends = {}

# Button to trigger data fetching and visualization
if st.button("Fetch and Display YieldMax Data"):
    st.write("Fetching data... This may take a moment.")

    # Fetch the data
    st.session_state.fund_data, st.session_state.fund_dividends = fetch_yieldmax_data(selected_tickers)

# Determine the date range from the fetched data
if st.session_state.fund_dividends:
    all_dividends = [dividends for dividends in st.session_state.fund_dividends.values()]
    combined_dividends = pd.concat(all_dividends)
    combined_dividends["Date"] = pd.to_datetime(combined_dividends["Date"]).dt.tz_localize(None)
    min_date = combined_dividends["Date"].min()
    max_date = combined_dividends["Date"].max()
else:
    min_date = datetime(2000, 1, 1)
    max_date = datetime.today()

# Sidebar for date range filter
st.sidebar.title("Filter Date Range")
start_date = st.sidebar.date_input("Start Date", min_date, min_value=min_date, max_value=max_date)
end_date = st.sidebar.date_input("End Date", max_date, min_value=min_date, max_value=max_date)

# Plotting the fund values
if st.session_state.fund_data:
    st.subheader("Fund Values Since Inception")
    fig = go.Figure()
    for ticker, hist in st.session_state.fund_data.items():
        fig.add_trace(go.Scatter(x=hist.index, y=hist["Close"], mode='lines', name=ticker))
    fig.update_layout(
        title="YieldMax Fund Values Since Inception",
        xaxis_title="Date",
        yaxis_title="Value ($)",
        legend_title="Funds",
        height=600,  # Increased plot size
        margin=dict(t=50, b=100)
    )
    st.plotly_chart(fig)

# Display dividends for all selected funds
if st.session_state.fund_dividends:
    st.subheader("Dividends Paid for All Selected Funds")
    all_dividends = []
    for ticker, dividends in st.session_state.fund_dividends.items():
        dividends["Ticker"] = ticker
        all_dividends.append(dividends)

    if all_dividends:
        combined_dividends = pd.concat(all_dividends)
        combined_dividends["Date"] = pd.to_datetime(combined_dividends["Date"]).dt.tz_localize(None)  # Remove timezone info
        filtered_dividends = combined_dividends[(combined_dividends["Date"] >= pd.to_datetime(start_date)) & (combined_dividends["Date"] <= pd.to_datetime(end_date))]
        pivoted_dividends = filtered_dividends.pivot(index="Ticker", columns="Date", values="Dividends")
        # Drop columns with only 0, 1, or NaN values
        pivoted_dividends = pivoted_dividends.loc[:, ~((pivoted_dividends == 0).all(axis=0) | (pivoted_dividends == 1).all(axis=0) | pivoted_dividends.isna().all(axis=0))]
        st.dataframe(pivoted_dividends)

        # Create a bar chart for dividends
        st.subheader("Dividends Visualization")
        fig_dividends = make_subplots(specs=[[{"secondary_y": False}]])
        for ticker in pivoted_dividends.index:
            non_zero_data = pivoted_dividends.loc[ticker][pivoted_dividends.loc[ticker] > 0]
            fig_dividends.add_trace(
                go.Bar(
                    x=non_zero_data.index,
                    y=non_zero_data.values,
                    name=ticker
                )
            )
        fig_dividends.update_layout(
            title="Dividends Over Time",
            xaxis_title="Date",
            yaxis_title="Dividends ($)",
            barmode="group",
            height=500,
            margin=dict(t=50, b=50)
        )
        st.plotly_chart(fig_dividends)
    else:
        st.write("No dividend data available for the selected funds.")
else:
    st.write("Click the button above to fetch and display YieldMax fund data.")
