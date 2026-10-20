"""
Page 2: Ingredient Table.
This dashboard shows a table containing the forcast 
of the ingredients for the next 3 upcomming days with an extra column 
where the user can input grams or unitis to make their calculations.
"""

import numpy as np
import pandas as pd
import streamlit as st

from data_loader import load_ingredient_data, get_last_update

st.set_page_config(page_title="Ingredientes / Forecast", layout="wide")
st.title("Ingredientes Table")

# Load ingredient sheet"
df = load_ingredient_data()
# Separate date columns as the header of this columns will change every day 
forecast_cols = [c for c in df.columns if c not in ("Ingredient", "total")]

# Timestamp calculated to know when the pipeline was executed
st.caption(f"Last Update: {get_last_update()}")

# Keep the user's stock input across reruns using session_state
if "stock" not in st.session_state:
    st.session_state.stock = {ingredient: 0.0 for ingredient in df["Ingredient"]}


base = df.set_index("Ingredient").sort_values("total", ascending=False)

st.subheader("Stock coverage calculator")
st.caption("Type how much stock you have for each ingredient, the table shows how much is missing per day.")
 
# TABLE 1: 
# Small, editable-only table with just Ingredient + Stock.
stock_series = pd.Series(st.session_state.stock).reindex(base.index).fillna(0.0)
stock_input_df = pd.DataFrame({"Ingredient": base.index, "Available stock (g)": stock_series.values})
 
edited_stock_df = st.data_editor(
    stock_input_df,
    disabled=["Ingredient"],
    hide_index=True,
    width='stretch',
    height=220,
    key="stock_editor",
    column_config={
        "Ingredient": st.column_config.TextColumn(width="medium"),
        "Available stock (g)": st.column_config.NumberColumn(width="small"),
    },
)
 
# Save the user's edits back into session_state so they persist on the next rerun
st.session_state.stock = edited_stock_df.set_index("Ingredient")["Available stock (g)"].to_dict()
 
# STEP 2: 
# Compute the daily shortfall using this run's fresh stock values.
fresh_stock = edited_stock_df.set_index("Ingredient")["Available stock (g)"].reindex(base.index)
 
# Running total of what's needed up to and including each day
cumulative_need = base[forecast_cols].cumsum(axis=1)
 
# How much need is left AFTER using up the stock, up to each day (never below 0)
excess_need = cumulative_need.sub(fresh_stock, axis=0).clip(lower=0)
 
# The shortfall for a single day is the jump in excess_need from the day before
# (day 1 has no "day before", so its shortfall is just its own excess_need)
daily_shortfall = excess_need.diff(axis=1)
daily_shortfall.iloc[:, 0] = excess_need.iloc[:, 0]

st.subheader("Coverage result")
st.caption("How much of each ingredient is still missing per day, after using up your available stock.")

computed_df = pd.DataFrame({"Ingredient": base.index, "Available stock (g)": fresh_stock.values})
for col in forecast_cols:
    computed_df[col] = daily_shortfall[col].values.round(0)
computed_df["Missing stock (g)"] = excess_need[forecast_cols[-1]].values.round(0)
 
st.dataframe(computed_df, hide_index=True, width='stretch', height=500)
 
# Placeholder note
st.markdown("Note: the 95% confidence margin is ±2.45 pizzas for day 1, ±2.45 for day 2, and ±2.48 for day 3 — calculated from the model's historical error observed in December 2015.")