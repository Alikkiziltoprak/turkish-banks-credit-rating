# Data Sources Guide
## Turkish Banks Credit Risk & Rating Analysis Platform

---

## 1. Bank Financial Data — BDDK (Primary Source)

**Source:** Banking Regulation and Supervision Agency of Turkey  
**URL:** https://www.bddk.org.tr/BultenV2/

### How to download:
1. Go to https://www.bddk.org.tr/BultenV2/
2. Select "Türk Bankacılık Sektörü Temel Göstergeleri" (Turkish Banking Sector Key Indicators)
3. Download quarterly Excel files
4. Save to `data/raw/bddk_quarterly_YYYY_QX.xlsx`

### Key metrics available:
- Capital adequacy ratios (CAR, CET1)
- NPL ratios and coverage
- ROE, ROA, NIM
- Liquidity ratios
- FX loan breakdown

---

## 2. Macro Data — TCMB EVDS API

**Source:** Central Bank of Turkey — Electronic Data Delivery System  
**URL:** https://evds2.tcmb.gov.tr/

### Setup:
1. Register for free API key at https://evds2.tcmb.gov.tr/
2. Add to `.env` file: `TCMB_API_KEY=your_key_here`

### Key series:
| Series Code | Description |
|-------------|-------------|
| TP.DK.USD.A | USD/TRY daily rate |
| TP.DK.EUR.A | EUR/TRY daily rate |
| TP.TG2.Y01  | CBRT policy rate |
| TP.FG.J0   | CPI inflation |

---

## 3. Market Data — Yahoo Finance (yfinance)

**Access:** Free, via Python yfinance library  
**Tickers:** GARAN.IS, AKBNK.IS, ISCTR.IS, YKBNK.IS, HALKB.IS, VAKBN.IS

```python
import yfinance as yf
df = yf.download("GARAN.IS", start="2020-01-01")
```

---

## 4. Sovereign/Macro Indicators — World Bank API

**Access:** Free, via wbgapi Python library

```python
import wbgapi as wb
inflation = wb.data.DataFrame("FP.CPI.TOTL.ZG", "TUR", mrv=10)
```

---

## 5. CDS Spreads — Manual Collection

**Source:** Investing.com or Bloomberg Terminal  
**URL:** https://www.investing.com/rates-bonds/turkey-5-years-cds

Turkey 5Y CDS spreads must be collected manually and saved to:
`data/raw/turkey_cds_spreads.csv`

---

## 6. Bank Annual Reports & Earnings — KAP

**Source:** Public Disclosure Platform (Kamuyu Aydınlatma Platformu)  
**URL:** https://www.kap.org.tr/

Use for NLP phase (Phase 3):
- Annual reports (PDF)
- Earnings release presentations
- Investor day materials

---

## Sample Data

The project includes sample/illustrative data in `src/data_loader.py`  
based on approximate 2023 figures from public sources.  
Replace with actual BDDK data for production-quality analysis.
