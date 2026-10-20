Restaurant Demand Forecasting & Food Waste Reduction

MSc Big Data Management & Analytics — Griffith College Dublin (2026) Author: Eduardo [Apellido]

Overview

Restaurants routinely over-prepare ingredients to avoid running out, which leads to significant food waste and cost. This project builds an end-to-end big data pipeline that ingests sales data, models historical demand, and forecasts future sales so that kitchens can plan ingredient preparation more accurately.

Goals

Forecast product-level demand (daily / hourly)
Translate forecasts into ingredient requirements
Quantify the potential reduction in food waste versus naive planning
Dataset

Pizza Sales dataset (Kaggle) — replace with exact link

Table	Rows	Description
product_catalog	91	Pizza types, sizes, categories, ingredients, prices
orders	48,619	Order lines with timestamps and quantities
Architecture
CSV / Kaggle ──► Kafka (streaming ingestion)
                    │
                    ▼
              PySpark (processing & feature engineering)
                    │
                    ▼
              Delta Lake (bronze / silver / gold layers)
                    │
                    ▼
              BigQuery (analytics & serving)
                    │
                    ▼
              Forecasting model ──► Demand & ingredient forecasts

PostgreSQL (Docker) is used as a staging store during development.

Tech Stack
Ingestion: Apache Kafka
Processing: PySpark
Storage: Delta Lake, PostgreSQL (Docker)
Warehouse: Google BigQuery
Modelling: [e.g. Prophet / XGBoost / SARIMA]
Language: Python
