def test_create_request_success(client):
    payload = {
        "subject": "Broken laptop keyboard",
        "description": "Spacebar key is stuck and not registering keystrokes.",
        "category_id": 1,
        "priority": "HIGH",
        "requester_id": 3
    }
    response = client.post("/api/v1/requests", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["subject"] == payload["subject"]
    assert data["priority"] == "HIGH"
    assert data["status"] == "NEW"
    assert data["request_number"].startswith("SR-")
    assert data["sla_target_hours"] == 8.0
    assert data["sla_status"] == "WITHIN_SLA"
    assert data["is_sla_breached"] is False

def test_list_requests_and_filters(client):
    # Create multiple requests
    client.post("/api/v1/requests", json={
        "subject": "Printer paper jam",
        "description": "3rd floor laser printer is jammed with heavy cardstock.",
        "category_id": 1,
        "priority": "LOW",
        "requester_id": 3
    })
    client.post("/api/v1/requests", json={
        "subject": "VPN connection dropping",
        "description": "VPN disconnects every 5 minutes during remote work.",
        "category_id": 2,
        "priority": "CRITICAL",
        "requester_id": 3
    })

    # List all
    res = client.get("/api/v1/requests")
    assert res.status_code == 200
    assert len(res.json()) == 2

    # Filter by priority
    res_crit = client.get("/api/v1/requests?priority=CRITICAL")
    assert res_crit.status_code == 200
    assert len(res_crit.json()) == 1
    assert res_crit.json()[0]["priority"] == "CRITICAL"

    # Search query
    res_search = client.get("/api/v1/requests?search=Printer")
    assert res_search.status_code == 200
    assert len(res_search.json()) == 1
    assert "Printer" in res_search.json()[0]["subject"]

def test_get_request_details(client):
    res_create = client.post("/api/v1/requests", json={
        "subject": "Monitor flicker",
        "description": "External monitor flickers every 10 seconds.",
        "category_id": 1,
        "priority": "MEDIUM",
        "requester_id": 3
    })
    req_id = res_create.json()["id"]

    res_detail = client.get(f"/api/v1/requests/{req_id}")
    assert res_detail.status_code == 200
    data = res_detail.json()
    assert data["id"] == req_id
    assert "history" in data
    assert len(data["history"]) >= 1
    assert data["history"][0]["action_type"] == "CREATED"
