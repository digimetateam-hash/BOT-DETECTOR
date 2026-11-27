# 1. REPOSITORY AUDIT — `DETEKSI BOT` vs `ThisIsEconomy`

**Tanggal Audit:** 27 November 2026  
**Mode:** Read-Only Scientific Reverse Engineering  

---

## 1. Profil Proyek Utama: `DETEKSI BOT` (`TOPENG`)
- **Entry Point Aplikasi:** `streamlit_app.py` (meneruskan ke `app/main.py`)
- **Arsitektur Aplikasi:** Modular Python 3.11 + Streamlit Dashboard + SQLAlchemy ORM (11 tabel sesuai PRD Bagian 12a) + Konfigurasi eksternal `config.yaml` & `.env`.
- **Modul Deteksi Bot:** `pipeline/models/detector.py` (`calculate_bot_score_and_explain`, `calculate_intercoder_agreement`).
- **Modul Preprocessing & Ingest:** `pipeline/ingest/parser.py` (`parse_dataset_file`, `parse_nodexl_sheets`, `standardize_postings_df`, `generate_mock_mbg_corpus`) dan `pipeline/features/extractor.py` (`clean_text_for_nlp`).
- **Modul Database:** `db/schema.py` (11 tabel: `korpus`, `akun`, `posting`, `interaksi`, `run_model`, `skor_akun`, `label_manual`, `klaster_koordinasi`, `anggota_klaster`, `validasi_eksternal`, `alert` + `hash_handle` SHA-256 + salt) dan `db/crud.py`.
- **Modul Visualisasi:** `app/main.py` (7 layar Streamlit + Plotly Express/Graph Objects + `assets/hero_3d_material3.svg`).
- **Modul Machine Learning & NLP:** Saat ini masih berupa skoring berbasis bobot aturan + MinHash/LSH (`datasketch`) di `pipeline/features/extractor.py` dan `pipeline/models/detector.py`; belum ada model ML terlatih (LightGBM/XGBoost) maupun inferensi IndoBERT aktif.
- **API & Integrasi Eksternal:** Belum aktif (disiapkan placeholder `.env.example` untuk `ANTHROPIC_API_KEY`, `TELEGRAM_BOT_TOKEN`, `HUGGINGFACE_TOKEN`).

---

## 2. Profil Proyek Referensi: `ThisIsEconomy` (`./ThisIsEconomy`)
- **Entry Point Aplikasi:** `dashboard/app.py` (Streamlit), `backend/main.py` (FastAPI/Backend services), `frontend/` (Next.js/TypeScript).
- **Arsitektur Aplikasi:** Repositori riset tesis & publikasi *Computational Social Science* (analisis wacana MBG di X), terdiri dari `scripts/` (pipeline batch & audit), `ews/` (Early Warning System v2), `backend/services/` (layanan NLP/SNA), `dashboard/`, `data/`, `results/`, dan `reports/`.
- **Modul NLP & Deep Learning:**
  - `scripts/train_indobert_group_aware.py`: Fine-tuning `indobenchmark/indobert-base-p2` (9 kelas emosi, `GroupShuffleSplit`, `seed=42`).
  - `scripts/sna.py`: Stemming Sastrawi + inferensi IndoBERT + pembangunan graf mention.
  - `scripts/execute_end_to_end_audit.py`: Baseline `TfidfVectorizer` + `LogisticRegression` & `LinearSVC` pada protokol group-aware.
- **Modul SNA:** `scripts/compute_actor_centrality_typology.py`, `scripts/compute_community_echo_chambers.py`, `scripts/compute_macro_topology_metrics.py` (`networkx` + `community_louvain`).
- **Modul Deteksi Anomali:** `ews/anomaly_detector.py` (agregasi harian, rolling mean/std 7 hari, Z-Score global dengan threshold `z >= 2.0`).

---

## 3. Tabel Perbandingan Kedua Proyek

| Dimensi | `DETEKSI BOT` (TOPENG) | `ThisIsEconomy` (Referensi) | Peluang Adopsi / Integrasi |
| :--- | :--- | :--- | :--- |
| **Tujuan Utama** | Deteksi akun bot, CIB, dan engagement semu | Analisis wacana, 9 emosi, sarkasme, ABSA, dan SNA isu MBG | Adopsi lapisan NLP, SNA, dan EWS ke fitur deteksi bot |
| **Bahasa & Environment** | Python 3.11 (`pyproject.toml`, `requirements.txt`) | Python 3.10+ (`requirements.txt`) + Next.js (`frontend/`) | Selaras pada ekosistem Python & Streamlit |
| **Database & Privasi** | SQLAlchemy 11 tabel + `handle_hash` SHA-256 + salt (`db/schema.py`) | Berbasis file CSV/Parquet/XLSX; username mentah tersimpan (`author_username`) | **Wajib pertahankan** hashing SHA-256 milik `DETEKSI BOT` |
| **NLP & Deep Learning** | MinHash/LSH (`datasketch`), regex cleaning dasar | `indobenchmark/indobert-base-p2`, `TfidfVectorizer`, Sastrawi, ABSA | Adopsi embedding/fitur IndoBERT & TF-IDF baseline |
| **Machine Learning** | Rule-based weighted score + SHAP-style attribution | `LogisticRegression`, `LinearSVC` (group-aware split, `seed=42`) | Adopsi protokol `GroupShuffleSplit` anti-leakage |
| **Social Network Analysis** | Graf Co-Retweet & Co-Text (`pipeline/network/graph.py`) | 971 node, 666 unique directed edges, Louvain ($Q=0.9837$), 5 metrik sentralitas, tipologi peran | Adopsi 5 metrik sentralitas & tipologi aktor (`compute_actor_centrality_typology.py`) |
| **Anomaly Detection** | Belum ada modul deret waktu | `ews/anomaly_detector.py` (Rolling 7d + Z-Score $\ge 2.0$) | Adopsi deteksi *burst/spike* temporal harian |
| **Label Bot/Human** | Belum ada data berlabel | **Tidak ada label bot/human** (hanya emosi, sentimen, sarkasme) | Gunakan pendekatan *unsupervised anomaly* + pelabelan manual sebelum supervised |
