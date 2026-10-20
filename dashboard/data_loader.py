"""
Functions to read and load data for the generated Excel
And to get the last update day (wich day this code was runned)
"""

import os
import pandas as pd
import streamlit as st

# Path to where the generated Excel is (change if needed)
DATA_PATH = os.path.join(os.path.dirname(__file__), "daily_sales_forecast.xlsx")

# @st.cache_data stores this function's output so Streamlit skips re-running it.
@st.cache_data
def load_sales_data(path: str = DATA_PATH) -> pd.DataFrame:
    # read_excel with sheet_name, reading only the first page
    df = pd.read_excel(path, sheet_name="sales_last3months_forecast")

    # make sure 'date' is a real datetime column, not text, so we can sort/filter by day
    df["date"] = pd.to_datetime(df["date"])

    return df


@st.cache_data
def load_ingredient_data(path: str = DATA_PATH) -> pd.DataFrame:
    # read_excel with sheet_name, reading only the second page
    df = pd.read_excel(path, sheet_name="ingredient_forecast")
    return df


def get_last_update(path: str = DATA_PATH) -> str:
    # os.path.getmtime gives seconds since epoch, pd.Timestamp turns it into a date/time we can format
    mtime = os.path.getmtime(path)
    return pd.Timestamp(mtime, unit="s").strftime("%Y-%m-%d %H:%M")
