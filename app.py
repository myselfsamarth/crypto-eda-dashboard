import os
import streamlit as st
import pandas as pd
import plotly.express as px

PALETTE = px.colors.qualitative.Dark24

# — Page config —
st.set_page_config(
    page_title="Crypto EDA Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

# — Title & last‐updated date —
st.title("📊 Crypto EDA Dashboard")
@st.cache_data
def load_dates(path):
    df = pd.read_csv(path, parse_dates=["Date"], usecols=["Date"])
    return df["Date"].max().strftime("%Y-%m-%d")

# Try relative first, then fallback to absolute
for candidate in ["crypto_features.csv", "master_crypto_daily_prices.csv",
                  os.path.expanduser("~/Documents/Germany/TUBerlin/Projects/crypto_features.csv"),
                  os.path.expanduser("~/Documents/Germany/TUBerlin/Projects/master_crypto_daily_prices.csv")]:
    if os.path.exists(candidate):
        last_updated = load_dates(candidate)
        break
else:
    last_updated = None

if last_updated:
    st.markdown(f"**Data last updated on: {last_updated}**")
else:
    st.warning("⚠️ Could not locate any CSV for ‘last updated’ stamp.")

# — Data loading —
@st.cache_data
def load_data():
    # identical loader from before (see previous code)...
    # tries the same candidate paths, then prompts uploader
    import pandas as pd
    for path in ["crypto_features.csv", "master_crypto_daily_prices.csv",
                 os.path.expanduser("~/Documents/Germany/TUBerlin/Projects/crypto_features.csv"),
                 os.path.expanduser("~/Documents/Germany/TUBerlin/Projects/master_crypto_daily_prices.csv")]:
        if os.path.exists(path):
            df = pd.read_csv(path, parse_dates=["Date"])
            break
    else:
        st.sidebar.info("Upload your `crypto_features.csv` to get started:")
        upload = st.sidebar.file_uploader("Upload CSV", type="csv")
        if not upload:
            st.stop()
        df = pd.read_csv(upload, parse_dates=["Date"])

    # if raw master, do feature engineering...
    if "crypto_features.csv" not in path:
        df = df.sort_values(["Ticker", "Date"]).reset_index(drop=True)
        df["Daily change"]   = df.groupby("Ticker")["Close"].diff()
        df["Daily % change"] = df["Daily change"] / df.groupby("Ticker")["Close"].shift(1) * 100
        df["Price range"]    = df["High"] - df["Low"]
        df["Average price"]  = (df["High"] + df["Low"]) / 2
        df["7d ma"]          = df.groupby("Ticker")["Close"].transform(lambda x: x.rolling(7).mean())
        df["7d volatility"]  = df.groupby("Ticker")["Close"].transform(lambda x: x.pct_change().rolling(7).std() * 100)
        num_cols = df.select_dtypes(include="number").columns
        df[num_cols] = df[num_cols].round(4)
    return df

df = load_data()

# — Sidebar filters —
st.sidebar.header("Filters")
tickers = sorted(df["Ticker"].unique().tolist())
default = ["BTC"] if "BTC" in tickers else [tickers[0]]
selected = st.sidebar.multiselect("Select Tickers", tickers, default=default)

date_min, date_max = df["Date"].min(), df["Date"].max()
start, end = st.sidebar.date_input("Date range", [date_min, date_max])

ma_window = st.sidebar.slider("MA window (days)", 7, 100, 30)
vol_window = st.sidebar.slider("Volatility window (days)", 7, 100, 7)
st.sidebar.markdown("---")
st.sidebar.markdown("[View on GitHub](https://github.com/myselfsamarth/crypto-eda-dashboard)")

# — Filter data —
d = df[
    df["Ticker"].isin(selected) &
    (df["Date"] >= pd.to_datetime(start)) &
    (df["Date"] <= pd.to_datetime(end))
].copy().sort_values("Date")

# — Compute dynamic MA —
d[f"{ma_window}d MA"] = d.groupby("Ticker")["Close"].transform(lambda x: x.rolling(ma_window).mean())

# dynamic volatility based on slider
d[f"{vol_window}d volatility"] = (
    d.groupby("Ticker")["Close"]
     .transform(lambda x: x.pct_change().rolling(vol_window).std() * 100)
)

# — KPI / Metrics —
if len(selected) == 1:
    latest = d.iloc[-1]
    drawdowns = (d["Close"] - d["Close"].cummax()) / d["Close"].cummax() * 100
    max_dd = drawdowns.min()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Current Price", f"${latest.Close:,.2f}")
    c2.metric("7d Volatility", f"{latest['7d volatility']:.2f}%")
    c3.metric("Daily Change", f"{latest['Daily % change']:.2f}%")
    c4.metric("Max Drawdown", f"{max_dd:.2f}%")
else:
    # Show a small table of metrics per ticker
    metrics = []
    for t in selected:
        sub = d[d["Ticker"] == t]
        if sub.empty: continue
        last = sub.iloc[-1]
        dd = (sub["Close"] - sub["Close"].cummax()) / sub["Close"].cummax() * 100
        metrics.append({
            "Ticker": t,
            "Current Price": f"${last.Close:,.2f}",
            "7d Vol": f"{last['7d volatility']:.2f}%",
            "Daily Δ%": f"{last['Daily % change']:.2f}%",
            "Max DD": f"{dd.min():.2f}%"
        })
    st.dataframe(pd.DataFrame(metrics), use_container_width=True)

# — Tabs & Charts —
tabs = st.tabs([
    "Price & MA", "Volatility", "Returns Dist.", "Drawdown", "Seasonality"
])

# 1) Price & MA
with tabs[0]:
    st.subheader("Close Price Comparison")
    fig = px.line(
        d,
        x="Date",
        y="Close",
        color="Ticker",
        labels={"Close": "Price (USD)"},
        template="plotly_dark", 
        color_discrete_sequence=PALETTE
    )
    # Full dates, rotated
    fig.update_xaxes(tickformat="%d %b %Y", tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

    if len(selected) == 1:
        st.subheader(f"{ma_window}d Moving Average")
        fig2 = px.line(
            d,
            x="Date",
            y=f"{ma_window}d MA",
            labels={f"{ma_window}d MA": f"{ma_window}d MA (USD)"},
            template="plotly_dark",
            color_discrete_sequence=["lightgray"]
        )
        fig2.update_xaxes(tickformat="%d %b %Y", tickangle=-45)
        st.plotly_chart(fig2, use_container_width=True)

# 2) Volatility
with tabs[1]:
    st.subheader(f"{vol_window}-Day Rolling Volatility")
    fig = px.line(
        d,
        x="Date",
        y=f"{vol_window}d volatility",
        color="Ticker",
        labels={f"{vol_window}d volatility": "Volatility (%)"},
        template="plotly_dark",
        color_discrete_sequence=PALETTE
    )
    # show full dates and tilt labels for readability
    fig.update_xaxes(tickformat="%d %b %Y", tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

# 3) Return Distribution
with tabs[2]:
    st.subheader("Daily Return Distribution")
    fig = px.histogram(
        d, x="Daily % change", color="Ticker", nbins=80,
        labels={"Daily % change": "Daily % Change (%)"},
        template="plotly_dark", barmode="overlay", opacity=0.6
    )
    st.plotly_chart(fig, use_container_width=True)

# 4) Drawdown
with tabs[3]:
    st.subheader("Peak‑to‑Trough Drawdown (%)")
    d["Running Max"] = d.groupby("Ticker")["Close"].cummax()
    d["Drawdown"] = (d["Close"] - d["Running Max"]) / d["Running Max"] * 100
    fig = px.area(
        d, x="Date", y="Drawdown", color="Ticker",
        labels={"Drawdown": "Drawdown (%)"},
        template="plotly_dark"
    )
    fig.add_hline(y=0, line_dash="dash", line_color="black")
    st.plotly_chart(fig, use_container_width=True)

# 5) Seasonality
with tabs[4]:
    st.subheader("Seasonality: Avg Daily % Change by Weekday")
    tmp = d.copy()
    tmp["Weekday"] = tmp["Date"].dt.day_name()
    avg_wk = tmp.groupby(["Weekday", "Ticker"])["Daily % change"]\
        .mean().reset_index()
    order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    fig = px.bar(
        avg_wk,
        x="Weekday", y="Daily % change", color="Ticker",
        category_orders={"Weekday": order},
        labels={"Daily % change": "Avg % Change"},
        barmode="group",
        template="plotly_dark"
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
