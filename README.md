# Store Intelligence Platform

## Overview

Store Intelligence Platform is a retail analytics solution built using FastAPI, SQLite, YOLO-based visitor tracking, and a lightweight dashboard.

The platform processes visitor events, calculates store analytics, and exposes insights through REST APIs and a dashboard.

## Features

* Event ingestion API
* Visitor metrics
* Conversion funnel analytics
* Zone heatmap analytics
* Anomaly detection
* Dashboard visualization
* Dockerized deployment

## Architecture

Visitor Tracking → Event Generation → SQLite Storage → Analytics APIs → Dashboard

## APIs

### Health

GET /health

### Event Ingestion

POST /events/ingest

### Metrics

GET /stores/{store_id}/metrics

### Heatmap

GET /stores/{store_id}/heatmap

### Funnel

GET /stores/{store_id}/funnel

### Anomalies

GET /stores/{store_id}/anomalies

## Dashboard

Dashboard URL:

http://localhost:8000/dashboard

## Local Setup

Install dependencies:

pip install -r requirements.txt

Run application:

uvicorn main:app --reload

## Docker Setup

docker compose up --build

## Technologies

* Python
* FastAPI
* SQLite
* Docker
* YOLOv8
* OpenCV

## Sample Analytics

Metrics:

* Visitors
* Revenue
* Transactions
* Conversion Rate

Heatmap:

* Zone activity visualization

Anomalies:

* High dwell-time detection
