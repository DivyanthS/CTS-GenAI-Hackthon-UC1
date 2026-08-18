from __future__ import annotations


def test_get_claims_paginated(client):
    response = client.get("/api/v1/claims?page=1&page_size=5")
    assert response.status_code == 200
    res = response.get_json()
    assert res["page"] == 1
    assert res["page_size"] == 5
    assert res["total"] >= 10
    assert len(res["claims"]) == 5

    c = res["claims"][0]
    assert "claim_id" in c
    assert "provider_id" in c
    # Legacy fields
    assert "ClaimID" in c
    assert "Provider" in c


def test_get_claims_filter_provider(client):
    response = client.get("/api/v1/claims?provider_id=PRV0001")
    assert response.status_code == 200
    res = response.get_json()
    assert res["total"] >= 3
    assert len(res["claims"]) > 0
    for c in res["claims"]:
        assert c["provider_id"] == "PRV0001"


def test_get_claim_detail(client):
    response = client.get("/api/v1/claims/CLM0001")
    assert response.status_code == 200
    res = response.get_json()
    assert "claim" in res
    assert res["claim"]["claim_id"] == "CLM0001"


def test_get_claim_explanation(client):
    response = client.get("/api/v1/claims/CLM0001/explanation")
    assert response.status_code == 200
    res = response.get_json()
    assert res["claim_id"] == "CLM0001"
    assert "risk" in res
    assert "factors" in res
    assert "summary" in res
    assert "disclaimer" in res
