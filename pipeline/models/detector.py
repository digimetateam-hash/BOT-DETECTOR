"""
Mesin Skoring Deteksi Bot & Explainability SHAP (PRD Bagian 7 & 13a)
"""
import json
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score


def calculate_bot_score_and_explain(
    df_features: pd.DataFrame,
    thresholds: Optional[Dict[str, Any]] = None,
) -> pd.DataFrame:
    """
    Menghitung skor bot (0.0 - 1.0) dan mengekstrak Top-5 fitur pemicu (SHAP / feature contribution).
    Aturan Kategori (PRD 13a R-D1 & R-D2):
      - Skor < 0.40        : organik
      - Skor 0.40 - 0.69   : mencurigakan
      - Skor >= 0.70       : mirip_bot
      - Total posting < 5  : Tidak diberi kategori (hanya skor)
    """
    if thresholds is None:
        thresholds = {
            "organik_max": 0.40,
            "mencurigakan_min": 0.40,
            "mencurigakan_max": 0.69,
            "mirip_bot_min": 0.70,
            "min_posts": 5,
        }

    results = []
    for _, row in df_features.iterrows():
        # Komponen sinyal dan bobot kontribusi
        # 1. Rasio Following / Follower tinggi (akun buzzer sering follow banyak tapi sedikit follower)
        ff_sig = min(max((row.get("ff_ratio", 1.0) - 1.5) / 10.0, 0.0), 1.0)

        # 2. Umur akun baru (< 90 hari)
        age_days = row.get("account_age_days", 365)
        age_sig = max((90.0 - age_days) / 90.0, 0.0) if age_days < 90 else 0.0

        # 3. Avatar default & bio kosong
        profile_sig = (row.get("is_default_avatar", 0) * 0.6) + (row.get("is_empty_bio", 0) * 0.4)

        # 4. Proporsi retweet tinggi (> 70%)
        rt_ratio = row.get("retweet_ratio", 0.0)
        rt_sig = min(max((rt_ratio - 0.5) / 0.5, 0.0), 1.0) if rt_ratio > 0.5 else 0.0

        # 5. Entropi jam aktif rendah (hanya aktif di jam tertentu atau terlalu teratur)
        entropy = row.get("active_hours_entropy", 0.8)
        entropy_sig = max(1.0 - entropy, 0.0)

        # 6. Duplikasi teks internal
        unique_text = row.get("unique_text_ratio", 1.0)
        copy_sig = max(1.0 - unique_text, 0.0)

        # Agregasi skor bobot
        # Fitur Profil: 35%, Fitur Aktivitas: 40%, Fitur Konten: 25%
        raw_score = (
            (ff_sig * 0.15 + age_sig * 0.10 + profile_sig * 0.10) +
            (rt_sig * 0.25 + entropy_sig * 0.15) +
            (copy_sig * 0.25)
        )
        skor = float(np.clip(raw_score, 0.0, 1.0))

        # Kontribusi tiap fitur untuk penjelasan (Explainability - PRD 13a R-D9 Top-5)
        contributions = [
            {"fitur": "Rasio Following/Follower Tinggi", "nilai": round(ff_sig * 0.15, 3), "keterangan": f"Rasio: {row.get('ff_ratio', 1.0):.1f}"},
            {"fitur": "Proporsi Retweet Ekstrem", "nilai": round(rt_sig * 0.25, 3), "keterangan": f"Retweet: {rt_ratio*100:.0f}%"},
            {"fitur": "Akun Berusia Baru", "nilai": round(age_sig * 0.10, 3), "keterangan": f"Umur: {age_days} hari"},
            {"fitur": "Profil Default / Bio Kosong", "nilai": round(profile_sig * 0.10, 3), "keterangan": "Avatar bawaan atau bio kosong"},
            {"fitur": "Jadwal Jam Aktif Tidak Wajar", "nilai": round(entropy_sig * 0.15, 3), "keterangan": f"Entropi: {entropy:.2f}"},
            {"fitur": "Pengulangan Teks Identik", "nilai": round(copy_sig * 0.25, 3), "keterangan": f"Keunikan teks: {unique_text*100:.0f}%"},
        ]
        # Urutkan berdasarkan kontribusi terbesar
        top_5_shap = sorted(contributions, key=lambda x: x["nilai"], reverse=True)[:5]

        # Penentuan Kategori berdasarkan ambang batas
        total_posts = row.get("total_posts", 1)
        if total_posts < thresholds.get("min_posts", 5):
            kategori = "kurang_data"  # R-D2: <5 posting tidak diberi kategori
        elif skor >= thresholds.get("mirip_bot_min", 0.70):
            kategori = "mirip_bot"
        elif skor >= thresholds.get("mencurigakan_min", 0.40):
            kategori = "mencurigakan"
        else:
            kategori = "organik"

        results.append({
            "author_username": row["author_username"],
            "total_posts": total_posts,
            "skor": round(skor, 4),
            "kategori": kategori,
            "top_features": json.dumps(top_5_shap),
        })

    return pd.DataFrame(results)


def calculate_intercoder_agreement(labels_a: List[str], labels_b: List[str]) -> Dict[str, Any]:
    """
    Menghitung kesepakatan antar coder (Cohen's Kappa & Agreement rate).
    Target PRD: Cohen's kappa >= 0.70
    """
    if len(labels_a) != len(labels_b) or len(labels_a) == 0:
        return {"kappa": 0.0, "agreement_rate": 0.0, "status": "Data label tidak valid"}

    kappa = cohen_kappa_score(labels_a, labels_b)
    matches = sum(1 for a, b in zip(labels_a, labels_b) if a == b)
    agreement_rate = matches / len(labels_a)

    return {
        "kappa": round(float(kappa), 3) if not np.isnan(kappa) else 1.0,
        "agreement_rate": round(agreement_rate, 3),
        "total_sampel": len(labels_a),
        "status": "Baik (Memenuhi Target ≥0.70)" if kappa >= 0.70 else "Perlu Adjudikasi (<0.70)",
    }
