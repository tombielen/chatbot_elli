import pandas as pd
import statsmodels.formula.api as smf
import os

df = pd.read_csv("data/Chatbot_Study_Data_Cleaned.csv")
df = df[df["Dropout_status"] == 0].copy()

df["Version"] = df["Version"].str.strip().str.capitalize()
df["Gender"] = df["Gender"].str.lower().str.strip()

df = df[df["Gender"].isin(["male", "female"])].copy()

outcomes = ["Trust", "Comfort", "Empathy"]
for col in outcomes:
    df[col] = pd.to_numeric(df[col], errors="coerce")

output_dir = "outputs/interaction_models"
os.makedirs(output_dir, exist_ok=True)

for outcome in outcomes:
    print(f"\n🔍 Running OLS model for {outcome} (Version × Gender)...\n")
    model = smf.ols(f"{outcome} ~ Version * Gender", data=df).fit()

    print(model.summary())

    results_df = model.summary2().tables[1]
    results_df.to_csv(f"{output_dir}/{outcome.lower()}_interaction_model.csv")

