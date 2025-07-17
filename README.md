# Crypto EDA Dashboard

A comprehensive exploratory data analysis (EDA) and interactive dashboard for Bitcoin and other cryptocurrencies. This project fetches daily price data from Kaggle, cleans and engineers key features, answers ten analytical questions with visualizations, and presents an interactive Streamlit dashboard for dynamic exploration.

---

## Repository Structure

```
crypto-eda-dashboard/
├── LICENSE
├── README.md
├── .gitignore
├── requirements.txt
├── data_update_script.ipynb          # Ingestion & cleaning pipeline
├── feature_engineering_and_eda.ipynb # Feature engineering + 10-question analysis
├── crypto_features.csv               # (Optional) Precomputed features CSV
├── master_crypto_daily_prices.csv    # Cleaned raw data CSV
├── app.py                            # Streamlit dashboard
└── raw_csv/                          # Incoming raw Kaggle downloads
    ├── incoming/                     # New files for ingestion
    └── processed/                    # Archived raw files
```

---

## Setup

1. **Clone the repository**:

   ```bash
   git clone https://github.com/myselfsamarth/crypto-eda-dashboard.git
   cd crypto-eda-dashboard
   ```

2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Kaggle API** (if you plan to run ingestion):

   * Place your `kaggle.json` file in the project root or set the `KAGGLE_CONFIG_DIR` environment variable.

---

## Usage

### 1. Data Ingestion & Cleaning

Run the ingestion notebook or script to fetch and clean raw data:

```bash
# Launch Jupyter and open the notebook
jupyter notebook data_update_script.ipynb
# Or run headlessly
jupyter nbconvert --to notebook --execute data_update_script.ipynb
```

This produces `master_crypto_daily_prices.csv` in the root directory.

### 2. Feature Engineering & EDA

Compute engineered features and answer analytical questions:

```bash
jupyter notebook feature_engineering_and_eda.ipynb
```

Generates `crypto_features.csv` and contains ten analysis sections:

1. Price Trend Over Time
2. Rolling Volatility Dynamics
3. Return Distribution
4. Moving‑Average Crossovers
5. Price Range vs. Returns
6. Drawdown Analysis
7. Seasonality Effects
8. High‑Volatility Regimes
9. Price Range Dynamics
10. Event‑Based Spikes

### 3. Launch Dashboard

Start the interactive Streamlit app:

```bash
streamlit run app.py
```

Use the sidebar to:

* Select ticker (e.g., BTC)
* Choose a date range
* Adjust moving‑average window

Access the dashboard at `http://localhost:8501` and click **View on GitHub** in the sidebar to revisit this repo.

---

## License

This project is licensed under the [MIT License](LICENSE).
