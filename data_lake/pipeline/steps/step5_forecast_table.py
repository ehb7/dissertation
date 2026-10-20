"""
Step 5. Drop past day forecast table. Create a new one and add the new forcats with the 3 days.
"""

import logging
import pandas as pd
from io import StringIO

import sys
sys.path.append("..")
from config import FORECAST_TABLE 

logger = logging.getLogger(__name__)

def run(conn, forecast_df: pd.DataFrame) -> None:

    create_table = f"""
        CREATE TABLE {FORECAST_TABLE} (
            item_id INTEGER NOT NULL,
            forecast_date DATE NOT NULL,
            horizon_day SMALLINT NOT NULL,
            predicted_quantity NUMERIC NOT NULL,
            created_at TIMESTAMP DEFAULT NOW(),
            PRIMARY KEY (item_id, forecast_date)
        );
    """      
    #Drop and recreate the forecast table
    with conn.cursor() as cur:
        cur.execute(f"DROP TABLE IF EXISTS {FORECAST_TABLE};")
        cur.execute(create_table)
    logger.info("Recreated table %s", FORECAST_TABLE)                                   

    # Prepare table for insert
    forecast_csv = forecast_df[
        ["item_id", "forecast_date", "horizon_day", "predicted_quantity"]
    ]

    buffer = StringIO()
    # Read line by line with the buffer
    forecast_csv.to_csv(buffer, index=False, header=False)
    buffer.seek(0)

    with conn.cursor() as cur:
        cur.copy_expert(
            f"COPY {FORECAST_TABLE} (item_id, forecast_date, horizon_day, predicted_quantity) "
            f"FROM STDIN WITH CSV",
            buffer,
        )

    logger.info("Inserted %d rows into %s", len(forecast_df), FORECAST_TABLE)
