"""
PROMPT BLOCK

Goal:
Verify that the Store Intelligence Platform APIs are reachable
and return successful responses.

Tested Endpoints:
- /health
- /stores/STORE_001/metrics
- /stores/STORE_001/heatmap
- /stores/STORE_001/funnel
- /stores/STORE_001/anomalies

Expected Result:
HTTP 200 response for all endpoints.
"""

import requests

BASE_URL = "http://localhost:8000"


def test_health():
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200


def test_metrics():
    response = requests.get(
        f"{BASE_URL}/stores/STORE_001/metrics"
    )
    assert response.status_code == 200


def test_heatmap():
    response = requests.get(
        f"{BASE_URL}/stores/STORE_001/heatmap"
    )
    assert response.status_code == 200


def test_funnel():
    response = requests.get(
        f"{BASE_URL}/stores/STORE_001/funnel"
    )
    assert response.status_code == 200


def test_anomalies():
    response = requests.get(
        f"{BASE_URL}/stores/STORE_001/anomalies"
    )
    assert response.status_code == 200