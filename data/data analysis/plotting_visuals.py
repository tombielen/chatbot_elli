"""
Exploratory interaction analysis:
Test whether Gender moderates the effect of chatbot Version on:
- Trust
- Comfort
- Empathy

Steps:
1. Filter to Dropout_status == 0
2. Standardize Gender values (male/female only)
3. Run OLS models: Outcome ~ Version * Gender
4. Save model coefficients to CSVs in ../../outputs/interaction_models/
"""

import pandas as pd
import statsmodels.formula.api as smf
import os

# Load and filter data
df = pd.read_csv("../Chatbot_Study_Data_Cleaned.csv")
df = df[df["Dropout_status"] == 0].copy()

# Standardize gender
df["Gender"] = df["Gender"].str.lower().str.strip()
df = df[df["Gender"].isin(["male", "female"])].copy()

# Ensure outputs folder exists
output_dir = "../../outputs/interaction_models"
os.makedirs(output_dir, exist_ok=True)

# Variables to analyze
outcomes = ["Trust", "Comfort", "Empathy"]

# Loop and run models
for outcome in outcomes:
    formula = f"{outcome} ~ Version * Gender"
    model = smf.ols(formula, data=df).fit()
    print(f"\n📊 Interaction model for {outcome}:\n")
    print(model.summary())

    # Save summary table (coefficients, p-values, etc.)
    summary_df = model.summary2().tables[1]
    output_path = os.path.join(output_dir, f"{outcome.lower()}_interaction_model.csv")
    summary_df.to_csv(output_path)

print("\n✅ All interaction models completed and saved to: ../../outputs/interaction_models/")