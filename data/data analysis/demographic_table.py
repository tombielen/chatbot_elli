import pandas as pd
from scipy.stats import ttest_ind, chi2_contingency
import numpy as np

# Load data
df = pd.read_csv("../../data/Chatbot_Study_Data_Cleaned.csv")

# Step 1: Filter final analytic sample
analytic_df = df[df["Dropout_status"] == 0].copy()

# Convert Age to numeric (important for stats)
analytic_df["Age"] = pd.to_numeric(analytic_df["Age"], errors="coerce")

# Step 2: Normalize gender values
def normalize_gender(val):
    if pd.isna(val):
        return "Prefer not to say"
    val = str(val).strip().lower()
    if val in ["female", "f"]:
        return "Female"
    elif val in ["male", "m"]:
        return "Male"
    elif val in ["other", "nonbinary", "non-binary"]:
        return "Other"
    elif "prefer" in val:
        return "Prefer not to say"
    else:
        return "Prefer not to say"

analytic_df["Gender"] = analytic_df["Gender"].apply(normalize_gender)
analytic_df["Version"] = analytic_df["Version"].str.strip().str.capitalize()

# Step 3a: Age stats
elli = analytic_df[analytic_df["Version"] == "Elli"]
static = analytic_df[analytic_df["Version"] == "Static"]

def mean_sd(series):
    return np.nanmean(series), np.nanstd(series)

age_elli = mean_sd(elli["Age"])
age_static = mean_sd(static["Age"])
age_total = mean_sd(analytic_df["Age"])

# Step 3b: Gender counts
gender_levels = ["Female", "Male", "Other", "Prefer not to say"]
gender_counts = pd.crosstab(analytic_df["Version"], analytic_df["Gender"]).reindex(index=["Elli", "Static"], columns=gender_levels, fill_value=0)
gender_totals = analytic_df["Gender"].value_counts().reindex(gender_levels, fill_value=0)

# Step 4a: Age t-test
t_stat, p_val = ttest_ind(elli["Age"].dropna(), static["Age"].dropna(), equal_var=False)

# Step 4b: Chi-square for gender
chi2, chi_p, chi_dof, _ = chi2_contingency(gender_counts)

# Step 5: Print Table 1
n_elli, n_static, n_total = len(elli), len(static), len(analytic_df)
print("\nTable 1: Demographic Characteristics of Final Analytic Sample\n")
print(f"{'Variable':<35} {'Elli (n=' + str(n_elli) + ')':<20} {'Static (n=' + str(n_static) + ')':<20} {'Total (N=' + str(n_total) + ')':<20} {'Statistical Test'}")
print("-" * 120)
print(f"{'Age (M ± SD)':<35} {age_elli[0]:.2f} ± {age_elli[1]:.2f}{'':<10} {age_static[0]:.2f} ± {age_static[1]:.2f}{'':<10} {age_total[0]:.2f} ± {age_total[1]:.2f}{'':<10} t = {t_stat:.2f}, p = {p_val:.3f}")
print(f"{'Gender (%)':<35}")

for gender in gender_levels:
    count_elli = gender_counts.loc["Elli", gender]
    count_static = gender_counts.loc["Static", gender]
    count_total = gender_totals[gender]
    percent_elli = 100 * count_elli / n_elli if n_elli > 0 else 0
    percent_static = 100 * count_static / n_static if n_static > 0 else 0
    percent_total = 100 * count_total / n_total if n_total > 0 else 0
    print(f"  {gender:<32} {percent_elli:.1f}%{'':<12} {percent_static:.1f}%{'':<12} {percent_total:.1f}%")

print(f"{'':<97} χ²({chi_dof}) = {chi2:.2f}, p = {chi_p:.3f}")

# Optionally, save as CSV
table1 = []
table1.append([
    "Age (M ± SD)",
    f"{age_elli[0]:.2f} ± {age_elli[1]:.2f}",
    f"{age_static[0]:.2f} ± {age_static[1]:.2f}",
    f"{age_total[0]:.2f} ± {age_total[1]:.2f}",
    f"t = {t_stat:.2f}, p = {p_val:.3f}"
])
for gender in gender_levels:
    count_elli = gender_counts.loc["Elli", gender]
    count_static = gender_counts.loc["Static", gender]
    count_total = gender_totals[gender]
    percent_elli = 100 * count_elli / n_elli if n_elli > 0 else 0
    percent_static = 100 * count_static / n_static if n_static > 0 else 0
    percent_total = 100 * count_total / n_total if n_total > 0 else 0
    table1.append([
        f"Gender: {gender}",
        f"{percent_elli:.1f}%",
        f"{percent_static:.1f}%",
        f"{percent_total:.1f}%",
        f"χ²({chi_dof}) = {chi2:.2f}, p = {chi_p:.3f}" if gender == "Female" else ""
    ])

pd.DataFrame(table1, columns=["Variable", f"Elli (n={n_elli})", f"Static (n={n_static})", f"Total (N={n_total})", "Statistical Test"]).to_csv("../../outputs/demographic_table1.csv", index=False)