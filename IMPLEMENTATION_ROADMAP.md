# 10. IMPLEMENTATION ROADMAP — Peta Jalan Implementasi Bertahap

**Status Saat Ini:** Seluruh audit Phase 1–9 selesai. Belum ada perubahan kode pada modul inti tanpa persetujuan pengguna.

---

## Tahapan Implementasi Setelah Persetujuan

### Tahap 1 — Fondasi Data & Unsupervised Baseline (Minggu 1–2)
1. **Perkuat Ingest (`pipeline/ingest/parser.py`):** Tambah dukungan pembacaan langsung `mbg_tweets_master_clean.parquet` dan `indobert_9_emosi_fixed.csv` dengan hashing SHA-256 wajib di pintu masuk.
2. **Modul Anomali Unsupervised (`pipeline/features/anomaly.py`):** Integrasikan detektor lonjakan harian Z-score dari `ThisIsEconomy/ews/anomaly_detector.py` dan tambahkan `IsolationForest` untuk skor anomali perilaku akun.
3. **Pengayaan Fitur Jaringan (`pipeline/network/graph.py`):** Adopsi perhitungan `In_Degree`, `Out_Degree`, `Betweenness_Centrality`, `PageRank`, `Closeness_Centrality`, dan tipologi peran dari `compute_actor_centrality_typology.py`.

### Tahap 2 — Pelabelan Ground Truth & Validasi Manusia (Minggu 3–4)
1. Gunakan layar **Validasi Manual** di `app/main.py` untuk melabeli 300–500 akun unik oleh 2 coder independen.
2. Hitung reliabilitas antar-coder; pastikan **Cohen's $\kappa \ge 0.70$** sebelum melatih model supervised.
3. Lengkapi metadata profil akun (`followers`, `following`, `account_created_at`) jika memungkinkan dari sumber data tambahan.

### Tahap 3 — Hybrid Supervised Model, IndoBERT & Ablation Study (Minggu 5–6)
1. Implementasikan `pipeline/models/evaluation.py` dengan `GroupShuffleSplit` anti-leakage.
2. Latih baseline (`TF-IDF + LogReg/SVM`) dan model utama (`LightGBM + Top-5 SHAP`).
3. Tambahkan ekstraksi embedding `indobenchmark/indobert-base-p2` di `pipeline/features/semantic.py` untuk ketahanan terhadap parafrase AI (R-D5).
4. Jalankan *ablation study* dan uji signifikansi McNemar.

### Tahap 4 — Pembaruan Dashboard & Pengujian Menyeluruh (Minggu 7–8)
1. Perbarui `app/main.py` agar menampilkan secara terpisah: *Bot Probability*, *Behavioral Anomaly Score*, dan *Coordinated Cluster Evidence*, serta tombol ekspor Excel (`.xlsx`).
2. Tambahkan unit test lengkap di `tests/` (target coverage $\ge 80\%$) dan jalankan `pytest` serta `ruff check`.

---

## Rekomendasi Metode Terbaik (Menunggu Persetujuan Anda)
1. **Untuk kondisi data saat ini (0 label bot/human):** Jalankan **Pipeline Unsupervised Hybrid** terlebih dahulu — menggabungkan *Isolation Forest* (fitur perilaku & temporal dari `indobert_9_emosi_fixed.csv`), *Rolling Z-Score* (`ews/anomaly_detector.py`), *MinHash/LSH* (teks kembar), dan *SNA Role Typology + Louvain* (`compute_actor_centrality_typology.py`).
2. **Untuk tahap supervised berikutnya:** Gunakan **LightGBM + SHAP** dengan protokol **GroupShuffleSplit** (berbasis `handle_hash` dan `clean_text`) setelah minimal 300 akun memiliki label konsensus ($\kappa \ge 0.70$).
