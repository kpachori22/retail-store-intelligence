import sqlite3
import json
import csv

conn = sqlite3.connect("retail_analytics.db")
cursor = conn.cursor()
cursor.execute("DROP TABLE IF EXISTS events")
cursor.execute("DROP TABLE IF EXISTS transactions")

cursor.execute("""
CREATE TABLE IF NOT EXISTS events (

    event_id TEXT PRIMARY KEY,

    store_id TEXT,
    camera_id TEXT,

    visitor_id TEXT,

    event_type TEXT,

    timestamp TEXT,

    zone_id TEXT,

    dwell_ms INTEGER,

    is_staff INTEGER,

    confidence REAL,

    metadata TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS transactions (

    transaction_id TEXT PRIMARY KEY,

    store_id TEXT,

    transaction_time TEXT,

    basket_value REAL
)
""")

with open("events.jsonl", "r") as f:

    for line in f:

        line = line.strip()

        if not line:
            continue

        event = json.loads(line)

        cursor.execute("""
        INSERT INTO events (
            event_id,
            store_id,
            camera_id,
            visitor_id,
            event_type,
            timestamp,
            zone_id,
            dwell_ms,
            is_staff,
            confidence,
            metadata
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event["event_id"],
            event["store_id"],
            event["camera_id"],
            event["visitor_id"],
            event["event_type"],
            event["timestamp"],
            event["zone_id"],
            event["dwell_ms"],
            event["is_staff"],
            event["confidence"],
            json.dumps(event["metadata"])
        ))

with open("POS - sample transactionsb1e826f.csv", "r", encoding="utf-8") as f:

    reader = csv.DictReader(f)

    for row in reader:

        timestamp = (
            row["order_date"] +
            " " +
            row["order_time"]
        )

        cursor.execute("""
        INSERT OR REPLACE INTO transactions (
            transaction_id,
            store_id,
            transaction_time,
            basket_value
        )
        VALUES (?, ?, ?, ?)
        """, (
            str(row["order_id"]),
            row["store_id"],
            timestamp,
            float(row["total_amount"])
        ))

conn.commit()
conn.close()

print("Database created successfully!")