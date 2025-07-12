import pandas as pd
from scipy.stats import ttest_ind, mannwhitneyu, shapiro, levene
import numpy as np
import os

df = pd.read_csv("../../data/Chatbot_Study_Data_Cleaned.csv")

df = df[df["Dropout_status"] == 0].copy()

for col in ["Trust", "Comfort", "Empathy", "Total_PHQ", "Total_GAD"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

variables = ["Trust", "Comfort", "Empathy", "Total_PHQ", "Total_GAD"]

elli = df[df["Version"].str.strip().str.capitalize() == "Elli"]
static = df[df["Version"].str.strip().str.capitalize() == "Static"]

def cohens_d(x, y):
    nx, ny = len(x), len(y)
    pooled_std = np.sqrt(((nx - 1)*np.nanstd(x, ddof=1)**2 + (ny - 1)*np.nanstd(y, ddof=1)**2) / (nx + ny - 2))
    return (np.nanmean(x) - np.nanmean(y)) / pooled_std if pooled_std > 0 else np.nan

results = []

for var in variables:
    x = elli[var].dropna()
    y = static[var].dropna()

    mean_x, std_x = np.nanmean(x), np.nanstd(x, ddof=1)
    mean_y, std_y = np.nanmean(y), np.nanstd(y, ddof=1)

    t_stat, p_t = ttest_ind(x, y, equal_var=False, nan_policy="omit")
    u_stat, p_u = mannwhitneyu(x, y, alternative="two-sided")
    d = cohens_d(x, y)

    sw_x_stat, sw_x_p = shapiro(x)
    sw_y_stat, sw_y_p = shapiro(y)
    lev_stat, lev_p = levene(x, y)

    results.append({
        "Measure": var,
        "Elli (M ± SD)": f"{mean_x:.2f} ± {std_x:.2f}",
        "Static (M ± SD)": f"{mean_y:.2f} ± {std_y:.2f}",
        "t-stat": round(t_stat, 2),
        "t p-value": round(p_t, 3),
        "U-stat": round(u_stat, 2),
        "U p-value": round(p_u, 3),
        "Cohen's d": round(d, 2),
        "Shapiro p (Elli)": round(sw_x_p, 3),
        "Shapiro p (Static)": round(sw_y_p, 3),
        "Levene p": round(lev_p, 3)
    })

table2_df = pd.DataFrame(results)
os.makedirs("../../outputs", exist_ok=True)
table2_df.to_csv("../../outputs/table2_outcomes.csv", index=False)