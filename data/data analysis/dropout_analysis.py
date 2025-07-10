"""
Dropout Analysis: Test whether dropout rates differ between Elli and Static conditions

Steps:
1. Use all participants (regardless of Dropout_status)
2. Create 2×2 contingency table:
   - Rows: Version (Elli, Static)
   - Columns: Dropout_status (0 = completed, 1 = dropped out)
3. Run chi-square test of independence
4. Print observed counts, expected counts, chi² statistic, p-value
5. Save a clean barplot of dropout % by condition
"""

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import chi2_contingency
import os

# Load data
df = pd.read_csv("../Chatbot_Study_Data_Cleaned.csv")

# Contingency table
contingency = pd.crosstab(df["Version"], df["Dropout_status"])

# Chi-square test
chi2, p, dof, expected = chi2_contingency(contingency)

print("📊 Dropout Contingency Table:")
print(contingency)
print(f"\nExpected counts:\n{pd.DataFrame(expected, index=contingency.index, columns=contingency.columns)}")
print(f"\nChi² = {chi2:.2f}, df = {dof}, p = {p:.3f}")

# Create output folder
os.makedirs("figures", exist_ok=True)

# Barplot of dropout % by condition
df["Dropped"] = df["Dropout_status"].replace({0: "Completed", 1: "Dropped Out"})

plt.figure(figsize=(7, 5))
ax = sns.countplot(
    data=df, x="Version", hue="Dropped", palette="Set2"
)
# Calculate percentages for annotation
total_per_version = df.groupby("Version")["Dropped"].count()
for p in ax.patches:
    height = p.get_height()
    version = p.get_x() + p.get_width() / 2
    ax.annotate(f"{height}", (p.get_x() + p.get_width() / 2, height), ha='center', va='bottom', fontsize=11)

plt.ylabel("Number of Participants")
plt.title("Dropout Rate by Chatbot Condition")
plt.legend(title="Status")
plt.tight_layout()
plt.savefig("figures/dropout_barplot.png", dpi=300, bbox_inches="tight")
plt.close()

print("✅ Chi-square test complete and dropout barplot saved.")