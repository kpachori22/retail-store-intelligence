from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from typing import Optional
from pydantic import BaseModel
import sqlite3

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

DB_NAME = "retail_analytics.db"

class Event(BaseModel):
    event_id: str
    store_id: str
    camera_id: str
    visitor_id: str
    event_type: str
    timestamp: str
    zone_id: str
    dwell_ms: int
    is_staff: bool = False
    confidence: float = 0.8
    metadata: Optional[dict] = {}

@app.get("/health")
def health():

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT timestamp
        FROM events
        ORDER BY timestamp DESC
        LIMIT 1
    """)

    row = cursor.fetchone()

    conn.close()

    if row:

        last_event_timestamp = row[0]

        return {
            "status": "healthy",
            "last_event_timestamp": last_event_timestamp,
            "stale_feed": False
        }

    return {
        "status": "healthy",
        "last_event_timestamp": None,
        "stale_feed": True
    }


@app.get("/events")
def get_events():

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT visitor_id,
               event_type,
               zone,
               dwell_seconds
        FROM events
    """)

    rows = cursor.fetchall()

    conn.close()

    return [
        {
            "visitor_id": row[0],
            "event_type": row[1],
            "zone": row[2],
            "dwell_seconds": row[3]
        }
        for row in rows
    ]


@app.get("/metrics")
def get_metrics():

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM events")
    total_events = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(DISTINCT visitor_id)
        FROM events
    """)
    unique_visitors = cursor.fetchone()[0]

    cursor.execute("""
        SELECT AVG(dwell_seconds)
        FROM events
    """)
    avg_dwell = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM events
        WHERE zone='DISPLAY_ZONE'
    """)
    summer_visits = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM events
        WHERE zone='MAKEUP_ZONE'
    """)
    makeup_visits = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM events
        WHERE zone='FRAGRANCE_ZONE'
    """)
    haircare_visits = cursor.fetchone()[0]

    conn.close()

    return {
        "total_events": total_events,
        "unique_visitors": unique_visitors,
        "average_dwell_time": round(avg_dwell, 1),
        "DISPLAY_ZONE_visits": summer_visits,
        "makeup_zone_visits": makeup_visits,
        "FRAGRANCE_ZONE_visits": haircare_visits
    }

@app.get("/zones")
def get_zones():

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    zones = [
        "DISPLAY_ZONE",
        "MAKEUP_ZONE",
        "FRAGRANCE_ZONE"
    ]

    result = {}

    for zone in zones:

        cursor.execute("""
            SELECT COUNT(*),
                   AVG(dwell_seconds)
            FROM events
            WHERE zone=?
        """, (zone,))

        visits, avg_dwell = cursor.fetchone()

        result[zone] = {
            "visits": visits,
            "average_dwell": round(avg_dwell, 1) if avg_dwell else 0
        }

    conn.close()

    return result

@app.post("/events/ingest")
def ingest_event(event: Event):

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Duplicate protection
    cursor.execute(
        "SELECT event_id FROM events WHERE event_id=?",
        (event.event_id,)
    )

    existing = cursor.fetchone()

    if existing:

        conn.close()

        return {
            "status": "duplicate",
            "event_id": event.event_id
        }

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
        event.event_id,
        event.store_id,
        event.camera_id,
        event.visitor_id,
        event.event_type,
        event.timestamp,
        event.zone_id,
        event.dwell_ms,
        int(event.is_staff),
        event.confidence,
        str(event.metadata)
    ))

    conn.commit()
    conn.close()

    return {
        "status": "success",
        "event_id": event.event_id
    }

