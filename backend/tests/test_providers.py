from __future__ import annotations


def test_get_providers_paginated(client):
    response = client.get("/api/v1/providers?page=1&page_size=3")
    assert response.status_code == 200
    res = response.get_json()
    assert res["page"] == 1
    assert res["page_size"] == 3
    assert res["total"] >= 5
    assert len(res["providers"]) == 3

    p = res["providers"][0]
    assert "provider_id" in p
    assert "risk_score" in p
    assert "risk_level" in p
    # Verify legacy fields for frontend compatibility
    assert "Provider" in p
    assert "TotalClaims" in p


def test_get_providers_filter_risk(client):
    response = client.get("/api/v1/providers?risk_level=High")
    assert response.status_code == 200
    res = response.get_json()
    assert isinstance(res["providers"], list)


def test_get_provider_detail_success(client):
    response = client.get("/api/v1/providers/PRV0001")
    assert response.status_code == 200
    res = response.get_json()
    assert "provider" in res
    assert res["provider"]["provider_id"] == "PRV0001"
    assert "claims_summary" in res
    assert "charts" in res
    assert "risk_factors" in res


def test_get_provider_detail_not_found(client):
    response = client.get("/api/v1/providers/PRV_NONEXISTENT_9999")
    assert response.status_code == 404
    res = response.get_json()
    assert res["error"] == "PROVIDER_NOT_FOUND"
