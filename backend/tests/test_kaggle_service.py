from __future__ import annotations

from services.kaggle.kaggle_service import KaggleService


def test_kaggle_service_metadata():
    svc = KaggleService(username="", key="")
    meta = svc.get_environment_metadata()

    assert meta["configured"] is False
    assert meta["mode"] == "local_execution"
    assert "dataset_slug" in meta
    assert "kernel_slug" in meta


def test_kaggle_service_local_mode_execution():
    svc = KaggleService(username="", key="")
    res = svc.trigger_kernel()

    assert res["status"] == "local_mock_success"
    assert "local pipeline" in res["message"]
