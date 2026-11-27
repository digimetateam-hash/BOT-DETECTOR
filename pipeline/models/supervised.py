"""
Pipeline Supervised Machine Learning (PRD Bagian 7, 13b, 16b, 16c).
- Quality Gate pelabelan manual: minimal 300 akun & Cohen's Kappa >= 0.70.
- Protokol GroupShuffleSplit berbasis handle_hash dan clean_text (anti-leakage).
- Model Utama: LightGBM + Top-5 SHAP (TreeExplainer).
- Pembanding Baseline: TF-IDF + LogisticRegression & LinearSVC (diadopsi dari ThisIsEconomy).
"""
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import shap
from lightgbm import LGBMClassifier
from scipy.stats import binomtest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GroupShuffleSplit
from sklearn.svm import LinearSVC

from pipeline.models.detector import calculate_intercoder_agreement


def validate_labeling_gate(
    labels_coder_a: List[str],
    labels_coder_b: List[str],
    min_accounts: int = 300,
    min_kappa: float = 0.70,
    enforce_gate: bool = True,
) -> Dict[str, Any]:
    """
    Memvalidasi gerbang kualitas label manual (PRD 16b & 13b):
    - Minimal `min_accounts` akun berlabel.
    - Cohen's Kappa antar dua coder >= `min_kappa`.
    - Akun berlabel 'ragu' atau tidak sepakat dikeluarkan dari data latih.
    """
    agreement = calculate_intercoder_agreement(labels_coder_a, labels_coder_b)
    n_total = len(labels_coder_a)
    kappa = agreement["kappa"]

    consensus_mask = [
        (a == b) and (a in {"bot", "manusia"})
        for a, b in zip(labels_coder_a, labels_coder_b)
    ]
    n_consensus = sum(consensus_mask)

    passed = (n_total >= min_accounts) and (kappa >= min_kappa) and (n_consensus >= 10)
    if enforce_gate and not passed:
        raise ValueError(
            f"Gerbang kualitas label belum terpenuhi: N={n_total} (min {min_accounts}), "
            f"kappa={kappa:.3f} (min {min_kappa}), konsensus={n_consensus}."
        )

    return {
        "passed": passed,
        "total_labeled": n_total,
        "consensus_count": n_consensus,
        "kappa": kappa,
        "consensus_mask": consensus_mask,
    }


