def test_complete_ticket_lifecycle(client):
    # 1. Create ticket (NEW)
    create_res = client.post("/api/v1/requests", json={
        "subject": "Outlook crashing upon opening attachment",
        "description": "Outlook client terminates when double-clicking PDF files.",
        "category_id": 2,
        "priority": "HIGH",
        "requester_id": 3
    })
    req_id = create_res.json()["id"]
    assert create_res.json()["status"] == "NEW"

    # 2. Assign to IT Tech (Transitions to ASSIGNED)
    assign_res = client.post(f"/api/v1/requests/{req_id}/assign", json={
        "assigned_to_id": 1,
        "actor_id": 2,
        "remarks": "Assigned to software specialist"
    })
    assert assign_res.status_code == 200
    assert assign_res.json()["status"] == "ASSIGNED"
    assert assign_res.json()["assigned_to"]["id"] == 1

    # 3. Advance status to IN_PROGRESS
    prog_res = client.post(f"/api/v1/requests/{req_id}/status", json={
        "new_status": "IN_PROGRESS",
        "actor_id": 1,
        "remarks": "Investigating add-in conflicts"
    })
    assert prog_res.status_code == 200
    assert prog_res.json()["status"] == "IN_PROGRESS"

    # 4. Place ON_HOLD (waiting on user response)
    hold_res = client.post(f"/api/v1/requests/{req_id}/status", json={
        "new_status": "ON_HOLD",
        "actor_id": 1,
        "remarks": "Awaiting user laptop availability for remote session"
    })
    assert hold_res.status_code == 200
    assert hold_res.json()["status"] == "ON_HOLD"

    # 5. Resume to IN_PROGRESS
    resume_res = client.post(f"/api/v1/requests/{req_id}/status", json={
        "new_status": "IN_PROGRESS",
        "actor_id": 1,
        "remarks": "Remote session started"
    })
    assert resume_res.status_code == 200
    assert resume_res.json()["status"] == "IN_PROGRESS"

    # 6. Add comment / work note
    comment_res = client.post(f"/api/v1/requests/{req_id}/comments", json={
        "author_id": 1,
        "comment": "Disabled obsolete Acrobat plugin. Tested opening PDFs cleanly.",
        "is_internal": False
    })
    assert comment_res.status_code == 201

    # 7. Resolve Request (RESOLVED)
    resolve_res = client.post(f"/api/v1/requests/{req_id}/resolve", json={
        "resolved_by_id": 1,
        "resolution_details": "Disabled incompatible Adobe COM add-in in Outlook Options and cleared temp cache."
    })
    assert resolve_res.status_code == 200
    assert resolve_res.json()["status"] == "RESOLVED"
    assert resolve_res.json()["resolution_details"] is not None

    # 8. Close Request (CLOSED)
    close_res = client.post(f"/api/v1/requests/{req_id}/close", json={
        "actor_id": 3,
        "remarks": "Verified working fine by requester."
    })
    assert close_res.status_code == 200
    assert close_res.json()["status"] == "CLOSED"
    assert close_res.json()["closed_at"] is not None

    # 9. Reopen Request (Documented assumption: Reopened ticket transitions back to IN_PROGRESS)
    reopen_res = client.post(f"/api/v1/requests/{req_id}/reopen", json={
        "actor_id": 3,
        "reason": "Issue reappeared after reboot."
    })
    assert reopen_res.status_code == 200
    assert reopen_res.json()["status"] == "IN_PROGRESS"
    assert reopen_res.json()["reopened_at"] is not None
