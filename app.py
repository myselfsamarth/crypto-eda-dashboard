import os
import streamlit as st
import pandas as pd
import plotly.express as px

# — Page configuration —
st.set_page_config(
    page_title="Crypto EDA Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# — Title —
st.title("📊 Crypto EDA Dashboard")

# — Palette for dark mode —
PALETTE = px.colors.qualitative.Dark24

# — Cached CSV readers —
@st.cache_data
def _read_csv(path):
    return pd.read_csv(path, parse_dates=["Date"])

@st.cache_data
def _get_last_date(path):
    tmp = pd.read_csv(path, usecols=["Date"], parse_dates=["Date"])
    return tmp["Date"].max()

# — Attempt to load local data —
candidates = [
    "crypto_features.csv",
    "master_crypto_daily_prices.csv",
    os.path.expanduser("~/Documents/Germany/TUBerlin/Projects/crypto_features.csv"),
    os.path.expanduser("~/Documents/Germany/TUBerlin/Projects/master_crypto_daily_prices.csv"),
]

df = None
data_path = None
for p in candidates:
    if os.path.exists(p):
        df = _read_csv(p)
        data_path = p
        break

# — Fallback upload if no CSV found —
if df is None:
    st.sidebar.warning("No local CSV found. Please upload `crypto_features.csv`:")
    upload = st.sidebar.file_uploader("Upload CSV", type="csv")
    if upload is not None:
        df = pd.read_csv(upload, parse_dates=["Date"])
        data_path = None
    else:
        st.stop()

# — Display last-updated stamp if available —
if data_path:
    last_dt = _get_last_date(data_path).strftime("%Y-%m-%d")
    st.markdown(f"**Data last updated on: {last_dt}**")

# — Ensure engineered features exist —
if "Daily change" not in df.columns:
    df = df.sort_values(["Ticker", "Date"]).reset_index(drop=True)
    df["Daily change"]   = df.groupby("Ticker")["Close"].diff()
    df["Daily % change"] = df["Daily change"] / df.groupby("Ticker")["Close"].shift(1) * 100
    df["Price range"]    = df["High"] - df["Low"]
    df["Average price"]  = (df["High"] + df["Low"]) / 2
    df["7d ma"]          = df.groupby("Ticker")["Close"].transform(lambda x: x.rolling(7).mean())
    df["7d volatility"]  = df.groupby("Ticker")["Close"].transform(lambda x: x.pct_change().rolling(7).std() * 100)
    num_cols = df.select_dtypes(include="number").columns
    df[num_cols] = df[num_cols].round(4)

# — Sidebar: Filters —
st.sidebar.header("Filters")
tickers = sorted(df["Ticker"].unique().tolist())
default = ["BTC"] if "BTC" in tickers else [tickers[0]]
selected = st.sidebar.multiselect("Select Tickers", tickers, default=default)

dmin, dmax = df["Date"].min(), df["Date"].max()
start, end = st.sidebar.date_input("Date range", [dmin, dmax])

ma_window  = st.sidebar.slider("MA window (days)",        7, 100, 30)
vol_window = st.sidebar.slider("Volatility window (days)", 7, 100, 7)
st.sidebar.markdown("---")
st.sidebar.markdown("[View on GitHub](https://github.com/myselfsamarth/crypto-eda-dashboard)")

# — Filter data based on selections —
d = (
    df[df["Ticker"].isin(selected)]
    .loc[lambda x: (x["Date"] >= pd.to_datetime(start)) & (x["Date"] <= pd.to_datetime(end))]
    .sort_values("Date")
    .copy()
)

# — Compute dynamic indicators —
d[f"{ma_window}d MA"]        = d.groupby("Ticker")["Close"].transform(lambda x: x.rolling(ma_window).mean())
d[f"{vol_window}d volatility"] = d.groupby("Ticker")["Close"].transform(lambda x: x.pct_change().rolling(vol_window).std() * 100)

# — KPI / Metrics —
if len(selected) == 1:
    latest = d.iloc[-1]
    drawdowns = (d["Close"] - d["Close"].cummax()) / d["Close"].cummax() * 100
    max_dd = drawdowns.min()

    end_price   = latest["Close"]
    start_price = d.iloc[0]["Close"]
    period_pct  = (end_price - start_price) / start_price * 100

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Current Price",  f"${end_price:,.2f}")
    c2.metric("Daily Change",   f"{latest['Daily % change']:.2f}%")
    c3.metric("Period Change",  f"{period_pct:.2f}%")
    c4.metric("Max Drawdown",   f"{max_dd:.2f}%")
else:
    metrics = []
    for t in selected:
        sub = d[d["Ticker"] == t]
        if sub.empty:
            continue
        last = sub.iloc[-1]
        dd = (sub["Close"] - sub["Close"].cummax()) / sub["Close"].cummax() * 100
        metrics.append({
            "Ticker": t,
            "Price": f"${last.Close:,.2f}",
            "7d Vol": f"{last['7d volatility']:.2f}%",
            "Daily %": f"{last['Daily % change']:.2f}%",
            "Max DD": f"{dd.min():.2f}%"
        })
    st.dataframe(pd.DataFrame(metrics), use_container_width=True)

# — Charts in Tabs —
tabs = st.tabs([
    "Price & MA", "Volatility", "Returns Dist.", "Drawdown", "Seasonality"
])

with tabs[0]:
    st.subheader("Close Price Comparison")
    fig = px.line(
        d, x="Date", y="Close",
        color="Ticker",
        labels={"Close": "Price (USD)"},
        template="plotly_dark",
        color_discrete_sequence=PALETTE
    )
    fig.update_xaxes(tickformat="%d %b %Y", tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

    if len(selected) == 1:
        st.subheader(f"{ma_window}d Moving Average")
        fig2 = px.line(
            d, x="Date", y=f"{ma_window}d MA",
            labels={f"{ma_window}d MA": f"{ma_window}d MA (USD)"},
            template="plotly_dark",
            color_discrete_sequence=["lightgray"]
        )
        fig2.update_xaxes(tickformat="%d %b %Y", tickangle=-45)
        st.plotly_chart(fig2, use_container_width=True)

with tabs[1]:
    st.subheader(f"{vol_window}-Day Rolling Volatility")
    fig = px.line(
        d, x="Date", y=f"{vol_window}d volatility",
        color="Ticker",
        labels={f"{vol_window}d volatility": "Volatility (%)"},
        template="plotly_dark",
        color_discrete_sequence=PALETTE
    )
    fig.update_xaxes(tickformat="%d %b %Y", tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

with tabs[2]:
    st.subheader("Daily Return Distribution")
    fig = px.histogram(
        d, x="Daily % change", color="Ticker",
        nbins=80, barmode="overlay", opacity=0.7,
        labels={"Daily % change": "Daily % Change (%)"},
        template="plotly_dark",
        color_discrete_sequence=PALETTE
    )
    st.plotly_chart(fig, use_container_width=True)

with tabs[3]:
    st.subheader("Peak‑to‑Trough Drawdown (%)")
    d["Running Max"] = d.groupby("Ticker")["Close"].cummax()
    d["Drawdown"] = (d["Close"] - d["Running Max"]) / d["Running Max"] * 100
    fig = px.area(
        d, x="Date", y="Drawdown", color="Ticker",
        labels={"Drawdown": "Drawdown (%)"},
        template="plotly_dark",
        color_discrete_sequence=PALETTE
    )
    fig.add_hline(y=0, line_dash="dash", line_color="white")
    fig.update_xaxes(tickformat="%d %b %Y", tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

with tabs[4]:
    st.subheader("Seasonality: Avg Daily % Change by Weekday")
    tmp = d.copy()
    tmp["Weekday"] = tmp["Date"].dt.day_name()
    avg_wk = tmp.groupby(["Weekday", "Ticker"])["Daily % change"]\
        .mean().reset_index()
    order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    fig = px.bar(
        avg_wk, x="Weekday", y="Daily % change", color="Ticker",
        category_orders={"Weekday": order},
        labels={"Daily % change": "Avg % Change (%)"},
        template="plotly_dark",
        color_discrete_sequence=PALETTE,
        barmode="group"
    )
    st.plotly_chart(fig, use_container_width=True)

# — Download & Footer —
st.markdown("---")
st.download_button(
    "📥 Download filtered data as CSV",
    data=d.to_csv(index=False),
    file_name=f"{'_'.join(selected)}_{start}_{end}.csv",
    mime="text/csv",
)
st.markdown("---")
st.markdown("*Data via Kaggle API | Built by Samarth*")
