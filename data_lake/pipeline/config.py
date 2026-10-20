# Centralized configuration for the forecasting pipeline.
# TODO: change Data Base configuration so it can run on your machine 

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "dissertation",
    "user": "postgres",
    "password": "tuclave",
}

# Directory where the Map & Reduce job writes the daily ingested CSV
RAW_CSV_DIR = "data"

# Path to the trained production model (XGBoost)
MODEL_PATH = "model/xgb_model.pkl"

# Output of the pipeline, consumed independently by the Streamlit dashboard
EXCEL_OUTPUT_PATH = "output/daily_sales_forecast.xlsx"

# Forecast horizon in days (recursive multi-day forecasting)
FORECAST_DAYS = 3

# Text file containing the list of ingredients : weight in grams 
INGREDIENT_QUANTITIES_PATH = "extra/ing_quant.txt"

# Since larger pizzas use more of each ingredient, a size multiplier is applied before calculating total ingredient needs. This assumes a medium (M) pizza as the baseline unit.
SIZE_MULTIPLIER = {
    "S": 0.75,
    "M": 1.00,
    "L": 1.25,
    "XL": 1.50,
    "XXL": 1.75,
}

# Postgres table names
ORDERS_TABLE = "orders"
FORECAST_TABLE = "forecast"
PRODUCT_CATALOG_TABLE = "product_catalog"