@app.get("/stores/{store_id}/metrics")
def store_metrics(store_id: str):

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM events")
    total_events = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(DISTINCT visitor_id)
        FROM events
    """)
    unique_visitors = cursor.fetchone()[0]

    cursor.execute("""
        SELECT AVG(dwell_ms)
                   FROM events
    """)
    avg_dwell = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*),
            SUM(basket_value),
            AVG(basket_value)
        FROM transactions
    """)

    txn_count, revenue, avg_basket = cursor.fetchone()

    cursor.execute("""
        SELECT COUNT(DISTINCT visitor_id)
        FROM events
        WHERE zone_id='BILLING_ZONE'
    """)

    purchases = cursor.fetchone()[0]

    conversion_rate = (
        round((purchases / unique_visitors) * 100, 1)
        if unique_visitors > 0
        else 0
    )

    conn.close()

    return {
        "store_id": store_id,
        "total_events": total_events,
        "unique_visitors": unique_visitors,
        "average_dwell_time_seconds": round(avg_dwell / 1000, 1) if avg_dwell else 0,
        "transactions": txn_count,
        "revenue": round(revenue, 2) if revenue else 0,
        "average_basket_value": round(avg_basket, 2) if avg_basket else 0,
        "conversion_rate": conversion_rate
    }

