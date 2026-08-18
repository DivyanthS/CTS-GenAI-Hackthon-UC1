from __future__ import annotations

from services.risk.threshold_engine import ThresholdEngine


def test_threshold_engine_classification():
    engine = ThresholdEngine(low_threshold=0.23, high_threshold=0.60, critical_threshold=0.80)

    assert engine.classify(0.10) == ("Low", "NORMAL", 4)
    assert engine.classify(0.23) == ("Medium", "MONITOR", 3)
    assert engine.classify(0.55) == ("Medium", "MONITOR", 3)
    assert engine.classify(0.60) == ("High", "REVIEW", 2)
    assert engine.classify(0.79) == ("High", "REVIEW", 2)
    assert engine.classify(0.80) == ("Critical", "URGENT_REVIEW", 1)
    assert engine.classify(0.95) == ("Critical", "URGENT_REVIEW", 1)


def test_threshold_engine_update():
    engine = ThresholdEngine(low_threshold=0.20, high_threshold=0.50, critical_threshold=0.75)
    config = engine.update_thresholds(low_threshold=0.30, high_threshold=0.65, critical_threshold=0.85)

    assert config["low_threshold"] == 0.30
    assert config["high_threshold"] == 0.65
    assert config["critical_threshold"] == 0.85


def test_threshold_endpoints(client):
    get_resp = client.get("/api/v1/model/threshold")
    assert get_resp.status_code == 200
    assert "low_threshold" in get_resp.get_json()

    put_resp = client.put(
        "/api/v1/model/threshold",
        json={"low_threshold": 0.25, "high_threshold": 0.65, "critical_threshold": 0.85},
    )
    assert put_resp.status_code == 200
    assert put_resp.get_json()["low_threshold"] == 0.25
