from datetime import datetime, timedelta
from app.models.request import ServiceRequest

def test_sla_hours_assignment_by_priority(client):
    # Critical -> 4 hours
    res_crit = client.post("/api/v1/requests", json={
        "subject": "Core Switch Down",
        "description": "Building B network unreachable",
        "category_id": 1,
        "priority": "CRITICAL",
        "requester_id": 3
    })
    assert res_crit.json()["sla_target_hours"] == 4.0

    # High -> 8 hours
    res_high = client.post("/api/v1/requests", json={
        "subject": "Billing software error",
        "description": "Invoices failing to export",
        "category_id": 2,
        "priority": "HIGH",
        "requester_id": 3
    })
    assert res_high.json()["sla_target_hours"] == 8.0

    # Medium -> 24 hours
    res_med = client.post("/api/v1/requests", json={
        "subject": "Shared mailbox access",
        "description": "Add user to sales@company.com",
        "category_id": 2,
        "priority": "MEDIUM",
        "requester_id": 3
    })
    assert res_med.json()["sla_target_hours"] == 24.0

    # Low -> 48 hours
    res_low = client.post("/api/v1/requests", json={
        "subject": "Cable organizer request",
        "description": "Velcro straps for desk cables",
        "category_id": 1,
        "priority": "LOW",
        "requester_id": 3
    })
    assert res_low.json()["sla_target_hours"] == 48.0

def test_sla_configuration_update_dynamically(client):
    # Update Critical SLA to 2 hours
    res_update_sla = client.put("/api/v1/sla/CRITICAL", json={
        "resolution_sla_hours": 2.0
    })
    assert res_update_sla.status_code == 200
    assert res_update_sla.json()["resolution_sla_hours"] == 2.0

    # New Critical ticket should now use 2.0 hours target
    res_new_ticket = client.post("/api/v1/requests", json={
        "subject": "Production DB Crash",
        "description": "Cluster primary failed",
        "category_id": 2,
        "priority": "CRITICAL",
        "requester_id": 3
    })
    assert res_new_ticket.json()["sla_target_hours"] == 2.0
