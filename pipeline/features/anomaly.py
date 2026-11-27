"""
Modul Deteksi Anomali Unsupervised (Temporal Z-Score & Behavioral Isolation Forest).
Mengadopsi metode Rolling Z-Score dari ThisIsEconomy/ews/anomaly_detector.py
dan menambahkan Isolation Forest multivariat untuk skor anomali perilaku akun.
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


def detect_temporal_spikes(
    df_postings: pd.DataFrame,
    date_col: str = "created_at",
    window: int = 7,
    threshold: float = 2.0,
) -> pd.DataFrame:
    """
    Mendeteksi lonjakan (spike) volume posting harian menggunakan Rolling Mean & Z-Score.
    """
    if df_postings.empty or date_col not in df_postings.columns:
        return pd.DataFrame(
            columns=["date", "mentions", "rolling_mean", "rolling_std", "z_score", "is_anomaly"]
        )

    temp = df_postings[[date_col]].copy()
    temp["datetime"] = pd.to_datetime(temp[date_col], errors="coerce")
    temp = temp.dropna(subset=["datetime"])
    if temp.empty:
        return pd.DataFrame(
            columns=["date", "mentions", "rolling_mean", "rolling_std", "z_score", "is_anomaly"]
        )

    temp["date"] = temp["datetime"].dt.date
    daily = temp.groupby("date").size().reset_index(name="mentions").sort_values("date").reset_index(drop=True)

    daily["rolling_mean"] = daily["mentions"].rolling(window=window, min_periods=1).mean().round(2)
    daily["rolling_std"] = daily["mentions"].rolling(window=window, min_periods=1).std().fillna(0.0).round(2)

    mean_val = daily["mentions"].mean()
    std_val = daily["mentions"].std()
    if std_val and not np.isnan(std_val) and std_val > 0:
        daily["z_score"] = ((daily["mentions"] - mean_val) / std_val).round(4)
    else:
        daily["z_score"] = 0.0

    daily["is_anomaly"] = daily["z_score"] >= threshold
    return daily


def compute_behavioral_anomaly_scores(
    df_features: pd.DataFrame,
    contamination: float = 0.15,
    random_state: int = 42,
) -> pd.DataFrame:
    """
    Menghitung Behavioral Anomaly Score (0.0 - 1.0) per akun secara unsupervised
    menggunakan Isolation Forest pada fitur perilaku dan aktivitas.
    """
    res = df_features[["author_username"]].copy()
    if df_features.empty or len(df_features) < 5:
        res["anomaly_score"] = 0.0
        res["is_anomaly_outlier"] = False
        return res

    feature_cols = [
        "total_posts",
        "ff_ratio",
        "retweet_ratio",
        "active_hours_entropy",
        "burstiness",
        "unique_text_ratio",
    ]
    available_cols = [c for c in feature_cols if c in df_features.columns]
    if not available_cols:
        res["anomaly_score"] = 0.0
        res["is_anomaly_outlier"] = False
        return res

    X = df_features[available_cols].fillna(0.0).to_numpy(dtype=float)
    X_scaled = StandardScaler().fit_transform(X)

    iso = IsolationForest(
        contamination=min(max(contamination, 0.01), 0.49),
        random_state=random_state,
        n_estimators=100,
    )
    preds = iso.fit_predict(X_scaled)  # -1 = outlier, 1 = inlier
    raw_scores = -iso.decision_function(X_scaled)  # semakin besar semakin anomali

    min_s, max_s = float(np.min(raw_scores)), float(np.max(raw_scores))
    if max_s - min_s > 1e-9:
        norm_scores = (raw_scores - min_s) / (max_s - min_s)
    else:
        norm_scores = np.zeros_like(raw_scores)

    res["anomaly_score"] = np.round(np.clip(norm_scores, 0.0, 1.0), 4)
    res["is_anomaly_outlier"] = preds == -1
    return res
