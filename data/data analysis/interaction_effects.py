import pandas as pd
import statsmodels.formula.api as smf
import os

# Load and filter data
df = pd.read_csv("data/Chatbot_Study_Data_Cleaned.csv")
df = df[df["Dropout_status"] == 0].copy()

# Clean labels
df["Version"] = df["Version"].str.strip().str.capitalize()
df["Gender"] = df["Gender"].str.lower().str.strip()

# Filter to male/female only
df = df[df["Gender"].isin(["male", "female"])].copy()

# Ensure outcomes are numeric
outcomes = ["Trust", "Comfort", "Empathy"]
for col in outcomes:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Prepare output folder
output_dir = "outputs/interaction_models"
os.makedirs(output_dir, exist_ok=True)

# Run and save models
for outcome in outcomes:
    print(f"\n🔍 Running OLS model for {outcome} (Version × Gender)...\n")
    model = smf.ols(f"{outcome} ~ Version * Gender", data=df).fit()

    # Show result in console
    print(model.summary())

    # Save results to CSV
    results_df = model.summary2().tables[1]
    results_df.to_csv(f"{output_dir}/{outcome.lower()}_interaction_model.csv")

print("\n✅ All models complete. CSVs saved in: ../../outputs/interaction_models/")
