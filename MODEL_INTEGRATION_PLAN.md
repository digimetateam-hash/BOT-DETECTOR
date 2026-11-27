# 7. MODEL INTEGRATION PLAN — Integrasi `ThisIsEconomy` ke `DETEKSI BOT`

**Prinsip:** Pertahankan arsitektur existing `DETEKSI BOT` (`db/`, `pipeline/`, `app/`, `config.yaml`) tanpa merusak fungsi yang sudah berjalan.

---

## 1. Pemetaan Modul Usulan ke Struktur Existing `DETEKSI BOT`

| Modul Usulan | Lokasi di `DETEKSI BOT` | Status | Keterangan Integrasi |
| :--- | :--- | :--- | :--- |
| `dataset_loader.py` | `pipeline/ingest/parser.py` | **Modifikasi** | Tambah loader untuk format `indobert_9_emosi_fixed.csv` & `mbg_tweets_master_clean.parquet` |
| `data_preprocessing.py` | `pipeline/features/extractor.py` | **Modifikasi** | Pertahankan `text` mentah untuk URL/hashtag; tambah normalisasi slang Indonesia |
| `behavioral_features.py` | `pipeline/features/extractor.py` | **Modifikasi** | Tambah `post_frequency`, `avg_post_interval`, `engagement_rate` |
| `nlp_analysis.py` | `pipeline/features/semantic.py` | **Buat Baru** | Ekstraksi embedding `indobenchmark/indobert-base-p2` + cosine similarity (R-D5) |
| `network_analysis.py` | `pipeline/network/graph.py` | **Modifikasi** | Adopsi metrik sentralitas (`PageRank`, `Betweenness`, `Closeness`, `In/Out Degree`) & tipologi peran |
| `anomaly_detection.py` | `pipeline/features/anomaly.py` | **Buat Baru** | Adopsi `ews/anomaly_detector.py` (Z-score temporal) + `IsolationForest` multivariat |
| `hybrid_bot_classifier.py` | `pipeline/models/detector.py` | **Modifikasi** | Pisahkan *Anomaly Score*, *Coordination Evidence*, dan *Supervised Bot Probability* (LightGBM + SHAP) |
| `model_evaluation.py` | `pipeline/models/evaluation.py` | **Buat Baru** | Implementasi `GroupShuffleSplit`, PR-AUC, F1, Confusion Matrix, McNemar test |
| `bot_dashboard.py` | `app/main.py` | **Modifikasi** | Tambah visualisasi *Anomaly Score*, *Network Typology*, dan ekspor Excel (`.xlsx`) |

---

## 2. Kebutuhan Dependency, Hardware, Risiko & Rollback
- **Dependency Baru:** Seluruh library utama (`torch`, `transformers`, `scikit-learn`, `lightgbm`, `shap`, `networkx`, `leidenalg`, `openpyxl`) **sudah terpasang** di `.venv` (Python 3.11.15). Tidak perlu instalasi paket berat baru.
- **Kebutuhan Hardware & Komputasi:**
  - *Tanpa IndoBERT (Layer 1, 3, 4 + MinHash):* CPU standar, RAM 4–8 GB, proses 10.000 tweet < 30 detik.
  - *Dengan IndoBERT Embedding:* Disarankan Apple Silicon (MPS) atau GPU, atau CPU batching (`batch_size=32`, `max_length=128`), estimasi 2–4 menit untuk 5.000 tweet unik.
- **Risiko Integrasi:**
  1. *Memory OOM* saat memuat IndoBERT di Streamlit Cloud (RAM 1 GB limit) $\rightarrow$ **Mitigasi:** jadikan inferensi IndoBERT opsional/terpisah dari Streamlit Cloud free tier atau gunakan mode ringan TF-IDF + MinHash sebagai default cloud.
  2. *Perbedaan skema kolom* antar dataset $\rightarrow$ **Mitigasi:** validasi ketat di `parser.py` dan unit test di `tests/`.
- **Strategi Pengujian & Rollback:**
  - Setiap modul baru wajib memiliki unit test di `tests/` dan lolos `pytest` + `ruff check` sebelum commit.
  - Seluruh perubahan diisolasi pada branch fitur Git; rollback cukup dengan `git revert` atau mengembalikan `app/main.py` ke tag rilis stabil sebelumnya.
