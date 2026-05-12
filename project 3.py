import pandas as pd
import numpy as np


zillow_path = '### input zillow file ###'
income_path = '###input income file###'


df = pd.read_csv(zillow_path)
income_df = pd.read_csv(income_path)

df.columns = df.columns.str.strip()
income_df.columns = income_df.columns.str.strip()


time_cols = [col for col in df.columns if col[:4].isdigit()]
time_cols = sorted(time_cols)


df = df[df["RegionName"] != "United States"].copy()


for col in time_cols:
    df[col] = (
        df[col]
        .astype(str)
        .str.replace(",", "", regex=False)
        .str.replace("'", "", regex=False)
    )
    df[col] = pd.to_numeric(df[col], errors="coerce")

city_state = df["RegionName"].str.split(",", expand=True)
city_state.columns = ["City", "State"]

city_state["City"] = city_state["City"].str.strip()
city_state["State"] = city_state["State"].str.strip()

df = pd.concat([df, city_state], axis=1)
df = df[df["State"].str.len() == 2]


latest_col = time_cols[-1]
prev_col = time_cols[-13]  # ~1 year ago

master = df[["RegionName", "City", "State", latest_col, prev_col]].copy()

master = master.rename(columns={
    latest_col: "IncomeNeeded",
    prev_col: "IncomeNeeded_1yrAgo"
})


master = master.dropna(subset=["IncomeNeeded", "IncomeNeeded_1yrAgo"])


master["IncomeChange_1yr"] = master["IncomeNeeded"] - master["IncomeNeeded_1yrAgo"]
master["IncomeChangePct_1yr"] = master["IncomeChange_1yr"] / master["IncomeNeeded_1yrAgo"]

date_col = [col for col in income_df.columns if "date" in col.lower()][0]
value_col = [col for col in income_df.columns if col != date_col][0]

income_df[date_col] = pd.to_datetime(income_df[date_col])
income_df = income_df.sort_values(date_col)

median_income = income_df[value_col].dropna().iloc[-1]


master["MedianIncome"] = median_income

master["AffordabilityRatio"] = master["IncomeNeeded"] / median_income

master["AffordabilityCategory"] = pd.cut(
    master["AffordabilityRatio"],
    bins=[0, 1, 1.5, np.inf],
    labels=["Affordable", "Moderate", "Unaffordable"]
)


df_time = df[["RegionName", "City", "State"] + time_cols].copy()

df_time = df_time.melt(
    id_vars=["RegionName", "City", "State"],
    var_name="Date",
    value_name="IncomeNeeded"
)

df_time["Date"] = pd.to_datetime(df_time["Date"], errors="coerce")
df_time["IncomeNeeded"] = pd.to_numeric(df_time["IncomeNeeded"], errors="coerce")

df_time = df_time.dropna(subset=["Date", "IncomeNeeded"])


output_path = '### input desired output path###'

with pd.ExcelWriter(output_path) as writer:
    master.to_excel(writer, sheet_name="Master", index=False)
    df_time.to_excel(writer, sheet_name="TimeSeries", index=False)

print("Balanced dataset ready:", output_path)