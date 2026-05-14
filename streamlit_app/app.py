"""
app.py
------
Turkish Banks Credit Risk & Rating Analysis Platform
Interactive Streamlit Dashboard
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from src.data_loader import FinancialDataLoader, BANKS, FITCH_RATINGS
from src.financial_metrics import FinancialMetricsEngine

# ── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Turkish Banks Credit Rating Platform",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        font-size: 2rem;
        font-weight: bold;
        color: #003366;
        text-align: center;
        padding: 1rem 0;
    }
    .sub-header {
        font-size: 1rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f4f8;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
    }
    .disclaimer {
        font-size: 0.75rem;
        color: #999;
        text-align: center;
        margin-top: 2rem;
        padding: 1rem;
        border-top: 1px solid #eee;
    }
</style>
""", unsafe_allow_html=True)

# ── Load Data ──────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    loader = FinancialDataLoader()
    df = loader.load_sample_financials()
    engine = FinancialMetricsEngine(df)
    scores = engine.calculate_pillar_scores()
    comparison = engine.generate_rating_comparison()
    return df, scores, comparison, engine

df, scores, comparison, engine = load_data()

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown('<div class="main-header">🏦 Turkish Banks Credit Risk & Rating Analysis Platform</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">An Analyst Simulation | Methodology aligned with Fitch Ratings FI Framework</div>', unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────────
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/Flag_of_Turkey.svg/320px-Flag_of_Turkey.svg.png", width=100)
st.sidebar.title("Navigation")
page = st.sidebar.radio("Select View", [
    "📊 Sector Overview",
    "🏦 Bank Deep Dive",
    "📈 Peer Comparison",
    "🌍 Sovereign Linkage",
    "📋 Analyst Memos"
])

st.sidebar.markdown("---")
st.sidebar.markdown("**Coverage Universe**")
for ticker, info in BANKS.items():
    rating = FITCH_RATINGS[ticker]
    st.sidebar.markdown(f"**{ticker}** — {rating['LT_IDR']} ({rating['Outlook']})")

st.sidebar.markdown("---")
st.sidebar.markdown("**Analyst:** Ali Kızıltoprak")
st.sidebar.markdown("**SPK Düzey 3 | Derecelendirme**")
st.sidebar.markdown("**M.Sc. Data Science, Pitt**")

# ── Page: Sector Overview ──────────────────────────────────────────────────────
if page == "📊 Sector Overview":
    st.subheader("Sector Overview — Turkish Banks Credit Scorecard")

    # KPI metrics row
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Sector Avg CAR", "16.3%", "+0.8% YoY")
    col2.metric("Sector Avg NPL", "3.5%", "-0.2% YoY")
    col3.metric("Sector Avg ROE", "30.7%", "+2.1% YoY")
    col4.metric("Sector Avg NIM", "4.4%", "+0.6% YoY")
    col5.metric("Sovereign Rating", "B / Stable", "Turkey")

    st.markdown("---")

    # Composite scores chart
    st.subheader("Composite Credit Scores vs Fitch Ratings")
    comparison_sorted = comparison.sort_values("composite_score", ascending=True)

    colors = []
    for score in comparison_sorted["composite_score"]:
        if score >= 65:
            colors.append("#006633")
        elif score >= 45:
            colors.append("#FF9900")
        else:
            colors.append("#CC3300")

    fig = go.Figure(go.Bar(
        x=comparison_sorted["composite_score"],
        y=comparison_sorted["name"],
        orientation="h",
        marker_color=colors,
        text=[f"Model: {r} | Fitch: {f}"
              for r, f in zip(comparison_sorted["model_implied_rating"],
                              comparison_sorted["fitch_lt_idr"])],
        textposition="outside",
    ))
    fig.add_vline(x=65, line_dash="dash", line_color="gray", annotation_text="BB- threshold")
    fig.add_vline(x=45, line_dash="dash", line_color="red", annotation_text="B threshold")
    fig.update_layout(height=400, xaxis_title="Composite Score (0-100)",
                      xaxis_range=[0, 120], showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    # Pillar heatmap
    st.subheader("Pillar Score Heatmap")
    pillars = ["capital", "asset_quality", "profitability", "liquidity", "fx_sensitivity"]
    heatmap_data = scores[pillars].copy()
    heatmap_data.index = scores["name"]

    fig2 = px.imshow(
        heatmap_data,
        color_continuous_scale="RdYlGn",
        zmin=0, zmax=100,
        text_auto=".0f",
        labels=dict(color="Score"),
        title="Credit Pillar Scores by Bank (0=Weak, 100=Strong)"
    )
    fig2.update_layout(height=350)
    st.plotly_chart(fig2, use_container_width=True)

# ── Page: Bank Deep Dive ───────────────────────────────────────────────────────
elif page == "🏦 Bank Deep Dive":
    st.subheader("Bank Deep Dive")

    selected_bank = st.selectbox(
        "Select Bank",
        options=list(BANKS.keys()),
        format_func=lambda x: f"{x} — {BANKS[x]['name']}"
    )

    bank_data = df.loc[selected_bank]
    bank_score = scores.loc[selected_bank]
    fitch = FITCH_RATINGS[selected_bank]

    col1, col2, col3 = st.columns(3)
    col1.metric("Composite Score", f"{bank_score['composite_score']:.1f}/100")
    col2.metric("Fitch LT IDR", fitch['LT_IDR'])
    col3.metric("Fitch Outlook", fitch['Outlook'])

    st.markdown("---")

    # Financial metrics table
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("**Capital & Asset Quality**")
        cap_aq = pd.DataFrame({
            "Metric": ["CAR (%)", "CET1 (%)", "NPL Ratio (%)", "Coverage (%)", "Cost of Risk (%)"],
            "Value": [bank_data["car_pct"], bank_data["cet1_pct"],
                      bank_data["npl_ratio"], bank_data["coverage_ratio"],
                      bank_data["cost_of_risk"]]
        })
        st.dataframe(cap_aq, hide_index=True, use_container_width=True)

    with col_right:
        st.markdown("**Profitability & Liquidity**")
        prof_liq = pd.DataFrame({
            "Metric": ["ROE (%)", "ROA (%)", "NIM (%)", "Cost/Income (%)",
                       "Loan/Deposit (%)", "LCR (%)"],
            "Value": [bank_data["roe_pct"], bank_data["roa_pct"],
                      bank_data["nim_pct"], bank_data["cost_income"],
                      bank_data["loan_deposit"], bank_data["lcr_pct"]]
        })
        st.dataframe(prof_liq, hide_index=True, use_container_width=True)

    # Radar chart for selected bank vs sector average
    st.markdown("**Pillar Scores vs Sector Average**")
    pillars = ["capital", "asset_quality", "profitability", "liquidity", "fx_sensitivity"]
    bank_vals = [bank_score[p] for p in pillars]
    avg_vals = [scores[p].mean() for p in pillars]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=bank_vals + [bank_vals[0]],
        theta=[p.replace("_", " ").title() for p in pillars] + [pillars[0].replace("_", " ").title()],
        fill="toself", name=BANKS[selected_bank]["name"],
        line_color="#003366"
    ))
    fig.add_trace(go.Scatterpolar(
        r=avg_vals + [avg_vals[0]],
        theta=[p.replace("_", " ").title() for p in pillars] + [pillars[0].replace("_", " ").title()],
        fill="toself", name="Sector Average",
        line_color="#FF9900", opacity=0.5
    ))
    fig.update_layout(polar=dict(radialaxis=dict(range=[0, 100])), height=400)
    st.plotly_chart(fig, use_container_width=True)

