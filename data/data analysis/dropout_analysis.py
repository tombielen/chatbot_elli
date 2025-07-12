import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import chi2_contingency
import os

df = pd.read_csv("../Chatbot_Study_Data_Cleaned.csv")

contingency = pd.crosstab(df["Version"], df["Dropout_status"])

chi2, p, dof, expected = chi2_contingency(contingency)

print("📊 Dropout Contingency Table:")
print(contingency)
print(f"\nExpected counts:\n{pd.DataFrame(expected, index=contingency.index, columns=contingency.columns)}")
print(f"\nChi² = {chi2:.2f}, df = {dof}, p = {p:.3f}")

os.makedirs("figures", exist_ok=True)

df["Dropped"] = df["Dropout_status"].replace({0: "Completed", 1: "Dropped Out"})

plt.figure(figsize=(7, 5))
ax = sns.countplot(
    data=df, x="Version", hue="Dropped", palette="Set2"
)
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