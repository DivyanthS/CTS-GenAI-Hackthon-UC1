from __future__ import annotations

import pandas as pd
from pathlib import Path
from services.provider_export_service import ProviderExportService, INFERENCE_COLUMNS, TRAINING_COLUMNS


def test_export_deterministic_column_ordering():
    export_svc = ProviderExportService()

    inf_res = export_svc.export_for_inference()
    assert inf_res["column_list"] == INFERENCE_COLUMNS
    df_inf = pd.read_csv(inf_res["file"])
    assert list(df_inf.columns) == INFERENCE_COLUMNS

    train_res = export_svc.export_for_training()
    assert train_res["column_list"] == TRAINING_COLUMNS
    df_train = pd.read_csv(train_res["file"])
    assert list(df_train.columns) == TRAINING_COLUMNS


def test_export_with_custom_output_path(tmp_path):
    custom_file = tmp_path / "custom_inference.csv"
    export_svc = ProviderExportService()
    res = export_svc.export_for_inference(output_path=custom_file)

    assert Path(res["file"]).resolve() == custom_file.resolve()
    assert custom_file.is_file()
