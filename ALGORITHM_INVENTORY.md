# 3. ALGORITHM INVENTORY — Verifikasi Kode Sumber `ThisIsEconomy`

**Tanggal Audit:** 27 November 2026  
**Aturan Verifikasi:** Hanya algoritma yang terbukti diimplementasikan di dalam kode sumber Python yang dicatat sebagai aktif.

---

## A. Natural Language Processing & Deep Learning

1. **IndoBERT (`indobenchmark/indobert-base-p2`)**
   - **Lokasi Kode:** `ThisIsEconomy/scripts/train_indobert_group_aware.py` (baris 20–66), `ThisIsEconomy/scripts/sna.py` (baris 65–80)
   - **Fungsi:** Klasifikasi sekuens teks 9 kelas emosi (`AutoModelForSequenceClassification`, `max_length=128`).
   - **Parameter:** `num_train_epochs=3`, `per_device_train_batch_size=32`, `learning_rate=2e-5`, `seed=42`.
   - **Hasil Evaluasi (`results/FINAL_MODEL_COMPARISON.csv`):** Accuracy `0.7940`, Macro-F1 `0.5160`, Weighted-F1 `0.7851` (Train N=4.205, Test N=1.058, protokol `GROUP-AWARE`, tanpa text leakage).
   - **Relevansi Deteksi Bot:** Dapat diekstrak *CLS embedding*-nya untuk mendeteksi parafrase AI/LLM (PRD R-D5) serta fitur emosi/sarkasme sebagai sinyal tambahan pembeda kritik warga vs template.

2. **TF-IDF (`TfidfVectorizer`)**
   - **Lokasi Kode:** `ThisIsEconomy/scripts/execute_end_to_end_audit.py` (baris 196–199), `ThisIsEconomy/scripts/run_baseline_predictions.py`
   - **Fungsi:** Ekstraksi fitur n-gram teks (`max_features=5000`, `ngram_range=(1, 2)`).
   - **Relevansi Deteksi Bot:** Baseline cepat & ringan untuk deteksi kemiripan kosinus teks serta fitur klasifikasi konten tanpa GPU.

3. **Indonesian Stemming (`Sastrawi`) & Regex Cleaning**
   - **Lokasi Kode:** `ThisIsEconomy/scripts/sna.py` (baris 46–56)
   - **Fungsi:** Lowercasing, penghapusan URL/mention/hashtag, stemming kata bahasa Indonesia.
   - **Kelemahan untuk Bot Detection:** Menghapus URL dan mention saat stemming menghilangkan sinyal koordinasi `co-URL` dan `co-mention`; untuk deteksi bot, teks mentah (dengan URL/emoji) harus tetap disimpan terpisah.

---

## B. Machine Learning Klasik

1. **Logistic Regression (`LogisticRegression`)**
   - **Lokasi Kode:** `ThisIsEconomy/scripts/execute_end_to_end_audit.py` (baris 206–208), `ThisIsEconomy/scripts/run_baseline_predictions.py` (baris 173)
   - **Parameter:** `max_iter=1000`, `C=1.0`, `random_state=42`.
   - **Evaluasi (`FINAL_MODEL_COMPARISON.csv`):** Accuracy `0.6947`, Macro-F1 `0.3429`, Weighted-F1 `0.6457`.

2. **Linear Support Vector Machine (`LinearSVC`)**
   - **Lokasi Kode:** `ThisIsEconomy/scripts/execute_end_to_end_audit.py` (baris 229–231), `ThisIsEconomy/scripts/run_baseline_predictions.py` (baris 180)
   - **Parameter:** `max_iter=2000`, `C=1.0`, `random_state=42`.
   - **Evaluasi (`FINAL_MODEL_COMPARISON.csv`):** Accuracy `0.6720`, Macro-F1 `0.4095`, Weighted-F1 `0.6558`.

*(Catatan: LightGBM, XGBoost, Random Forest, Naive Bayes tidak ditemukan implementasinya pada kode sumber `ThisIsEconomy`).*

---

## C. Social Network Analysis (SNA)

1. **Multi-Metric Centrality & Role Typology**
   - **Lokasi Kode:** `ThisIsEconomy/scripts/compute_actor_centrality_typology.py` (baris 44–87)
   - **Algoritma (`networkx`):** `in_degree`, `out_degree`, `degree_centrality`, `betweenness_centrality(normalized=True)`, `closeness_centrality`, `pagerank(alpha=0.85)`.
   - **Output:** Tipologi 6 peran komunikasi (*Algorithmic Oracle*, *Target Sink*, *Opinion Broker*, *Information Broadcaster*, *Secondary Influencer*, *Peripheral Citizen*).
   - **Relevansi Deteksi Bot:** Sangat tinggi; membedakan akun penyebar satu arah (*Information Broadcaster*: `out_deg >= 3, in_deg <= 1`) dari warga organik atau otoritas (*Target Sink*).

2. **Louvain Community Detection & Macro Topology**
   - **Lokasi Kode:** `ThisIsEconomy/scripts/sna.py` (baris 7), `ThisIsEconomy/results/macro_topology_metrics.json`
   - **Hasil Terukur:** 971 vertices, 666 unique directed edges, Louvain Modularity $Q = 0.9837$, 341 WCC, Density `0.000707` (directed), Reciprocity `1.20%`.

---

## D. Anomaly Detection & Early Warning System

1. **Statistical Rolling Z-Score Spike Detector**
   - **Lokasi Kode:** `ThisIsEconomy/ews/anomaly_detector.py` (baris 42–79), `ThisIsEconomy/scripts/final_ews_audit.py` (baris 217–237)
   - **Algoritma:** Agregasi mention harian $\rightarrow$ `rolling(window=7, min_periods=1)` $\rightarrow$ $Z = (x - \mu) / \sigma$ $\rightarrow$ flag `is_anomaly = (z_score >= 2.0)`.
   - **Temuan:** 4 hari anomali terdeteksi dari 83 hari aktif (`reports/anomaly_events.csv`).
   - **Catatan:** Isolation Forest, Local Outlier Factor, DBSCAN, dan One-Class SVM **tidak ditemukan** implementasinya di `ThisIsEconomy`.

---

## E. Coordinated Behavior Detection
- **Status di `ThisIsEconomy`:** **Tidak ada** detektor *co-retweet*, *co-URL*, *burstiness* antar-posting dalam hitungan detik, maupun *MinHash* di source code `ThisIsEconomy`. Fitur-fitur ini merupakan keunggulan unik yang dibangun di `DETEKSI BOT` (`pipeline/features/extractor.py` & `pipeline/network/graph.py`).
