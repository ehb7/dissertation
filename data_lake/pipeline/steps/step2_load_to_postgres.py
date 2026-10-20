"""
Step2: Load the generated output from map & reduce process
and incert into "orders" table in PostgreSQL.
"""

import os
import glob
import logging
import pandas as pd

import sys
sys.path.append("..")
from config import RAW_CSV_DIR, ORDERS_TABLE, PRODUCT_CATALOG_TABLE 

logger = logging.getLogger(__name__)


def _get_csv(csv_dir: str) -> str:
    csv_files = glob.glob(os.path.join(csv_dir, "*.csv"))
    # If no output was generated cancel the pipeline
    if len(csv_files) == 0:
        raise FileNotFoundError(f"No CSV file found in {csv_dir}")
    # If more than one output was generated cancel the pipeline
    if len(csv_files) > 1:
        raise RuntimeError(
            f"Expected exactly 1 CSV in {csv_dir}, found {len(csv_files)}: {csv_files}"
        )
    # glob.glob() returns a list so return only first element 
    return csv_files[0]

def _map_item_id(conn, df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Mapping pizza_id to item_id using product_catalog")
    catalog_df = pd.read_sql(f"SELECT item_id, product_id, variant FROM {PRODUCT_CATALOG_TABLE}", conn)

    df = df.merge(catalog_df, on="product_id", how="left")

    # Exclude XL/XXL sizes as they  were removed before model training due to insufficient volume for reliable forecasting.
    excluded_sizes = ["XL", "XXL"]
    excluded_mask = df["variant"].isin(excluded_sizes)
    if excluded_mask.any():
        logger.info(f"Excluding {excluded_mask.sum()} order(s) with size in {excluded_sizes}, consistent with model training data.")
        df = df[~excluded_mask]
 
    # In case a pizza_id was badly writen or a new pizza was created raise an error so it can be solved
    unmapped = df[df["item_id"].isna()]
    if len(unmapped) > 0:
        logger.warning(
            f"Found {len(unmapped)} pizza_id(s) not present in product_catalog: {unmapped['product_id'].unique().tolist()}"
        )

    df.drop(columns="variant", inplace=True)
    return df

def _fill_item_id(conn, df: pd.DataFrame) -> pd.DataFrame:
    # Ensures every valid product has a row for the order_date 
    logger.info("Ensuring complete product grid for the processed date")

    order_date = df["order_date"].iloc[0]

    catalog_df = pd.read_sql(f"SELECT item_id FROM {PRODUCT_CATALOG_TABLE} WHERE variant NOT IN ('XL', 'XXL')",conn)

    full_index = pd.DataFrame({
        "item_id": catalog_df["item_id"],
        "order_date": order_date,
    })

    # Left join so the rela sales are not affected
    df = full_index.merge(df, on=["item_id", "order_date"], how="left")
    df["quantity"] = df["quantity"].fillna(0)

    logger.info(f"All products have been maped. {int(df['quantity'].eq(0).sum())} had zero sales this run.")

    return df

def run(conn) -> dict:
   # Make sure the csv exist 
    csv_path = _get_csv(RAW_CSV_DIR)
    logger.info("Loading CSV: %s", csv_path)

    df = pd.read_csv(csv_path)

    # Add todays date as this column was not created on map reduce
    today = pd.Timestamp.today().normalize()
    #df["order_date"] = today
    # For this run, add 01/01/2016 as the last day on the dataset is 31/12/2015 
    df["order_date"] = pd.Timestamp("2016-01-01")
    logger.info("Stamped order_date: %s", today.strftime("%Y-%m-%d"))
    print(df.columns.tolist())

    df = _map_item_id(conn, df)
    df = _fill_item_id(conn,df)

    # Keep only the columns "orders" expects, in the right order
    df = df[["item_id", "order_date", "quantity"]]

    # Create query
    columns = ", ".join(df.columns)
    # Build a "%s, %s, %s..." placeholder string with one %s per column.
    # prevents SQL injection
    vals = ", ".join(["%s"] * len(df.columns))
    insert_query = f"INSERT INTO {ORDERS_TABLE} ({columns}) VALUES ({vals})"

    with conn.cursor() as cur:
        # Insert row per row 
        for row in df.itertuples(index=False, name=None):
            cur.execute(insert_query, row)

    logger.info("Inserted %d rows into %s", len(df), ORDERS_TABLE)
