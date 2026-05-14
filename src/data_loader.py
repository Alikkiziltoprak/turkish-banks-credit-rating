"""
data_loader.py
--------------
Data ingestion module for Turkish Banks Credit Rating Analysis Platform.
Fetches financial and macro data from public APIs.
"""

import pandas as pd
import numpy as np
import yfinance as yf
import requests
import wbgapi as wb
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# ── Bank Universe ──────────────────────────────────────────────────────────────
BANKS = {
    "GARAN": {"name": "Garanti BBVA",  "ownership": "Private", "ticker_yahoo": "GARAN.IS"},
    "AKBNK": {"name": "Akbank",        "ownership": "Private", "ticker_yahoo": "AKBNK.IS"},
    "ISCTR": {"name": "İş Bankası",    "ownership": "Private", "ticker_yahoo": "ISCTR.IS"},
    "YKBNK": {"name": "Yapı Kredi",    "ownership": "Private", "ticker_yahoo": "YKBNK.IS"},
    "HALKB": {"name": "Halkbank",      "ownership": "State",   "ticker_yahoo": "HALKB.IS"},
    "VAKBN": {"name": "Vakıfbank",     "ownership": "State",   "ticker_yahoo": "VAKBN.IS"},
}

# ── Fitch Reference Ratings (as of latest available) ──────────────────────────
FITCH_RATINGS = {
    "GARAN": {"LT_IDR": "B",  "Outlook": "Stable"},
    "AKBNK": {"LT_IDR": "B",  "Outlook": "Stable"},
    "ISCTR": {"LT_IDR": "B",  "Outlook": "Stable"},
    "YKBNK": {"LT_IDR": "B",  "Outlook": "Stable"},
    "HALKB": {"LT_IDR": "B-", "Outlook": "Stable"},
    "VAKBN": {"LT_IDR": "B",  "Outlook": "Stable"},
}


class MarketDataLoader:
    """Fetches market prices and macro indicators via yfinance and World Bank API."""

    def __init__(self, start_date: str = "2020-01-01"):
        self.start_date = start_date
        self.end_date = datetime.today().strftime("%Y-%m-%d")

    def get_stock_prices(self) -> pd.DataFrame:
        """Download adjusted closing prices for all banks from Yahoo Finance (Borsa Istanbul)."""
        tickers = [v["ticker_yahoo"] for v in BANKS.values()]
        print(f"Downloading stock prices for: {tickers}")
        df = yf.download(tickers, start=self.start_date, end=self.end_date, auto_adjust=True)["Close"]
        df.columns = [col.replace(".IS", "") for col in df.columns]
        return df

    def get_fx_data(self) -> pd.DataFrame:
        """Download USDTRY and EURTRY exchange rates."""
        fx_tickers = ["USDTRY=X", "EURTRY=X"]
        df = yf.download(fx_tickers, start=self.start_date, end=self.end_date, auto_adjust=True)["Close"]
        df.columns = ["EURTRY", "USDTRY"]
        return df

    def get_macro_data(self) -> pd.DataFrame:
        """
        Fetch macro indicators from World Bank API.
        Indicators:
          - FP.CPI.TOTL.ZG : Inflation, consumer prices (annual %)
          - NY.GDP.MKTP.KD.ZG: GDP growth (annual %)
          - GC.DOD.TOTL.GD.ZS: Government debt to GDP (%)
          - BN.CAB.XOKA.GD.ZS: Current account balance (% of GDP)
        """
        indicators = {
            "FP.CPI.TOTL.ZG":  "inflation_pct",
            "NY.GDP.MKTP.KD.ZG": "gdp_growth_pct",
            "GC.DOD.TOTL.GD.ZS": "govt_debt_gdp",
            "BN.CAB.XOKA.GD.ZS": "current_account_gdp",
        }
        frames = []
        for code, label in indicators.items():
            try:
                data = wb.data.DataFrame(code, "TUR", mrv=10).T
                data.index = pd.to_datetime(data.index, format="YR%Y")
                data.columns = [label]
                frames.append(data)
            except Exception as e:
                print(f"Warning: Could not fetch {label}: {e}")
        if frames:
            return pd.concat(frames, axis=1).sort_index()
        return pd.DataFrame()

    def get_cbrt_rate(self) -> pd.DataFrame:
        """
        Fetch CBRT policy rate from TCMB EVDS API.
        Note: Requires free API key from https://evds2.tcmb.gov.tr/
        Returns placeholder if API key not configured.
        """
        # TODO: Add EVDS API key to .env file as TCMB_API_KEY
        # Example endpoint: https://evds2.tcmb.gov.tr/service/evds/series=TP.DK.USD.A&...
        print("CBRT rate: Configure TCMB_API_KEY in .env for live data. Using placeholder.")
        dates = pd.date_range(start=self.start_date, end=self.end_date, freq="ME")
        return pd.DataFrame({"cbrt_policy_rate": np.nan}, index=dates)


