import pandas as pd
import os

# Load the cleaned dataset
df = pd.read_csv("data/Chatbot_Study_Data_Cleaned.csv")

# Normalize version names for grouping
df["Version"] = df["Version"].str.strip().str.capitalize()

# Prepare output directory
os.makedirs("outputs", exist_ok=True)

# Initialize list to store summary rows
flow_rows = []

for version in ["Elli", "Static"]:
    sub_df = df[df["Version"] == version]

    total_recruited = len(sub_df)
    excluded = sub_df[sub_df["Participant_status"] == 2].shape[0]
    dropped_out = sub_df[
        (sub_df["Participant_status"] == 1) | (sub_df["Dropout_status"] == 1)
    ].shape[0]
    final_sample = sub_df[
        (sub_df["Participant_status"] == 0) & (sub_df["Dropout_status"] == 0)
    ].shape[0]

    flow_rows.append({
        "Version": version,
        "Total recruited": total_recruited,
        "Excluded": excluded,
        "Dropped out": dropped_out,
        "Final analytic sample": final_sample
    })

# Create the summary table
flow_table = pd.DataFrame(flow_rows)

# Display the result
print(flow_table)

# Save to CSV
flow_table.to_csv("outputs/participant_flow_table.csv", index=False)