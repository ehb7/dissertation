# orchestrator.py
# Runs the full pipeline (steps 2-8) in a single process, sharing one DB connection.
# Step 1 (Map & Reduce) runs separately on Hadoop and produces the CSV consumed by step 2.
# Step numbering matches the thesis pipeline diagram; steps 8-9 were dropped on purpose
# (ingredient requirements do not need to be persisted in Postgres, see step7 docstring).

import logging
import psycopg2
from config import DB_CONFIG
from steps import (
    step2_load_to_postgres,
    step3_compute_features,
    step4_create_forecast,
    step5_forecast_table,
    step6_excel_sheets
)

# Configurate loggins so logs can be saved on logs/
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),                          
        logging.FileHandler("logs/pipeline.log"), 
    ],
)
logger = logging.getLogger("orchestrator")


if __name__ == "__main__":
    conn = psycopg2.connect(**DB_CONFIG)

    try:
        logger.info("Step 2: Load map&reduce output into PostgreSQL")
        step2_load_to_postgres.run(conn)

        logger.info("Step 3: Compute features")
        step3_result = step3_compute_features.run(conn)

        logger.info("Step 4: Calculate recursive 3-day forecast")
        step4_result = step4_create_forecast.run(conn, clean_df=step3_result)

        logger.info("Step 5: Recreate forecast table")
        step5_forecast_table.run(conn, forecast_df= step4_result)

        logger.info("Step 6: Build final Excel spreadsheet")
        step6_excel_sheets.run(conn, forecast_df=step4_result)

        conn.commit()
        logger.info("Pipeline completed successfully")

    except Exception:
        conn.rollback()
        logger.exception("Pipeline failed, rolling back all changes")
        raise
    finally:
        conn.close()
