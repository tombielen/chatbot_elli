import pandas as pd
import pingouin as pg
import os

df = pd.read_csv("data/Chatbot_Study_Data_Cleaned.csv")
df = df[df["Dropout_status"] == 0].copy()

df["Version"] = df["Version"].str.strip().str.capitalize()
df["Gender"] = df["Gender"].str.lower().str.strip()
df = df[df["Gender"].isin(["male", "female"])].copy()
df["Version_bin"] = df["Version"].map({"Elli": 0, "Static": 1})

df["Empathy"] = pd.to_numeric(df["Empathy"], errors="coerce")
df["Trust"] = pd.to_numeric(df["Trust"], errors="coerce")

df = df.dropna(subset=["Empathy", "Trust", "Version_bin"])

print("🔍 Running mediation analysis...")
results = pg.mediation_analysis(data=df, x="Version_bin", m="Empathy", y="Trust", alpha=0.05, n_boot=5000, seed=42)
print(results)

output_dir = "outputs/mediation"
os.makedirs(output_dir, exist_ok=True)

out_path = f"{output_dir}/version_empathy_trust.csv"
results.to_csv(out_path, index=False)

