"""
Step 3: Compute features for known past day
"""

import logging
import pandas as pd
import numpy as np
import holidays
import requests

import sys
sys.path.append("..")
from config import DB_CONFIG, ORDERS_TABLE 

logger = logging.getLogger(__name__)

def _lag_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(["item_id", "order_date"])
    # Compute lag for 1 and 7 days
    for lag in [1, 7]:
        df[f"lag_{lag}"] = df.groupby("item_id")["quantity"].shift(lag)
    return df


def _weather_score(df: pd.DataFrame, processing_date: pd.Timestamp) -> pd.DataFrame:
    last_date = processing_date.strftime("%Y-%m-%d")
    # Get the weather from a certaint location for a certaint date
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": 40.7357,
        "longitude": -74.1724,
        "start_date": last_date,
        "end_date": last_date,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "timezone": "America/New_York",
    }

    response = requests.get(url, params=params)
    weather_data = response.json()

    temp_max = weather_data["daily"]["temperature_2m_max"][0]
    temp_min = weather_data["daily"]["temperature_2m_min"][0]
    precip = weather_data["daily"]["precipitation_sum"][0]

    logger.info("Computing weather score (0-5)")

    avg_temp = (temp_max + temp_min) / 2
    temp_score = 5 - min(max(abs(avg_temp - 20) / 20 * 5, 0), 5)
    rain_penalty = min(max(precip / 10 * 2, 0), 2)
    weather_score = min(max(temp_score - rain_penalty, 0), 5)

    logger.info("Weather score for %s: %.2f", last_date, weather_score)
    df["weather"] = weather_score

    return df

def _calendar_features(df: pd.DataFrame) -> pd.DataFrame:
    day_of_week = df["order_date"].dt.dayofweek 
    month = df["order_date"].dt.month

    df["day_of_week_sin"] = np.sin(2 * np.pi * day_of_week / 7)
    df["day_of_week_cos"] = np.cos(2 * np.pi * day_of_week / 7)
    df["month_sin"] = np.sin(2 * np.pi * month / 12)
    df["month_cos"] = np.cos(2 * np.pi * month / 12)

    # US bank holidays as the dataSet comes from a pizza place in New Jersey
    # Extract year
    year= df["order_date"].dt.year.max()

    us_holidays = holidays.US(state="NY", years=year) 
    df["weekend_holiday"] = day_of_week.isin([5, 6]) | df['order_date'].dt.date.isin(us_holidays)

    return df


def run(conn) -> pd.DataFrame:
    # Get todays date to make sure its a constant 
    query = f"SELECT MAX(order_date) AS processing_date FROM {ORDERS_TABLE};"
    result = pd.read_sql(query, conn) 
    processing_date = pd.to_datetime(result["processing_date"].iloc[0])

    # Read last date orders + lag of 7 days 
    query = f"SELECT * FROM {ORDERS_TABLE} WHERE order_date >= (SELECT MAX(order_date) - INTERVAL '8 days' FROM orders);"
    df = pd.read_sql(query, conn)

    df["order_date"] = pd.to_datetime(df["order_date"])
    
    # Compute lags 1 & 7 days 
    df = _lag_features(df)
    logger.info("Lag features have been added")
    #######
    logger.info("processing_date=%s (type=%s)", processing_date, type(processing_date))
    logger.info("df order_date dtype=%s, sample=%s", df["order_date"].dtype, df["order_date"].head(3).tolist())

    df = df[df["order_date"] == processing_date].reset_index(drop=True)
    logger.info("Kept %d rows (one per item_id)", len(df))
    #######
    # Filtering to the latest available row per item_id
    
    df = df[df["order_date"] == processing_date].reset_index(drop=True)
    logger.info("Kept %d rows (one per item_id)", len(df))

    # Adding calendar features 
    df= _calendar_features(df)
    logger.info("Calendar features have been added")

    # Adding weather features 
    df = _weather_score(df, processing_date)
    logger.info("Weather features have been added")

    logger.info("Computed features for %d rows, %d columns", len(df), df.shape[1])

    return df
