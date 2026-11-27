"""
Unit tests untuk modul semantik Deep Learning (PRD R-D5).
Menguji logika cosine similarity >= 0.90 dalam jendela <= 10 menit
tanpa perlu mengunduh bobot model HuggingFace saat CI.
"""
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import torch

from pipeline.features.semantic import detect_paraphrase_coordination, get_torch_device


def test_get_torch_device():
    dev = get_torch_device()
    assert isinstance(dev, torch.device)
    assert dev.type in {"cuda", "mps", "cpu"}


def test_detect_paraphrase_coordination_r_d5():
    base = datetime(2026, 5, 1, 10, 0, 0)
    df = pd.DataFrame([
        # Pasangan 1: beda akun, dalam 4 menit, embedding sangat mirip -> TERDETEKSI
        {"author_username": "akun_a", "created_at": base, "text": "Program MBG sukses besar"},
        {"author_username": "akun_b", "created_at": base + timedelta(minutes=4), "text": "Makan bergizi gratis berhasil"},
        # Pasangan 2: beda akun, tapi selisih 25 menit (> 10 menit) -> TIDAK terdeteksi
        {"author_username": "akun_c", "created_at": base + timedelta(minutes=25), "text": "Program MBG sangat bagus"},
        # Pasangan 3: beda akun, dalam 2 menit, tapi embedding ortogonal -> TIDAK terdeteksi
        {"author_username": "akun_d", "created_at": base + timedelta(minutes=2), "text": "Cuaca hari ini cerah"},
    ])

    emb = np.array([
        [1.0, 0.0, 0.0],
        [0.98, 0.199, 0.0],   # cosine ~ 0.98 >= 0.90
        [0.99, 0.141, 0.0],   # cosine ~ 0.99, tapi delta 25 menit
        [0.0, 1.0, 0.0],      # cosine = 0.0
    ], dtype=np.float32)

    matches = detect_paraphrase_coordination(df, embeddings=emb)
    assert len(matches) == 1
    assert matches[0]["user_a"] == "akun_a"
    assert matches[0]["user_b"] == "akun_b"
    assert matches[0]["cosine_similarity"] >= 0.90
    assert matches[0]["delta_minutes"] <= 10.0
