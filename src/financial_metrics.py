"""
financial_metrics.py
--------------------
Core financial ratio calculations and scoring for Turkish banks.
CAMELS-inspired framework aligned with Fitch Ratings methodology.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, Tuple


# ── Scoring Weights (aligned with Fitch FI methodology) ───────────────────────
PILLAR_WEIGHTS = {
    "capital":       0.25,
    "asset_quality": 0.25,
    "profitability": 0.20,
    "liquidity":     0.15,
    "fx_sensitivity":0.15,
}

# ── Benchmark Thresholds (Turkish banking sector context) ─────────────────────
THRESHOLDS = {
    "car_pct":        {"strong": 18.0, "adequate": 14.0, "weak": 10.0},
    "cet1_pct":       {"strong": 15.0, "adequate": 12.0, "weak": 8.0},
    "npl_ratio":      {"strong": 2.0,  "adequate": 4.0,  "weak": 7.0},   # Lower is better
    "coverage_ratio": {"strong": 85.0, "adequate": 70.0, "weak": 55.0},
    "cost_of_risk":   {"strong": 1.0,  "adequate": 2.0,  "weak": 3.5},   # Lower is better
    "roe_pct":        {"strong": 30.0, "adequate": 20.0, "weak": 10.0},
    "nim_pct":        {"strong": 5.0,  "adequate": 3.5,  "weak": 2.0},
    "cost_income":    {"strong": 30.0, "adequate": 42.0, "weak": 55.0},  # Lower is better
    "loan_deposit":   {"strong": 85.0, "adequate": 100.0,"weak": 115.0}, # Lower is better
    "lcr_pct":        {"strong": 180.0,"adequate": 130.0,"weak": 100.0},
    "fx_loan_share":  {"strong": 20.0, "adequate": 35.0, "weak": 50.0},  # Lower is better
}


class FinancialMetricsEngine:
    """Calculates, scores and visualizes financial metrics for Turkish banks."""

    def __init__(self, df: pd.DataFrame):
        """
        Parameters
        ----------
        df : pd.DataFrame
            Financial data with banks as index, metrics as columns.
            Use FinancialDataLoader.load_sample_financials() to get the right format.
        """
        self.df = df.copy()
        self.scores = {}

    def score_metric(self, value: float, metric: str, lower_is_better: bool = False) -> float:
        """
        Score a single metric on 0-100 scale based on thresholds.
        Returns 100 (best) to 0 (worst).
        """
        if metric not in THRESHOLDS:
            return 50.0  # Neutral if no threshold defined

        t = THRESHOLDS[metric]
        strong, adequate, weak = t["strong"], t["adequate"], t["weak"]

        if lower_is_better:
            if value <= strong:
                return 100.0
            elif value <= adequate:
                return 100 - ((value - strong) / (adequate - strong)) * 50
            elif value <= weak:
                return 50 - ((value - adequate) / (weak - adequate)) * 40
            else:
                return max(0, 10 - (value - weak) * 2)
        else:
            if value >= strong:
                return 100.0
            elif value >= adequate:
                return 100 - ((strong - value) / (strong - adequate)) * 50
            elif value >= weak:
                return 50 - ((adequate - value) / (adequate - weak)) * 40
            else:
                return max(0, 10 - (weak - value) * 2)

    def calculate_pillar_scores(self) -> pd.DataFrame:
        """Calculate scores for each analytical pillar per bank."""
        results = []

        for bank in self.df.index:
            row = self.df.loc[bank]

            # Capital pillar
            cap_score = np.mean([
                self.score_metric(row["car_pct"],    "car_pct"),
                self.score_metric(row["cet1_pct"],   "cet1_pct"),
                self.score_metric(row["leverage_ratio"], "leverage_ratio"),
            ])

            # Asset Quality pillar
            aq_score = np.mean([
                self.score_metric(row["npl_ratio"],    "npl_ratio",    lower_is_better=True),
                self.score_metric(row["coverage_ratio"],"coverage_ratio"),
                self.score_metric(row["cost_of_risk"], "cost_of_risk", lower_is_better=True),
            ])

            # Profitability pillar
            prof_score = np.mean([
                self.score_metric(row["roe_pct"],     "roe_pct"),
                self.score_metric(row["nim_pct"],     "nim_pct"),
                self.score_metric(row["cost_income"], "cost_income", lower_is_better=True),
            ])

            # Liquidity pillar
            liq_score = np.mean([
                self.score_metric(row["loan_deposit"], "loan_deposit", lower_is_better=True),
                self.score_metric(row["lcr_pct"],      "lcr_pct"),
            ])

            # FX Sensitivity pillar
            fx_score = np.mean([
                self.score_metric(row["fx_loan_share"],  "fx_loan_share",  lower_is_better=True),
                self.score_metric(100 - row["fx_funding_gap"] * 10, "car_pct"),  # Proxy
            ])

            # Composite score
            composite = (
                cap_score   * PILLAR_WEIGHTS["capital"] +
                aq_score    * PILLAR_WEIGHTS["asset_quality"] +
                prof_score  * PILLAR_WEIGHTS["profitability"] +
                liq_score   * PILLAR_WEIGHTS["liquidity"] +
                fx_score    * PILLAR_WEIGHTS["fx_sensitivity"]
            )

            results.append({
                "bank":          bank,
                "name":          row["name"],
                "capital":       round(cap_score, 1),
                "asset_quality": round(aq_score, 1),
                "profitability": round(prof_score, 1),
                "liquidity":     round(liq_score, 1),
                "fx_sensitivity":round(fx_score, 1),
                "composite_score": round(composite, 1),
            })

        scores_df = pd.DataFrame(results).set_index("bank")
        self.scores = scores_df
        return scores_df

    def map_score_to_rating(self, score: float) -> Tuple[str, str]:
        """Map composite score to indicative rating and outlook."""
        if score >= 85:   return "BB+", "Positive"
        elif score >= 75: return "BB",  "Stable"
        elif score >= 65: return "BB-", "Stable"
        elif score >= 55: return "B+",  "Stable"
        elif score >= 45: return "B",   "Stable"
        elif score >= 35: return "B-",  "Negative"
        else:             return "CCC+","Negative"

    def generate_rating_comparison(self) -> pd.DataFrame:
        """Compare model-implied ratings vs Fitch actual ratings."""
        from src.data_loader import FITCH_RATINGS

        if self.scores is None or len(self.scores) == 0:
            self.calculate_pillar_scores()

        rows = []
        for bank in self.scores.index:
            score = self.scores.loc[bank, "composite_score"]
            implied_rating, implied_outlook = self.map_score_to_rating(score)
            fitch = FITCH_RATINGS.get(bank, {})
            rows.append({
                "bank": bank,
                "name": self.scores.loc[bank, "name"],
                "composite_score": score,
                "model_implied_rating": implied_rating,
                "model_outlook": implied_outlook,
                "fitch_lt_idr": fitch.get("LT_IDR", "N/A"),
                "fitch_outlook": fitch.get("Outlook", "N/A"),
            })
        return pd.DataFrame(rows).set_index("bank")

    def plot_radar_chart(self, save_path: str = None):
        """Generate radar chart comparing banks across all pillars."""
        pillars = ["capital", "asset_quality", "profitability", "liquidity", "fx_sensitivity"]
        n = len(pillars)
        angles = [x / float(n) * 2 * np.pi for x in range(n)]
        angles += angles[:1]

        fig, ax = plt.subplots(figsize=(10, 8), subplot_kw=dict(polar=True))
        colors = ["#003366", "#0066CC", "#3399FF", "#FF6600", "#FF9933", "#FFCC00"]

        for i, bank in enumerate(self.scores.index):
            values = [self.scores.loc[bank, p] for p in pillars]
            values += values[:1]
            ax.plot(angles, values, "o-", linewidth=2, color=colors[i],
                    label=self.scores.loc[bank, "name"])
            ax.fill(angles, values, alpha=0.1, color=colors[i])

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels([p.replace("_", "\n").title() for p in pillars], size=11)
        ax.set_ylim(0, 100)
        ax.set_yticks([20, 40, 60, 80, 100])
        ax.set_yticklabels(["20", "40", "60", "80", "100"], size=8)
        ax.legend(loc="upper right", bbox_to_anchor=(1.35, 1.1))
        ax.set_title("Turkish Banks — Credit Risk Profile\nMulti-Pillar Analysis",
                     size=14, fontweight="bold", pad=20)

        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches="tight")
        return fig

    def plot_composite_scores(self, save_path: str = None):
        """Bar chart of composite scores with Fitch rating labels."""
        comparison = self.generate_rating_comparison()
        comparison = comparison.sort_values("composite_score", ascending=True)

        fig, ax = plt.subplots(figsize=(10, 6))
        colors = ["#CC3300" if s < 50 else "#FF9900" if s < 65 else "#006633"
                  for s in comparison["composite_score"]]
        bars = ax.barh(comparison["name"], comparison["composite_score"],
                       color=colors, edgecolor="white", height=0.6)

        for bar, (_, row) in zip(bars, comparison.iterrows()):
            ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
                    f"Model: {row['model_implied_rating']} | Fitch: {row['fitch_lt_idr']}",
                    va="center", fontsize=10)

        ax.set_xlim(0, 115)
        ax.set_xlabel("Composite Credit Score (0-100)", fontsize=11)
        ax.set_title("Turkish Banks — Composite Credit Scores vs Fitch Ratings",
                     fontsize=13, fontweight="bold")
        ax.axvline(x=65, color="gray", linestyle="--", alpha=0.5, label="BB- threshold")
        ax.axvline(x=45, color="red",  linestyle="--", alpha=0.5, label="B threshold")
        ax.legend()

        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches="tight")
        return fig


if __name__ == "__main__":
    import sys
    sys.path.append("..")
    from src.data_loader import FinancialDataLoader

    loader = FinancialDataLoader()
    df = loader.load_sample_financials()

    engine = FinancialMetricsEngine(df)
    scores = engine.calculate_pillar_scores()

    print("=== Pillar Scores ===")
    print(scores[["name", "capital", "asset_quality", "profitability",
                  "liquidity", "fx_sensitivity", "composite_score"]].to_string())

    print("\n=== Rating Comparison ===")
    comparison = engine.generate_rating_comparison()
    print(comparison[["name", "composite_score", "model_implied_rating",
                       "fitch_lt_idr", "fitch_outlook"]].to_string())
