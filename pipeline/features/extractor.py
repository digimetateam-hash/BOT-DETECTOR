"""
Ekstraksi Fitur Profil, Aktivitas Waktu, dan Kemiripan Konten (PRD Bagian 7 & 13a)
"""
import re
from collections import Counter
from datetime import datetime
from typing import Any, Dict, List
import numpy as np
import pandas as pd
from datasketch import MinHash, MinHashLSH


def clean_text_for_nlp(text: str) -> str:
    """Membersihkan teks Indonesia (URL, mentions, karakter non-alfanumerik)."""
    if not text or pd.isna(text):
        return ""
    # Hapus URL
    text = re.sub(r"https?://\S+|www\.\S+", "", text)
    # Hapus mention (@username)
    text = re.sub(r"@\w+", "", text)
    # Hapus whitespace berlebih
    text = re.sub(r"\s+", " ", text).strip().lower()
    return text


def calculate_entropy(hour_series: pd.Series) -> float:
    """Menghitung entropi distribusi jam posting (0-24 jam)."""
    if len(hour_series) == 0:
        return 0.0
    counts = hour_series.value_counts()
    probs = counts / counts.sum()
    entropy = -np.sum(probs * np.log2(probs + 1e-12))
    # Entropi maksimum untuk 24 jam adalah log2(24) ~ 4.58
    max_entropy = np.log2(24)
    normalized_entropy = float(entropy / max_entropy)
    return min(max(normalized_entropy, 0.0), 1.0)


def calculate_burstiness(post_times: List[datetime]) -> float:
    """
    Menghitung ukuran burstiness interval antar posting (B = (sigma - mu) / (sigma + mu)).
    Nilai berkisar antara -1 (sangat teratur / bot cron) hingga +1 (sangat meletup-letup).
    """
    if len(post_times) < 3:
        return 0.0
    sorted_times = sorted(post_times)
    deltas = [(sorted_times[i+1] - sorted_times[i]).total_seconds() for i in range(len(sorted_times)-1)]
    deltas = [d for d in deltas if d > 0]
    if len(deltas) < 2:
        return 0.0

    mean_delta = np.mean(deltas)
    std_delta = np.std(deltas)
    if (std_delta + mean_delta) == 0:
        return 0.0
    b = (std_delta - mean_delta) / (std_delta + mean_delta)
    return float(b)


def extract_account_features(df_postings: pd.DataFrame) -> pd.DataFrame:
    """
    Mengekstraksi fitur profil, aktivitas, dan konten per akun.
    """
    account_features = []

    for author, group in df_postings.groupby("author_username"):
        total_posts = len(group)
        post_times = list(group["created_at"])
        hours = group["created_at"].apply(lambda dt: dt.hour if hasattr(dt, "hour") else 0)

        # 1. Fitur Profil
        followers = group["followers"].iloc[0] if "followers" in group.columns else 50
        following = group["following"].iloc[0] if "following" in group.columns else 100
        ratio_ff = following / (followers + 1.0)
        is_default_avatar = group["is_default_avatar"].iloc[0] if "is_default_avatar" in group.columns else False
        is_empty_bio = group["is_empty_bio"].iloc[0] if "is_empty_bio" in group.columns else False
        account_age_days = group["account_age_days"].iloc[0] if "account_age_days" in group.columns else 365

        # 2. Fitur Aktivitas
        retweet_count = (group["interaction_type"] == "retweet").sum()
        retweet_ratio = retweet_count / total_posts if total_posts > 0 else 0.0
        entropy_hours = calculate_entropy(hours)
        burstiness = calculate_burstiness(post_times)

        # 3. Fitur Konten (Kemiripan internal postingan akun sendiri)
        texts = [clean_text_for_nlp(t) for t in group["text"] if len(t) > 5]
        unique_texts_ratio = len(set(texts)) / len(texts) if texts else 1.0

        account_features.append({
            "author_username": author,
            "total_posts": total_posts,
            "followers": followers,
            "following": following,
            "ff_ratio": ratio_ff,
            "is_default_avatar": int(is_default_avatar),
            "is_empty_bio": int(is_empty_bio),
            "account_age_days": account_age_days,
            "retweet_ratio": retweet_ratio,
            "active_hours_entropy": entropy_hours,
            "burstiness": burstiness,
            "unique_text_ratio": unique_texts_ratio,
        })

    return pd.DataFrame(account_features)


def detect_text_duplicates_minhash(
    df_postings: pd.DataFrame, threshold: float = 0.85
) -> List[Dict[str, Any]]:
    """
    Mendeteksi teks kembar antar akun menggunakan MinHash/LSH (R-D4 threshold 0.85).
    """
    lsh = MinHashLSH(threshold=threshold, num_perm=64)
    minhashes = {}
    duplicates = []

    for idx, row in df_postings.iterrows():
        clean_text = clean_text_for_nlp(row["text"])
        tokens = clean_text.split()
        if len(tokens) < 4:
            continue

        m = MinHash(num_perm=64)
        for token in tokens:
            m.update(token.encode("utf8"))

        key = f"{row['author_username']}___{row['id_platform']}"
        minhashes[key] = (m, row["text"], row["author_username"], row["created_at"])

        # Query LSH
        matches = lsh.query(m)
        for match_key in matches:
            match_author, match_id = match_key.split("___")
            if match_author != row["author_username"]:
                sim = m.jaccard(minhashes[match_key][0])
                if sim >= threshold:
                    duplicates.append({
                        "user_a": match_author,
                        "user_b": row["author_username"],
                        "similarity": round(sim, 3),
                        "text_sample": row["text"][:120],
                    })
        lsh.insert(key, m)

    return duplicates
