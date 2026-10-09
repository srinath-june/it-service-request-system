def test_dashboard_metrics(client):
    # 1. Create a few requests
    client.post("/api/v1/requests", json={
        "subject": "Ticket 1", "description": "Desc 1", "category_id": 1, "priority": "CRITICAL", "requester_id": 3
    })
    t2 = client.post("/api/v1/requests", json={
        "subject": "Ticket 2", "description": "Desc 2", "category_id": 2, "priority": "MEDIUM", "requester_id": 3
    }).json()

    # Assign Ticket 2
    client.post(f"/api/v1/requests/{t2['id']}/assign", json={"assigned_to_id": 1, "actor_id": 2})

    # Resolve Ticket 2
    client.post(f"/api/v1/requests/{t2['id']}/resolve", json={
        "resolved_by_id": 1, "resolution_details": "Fixed completely."
    })

    # Query dashboard metrics
    res = client.get("/api/v1/reports/dashboard")
    assert res.status_code == 200
    data = res.json()

    assert data["total_requests"] == 2
    assert data["total_open_requests"] == 1
    assert data["total_resolved_requests"] == 1
    assert data["unassigned_requests"] == 1
    assert data["critical_open_requests"] == 1
    assert len(data["by_priority"]) >= 4
    assert len(data["by_category"]) >= 2
    assert len(data["by_status"]) >= 6
