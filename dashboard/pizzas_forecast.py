"""
Page 1: Pizza sales forecast dashboard.
This dashbord displays interactive insigts about yrend sales and
3 upcoming forecasted days. No information about ingridients is displayed in here.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from data_loader import load_sales_data, get_last_update

st.set_page_config(page_title="Pizzas / Forecast", layout="wide")
st.title("Pizzas — Forecast")

# Load sales sheet and split into history vs forecast rows
df = load_sales_data()
history = df[df["is_forecast"] == False]
forecast = df[df["is_forecast"] == True]

# Calculate daily totals (sum of all pizzas/sizes together) for history and forecast
history_daily = history.groupby("date")["quantity"].sum().sort_index()
forecast_daily = forecast.groupby("date")["quantity"].sum().sort_index()

# Get the 3 forecasted dates 
forecast_dates = forecast_daily.index.tolist()  

# Timestamp calculated to know when the pipeline was executed
st.caption(f"Last Update: {get_last_update()}")


# ---------------------------------------------------------------------------
# Part 1: Forecast Cards 
# Create 3 Cards, one for each forecasted day. Adding date, value and previous date comparison 
st.subheader("Forecast per day")

cols = st.columns(3)
last_actual_total = history_daily.iloc[-1]  # last real day, used as baseline for card 1's delta

for i, date in enumerate(forecast_dates):
    total_today = forecast_daily[date]

    # card 1 compares against the last real day; cards 2 and 3 compare against the previous forecast day
    previous_total = last_actual_total if i == 0 else forecast_daily[forecast_dates[i - 1]]
    delta = total_today - previous_total

    with cols[i]:
        st.metric(
            label=date.strftime("%A %d-%b"),
            value=f"{total_today:.0f} pizzas",
            delta=f"{delta:+.0f} vs. last day",
        )


# ---------------------------------------------------------------------------
# Part 2: History plot of 7 days + 3 forcast days 
st.subheader("Last 7 + 3 upcoming days (forecast)")

last_7_history = history_daily.tail(7)

fig_line = go.Figure()

# Solid line for historical sales
fig_line.add_trace(
    go.Scatter(
        x=last_7_history.index,
        y=last_7_history.values,
        mode="lines+markers",
        name="Historical",
        line=dict(color="#1f77b4"),
    )
)

# Dashed line for the forecast, starting from the last historical point so the lines connect visually
forecast_x = [last_7_history.index[-1]] + forecast_dates
forecast_y = [last_7_history.values[-1]] + forecast_daily.values.tolist()
fig_line.add_trace(
    go.Scatter(
        x=forecast_x,
        y=forecast_y,
        mode="lines+markers",
        name="Forecast",
        line=dict(color="#ff7f0e", dash="dash"),
    )
)

fig_line.update_layout(xaxis_title="Date", yaxis_title="Sold Pizzas")
st.plotly_chart(fig_line, use_container_width=True)


# ---------------------------------------------------------------------------
# PArt 3: 
st.subheader("Todays sales by size for forecast")

# Group by day and size so each day can get its own color
size_by_day = forecast.groupby(["date", "variant"])["quantity"].sum().reset_index()

# Make date label shorter
size_by_day["date"] = size_by_day["date"].dt.strftime("%a %d-%b")

size_by_day["quantity"]= size_by_day["quantity"].round()
 
fig_size = px.bar(
    size_by_day,
    x="variant",
    y="quantity",
    color="date",
    barmode="stack",
    # keep sizes and days in a fixed, meaningful order instead of alphabetical
    category_orders={
        "variant": size_by_day.index.tolist(),
        "Date": [forecast_dates],
    },
    labels={"variant": "size", "quantity": "pizzas"},
    text="quantity",
)
fig_size.update_traces(textposition="outside")
st.plotly_chart(fig_size, use_container_width=True)

# ---------------------------------------------------------------------------
# Part 4: Top forecasted pizza products x sizes for firts forecasted day (today)
st.subheader(f"Top 3 products x top 3 sizes for {size_by_day["date"][0]}")

today_df = forecast[forecast["date"] == forecast_dates[0]]

# Top 3 products by predicted quantity
top_flavors = (
    today_df.groupby("product_name")["quantity"].sum().sort_values(ascending=False).head(3).index.tolist()
)

# Top 3 sizes by predicted quantity
top_sizes = (
    today_df.groupby("variant")["quantity"].sum().sort_values(ascending=False).head(3).index.tolist()
)

matrix = (
    today_df[today_df["product_name"].isin(top_flavors)]
    .pivot_table(index="product_name", columns="variant", values="quantity", aggfunc="sum", fill_value=0)
    .reindex(index=top_flavors, columns=top_sizes)
)

st.dataframe(matrix.style.format("{:.0f}"), use_container_width=True)


# ---------------------------------------------------------------------------
# Part 5: Firts forecasted day (today) vs. the same weekday last week, with filters
st.subheader("Today vs. Last Week")

# Create 2 filters only for this section 
filter_cols = st.columns(2)
with filter_cols[0]:
    selected_categories = st.multiselect(
        "Category", options=sorted(df["category"].unique()), default=sorted(df["category"].unique())
    )
with filter_cols[1]:
    selected_sizes = st.multiselect(
        "Size", options=sorted(df["variant"].unique()), default=sorted(df["variant"].unique())
    )

# Apply filters to only this df (hist + forecast)
filtered_df = df[df["category"].isin(selected_categories) & df["variant"].isin(selected_sizes)]

today_total_filtered = filtered_df[filtered_df["date"] == forecast_dates[0]]["quantity"].sum()

# Calculate df for only one day
last_week_date = forecast_dates[0] - pd.Timedelta(days=7)
last_week_total_filtered = filtered_df[filtered_df["date"] == last_week_date]["quantity"].sum()

delta_week = today_total_filtered - last_week_total_filtered

st.metric(
    label=f"{forecast_dates[0].strftime('%A %d-%b')} vs. {last_week_date.strftime('%A %d-%b')}",
    value=f"{today_total_filtered:.0f} pizzas",
    delta=f"{delta_week:+.0f} vs. last week",
)
