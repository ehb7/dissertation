"""
Step6. Create two sheets that will be consumed by the Streamlit dashboard
and write them as an Excel.
- "sales_last3months_forecast": last 3 months of real orders + the 3-day forecast
- "ingredient_requirements": ingredient needs per forecast date
"""

import logging
import pandas as pd

import sys
sys.path.append("..")
from config import ORDERS_TABLE, PRODUCT_CATALOG_TABLE, EXCEL_OUTPUT_PATH, SIZE_MULTIPLIER, INGREDIENT_QUANTITIES_PATH

logger = logging.getLogger(__name__)

def _load_pc(conn) -> pd.DataFrame:
    # Load product_catalog
    query = f"SELECT * FROM {PRODUCT_CATALOG_TABLE}"
    df = pd.read_sql(query, conn) 
    return df

def _sales_sheet(conn, forecast_df: pd.DataFrame, catalog_df: pd.DataFrame) -> pd.DataFrame:

    logger.info("Loading last 3 months of orders history")
    query = f"""
        SELECT item_id, order_date AS date, quantity
        FROM {ORDERS_TABLE}
        WHERE order_date >= (SELECT MAX(order_date) - INTERVAL '3 months' FROM {ORDERS_TABLE})
    """
    history_df = pd.read_sql(query, conn)
    history_df["date"] = pd.to_datetime(history_df["date"])
    history_df["is_forecast"] = False

    logger.info("Formatting forecast rows")
    forecast_rows = forecast_df.rename(
        columns={"forecast_date": "date", "predicted_quantity": "quantity"}
    )[["item_id", "date", "quantity"]]
    forecast_rows["is_forecast"] = True

    logger.info("Merging with product_catalog for product_name/category/variant")
    combined = pd.concat([history_df, forecast_rows], ignore_index=True)
    combined = combined.merge(
        catalog_df[["item_id", "product_name", "category", "variant"]], on="item_id", how="left"
    )

    sales_sheet = combined[["date", "product_name", "variant", "category", "quantity", "is_forecast"]]
    sales_sheet = sales_sheet.sort_values(['date', 'product_name', 'variant']).reset_index(drop=True)

    logger.info("Sales sheet built: %d rows (%d historical, %d forecast)",
                len(sales_sheet), len(history_df), len(forecast_rows))
    return sales_sheet

def _ingredient_quantities() -> dict:
    logger.info(f"Loading ingredient base quantities from {INGREDIENT_QUANTITIES_PATH}")
    quantities_df = pd.read_csv(INGREDIENT_QUANTITIES_PATH)
    return dict(zip(quantities_df["ingredient"], quantities_df["base_quantity_g"]))


def _ingredient_sheet(forecast_df: pd.DataFrame, catalog_df: pd.DataFrame) -> pd.DataFrame:

    logger.info("Applying size_multiplier to predicted quantities")
    catalog_df["size_multiplier"] = catalog_df["variant"].map(SIZE_MULTIPLIER)

    logger.info("Exploding comma-separated ingredients into individual rows")
    # Every pizza also uses Dough and Tomato Sauce as base ingredients, not
    # listed explicitly in the raw ingredients column
    exploded = catalog_df[["item_id", "ingredients", "size_multiplier"]].copy()
    exploded["ingredients"] = exploded["ingredients"].str.split(",")
    exploded["ingredients"] = exploded["ingredients"].apply(
        lambda ing_list: ["Dough", "Tomato Sauce"] + ing_list
    )
    exploded = exploded.explode("ingredients")
    exploded["ingredients"] = exploded["ingredients"].str.strip()

    logger.info("Mapping each ingredient to its assumed base quantity (grams)")
    ingredient_quantities = _ingredient_quantities()
    exploded["base_quantity_g"] = exploded["ingredients"].map(ingredient_quantities)

    # Fill ingredients missing from quantities file
    exploded["base_quantity_g"] = exploded["base_quantity_g"].fillna(0)

    # Scale each ingredient's base quantity by the product size
    exploded["ingredient_quantity_g"] = exploded["base_quantity_g"] * exploded["size_multiplier"]

    merged_with_ingredients = forecast_df.merge(
        exploded[["item_id", "ingredients", "ingredient_quantity_g"]], on="item_id", how="left"
    )

    logger.info("Computing ingredient needs per forecast date")
    merged_with_ingredients["adjusted_quantity"] = ( merged_with_ingredients["predicted_quantity"] * merged_with_ingredients["ingredient_quantity_g"])

    logger.info("Summing ingredient needs per forecast date")
    totals = (
        merged_with_ingredients
        .groupby(["ingredients", "forecast_date"])["adjusted_quantity"]
        .sum()
        .round(2)
        .reset_index()
    )

    logger.info("Pivoting to wide format (one column per forecast date)")
    ingredient_sheet = totals.pivot(index="ingredients", columns="forecast_date", values="adjusted_quantity").reset_index()
    ingredient_sheet.columns.name = None
    ingredient_sheet = ingredient_sheet.rename(columns={"ingredients": "Ingredient"})

    date_cols = [c for c in ingredient_sheet.columns if c != "Ingredient"]
    ingredient_sheet = ingredient_sheet.rename(columns={c: c.strftime("%Y-%m-%d") for c in date_cols})
    date_col_names = [c.strftime("%Y-%m-%d") for c in date_cols]

    ingredient_sheet["total"] = ingredient_sheet[date_col_names].sum(axis=1).round(2)

    logger.info("Ingredient sheet built")
    return ingredient_sheet

def run(conn, forecast_df: pd.DataFrame) -> None:
    # Load product catalog as both sheets uses it 
    pc_df = _load_pc(conn)

    # Build sales_last3months_forecast 
    sales_sheet = _sales_sheet(conn, forecast_df, pc_df)

    # Build ingredient_requirements
    ingredient_sheet = _ingredient_sheet(forecast_df, pc_df)

    logger.info("Writing Excel file to %s", EXCEL_OUTPUT_PATH)
    with pd.ExcelWriter(EXCEL_OUTPUT_PATH, engine="openpyxl") as writer:
        sales_sheet.to_excel(writer, index=False, sheet_name='sales_last3months_forecast')
        ingredient_sheet.to_excel(writer, index=False, sheet_name='ingredient_forecast')

    logger.info("Excel export complete")


