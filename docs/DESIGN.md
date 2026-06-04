# DESIGN.md

# Store Intelligence Platform – System Design

## Overview

The goal of this project is to transform raw retail store activity into actionable analytics through an event-driven architecture.

The system ingests visitor activity, stores structured events, computes analytics, and exposes operational intelligence through REST APIs and a dashboard.

The solution was designed to be lightweight, easy to deploy, and suitable for small to medium retail environments.

---

# Architecture

The platform follows a pipeline-based architecture:

Detection Layer
↓
Event Generation
↓
FastAPI Ingestion Layer
↓
SQLite Storage
↓
Analytics Engine
↓
Dashboard & REST APIs

The detection layer identifies visitors and generates structured events.

These events are ingested by FastAPI and stored in SQLite.

Analytics endpoints process the stored events and generate business metrics such as visitor counts, conversion rates, heatmaps, funnels, and anomalies.

The dashboard consumes the same analytics layer and presents the results visually.

---

# Event Pipeline

The system uses an event-driven approach.

Each visitor action is represented as a structured event containing:

* event_id
* store_id
* visitor_id
* event_type
* timestamp
* zone_id
* dwell_time
* confidence

This design allows new event types to be added without changing the analytics architecture.

The event stream becomes the source of truth for all downstream computations.

---

# Storage Layer

SQLite was selected as the storage engine.

Reasons:

* Zero configuration
* Lightweight deployment
* Easy local development
* Sufficient for challenge-scale workloads

The database stores:

1. Visitor events
2. Transaction records

Analytics endpoints aggregate data directly from these tables.

---

# Analytics Engine

The analytics layer computes:

## Metrics

* Unique visitors
* Revenue
* Transactions
* Average basket value
* Average dwell time
* Conversion rate

## Funnel

Tracks visitor progression through:

Store Entry → Zone Visit → Billing → Purchase

This provides visibility into drop-off points.

## Heatmap

Aggregates zone activity and dwell behavior.

Zone activity is visualized both as tabular data and through the dashboard heatmap overlay.

## Anomalies

Detects operational issues including:

* High dwell time
* Potential checkout congestion

Anomalies include severity and suggested actions.

---

# Dashboard

The dashboard provides a visual interface for business users.

Components include:

* KPI cards
* Conversion funnel
* Zone heatmap visualization
* Anomaly alerts

The dashboard is powered by the same analytics APIs used by external consumers.

---

# AI-Assisted Decisions

AI tools were used throughout development to accelerate implementation and evaluate design alternatives.

Examples include:

### Event Schema Design

AI-assisted brainstorming was used to evaluate different event structures.

The final schema was simplified to focus on analytics requirements while maintaining extensibility.

### Analytics API Design

AI suggestions were used when designing metrics, funnel, heatmap, and anomaly endpoints.

Several generated approaches were modified before implementation to better fit the project requirements.

### Dashboard Design

AI-assisted iterations helped improve the dashboard layout, KPI presentation, funnel visualization, and heatmap representation.

The final implementation was chosen based on clarity and simplicity rather than feature count.

### Architectural Trade-Offs

AI suggested multiple storage and deployment approaches.

After evaluation, a lightweight FastAPI + SQLite architecture was selected because it reduced operational complexity while still meeting all requirements.

---

# Future Improvements

Potential future enhancements include:

* Real-time event streaming
* Multi-store aggregation
* Queue depth prediction
* Customer journey analysis
* Advanced anomaly detection
* Interactive dashboards
* PostgreSQL migration for large-scale deployments

The current architecture was intentionally kept simple to prioritize reliability, maintainability, and rapid deployment.