# ── Page: Peer Comparison ──────────────────────────────────────────────────────
elif page == "📈 Peer Comparison":
    st.subheader("Peer Comparison")

    metric_options = {
        "CAR (%)": "car_pct",
        "CET1 (%)": "cet1_pct",
        "NPL Ratio (%)": "npl_ratio",
        "Coverage Ratio (%)": "coverage_ratio",
        "ROE (%)": "roe_pct",
        "ROA (%)": "roa_pct",
        "NIM (%)": "nim_pct",
        "Cost/Income (%)": "cost_income",
        "Loan/Deposit (%)": "loan_deposit",
        "LCR (%)": "lcr_pct",
        "FX Loan Share (%)": "fx_loan_share",
    }

    selected_metric = st.selectbox("Select Metric", list(metric_options.keys()))
    col = metric_options[selected_metric]

    fig = px.bar(
        df.sort_values(col, ascending=False),
        x="name", y=col,
        color="ownership",
        color_discrete_map={"Private": "#003366", "State": "#FF6600"},
        title=f"{selected_metric} — Peer Comparison",
        labels={"name": "Bank", col: selected_metric}
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

    # Full comparison table
    st.subheader("Full Metrics Table")
    display_cols = ["name", "ownership", "car_pct", "npl_ratio", "roe_pct",
                    "nim_pct", "loan_deposit", "lcr_pct", "fx_loan_share"]
    st.dataframe(df[display_cols].rename(columns={
        "name": "Bank", "ownership": "Type", "car_pct": "CAR%",
        "npl_ratio": "NPL%", "roe_pct": "ROE%", "nim_pct": "NIM%",
        "loan_deposit": "L/D%", "lcr_pct": "LCR%", "fx_loan_share": "FX Loan%"
    }), use_container_width=True)

# ── Page: Sovereign Linkage ────────────────────────────────────────────────────
elif page == "🌍 Sovereign Linkage":
    st.subheader("Sovereign Risk Linkage — Turkey")

    st.markdown("""
    All Turkish bank FC ratings are constrained by the **Turkey sovereign ceiling (B, Stable)**.
    This page illustrates the key macro variables driving sovereign risk and their transmission to bank credit profiles.
    """)

    macro_data = {
        "Indicator": ["GDP Growth (%)", "CPI Inflation (%)", "CBRT Rate (%)",
                      "USDTRY", "Current Account (% GDP)", "Turkey CDS (bps)"],
        "2023A": [5.1, 64.8, 42.5, 29.5, -4.0, 320],
        "2024A": [4.5, 65.2, 50.0, 32.5, -3.5, 280],
        "2025E": [3.8, 42.0, 47.5, 36.0, -3.0, 240],
        "2026F": [4.2, 28.0, 35.0, 38.5, -2.8, 200],
        "Credit Impact": ["Positive", "Negative", "Mixed", "Negative", "Negative", "Negative"]
    }

    macro_df = pd.DataFrame(macro_data)
    st.dataframe(macro_df, hide_index=True, use_container_width=True)

    st.markdown("---")
    st.markdown("**Rating Ceiling Effect**")
    st.markdown("""
    | Standalone Profile | Sovereign Ceiling | Actual FC Rating |
    |-------------------|------------------|-----------------|
    | BB+ (Akbank, Garanti) | B | **B** |
    | BB (İş Bankası) | B | **B** |
    | B+ (Yapı Kredi, Vakıfbank) | B | **B** |
    | B (Halkbank) | B | **B-** (state support discount) |

    > The sovereign ceiling is the primary binding constraint. Standalone improvements have limited rating impact until Turkey's sovereign rating improves.
    """)

# ── Page: Analyst Memos ────────────────────────────────────────────────────────
elif page == "📋 Analyst Memos":
    st.subheader("Rating Committee Memos")
    st.markdown("Fitch-style analyst memos for each bank in the coverage universe.")

    memo_bank = st.selectbox("Select Bank", ["Garanti BBVA (GARAN)", "Akbank (AKBNK)"])

    if "GARAN" in memo_bank:
        memo_path = "../reports/analyst_memos/GARAN_memo.md"
    else:
        memo_path = "../reports/analyst_memos/AKBNK_memo.md"

    try:
        with open(memo_path, "r", encoding="utf-8") as f:
            memo_content = f.read()
        st.markdown(memo_content)
    except FileNotFoundError:
        st.warning("Memo file not found. Please run from project root directory.")
        st.info("Memo files are located in: reports/analyst_memos/")

# ── Disclaimer ─────────────────────────────────────────────────────────────────
st.markdown("""
<div class="disclaimer">
⚠️ <strong>Disclaimer:</strong> This platform is an educational analyst simulation and does not represent investment advice or an official credit rating. 
All data is illustrative and based on publicly available information. Not affiliated with Fitch Ratings, Moody's, S&P Global, or any rating agency.
</div>
""", unsafe_allow_html=True)
