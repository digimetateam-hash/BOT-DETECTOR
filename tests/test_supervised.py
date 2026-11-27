"""
Unit tests untuk Fase Supervised (Quality Gate, GroupShuffleSplit,
LightGBM + Top-5 SHAP, Baseline TF-IDF + LogReg/SVM, dan McNemar Test).
"""
import numpy as np
import pandas as pd
import pytest

from pipeline.models.supervised import (
    compare_models_mcnemar,
    group_aware_split,
    train_lightgbm_with_shap,
    train_tfidf_baselines,
    validate_labeling_gate,
)


def test_labeling_quality_gate():
    # Lolos: 300 akun, kappa >= 0.70
    labels_a = ["bot"] * 150 + ["manusia"] * 150
    labels_b = ["bot"] * 145 + ["manusia"] * 5 + ["manusia"] * 150
    res = validate_labeling_gate(labels_a, labels_b, min_accounts=300, min_kappa=0.70)
    assert res["passed"] is True
    assert res["kappa"] >= 0.70
    assert res["consensus_count"] == 295

    # Gagal jika jumlah < 300
    with pytest.raises(ValueError, match="Gerbang kualitas label belum terpenuhi"):
        validate_labeling_gate(["bot"] * 20, ["bot"] * 20, min_accounts=300, min_kappa=0.70)

    # Gagal jika kappa < 0.70
    bad_a = ["bot"] * 150 + ["manusia"] * 150
    bad_b = ["manusia"] * 150 + ["bot"] * 150
    with pytest.raises(ValueError, match="Gerbang kualitas label belum terpenuhi"):
        validate_labeling_gate(bad_a, bad_b, min_accounts=300, min_kappa=0.70)


def test_group_aware_split_no_leakage():
    df = pd.DataFrame({
        "handle_hash": [f"h_{i // 3}" for i in range(60)],
        "clean_text": [f"teks kelompok {i // 4}" for i in range(60)],
        "label": [i % 2 for i in range(60)],
    })
    tr, te = group_aware_split(df, group_col="handle_hash", test_size=0.25, random_state=42)
    assert set(tr["handle_hash"]).isdisjoint(set(te["handle_hash"]))

    tr_t, te_t = group_aware_split(df, group_col="clean_text", test_size=0.25, random_state=42)
    assert set(tr_t["clean_text"]).isdisjoint(set(te_t["clean_text"]))


def test_lightgbm_with_top5_shap():
    rng = np.random.default_rng(42)
    n = 120
    labels = np.array([1] * 60 + [0] * 60)
    df = pd.DataFrame({
        "handle_hash": [f"hash_{i}" for i in range(n)],
        "ff_ratio": np.where(labels == 1, rng.uniform(5.0, 15.0, n), rng.uniform(0.3, 1.5, n)),
        "retweet_ratio": np.where(labels == 1, rng.uniform(0.7, 0.98, n), rng.uniform(0.05, 0.4, n)),
        "active_hours_entropy": np.where(labels == 1, rng.uniform(0.1, 0.4, n), rng.uniform(0.6, 0.95, n)),
        "burstiness": rng.uniform(-0.8, 0.8, n),
        "unique_text_ratio": np.where(labels == 1, rng.uniform(0.1, 0.4, n), rng.uniform(0.7, 1.0, n)),
        "account_age_days": np.where(labels == 1, rng.integers(5, 60, n), rng.integers(300, 2000, n)),
        "label": labels,
    })

    out = train_lightgbm_with_shap(df, target_col="label", group_col="handle_hash", random_state=42)
    assert out["metrics"]["macro_f1"] >= 0.85
    assert len(out["top_shap"]) == out["test_n"]
    assert len(out["top_shap"][0]) == 5
    assert "shap_value" in out["top_shap"][0][0]


def test_tfidf_baselines_and_mcnemar():
    rows = []
    for i in range(80):
        if i % 2 == 0:
            rows.append({
                "clean_text": f"dukung program makan bergizi gratis mbg sukses {i // 2}",
                "label": 1,
            })
        else:
            rows.append({
                "clean_text": f"diskusi warga soal anggaran dan menu sekolah hari ini {i // 2}",
                "label": 0,
            })
    df_texts = pd.DataFrame(rows)
    res_df = train_tfidf_baselines(df_texts, group_col="clean_text", random_state=42)
    assert len(res_df) == 2
    assert set(res_df["Model"]) == {"TF-IDF + Logistic Regression", "TF-IDF + Linear SVM"}

    sig = compare_models_mcnemar(
        np.array([1, 0, 1, 1, 0, 0]),
        np.array([1, 0, 1, 1, 0, 0]),
        np.array([1, 1, 0, 1, 0, 0]),
    )
    assert "p_value" in sig
    assert 0.0 <= sig["p_value"] <= 1.0
