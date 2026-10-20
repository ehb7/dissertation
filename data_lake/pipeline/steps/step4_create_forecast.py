"""
Step 4: Create the forcast for 3 days using the XGBoost mdel previously trained.
Thi is a recursive forecast as two of the forcated days will help to forcast other days.
"""

import logging
import pickle
import pandas as pd
import numpy as np
import holidays

import sys
sys.path.append("..")
from config import MODEL_PATH, FORECAST_DAYS, ORDERS_TABLE

logger = logging.getLogger(__name__)

def _calculate_lag7(conn, item_ids: list, target_date: pd.Timestamp) -> pd.Series:
    lookup_date = (target_date - pd.Timedelta(days=7)).strftime("%Y-%m-%d")
    # Create query that uses only the date 
    query = f"""
        SELECT item_id, SUM(quantity) AS quantity
        FROM {ORDERS_TABLE}
        WHERE order_date = %s 
        GROUP BY item_id
    """
    lag7_df = pd.read_sql(query, conn, params=(lookup_date,))
    lag7_series = lag7_df.set_index("item_id")["quantity"]

    # items with no order on that historical date get lag_7 = 0
    return lag7_series.reindex(item_ids, fill_value=0)

def _build_day_features(conn, target_date: pd.Timestamp, previous_predictions: pd.Series) -> pd.DataFrame:
    # Build a df for next day 

    month= target_date.month
    day= target_date.dayofweek

    us_holidays = holidays.US(state="NJ", years=[target_date.year])
    is_weekend = day in (5, 6) 
    is_holiday = target_date.date() in us_holidays
    weekend_holiday = int(is_weekend or is_holiday)

    # Get all ids
    query = f"SELECT DISTINCT item_id FROM {ORDERS_TABLE}"
    df = pd.read_sql(query, conn)
    item_ids= df["item_id"].tolist()

    # Calculate other features
    day_df = pd.DataFrame({"item_id": item_ids})
    day_df["lag_1"] = previous_predictions.reindex(item_ids, fill_value=0)
    # Use an special function
    day_df["lag_7"] = _calculate_lag7(conn, item_ids, target_date)
    day_df["weekend_holiday"]= weekend_holiday
    # Predicting the weather is not posible so put a default
    day_df["weather"]= 3
    day_df["day_of_week_sin"]= np.sin(2 * np.pi * day / 7)
    day_df["day_of_week_cos"]= np.cos(2 * np.pi * day / 7)
    day_df["month_sin"]= np.sin(2 * np.pi * month / 12)
    day_df["month_cos"]= np.cos(2 * np.pi * month / 12)
    
    return day_df

def run(conn, clean_df: pd.DataFrame) -> pd.DataFrame:
    with open(MODEL_PATH, "rb") as f:
            model = pickle.load(f)
    logger.info("Model loaded")

    features = ['item_id', 'lag_1', 'lag_7', 'weekend_holiday', 'weather',
                 'day_of_week_sin', 'day_of_week_cos', 'month_sin', 'month_cos']

    all_predictions = []
    day_df= clean_df.copy()

    today = clean_df["order_date"].iloc[0]

    for day_offset in range(1, FORECAST_DAYS + 1):
        target_date = today + pd.Timedelta(days=day_offset)
        logger.info("Forecasting day +%d (%s)", day_offset, target_date.strftime("%Y-%m-%d"))

        if day_offset != 1:
            logger.info("Building df for day +%d", day_offset)
            day_df = _build_day_features(conn, target_date, previous_predictions)

        predictions = model.predict(day_df[features])

        day_predictions = pd.DataFrame({
            "item_id": day_df["item_id"],
            "forecast_date": target_date,
            "horizon_day": day_offset,
            "predicted_quantity": predictions,
        })

        all_predictions.append(day_predictions)
        previous_predictions = day_predictions.set_index("item_id")["predicted_quantity"]

    forecast_df = pd.concat(all_predictions, ignore_index=True)
    logger.info("Generated forecast for %d item/day combinations", len(forecast_df))

    return forecast_df
