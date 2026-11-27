# 4. SCIENTIFIC METHOD MAPPING — Adopsi `ThisIsEconomy` ke `DETEKSI BOT`

| Komponen Ilmiah | Sumber di `ThisIsEconomy` | Status di `DETEKSI BOT` Saat Ini | Keputusan Strategis | Target Modul di `DETEKSI BOT` |
| :--- | :--- | :--- | :--- | :--- |
| **Group-Aware Split Anti-Leakage** | `scripts/train_indobert_group_aware.py` (`GroupShuffleSplit`) | Belum ada pipeline training | **Adopsi Penuh** — mencegah kebocoran teks kembar antar train/test | `pipeline/models/evaluation.py` |
| **Sentralitas & Tipologi Peran Aktor** | `scripts/compute_actor_centrality_typology.py` (PageRank, Betweenness, In/Out Degree) | Hanya `degree` dasar di `pipeline/network/graph.py` | **Adopsi & Modifikasi** — tambahkan In/Out ratio & PageRank untuk menandai *Broadcaster* searah | `pipeline/network/graph.py` |
| **Rolling Z-Score Temporal Spike** | `ews/anomaly_detector.py` | Belum ada detektor lonjakan harian | **Adopsi** — deteksi hari/jam lonjakan (*burst days*) sebelum membangun graf koordinasi | `pipeline/features/temporal_anomaly.py` |
| **IndoBERT Embeddings (`indobert-base-p2`)** | `scripts/train_indobert_group_aware.py`, `scripts/sna.py` | Baru memakai MinHash (`datasketch`) | **Adopsi Tahap Lanjut** — gunakan embedding CLS + cosine similarity untuk R-D5 (parafrase AI) | `pipeline/features/semantic.py` |
| **Deteksi Sarkasme (`dataset_sindiran_valid.csv`)** | `data/sarcasm/dataset_sindiran_valid.csv` (3.395 baris) | Belum ada | **Adopsi Opsional** — fitur pembeda kritik warga yang sarkastik vs buzzer | `pipeline/features/extractor.py` |
| **TF-IDF + LogReg/LinearSVC Baseline** | `scripts/execute_end_to_end_audit.py` | Belum ada | **Adopsi sebagai Baseline** — pembanding wajib sebelum mengklaim keunggulan model kompleks | `pipeline/models/baseline.py` |
| **SHA-256 + Salt Handle Hashing** | *Tidak ada* (username mentah terbuka) | Sudah ada di `db/schema.py` (`hash_handle`) | **Pertahankan & Wajibkan** di semua proses ingest data dari `ThisIsEconomy` | `db/schema.py` |
| **Co-Retweet & Graf Multiplex 4 Lapisan** | *Tidak ada* | Sudah ada fondasinya di `pipeline/network/graph.py` | **Pertahankan & Perkuat** dengan metrik sentralitas dari `ThisIsEconomy` | `pipeline/network/graph.py` |
