import pandas as pd
import statsmodels.formula.api as smf
import os
df = pd.read_csv("../Chatbot_Study_Data_Cleaned.csv")
df = df[df["Dropout_status"] == 0].copy()

df["Gender"] = df["Gender"].str.lower().str.strip()
df = df[df["Gender"].isin(["male", "female"])].copy()

output_dir = "../../outputs/interaction_models"
os.makedirs(output_dir, exist_ok=True)
outcomes = ["Trust", "Comfort", "Empathy"]

for outcome in outcomes:
    formula = f"{outcome} ~ Version * Gender"
    model = smf.ols(formula, data=df).fit()
    print(f"\n📊 Interaction model for {outcome}:\n")
    print(model.summary())

    summary_df = model.summary2().tables[1]
    output_path = os.path.join(output_dir, f"{outcome.lower()}_interaction_model.csv")
    summary_df.to_csv(output_path)
