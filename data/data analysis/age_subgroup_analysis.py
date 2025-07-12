import os
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import statsmodels.api as sm
from statsmodels.formula.api import ols

current_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(current_dir, "../../"))

data_path = os.path.join(project_root, "data", "Chatbot_Study_Data_Cleaned.csv")
figures_dir = os.path.join(project_root, "figures")
results_dir = os.path.join(project_root, "outputs")

os.makedirs(figures_dir, exist_ok=True)
os.makedirs(results_dir, exist_ok=True)

df = pd.read_csv(data_path)

df['Age'] = pd.to_numeric(df['Age'], errors='coerce')
df['Trust'] = pd.to_numeric(df['Trust'], errors='coerce')
df['Empathy'] = pd.to_numeric(df['Empathy'], errors='coerce')

df = df.dropna(subset=['Age', 'Trust', 'Empathy'])

def categorize_age(age):
    if age <= 25:
        return '18–25'
    elif age <= 35:
        return '26–35'
    else:
        return '36+'

df['Age_Group'] = df['Age'].apply(categorize_age)

df['Interface_Condition'] = df['Version'].str.lower().map({'elli': 'Elli', 'static': 'Static'})
df = df[df['Interface_Condition'].isin(['Elli', 'Static'])]

df['Interface_Condition'] = df['Interface_Condition'].astype('category')
df['Age_Group'] = df['Age_Group'].astype('category')

model_trust = ols('Trust ~ C(Interface_Condition) * C(Age_Group)', data=df).fit()
anova_trust = sm.stats.anova_lm(model_trust, typ=2)
print("\n--- Two-way ANOVA: Trust ---")
print(anova_trust)

model_empathy = ols('Empathy ~ C(Interface_Condition) * C(Age_Group)', data=df).fit()
anova_empathy = sm.stats.anova_lm(model_empathy, typ=2)
print("\n--- Two-way ANOVA: Empathy ---")
print(anova_empathy)

plt.figure(figsize=(8, 5))
sns.pointplot(data=df, x='Age_Group', y='Trust', hue='Interface_Condition',
              dodge=True, markers='o', capsize=.1)
plt.title('Trust by Age Group and Interface')
plt.xlabel('Age Group')
plt.ylabel('Trust (0–5)')
plt.tight_layout()
plt.savefig(os.path.join(figures_dir, "Trust_by_AgeGroup_Interface.png"))
plt.show()

plt.figure(figsize=(8, 5))
sns.pointplot(data=df, x='Age_Group', y='Empathy', hue='Interface_Condition',
              dodge=True, markers='o', capsize=.1)
plt.title('Empathy by Age Group and Interface')
plt.xlabel('Age Group')
plt.ylabel('Empathy (0–5)')
plt.tight_layout()
plt.savefig(os.path.join(figures_dir, "Empathy_by_AgeGroup_Interface.png"))
plt.show()

anova_trust.to_csv(os.path.join(results_dir, "anova_trust_agegroup.csv"))
anova_empathy.to_csv(os.path.join(results_dir, "anova_empathy_agegroup.csv"))