def group_aware_split(
    df: pd.DataFrame,
    group_col: str = "handle_hash",
    test_size: float = 0.2,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Membagi data latih dan uji menggunakan GroupShuffleSplit agar tidak ada
    akun (handle_hash) atau teks (clean_text) yang bocor antar split.
    """
    if group_col not in df.columns:
        raise ValueError(f"Kolom grup '{group_col}' tidak ditemukan pada DataFrame.")

    gss = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=random_state)
    train_idx, test_idx = next(gss.split(df, groups=df[group_col]))
    return df.iloc[train_idx].reset_index(drop=True), df.iloc[test_idx].reset_index(drop=True)


def _compute_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_prob: Optional[np.ndarray] = None,
) -> Dict[str, Any]:
    """Menghitung metrik klasifikasi standar PRD 16c."""
    metrics: Dict[str, Any] = {
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "macro_precision": round(float(precision_score(y_true, y_pred, average="macro", zero_division=0)), 4),
        "macro_recall": round(float(recall_score(y_true, y_pred, average="macro", zero_division=0)), 4),
        "macro_f1": round(float(f1_score(y_true, y_pred, average="macro", zero_division=0)), 4),
        "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
    }
    if y_prob is not None and len(np.unique(y_true)) > 1:
        metrics["pr_auc"] = round(float(average_precision_score(y_true, y_prob)), 4)
        metrics["roc_auc"] = round(float(roc_auc_score(y_true, y_prob)), 4)
    else:
        metrics["pr_auc"] = None
        metrics["roc_auc"] = None
    return metrics


def train_lightgbm_with_shap(
    df_features: pd.DataFrame,
    feature_cols: Optional[List[str]] = None,
    target_col: str = "label",
    group_col: str = "handle_hash",
    test_size: float = 0.2,
    random_state: int = 42,
    top_k_shap: int = 5,
) -> Dict[str, Any]:
    """
    Melatih LightGBM Classifier dengan protokol GroupShuffleSplit (berbasis handle_hash)
    dan menghitung Top-5 SHAP feature attribution per akun uji (PRD R-D9).
    """
    if feature_cols is None:
        excluded = {target_col, group_col, "author_username", "clean_text", "text"}
        feature_cols = [
            c for c in df_features.columns
            if c not in excluded and pd.api.types.is_numeric_dtype(df_features[c])
        ]

    train_df, test_df = group_aware_split(
        df_features, group_col=group_col, test_size=test_size, random_state=random_state
    )

    X_train = train_df[feature_cols].fillna(0.0)
    y_train = train_df[target_col].astype(int).to_numpy()
    X_test = test_df[feature_cols].fillna(0.0)
    y_test = test_df[target_col].astype(int).to_numpy()

    model = LGBMClassifier(
        n_estimators=100,
        learning_rate=0.05,
        class_weight="balanced",
        random_state=random_state,
        verbose=-1,
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]
    metrics = _compute_metrics(y_test, y_pred, y_prob)

    # Hitung SHAP values (TreeExplainer)
    explainer = shap.TreeExplainer(model)
    shap_vals = explainer.shap_values(X_test)
    if isinstance(shap_vals, list):
        shap_matrix = np.asarray(shap_vals[1])
    elif getattr(shap_vals, "ndim", 2) == 3:
        shap_matrix = shap_vals[:, :, 1]
    else:
        shap_matrix = np.asarray(shap_vals)

    top_shap_per_account = []
    for idx in range(len(X_test)):
        row_shap = shap_matrix[idx]
        ranked_indices = np.argsort(np.abs(row_shap))[::-1][:top_k_shap]
        top_feats = [
            {
                "fitur": feature_cols[f_idx],
                "shap_value": round(float(row_shap[f_idx]), 4),
                "nilai_fitur": round(float(X_test.iloc[idx, f_idx]), 4),
            }
            for f_idx in ranked_indices
        ]
        top_shap_per_account.append(top_feats)

    return {
        "model": model,
        "feature_cols": feature_cols,
        "train_n": len(train_df),
        "test_n": len(test_df),
        "metrics": metrics,
        "y_test": y_test,
        "y_pred": y_pred,
        "y_prob": y_prob,
        "top_shap": top_shap_per_account,
    }


def train_tfidf_baselines(
    df_texts: pd.DataFrame,
    text_col: str = "clean_text",
    target_col: str = "label",
    group_col: str = "clean_text",
    test_size: float = 0.2,
    random_state: int = 42,
) -> pd.DataFrame:
    """
    Melatih model baseline TF-IDF + LogisticRegression dan TF-IDF + LinearSVC
    menggunakan protokol GroupShuffleSplit berbasis clean_text (diadopsi dari ThisIsEconomy).
    """
    train_df, test_df = group_aware_split(
        df_texts, group_col=group_col, test_size=test_size, random_state=random_state
    )

    vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
    X_train = vectorizer.fit_transform(train_df[text_col].fillna("").astype(str))
    X_test = vectorizer.transform(test_df[text_col].fillna("").astype(str))
    y_train = train_df[target_col].astype(int).to_numpy()
    y_test = test_df[target_col].astype(int).to_numpy()

    rows = []

    # 1. Logistic Regression
    lr = LogisticRegression(max_iter=1000, random_state=random_state, class_weight="balanced")
    lr.fit(X_train, y_train)
    lr_pred = lr.predict(X_test)
    lr_prob = lr.predict_proba(X_test)[:, 1]
    lr_m = _compute_metrics(y_test, lr_pred, lr_prob)
    rows.append({
        "Model": "TF-IDF + Logistic Regression",
        "Protocol": f"GROUP-AWARE ({group_col})",
        "Train_N": len(train_df),
        "Test_N": len(test_df),
        **lr_m,
    })

    # 2. Linear SVM
    svm = LinearSVC(max_iter=2000, random_state=random_state, class_weight="balanced")
    svm.fit(X_train, y_train)
    svm_pred = svm.predict(X_test)
    svm_scores = svm.decision_function(X_test)
    svm_m = _compute_metrics(y_test, svm_pred, svm_scores)
    rows.append({
        "Model": "TF-IDF + Linear SVM",
        "Protocol": f"GROUP-AWARE ({group_col})",
        "Train_N": len(train_df),
        "Test_N": len(test_df),
        **svm_m,
    })

    return pd.DataFrame(rows)


def compare_models_mcnemar(
    y_true: np.ndarray, preds_a: np.ndarray, preds_b: np.ndarray
) -> Dict[str, Any]:
    """
    Menguji signifikansi statistik perbedaan dua model dengan McNemar's exact binomial test.
    """
    correct_a = (preds_a == y_true)
    correct_b = (preds_b == y_true)
    n01 = int(np.sum(~correct_a & correct_b))
    n10 = int(np.sum(correct_a & ~correct_b))
    total_discordant = n01 + n10
    if total_discordant == 0:
        p_val = 1.0
    else:
        p_val = float(binomtest(min(n01, n10), n=total_discordant, p=0.5).pvalue)

    return {
        "n01_b_only_correct": n01,
        "n10_a_only_correct": n10,
        "p_value": round(p_val, 6),
        "significant_at_0_05": p_val < 0.05,
    }
