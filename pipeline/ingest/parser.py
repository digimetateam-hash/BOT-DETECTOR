"""
Modul Ingest dan Parsing Data Media Sosial (NodeXL & CSV/XLSX)
PRD Bagian 4 & 15a
"""
import io
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd


def normalize_datetime(val: Any) -> Optional[datetime]:
    """Mengubah berbagai format tanggal/waktu ke objek datetime UTC."""
    if pd.isna(val) or val is None or val == "":
        return None
    if isinstance(val, (datetime, pd.Timestamp)):
        return val.to_pydatetime()
    try:
        dt = pd.to_datetime(val)
        return dt.to_pydatetime()
    except Exception:
        return None


def parse_dataset_file(
    file_bytes: bytes, filename: str
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Membaca dan mem-parsing berkas CSV atau Excel (termasuk format NodeXL).
    Mengembalikan DataFrame posting dan ringkasan metadata impor.
    """
    is_excel = filename.endswith((".xlsx", ".xls"))
    if is_excel:
        xl = pd.ExcelFile(io.BytesIO(file_bytes))
        sheet_names = xl.sheet_names

        # Cek apakah ini format NodeXL (punya sheet Edges atau Vertices)
        if "Edges" in sheet_names or "Vertices" in sheet_names:
            df_edges = xl.parse("Edges") if "Edges" in sheet_names else pd.DataFrame()
            df_vertices = xl.parse("Vertices") if "Vertices" in sheet_names else pd.DataFrame()
            return parse_nodexl_sheets(df_edges, df_vertices)

        # Jika Excel biasa, ambil sheet pertama
        df = xl.parse(sheet_names[0])
    else:
        # File CSV
        try:
            df = pd.read_csv(io.BytesIO(file_bytes), encoding="utf-8")
        except UnicodeDecodeError:
            df = pd.read_csv(io.BytesIO(file_bytes), encoding="latin-1")

    return standardize_postings_df(df)


def parse_nodexl_sheets(
    df_edges: pd.DataFrame, df_vertices: pd.DataFrame
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Mem-parsing data khusus format NodeXL."""
    records = []
    # Bersihkan header NodeXL jika baris pertama kosong/metadata
    if not df_edges.empty:
        col_v1 = next((c for c in df_edges.columns if "Vertex 1" in str(c)), None)
        col_v2 = next((c for c in df_edges.columns if "Vertex 2" in str(c)), None)
        col_rel = next((c for c in df_edges.columns if "Relationship" in str(c)), None)
        col_time = next((c for c in df_edges.columns if "Relationship Date" in str(c) or "Date" in str(c)), None)
        col_tweet = next((c for c in df_edges.columns if "Tweet" in str(c) or "Text" in str(c)), None)

        for idx, row in df_edges.iterrows():
            author = str(row[col_v1]).strip() if col_v1 and pd.notna(row[col_v1]) else f"user_{idx}"
            time_val = normalize_datetime(row[col_time]) if col_time else datetime.utcnow()
            text_val = str(row[col_tweet]) if col_tweet and pd.notna(row[col_tweet]) else ""
            rel_val = str(row[col_rel]).lower() if col_rel and pd.notna(row[col_rel]) else "mention"

            tipe = "retweet" if "retweet" in rel_val else ("reply" if "reply" in rel_val else "post")

            records.append({
                "id_platform": f"nodexl_{idx}",
                "author_username": author,
                "created_at": time_val or datetime.utcnow(),
                "text": text_val,
                "interaction_type": tipe,
                "target_username": str(row[col_v2]).strip() if col_v2 and pd.notna(row[col_v2]) else None,
                "followers": 100,
                "following": 100,
            })

    df = pd.DataFrame(records)
    return standardize_postings_df(df)


def standardize_postings_df(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Melakukan normalisasi nama kolom dan pembersihan data standar.
    Wajib ada: author_username, created_at, text, interaction_type.
    """
    total_raw = len(df)
    # Mapping kemungkinan variasi nama kolom
    col_mapping = {
        "author_username": ["author_username", "username", "user", "screen_name", "from_user", "author", "sender"],
        "created_at": ["created_at", "waktu", "date", "timestamp", "tanggal", "tweet_created_at"],
        "text": ["text", "teks", "full_text", "tweet", "content", "isi_tweet", "clean_text"],
        "interaction_type": ["interaction_type", "tipe", "type", "tweet_type"],
        "id_platform": ["id_platform", "id", "tweet_id", "status_id", "id_str"],
        "followers": ["followers", "followers_count", "follower"],
        "following": ["following", "following_count", "friends_count"],
        "retweet_count": ["retweet_count", "retweet", "rts"],
        "like_count": ["like_count", "like", "favorites", "favorite_count"],
    }

    normalized = pd.DataFrame()
    for target_col, variations in col_mapping.items():
        found = None
        for col in df.columns:
            if col.strip().lower() in variations:
                found = col
                break
        if found:
            normalized[target_col] = df[found]

    # Defaults jika kolom opsional tidak ada
    if "author_username" not in normalized.columns:
        if len(df.columns) > 0:
            normalized["author_username"] = df.iloc[:, 0].astype(str)
        else:
            normalized["author_username"] = "anonymous"

    if "created_at" not in normalized.columns:
        normalized["created_at"] = [datetime.utcnow() - timedelta(minutes=i*2) for i in range(len(df))]
    else:
        normalized["created_at"] = normalized["created_at"].apply(normalize_datetime)
        normalized["created_at"] = normalized["created_at"].fillna(datetime.utcnow())

    if "text" not in normalized.columns:
        normalized["text"] = ""
    else:
        normalized["text"] = normalized["text"].fillna("").astype(str)

    if "interaction_type" not in normalized.columns:
        normalized["interaction_type"] = "post"
    else:
        normalized["interaction_type"] = normalized["interaction_type"].fillna("post").astype(str).str.lower()

    if "id_platform" not in normalized.columns:
        normalized["id_platform"] = [f"post_{i+1}" for i in range(len(df))]
    else:
        normalized["id_platform"] = normalized["id_platform"].fillna("").astype(str)

    if "followers" not in normalized.columns:
        normalized["followers"] = 50
    if "following" not in normalized.columns:
        normalized["following"] = 150

    # Dedup id_platform
    normalized = normalized.drop_duplicates(subset=["id_platform"]).reset_index(drop=True)
    valid_count = len(normalized)

    metadata = {
        "total_raw": total_raw,
        "valid_count": valid_count,
        "rejected_count": total_raw - valid_count,
        "unique_authors": normalized["author_username"].nunique(),
        "date_min": normalized["created_at"].min(),
        "date_max": normalized["created_at"].max(),
    }

    return normalized, metadata


def generate_mock_mbg_corpus(n_posts: int = 350) -> pd.DataFrame:
    """
    Membuat dataset demo realistis berdasarkan isu MBG (Makan Bergizi Gratis)
    sesuai deskripsi PRD (Fase 1 & Kasus 30 akun terkoordinasi).
    """
    np.random.seed(42)
    base_time = datetime(2026, 3, 2, 8, 0, 0)

    # Pola akun:
    # 1. Akun buzzer terkoordinasi (klaster bot copy-paste & co-retweet)
    # 2. Akun organik (warga, netizen)
    # 3. Akun berita / institusi

    bot_cluster = [f"user_buzzer_{i:02d}" for i in range(1, 16)]
    organic_users = [f"warga_netizen_{i:02d}" for i in range(1, 35)]

    bot_templates = [
        "Program Makan Bergizi Gratis (MBG) terbukti sangat bermanfaat bagi pemenuhan nutrisi anak bangsa! #MBGSukses #GiziAnak",
        "Dukung penuh implementasi Makan Bergizi Gratis untuk generasi emas Indonesia! Pantau terus program MBG #MBGUntukSemua",
        "Senang sekali melihat adik-adik menerima program Makan Bergizi Gratis MBG di sekolah hari ini. Sangat bergizi dan sehat!",
        "Klarifikasi isu: Program MBG berjalan transparan dan diawasi ketat oleh dinas kesehatan. Mari sebarkan fakta!",
    ]

    organic_texts = [
        "Tadi liat menu MBG di sekolah keponakan, menunya lumayan sih ada ayam sama susu.",
        "Semoga anggaran MBG beneran sampai ke anak-anak tanpa potongan ya.",
        "Kritik buat menu MBG hari ini nasinya agak keras, tolong diperbaiki pihak katering.",
        "Diskusi MBG rame banget di linimasa pagi ini, pro dan kontra wajar.",
        "Pemerintah perlu evaluasi higienitas katering program makanan bergizi.",
    ]

    records = []
    # 1. Posting bot dalam jendela waktu sempit (co-retweet dan copy-paste)
    for cycle in range(5):
        burst_time = base_time + timedelta(hours=cycle * 12 + np.random.randint(1, 4))
        template = bot_templates[cycle % len(bot_templates)]

        for bot_user in bot_cluster:
            # Jeda waktu sempit (5-30 detik) = perilaku koordinasi tinggi
            post_time = burst_time + timedelta(seconds=int(np.random.randint(5, 45)))
            tipe = np.random.choice(["retweet", "post"], p=[0.75, 0.25])
            records.append({
                "id_platform": f"mbg_bot_{cycle}_{bot_user}",
                "author_username": bot_user,
                "created_at": post_time,
                "text": template if tipe == "post" else f"RT @akun_pusat: {template}",
                "interaction_type": tipe,
                "followers": int(np.random.randint(5, 30)),
                "following": int(np.random.randint(400, 900)),
                "is_default_avatar": bool(np.random.choice([True, False], p=[0.7, 0.3])),
                "is_empty_bio": bool(np.random.choice([True, False], p=[0.8, 0.2])),
                "account_age_days": int(np.random.randint(10, 80)),
            })

    # 2. Posting organik
    for i in range(n_posts - len(records)):
        user = np.random.choice(organic_users)
        post_time = base_time + timedelta(minutes=int(np.random.randint(10, 4000)))
        text = np.random.choice(organic_texts)
        tipe = np.random.choice(["post", "reply", "retweet"], p=[0.6, 0.25, 0.15])
        records.append({
            "id_platform": f"mbg_org_{i}",
            "author_username": user,
            "created_at": post_time,
            "text": text,
            "interaction_type": tipe,
            "followers": int(np.random.randint(120, 3500)),
            "following": int(np.random.randint(150, 800)),
            "is_default_avatar": False,
            "is_empty_bio": False,
            "account_age_days": int(np.random.randint(400, 3000)),
        })

    df = pd.DataFrame(records)
    df = df.sort_values("created_at").reset_index(drop=True)
    return df