class FinancialDataLoader:
    """
    Loads bank financial statement data.
    
    Data source: BDDK (Banking Regulation and Supervision Agency of Turkey)
    URL: https://www.bddk.org.tr/BultenV2/
    
    For this project, financial data is loaded from manually prepared Excel files
    downloaded from BDDK public bulletins. See data/raw/README_data_sources.md
    for download instructions.
    """

    def __init__(self, data_path: str = "../data/raw/"):
        self.data_path = data_path

    def load_sample_financials(self) -> pd.DataFrame:
        """
        Returns sample financial metrics for demonstration.
        Replace with actual BDDK data in data/raw/ folder.
        
        Metrics based on approximate 2023 annual figures (illustrative).
        """
        data = {
            "bank":          ["GARAN", "AKBNK", "ISCTR", "YKBNK", "HALKB", "VAKBN"],
            "name":          ["Garanti BBVA", "Akbank", "İş Bankası", "Yapı Kredi", "Halkbank", "Vakıfbank"],
            "ownership":     ["Private", "Private", "Private", "Private", "State", "State"],
            # Capital Adequacy
            "car_pct":       [17.2, 18.5, 16.8, 15.9, 14.2, 15.1],    # Capital Adequacy Ratio (%)
            "cet1_pct":      [14.1, 15.2, 13.9, 12.8, 11.5, 12.3],    # CET1 Ratio (%)
            "leverage_ratio":[8.2,  9.1,  7.8,  7.2,  6.5,  7.0],     # Leverage Ratio (%)
            # Asset Quality
            "npl_ratio":     [2.1,  1.8,  3.2,  4.5,  5.8,  3.9],     # NPL Ratio (%)
            "coverage_ratio":[85.0, 88.0, 75.0, 70.0, 60.0, 72.0],    # Loan Loss Coverage (%)
            "cost_of_risk":  [1.2,  1.0,  1.8,  2.1,  2.8,  2.0],     # Cost of Risk (%)
            # Profitability
            "roe_pct":       [38.5, 35.2, 32.1, 28.9, 22.5, 26.8],    # Return on Equity (%)
            "roa_pct":       [3.8,  3.5,  2.9,  2.4,  1.8,  2.2],     # Return on Assets (%)
            "nim_pct":       [5.2,  4.8,  4.5,  4.2,  3.8,  4.1],     # Net Interest Margin (%)
            "cost_income":   [28.5, 30.2, 35.8, 38.1, 42.5, 39.2],    # Cost-to-Income Ratio (%)
            # Liquidity
            "loan_deposit":  [88.5, 85.2, 92.1, 98.5, 102.3, 95.8],   # Loan-to-Deposit Ratio (%)
            "lcr_pct":       [185.0,192.0,175.0,162.0,145.0,158.0],   # Liquidity Coverage Ratio (%)
            # FX Sensitivity
            "fx_loan_share": [28.5, 25.2, 32.1, 35.8, 38.2, 36.5],   # FX loans / Total loans (%)
            "fx_funding_gap":[2.1,  1.8,  3.5,  4.2,  5.8,  4.8],    # FX funding gap (% of assets)
            # Size
            "total_assets_bn_try": [1850, 1650, 1920, 1420, 980, 1250],  # Total assets (TRY bn)
        }
        return pd.DataFrame(data).set_index("bank")

    def load_from_excel(self, filename: str) -> pd.DataFrame:
        """Load actual BDDK data from Excel file in data/raw/."""
        try:
            return pd.read_excel(f"{self.data_path}{filename}", index_col=0)
        except FileNotFoundError:
            print(f"File not found: {self.data_path}{filename}. Using sample data.")
            return self.load_sample_financials()


if __name__ == "__main__":
    # Quick test
    print("=== Testing Data Loaders ===\n")

    fin_loader = FinancialDataLoader()
    df = fin_loader.load_sample_financials()
    print("Sample Financial Data:")
    print(df[["name", "car_pct", "npl_ratio", "roe_pct", "nim_pct"]].to_string())

    print("\n--- Bank Universe ---")
    for ticker, info in BANKS.items():
        rating = FITCH_RATINGS[ticker]
        print(f"{ticker}: {info['name']} | Fitch: {rating['LT_IDR']} ({rating['Outlook']})")
