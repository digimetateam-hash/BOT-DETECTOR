# 2. DATASET FORENSIC REPORT — `ThisIsEconomy`

**Tanggal Audit:** 27 November 2026  
**Metode:** Inspeksi langsung menggunakan `pandas` (read-only) terhadap 14 berkas prioritas di `./ThisIsEconomy/`.

---

## 1. Ringkasan Eksekutif Temuan Forensik
1. **Tidak Ada Label Bot/Human:** Tidak satu pun dari 14 dataset memiliki kolom `bot_label`, `is_bot`, atau `account_type` (human vs bot). Seluruh label yang tersedia adalah label **emosi** (7–9 kelas), **sentimen** (Positif/Negatif/Netral), **sarkasme/sindiran** (`bool`), dan **anomali volume harian** (`is_anomaly` berbasis Z-score).
2. **Missing Values Kritis pada Identitas Akun:** Pada `mbg_tweets_master_clean.csv` (9.310 baris), kolom `author_username` kosong sebanyak **5.888 baris (63,24%)**, sehingga analisis level-akun hanya bisa dilakukan penuh pada ~3.422 baris yang memiliki username atau pada korpus `indobert_9_emosi_fixed.csv` (5.263 baris, 0 missing `author_username`).
3. **Duplikasi & Multi-Row:**
   - `indobert_9_emosi.csv` (5.309 baris) memiliki **1.356 baris duplikat identik**.
   - `indobert_9_emosi_fixed.csv` (5.263 baris) memiliki **1.349 baris duplikat identik** (merupakan versi terjemahan label emosi ke bahasa Indonesia dari `indobert_9_emosi.csv`).
   - `mbg_absa_dataset.csv` (6.352 baris) memiliki **1.830 baris duplikat identik** (ekspansi multi-aspek per tweet).
   - `data/sna/network_edges.csv` dan `results/mbg_network_edges_final.csv` **identik** (692 baris, 26 edge duplikat $\rightarrow$ 666 edge unik).
4. **Anotasi Peneliti Kosong:** `data/annotation/researcher_batch_100.csv` (100 baris) memiliki kolom `researcher_label`, `confidence_1to5`, dan `notes` yang **100% NaN**.

---

## 2. Tabel Audit 14 Dataset Prioritas

| # | Lokasi File | Format | Baris $\times$ Kolom | Missing Values (>0) | Duplikat | Target / Label Tersedia | Potensi untuk Bot Detection |
| :---: | :--- | :---: | :---: | :--- | :---: | :--- | :--- |
| 1 | `data/processed/mbg_tweets_master_clean.csv` | CSV | 9.310 $\times$ 13 | `author_username` (5.888), `author_name` (1.182), `clean_text` (1) | 0 | `predicted_emotion` | Fitur teks, waktu (`created_at`), metrik engagement (`like`, `retweet`, `reply`, `quote`, `view`) |
| 2 | `data/processed/mbg_tweets_master_clean.parquet` | Parquet | 9.310 $\times$ 13 | Sama persis dengan #1 | 0 | `predicted_emotion` | Sama dengan #1 (versi terkompresi lebih cepat dibaca) |
| 3 | `data/sna/network_edges.csv` | CSV | 692 $\times$ 2 | 0 | 26 | Tidak ada | Edge list `Source -> Target` untuk graf interaksi mention/reply |
| 4 | `data/results/indobert_9_emosi.csv` | CSV | 5.309 $\times$ 13 | `clean_text` (46), `processed_text` (46) | 1.356 | `predicted_emotion` (EN) | Korpus teks + timestamp + `author_username` lengkap (untuk fitur temporal & duplikasi) |
| 5 | `data/results/indobert_9_emosi_fixed.csv` | CSV | 5.263 $\times$ 13 | 0 | 1.349 | `predicted_emotion` (ID) | Versi bersih dari #4; `author_username` lengkap untuk analisis koordinasi |
| 6 | `data/results/mbg_absa_dataset.csv` | CSV | 6.352 $\times$ 6 | 0 | 1.830 | `aspect`, `sentiment`, `emotion` | Fitur gaya bahasa / aspek; tidak memiliki `author_username` |
| 7 | `data/sarcasm/dataset_sindiran_valid.csv` | CSV | 3.395 $\times$ 3 | 0 | 0 | `sindiran` (`bool`: 315 True) | Fitur tambahan pembeda kritik warga (sarkasme) vs buzzer template |
| 8 | `data/annotation/researcher_batch_100.csv` | CSV | 100 $\times$ 7 | `researcher_label` (100), `confidence_1to5` (100), `notes` (100) | 0 | `silver_label` | Template/contoh lembar validasi; belum terisi |
| 9 | `results/actor_centrality_typology.csv` | CSV | 971 $\times$ 12 | 0 | 0 | `Communication_Role`, `Community` | **Sangat tinggi:** fitur jaringan siap pakai (`In/Out/Total Degree`, `Betweenness`, `PageRank`, `Closeness`) |
| 10 | `results/community_echo_chambers.csv` | CSV | 6 $\times$ 7 | 0 | 0 | `Community_Id`, `Emosi_Dominan` | Ringkasan 6 klaster echo chamber terbesar (mis. klaster `@grok`, klaster `@prabowo`) |
| 11 | `results/mbg_network_nodes_final.csv` | CSV | 971 $\times$ 6 | 0 | 0 | `Community`, `Dominant_Emotion` | Subset kolom dari #9 (`Id`, `Label`, `Degree`, `Betweenness`, `Community`, `Dominant_Emotion`) |
| 12 | `results/mbg_network_edges_final.csv` | CSV | 692 $\times$ 2 | 0 | 26 | Tidak ada | Duplikat identik dari #3 (`data/sna/network_edges.csv`) |
| 13 | `results/sna_results.csv` | CSV | 986 $\times$ 2 | 0 | 0 | Tidak ada | Daftar `node` & `degree_centrality` (15 node lebih banyak dari #9/#11) |
| 14 | `reports/anomaly_events.csv` | CSV | 83 $\times$ 6 | `rolling_mean` (2), `rolling_std` (2) | 0 | `is_anomaly` (4 True, 79 False) | Referensi baseline lonjakan volume harian (*burst days*) untuk korelasi aktivitas terkoordinasi |

---

## 3. Catatan Risiko Kebocoran Data & Keterbatasan
- **Duplikasi Teks Tinggi:** Adanya 1.349–1.356 baris duplikat pada korpus emosi membuktikan bahwa split acak biasa (*random split*) menyebabkan **text leakage** parah. Wajib menggunakan `GroupShuffleSplit` berbasis teks bersih atau `author_username`.
- **Variabel Profil Akun Tidak Tersedia:** Kolom `followers_count`, `following_count`, `account_created_at`, `bio`, dan `avatar_default` **tidak tersedia** di ke-14 dataset ini.
