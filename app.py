import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# --- 1. Load data with fallback to feature engineering ---
@st.cache_data
def load_data(feature_path='crypto_features.csv', master_path='master_crypto_daily_prices.csv'):
    try:
        df = pd.read_csv(feature_path, parse_dates=['Date'])
    except FileNotFoundError:
        # Fallback: load master and compute features
        df = pd.read_csv(master_path, parse_dates=['Date'])
        df = df.sort_values(['Ticker','Date']).reset_index(drop=True)
        # Feature engineering
        df['Daily change']   = df.groupby('Ticker')['Close'].diff()
        df['Daily % change'] = df['Daily change'] / df.groupby('Ticker')['Close'].shift(1) * 100
        df['Price range']    = df['High'] - df['Low']
        df['Average price']  = (df['High'] + df['Low']) / 2
        df['7d ma']          = df.groupby('Ticker')['Close'].transform(lambda x: x.rolling(7).mean())
        df['7d volatility']  = df.groupby('Ticker')['Close'].transform(lambda x: x.pct_change().rolling(7).std() * 100)
        # Round numerics
        num_cols = df.select_dtypes(include='number').columns
        df[num_cols] = df[num_cols].round(4)
    return df

# --- 1b. Load data or prompt upload ---
df = pd.read_csv("/Users/samarth/Documents/Germany/TUBerlin/Projects/crypto_features.csv")


# --- 2. Sidebar controls ---
st.title('📈 Crypto Dashboard')

tickers = df['Ticker'].unique().tolist()
selected_ticker = st.sidebar.selectbox('Select Ticker', tickers)

date_min, date_max = df['Date'].min(), df['Date'].max()
selected_range = st.sidebar.date_input(
    'Select Date Range', [date_min, date_max]
)

ma_window = st.sidebar.slider('Moving Average Window (days)', 7, 60, value=30, step=1)

st.sidebar.markdown('[View on GitHub](https://github.com/yourusername/yourrepo)')

# --- 3. Filter data ---
mask = (
    (df['Ticker'] == selected_ticker) &
    (df['Date'] >= pd.to_datetime(selected_range[0])) &
    (df['Date'] <= pd.to_datetime(selected_range[1]))
)
btc = df.loc[mask].copy()

# --- 4. Compute dynamic MA ---
btc[f'{ma_window}d ma'] = btc['Close'].rolling(window=ma_window).mean()

# --- 5. Plot Close & MA ---
st.subheader(f'{selected_ticker} Close Price & {ma_window}d MA')
fig, ax = plt.subplots()
ax.plot(btc['Date'], btc['Close'], label='Close')
ax.plot(btc['Date'], btc[f'{ma_window}d ma'], label=f'{ma_window}d MA')
ax.set_xlabel('Date')
ax.set_ylabel('Price (USD)')
ax.legend()
st.pyplot(fig)

# --- 6. Volatility chart ---
st.subheader('7-Day Rolling Volatility')
fig2, ax2 = plt.subplots()
ax2.plot(btc['Date'], btc['7d volatility'])
ax2.set_xlabel('Date')
ax2.set_ylabel('Volatility (%)')
st.pyplot(fig2)

# --- 7. Distribution ---
st.subheader('Daily Return Distribution')
fig3, ax3 = plt.subplots()
ax3.hist(btc['Daily % change'].dropna(), bins=50, edgecolor='black')
ax3.set_xlabel('Daily % Change')
ax3.set_ylabel('Frequency')
st.pyplot(fig3)