@app.get("/stores/{store_id}/heatmap")
def heatmap(store_id: str):

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(DISTINCT visitor_id)
        FROM events
    """)

    total_sessions = cursor.fetchone()[0]

    data_confidence = (
    "LOW" if total_sessions < 20
    else "HIGH"
    )

    cursor.execute("""
    SELECT zone_id,
            COUNT(*),
            AVG(dwell_ms)
        FROM events
        GROUP BY zone_id
    """)

    rows = cursor.fetchall()

    conn.close()

    heatmap_data = []

    for row in rows:

        heatmap_data.append({
            "zone": row[0],
            "visit_count": row[1],
            "avg_dwell_seconds": round(row[2] / 1000, 1),
            "normalized_score": round(row[1], 2)
        })

    return {
        "store_id": store_id,
        "data_confidence": data_confidence,
        "heatmap": heatmap_data
    }

@app.get("/stores/{store_id}/funnel")
def funnel(store_id: str):

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Total visitors
    cursor.execute("""
        SELECT COUNT(DISTINCT visitor_id)
        FROM events
        WHERE is_staff = 0
    """)
    store_entries = cursor.fetchone()[0]

    # Visitors who visited any zone
    cursor.execute("""
        SELECT COUNT(DISTINCT visitor_id)
        FROM events
        WHERE event_type='ZONE_DWELL'
        AND is_staff = 0
    """)
    zone_visitors = cursor.fetchone()[0]

    # Visitors who reached billing
    cursor.execute("""
        SELECT COUNT(DISTINCT visitor_id)
        FROM events
        WHERE zone_id='BILLING_ZONE'
        AND is_staff = 0
    """)
    billing_visitors = cursor.fetchone()[0]

    # POS transactions
    cursor.execute("""
        SELECT COUNT(*)
        FROM transactions
    """)
    transaction_count = cursor.fetchone()[0]

    conn.close()

    purchases = min(
        billing_visitors,
        transaction_count
    )

    conversion_rate = (
        round((purchases / store_entries) * 100, 1)
        if store_entries > 0
        else 0
    )

    zone_dropoff_pct = round(((store_entries - zone_visitors) / store_entries) * 100, 1) if store_entries > 0 else 0

    billing_dropoff_pct = round(((zone_visitors - billing_visitors) / zone_visitors) * 100, 1) if zone_visitors > 0 else 0

    purchase_dropoff_pct = round(((billing_visitors - purchases) / billing_visitors) * 100, 1) if billing_visitors > 0 else 0

    return {
        "store_id": store_id,
        "funnel": {
            "store_entries": store_entries,
            "zone_visitors": zone_visitors,
            "billing_visitors": billing_visitors,
            "purchases": purchases,
            "conversion_rate": conversion_rate,
            "zone_dropoff_pct": zone_dropoff_pct,
            "billing_dropoff_pct": billing_dropoff_pct,
            "purchase_dropoff_pct": purchase_dropoff_pct
        }
    }

@app.get("/stores/{store_id}/anomalies")
def anomalies(store_id: str):

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT zone_id,
            AVG(dwell_ms)
        FROM events
        GROUP BY zone_id
    """)

    rows = cursor.fetchall()

    conn.close()

    anomalies = []

    for zone, avg_dwell in rows:

       if avg_dwell and avg_dwell > 20000:

        anomalies.append({
            "type": "HIGH_DWELL_TIME",
            "severity": "WARN",
            "zone": zone,
            "average_dwell_seconds": round(avg_dwell / 1000, 1),
            "suggested_action": "Investigate checkout congestion"
        })

    return {
        "store_id": store_id,
        "anomalies": anomalies
    }

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Metrics
    cursor.execute("SELECT COUNT(DISTINCT visitor_id) FROM events")
    visitors = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*),
               SUM(basket_value),
               AVG(basket_value)
        FROM transactions
    """)
    transactions, revenue, avg_basket = cursor.fetchone()

    cursor.execute("""
        SELECT COUNT(DISTINCT visitor_id)
        FROM events
        WHERE zone_id='BILLING_ZONE'
    """)
    purchases = cursor.fetchone()[0]

    conversion_rate = (
        round((purchases / visitors) * 100, 1)
        if visitors > 0 else 0
    )

    cursor.execute("""
        SELECT COUNT(DISTINCT visitor_id)
        FROM events
    """)
    store_entries = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(DISTINCT visitor_id)
        FROM events
    """)
    zone_visitors = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(DISTINCT visitor_id)
        FROM events
        WHERE zone_id='BILLING_ZONE'
    """)
    billing_visitors = cursor.fetchone()[0]

    # Heatmap
    cursor.execute("""
        SELECT zone_id,
               COUNT(*)
        FROM events
        GROUP BY zone_id
        ORDER BY COUNT(*) DESC
    """)
    heatmap_rows = cursor.fetchall()

    heatmap_html = ""

    for zone, visits in heatmap_rows:

        color_map = {
            "DISPLAY_ZONE": "🔴",
            "MAKEUP_ZONE": "🟠",
            "BILLING_ZONE": "🔵",
            "FRAGRANCE_ZONE": "🟢"
        }

        heatmap_html += (
            f"<tr>"
            f"<td>{color_map.get(zone, '⚪')}</td>"
            f"<td>{zone}</td>"
            f"<td>{visits}</td>"
            f"</tr>"
        )

    # Anomalies
    cursor.execute("""
        SELECT zone_id,
               AVG(dwell_ms)
        FROM events
        GROUP BY zone_id
    """)

    rows = cursor.fetchall()

    anomaly_html = ""

    for zone, avg_dwell in rows:

        if avg_dwell and avg_dwell > 20000:

            anomaly_html += (
                f"<li style='color:red; font-weight:bold'>"
                f"⚠ HIGH_DWELL_TIME - "
                f"{zone} "
                f"({round(avg_dwell / 1000, 1)} sec)"
                f"</li>"
            )

    conn.close()

    return f"""
    <html>
    <head>
        <title>Store Intelligence Dashboard</title>
    </head>

    <body style="font-family: Arial; margin:40px;">

        <h1>Store Intelligence Dashboard</h1>

       <h2>Key Metrics</h2>

        <div style="
        display:flex;
        gap:20px;
        flex-wrap:wrap;
        margin-bottom:30px;
        ">

            <div style="
            border:1px solid #ddd;
            border-radius:10px;
            padding:20px;
            width:180px;
            text-align:center;
            box-shadow:0 2px 5px rgba(0,0,0,0.1);
            ">
                <h3>Visitors</h3>
                <h1>{visitors}</h1>
            </div>

            <div style="
            border:1px solid #ddd;
            border-radius:10px;
            padding:20px;
            width:180px;
            text-align:center;
            box-shadow:0 2px 5px rgba(0,0,0,0.1);
            ">
                <h3>Transactions</h3>
                <h1>{transactions}</h1>
            </div>

            <div style="
            border:1px solid #ddd;
            border-radius:10px;
            padding:20px;
            width:220px;
            text-align:center;
            box-shadow:0 2px 5px rgba(0,0,0,0.1);
            ">
                <h3>Revenue</h3>
                <h1>₹{revenue:.0f}</h1>
            </div>

            <div style="
            border:1px solid #ddd;
            border-radius:10px;
            padding:20px;
            width:220px;
            text-align:center;
            box-shadow:0 2px 5px rgba(0,0,0,0.1);
            ">
                <h3>Avg Basket</h3>
                <h1>₹{avg_basket:.0f}</h1>
            </div>

            <div style="
            border:1px solid #ddd;
            border-radius:10px;
            padding:20px;
            width:220px;
            text-align:center;
            box-shadow:0 2px 5px rgba(0,0,0,0.1);
            ">
                <h3>Conversion Rate</h3>
                <h1>{conversion_rate}%</h1>
            </div>

        </div>

        <h2>Conversion Funnel</h2>

        <div style="
        border:1px solid #ddd;
        border-radius:10px;
        padding:20px;
        width:600px;
        box-shadow:0 2px 5px rgba(0,0,0,0.1);
        margin-bottom:30px;
        margin-top:20px;
        ">

            <div style="font-size:22px;">
                🏪 Store Entries: <b>{store_entries}</b>
            </div>

            <div style="font-size:30px;text-align:center;">
                ↓
            </div>

            <div style="font-size:22px;">
                👥 Zone Visitors: <b>{zone_visitors}</b>
            </div>

            <div style="font-size:30px;text-align:center;">
                ↓
            </div>

            <div style="font-size:22px;">
                💳 Billing Visitors: <b>{billing_visitors}</b>
            </div>

            <div style="font-size:30px;text-align:center;">
                ↓
            </div>

            <div style="font-size:22px;">
                🛒 Purchases: <b>{purchases}</b>
            </div>

            <hr>

            <div style="
            font-size:24px;
            font-weight:bold;
            color:green;
            ">
                Conversion Rate: {conversion_rate}%
            </div>

        </div>

        <h2>Heatmap</h2>

        <table border="1" cellpadding="8">
        <tr>
            <th>Color</th>
            <th>Zone</th>
            <th>Visits</th>
        </tr>

        {heatmap_html}

        </table>

        <p>
        Circle size represents visit volume. Larger circles indicate higher customer engagement.
        </p>

        <div style="
        position:relative;
        display:inline-block;
        ">

        <img
        src="/static/store_layout.png"
        width="1200"
        >

        <!-- DISPLAY_ZONE -->
        <div style="
        position:absolute;
        left:250px;
        top:60px;
        width:80px;
        height:80px;
        background:red;
        border-radius:50%;
        opacity:0.5;
        ">
        </div>

        <!-- MAKEUP_ZONE -->
        <div style="
        position:absolute;
        left:650px;
        top:300px;
        width:60px;
        height:60px;
        background:orange;
        border-radius:50%;
        opacity:0.5;
        ">
        </div>

        <!-- FRAGRANCE_ZONE -->
        <div style="
        position:absolute;
        left:350px;
        top:330px;
        width:35px;
        height:35px;
        background:green;
        border-radius:50%;
        opacity:0.5;
        ">
        </div>

        <!-- BILLING_ZONE -->
        <div style="
        position:absolute;
        left:1050px;
        top:280px;
        width:45px;
        height:45px;
        background:blue;
        border-radius:50%;
        opacity:0.5;
        ">
        </div>

        </div>

        <h2>Anomalies</h2>

        <ul>
            {anomaly_html}
        </ul>

    </body>
    </html>
    """