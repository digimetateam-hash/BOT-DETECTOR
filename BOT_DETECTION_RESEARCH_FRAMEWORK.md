# 5. BOT DETECTION RESEARCH FRAMEWORK (5-Layer Hybrid Architecture)

Kerangka riset *Computational Social Science* untuk **DETEKSI BOT (`TOPENG`)** dirancang dalam 5 lapisan yang saling melengkapi agar tidak menghakimi akun hanya dari satu indikator (misalnya frekuensi tinggi atau emosi negatif).

---

## Arsitektur 5 Lapisan

### LAYER 1 — Account Behavior Analysis
- **Variabel:** Frekuensi posting, interval antar-posting (*burstiness* $B = (\sigma - \mu)/(\sigma + \mu)$), entropi jam aktif 24 jam, rasio repost/retweet, rasio *in-degree / out-degree*.
- **Prinsip Ilmiah:** Akun manusia memiliki ritme sirkadian dan interaksi dua arah; frekuensi tinggi saja **tidak otomatis** berarti bot (bisa berupa akun berita atau aktivis).

### LAYER 2 — Textual & Semantic Analysis
- **Variabel:** Duplikasi teks MinHash/LSH (R-D4, Jaccard $\ge 0.85$), kemiripan kosinus embedding `indobert-base-p2` (R-D5, $\ge 0.90$ dalam 10 menit untuk mendeteksi parafrase LLM), rasio URL & hashtag berulang, serta fitur sarkasme/emosi sebagai konteks (emosi negatif $\neq$ bot).

### LAYER 3 — Network & Coordination Analysis
- **Variabel:** `In_Degree`, `Out_Degree`, `Betweenness_Centrality`, `PageRank`, `Closeness_Centrality` (diadopsi dari `compute_actor_centrality_typology.py`), deteksi komunitas Louvain/Leiden, serta graf koordinasi multiplex (co-retweet $\le 60$ detik, co-hashtag, co-URL, co-text).

### LAYER 4 — Unsupervised Anomaly Detection
- **Metode:**
  1. **Temporal Spike Detector (Z-Score):** Diadopsi dari `ews/anomaly_detector.py` untuk menandai jendela waktu anomali.
  2. **Multivariate Behavioral Anomaly (Isolation Forest / LOF):** Diterapkan pada vektor fitur Layer 1–3 untuk menghasilkan *Behavioral Anomaly Score* tanpa membutuhkan label bot/human terlebih dahulu.

### LAYER 5 — Hybrid Classification & Explainability
- **Strategi Penggabungan Berdasarkan Ketersediaan Label:**
  - **Tahap Unsupervised (Saat ini — 0 label bot/human):** Gunakan kombinasi *Anomaly Score* (Isolation Forest) + *Coordination Evidence* (graf multiplex $\ge 2$ lapisan). Tidak ada klaim akurasi supervised.
  - **Tahap Supervised (Setelah $\ge 300\text{–}500$ akun dilabeli 2 coder dengan $\kappa \ge 0.70$):** Latih **LightGBM / XGBoost** dengan `GroupShuffleSplit` dan jelaskan setiap prediksi dengan **Top-5 SHAP values** (R-D9).
- **Kategorisasi Output:** `Human Account`, `Automated Bot (Perilaku Mirip Bot)`, `Suspicious Account`, `Coordinated Account`, `Undetermined Account` (< 5 posting, R-D2).
