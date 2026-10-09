def test_validation_missing_required_fields(client):
    # Missing subject
    res = client.post("/api/v1/requests", json={
        "subject": "",
        "description": "Valid description",
        "category_id": 1,
        "priority": "HIGH",
        "requester_id": 3
    })
    assert res.status_code == 422

    # Missing requester
    res2 = client.post("/api/v1/requests", json={
        "subject": "Valid Subject",
        "description": "Valid description",
        "category_id": 1,
        "priority": "HIGH"
    })
    assert res2.status_code == 422

def test_validation_invalid_assignee_role(client):
    # Create request
    create_res = client.post("/api/v1/requests", json={
        "subject": "Hardware replacement",
        "description": "Mouse optical sensor broken",
        "category_id": 1,
        "priority": "LOW",
        "requester_id": 3
    })
    req_id = create_res.json()["id"]

    # Attempt to assign to a standard EMPLOYEE (User ID 3)
    res_assign_emp = client.post(f"/api/v1/requests/{req_id}/assign", json={
        "assigned_to_id": 3,
        "actor_id": 2
    })
    assert res_assign_emp.status_code == 400
    assert "cannot be assigned" in res_assign_emp.json()["detail"]

    # Attempt to assign to inactive IT staff (User ID 4)
    res_assign_inactive = client.post(f"/api/v1/requests/{req_id}/assign", json={
        "assigned_to_id": 4,
        "actor_id": 2
    })
    assert res_assign_inactive.status_code == 404

def test_validation_invalid_status_transition(client):
    create_res = client.post("/api/v1/requests", json={
        "subject": "Email bounce",
        "description": "Emails to external domain bouncing",
        "category_id": 2,
        "priority": "MEDIUM",
        "requester_id": 3
    })
    req_id = create_res.json()["id"]

    # Attempt direct transition from NEW to CLOSED without resolution (Forbidden)
    res_close = client.post(f"/api/v1/requests/{req_id}/close", json={
        "actor_id": 2
    })
    assert res_close.status_code == 400
    assert "Cannot close an unresolved request" in res_close.json()["detail"]

def test_validation_resolve_without_details(client):
    create_res = client.post("/api/v1/requests", json={
        "subject": "Database timeout",
        "description": "Queries timing out on replica",
        "category_id": 2,
        "priority": "HIGH",
        "requester_id": 3
    })
    req_id = create_res.json()["id"]

    # Attempt resolving with empty resolution details
    res_resolve = client.post(f"/api/v1/requests/{req_id}/resolve", json={
        "resolved_by_id": 1,
        "resolution_details": ""
    })
    assert res_resolve.status_code == 422

def test_validation_modify_closed_request(client):
    create_res = client.post("/api/v1/requests", json={
        "subject": "Phone extension setup",
        "description": "Setup desk phone extension for new hire",
        "category_id": 1,
        "priority": "LOW",
        "requester_id": 3
    })
    req_id = create_res.json()["id"]

    # Resolve and Close
    client.post(f"/api/v1/requests/{req_id}/resolve", json={
        "resolved_by_id": 1,
        "resolution_details": "Extension 4091 provisioned on PBX server."
    })
    client.post(f"/api/v1/requests/{req_id}/close", json={"actor_id": 3})

    # Attempt to update priority of closed request
    res_update = client.put(f"/api/v1/requests/{req_id}", json={
        "priority": "CRITICAL"
    })
    assert res_update.status_code == 400
    assert "closed request cannot be modified" in res_update.json()["detail"]

    # Attempt to add comment to closed request
    res_comment = client.post(f"/api/v1/requests/{req_id}/comments", json={
        "author_id": 3,
        "comment": "Late note"
    })
    assert res_comment.status_code == 400
