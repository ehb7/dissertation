# Restaurant Demand Forecasting & Food Waste Reduction

## MSc Big Data Management & Analytics — Griffith College Dublin (2026) Author: Eduardo Heras Barrales

## Overview
Restaurants routinely over-prepare ingredients to avoid running out, which leads to significant food waste and cost. This project builds an end-to-end big data pipeline that ingests sales data, models historical demand, and forecasts future sales so that kitchens can plan ingredient preparation more accurately.

## Goals
Daily forecast product-level demand 
Translate forecasts into ingredient requirements
Quantify the potential reduction in food waste versus naive planning

## Dataset
Pizza Sales dataset https://www.kaggle.com/datasets/shilongzhuang/pizza-sales

## Table	Rows	Description
product_catalog	91	Pizza types, sizes, categories, ingredients, prices
orders	48,619	Order lines with timestamps and quantities

## Architecture
CSV of orders (restaurant's daily raw data)
        │
        ▼
Ingestion (Step 2): simulated MapReduce + load to DB
        │
        ▼
Feature engineering (Steps 3-4): lags, cyclical encoding, weather
        │
        ▼
XGBoost forecast (Step 4): recursive 3-day forecast
        │
        ▼
Forecast table (Step 5): refreshed in PostgreSQL
        │
        ▼
Excel export (Step 6): sales + ingredient requirements
        │
        ▼
Streamlit dashboard: Forecast + Ingredients pages

*PostgreSQL (Docker) is used as a staging store during development.

## Tech Stack
- **Language:** Python
- **Ingestion:** Simulated MapReduce (Python)
- **Database:** PostgreSQL (Docker)
- **Feature engineering:** Lag features, cyclical time encoding, weather data
- **Model:** XGBoost (recursive 3-day forecast)
- **Reporting:** Excel export (sales + ingredient requirements)
- **Dashboard:** Streamlit
