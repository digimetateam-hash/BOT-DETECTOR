"""
Modul Deep Learning Semantik Bahasa Indonesia (PRD Bagian 7 & 13a R-D5).
Menggunakan indobenchmark/indobert-base-p2 untuk mendeteksi parafrase AI/LLM
antar akun dalam jendela waktu sempit (cosine >= 0.90, <= 10 menit).
"""
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import torch
from transformers import AutoModel, AutoTokenizer

from pipeline.config_loader import load_config
from pipeline.features.extractor import clean_text_for_nlp


def get_torch_device() -> torch.device:
    """Memilih device komputasi terbaik: CUDA -> Apple MPS -> CPU."""
    if torch.cuda.is_available():
        return torch.device("cuda")
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


class IndoBERTEmbedder:
    """Ekstraktor embedding kalimat berbasis indobenchmark/indobert-base-p2."""

    def __init__(
        self,
        model_name: str = "indobenchmark/indobert-base-p2",
        device: Optional[torch.device] = None,
        max_length: int = 128,
    ) -> None:
        self.model_name = model_name
        self.device = device or get_torch_device()
        self.max_length = max_length
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.model.to(self.device)
        self.model.eval()

    def encode(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """
        Menghasilkan matriks embedding ternormalisasi L2 (N x hidden_dim)
        menggunakan mean pooling atas attention mask.
        """
        if not texts:
            return np.empty((0, 768), dtype=np.float32)

        all_embeddings: List[np.ndarray] = []
        for i in range(0, len(texts), batch_size):
            batch = [clean_text_for_nlp(t) or str(t) for t in texts[i : i + batch_size]]
            encoded = self.tokenizer(
                batch,
                padding=True,
                truncation=True,
                max_length=self.max_length,
                return_tensors="pt",
            ).to(self.device)

            with torch.no_grad():
                outputs = self.model(**encoded)
                token_embeddings = outputs.last_hidden_state
                mask = encoded["attention_mask"].unsqueeze(-1).expand(token_embeddings.size()).float()
                sum_embeddings = torch.sum(token_embeddings * mask, dim=1)
                sum_mask = torch.clamp(mask.sum(dim=1), min=1e-9)
                mean_pooled = sum_embeddings / sum_mask
                normalized = torch.nn.functional.normalize(mean_pooled, p=2, dim=1)
                all_embeddings.append(normalized.cpu().numpy())

        return np.vstack(all_embeddings)


def detect_paraphrase_coordination(
    df_postings: pd.DataFrame,
    embeddings: Optional[np.ndarray] = None,
    embedder: Optional[IndoBERTEmbedder] = None,
    cosine_threshold: Optional[float] = None,
    window_minutes: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Mendeteksi koordinasi parafrase semantik antar akun berbeda (PRD R-D5).
    Ambang batas dibaca dari config.yaml jika tidak diberikan secara eksplisit.
    """
    if cosine_threshold is None or window_minutes is None:
        cfg = load_config()
        ts_cfg = cfg.get("detection", {}).get("text_similarity", {})
        if cosine_threshold is None:
            cosine_threshold = float(ts_cfg.get("indobert_cosine_threshold", 0.90))
        if window_minutes is None:
            window_minutes = int(ts_cfg.get("indobert_window_minutes", 10))

    if df_postings.empty or len(df_postings) < 2:
        return []

    df = df_postings.copy().reset_index(drop=True)
    df["created_at_dt"] = pd.to_datetime(df["created_at"], errors="coerce")

    if embeddings is None:
        if embedder is None:
            embedder = IndoBERTEmbedder()
        embeddings = embedder.encode(df["text"].fillna("").astype(str).tolist())

    # Pastikan vektor ternormalisasi L2 agar dot product == cosine similarity
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1.0, norms)
    norm_emb = embeddings / norms

    sim_matrix = norm_emb @ norm_emb.T
    max_delta_sec = window_minutes * 60.0
    matches: List[Dict[str, Any]] = []

    n = len(df)
    for i in range(n):
        t_i = df.loc[i, "created_at_dt"]
        u_i = str(df.loc[i, "author_username"])
        if pd.isna(t_i):
            continue

        for j in range(i + 1, n):
            u_j = str(df.loc[j, "author_username"])
            if u_i == u_j:
                continue

            sim = float(sim_matrix[i, j])
            if sim < cosine_threshold:
                continue

            t_j = df.loc[j, "created_at_dt"]
            if pd.isna(t_j):
                continue

            delta_sec = abs((t_j - t_i).total_seconds())
            if delta_sec <= max_delta_sec:
                matches.append({
                    "user_a": u_i,
                    "user_b": u_j,
                    "cosine_similarity": round(sim, 4),
                    "delta_minutes": round(delta_sec / 60.0, 2),
                    "text_a": str(df.loc[i, "text"])[:120],
                    "text_b": str(df.loc[j, "text"])[:120],
                })

    return matches
