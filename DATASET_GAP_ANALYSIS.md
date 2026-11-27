# 6. DATASET GAP ANALYSIS — Kesiapan Data untuk Deteksi Bot

**Dasar Audit:** Pemeriksaan 14 berkas dataset di `./ThisIsEconomy` dan perbandingan terhadap kebutuhan 17 variabel deteksi bot.

---

## 1. Matriks Ketersediaan Variabel

| Variabel Kebutuhan | Status di `ThisIsEconomy` | Bukti Lokasi Dataset | Catatan / Kesenjangan |
| :--- | :---: | :--- | :--- |
| `account_id` / `handle_hash` | ⚠️ Parsial | `author_username` di `indobert_9_emosi_fixed.csv` (lengkap), namun **5.888/9.310 kosong** di `mbg_tweets_master_clean.csv` | Wajib di-hash via `db/schema.py:hash_handle` saat ingest |
| `username` (mentah) | ⚠️ Parsial | Sama seperti di atas | Tidak boleh ditampilkan di UI/publik (PRD 13b) |
| `created_at` (umur akun) | ❌ **Tidak Tersedia** | — | **Gap Kritis:** tanggal pembuatan akun tidak ada di dataset |
| `post_timestamp` | ✅ Tersedia | `created_at` di `mbg_tweets_master_clean.csv` & `indobert_9_emosi_fixed.csv` | Siap untuk analisis interval & entropi waktu |
| `post_frequency` | ✅ Dapat Dihitung | Turunan dari `author_username` + `created_at` | Dapat dihitung per akun pada `indobert_9_emosi_fixed.csv` |
| `average_post_interval` | ✅ Dapat Dihitung | Turunan dari selisih `created_at` per akun | Memerlukan minimal $\ge 2$ posting per akun |
| `content_similarity` | ✅ Dapat Dihitung | `text` / `clean_text` di semua korpus | Siap untuk MinHash (`datasketch`) & IndoBERT embedding |
| `duplicate_ratio` | ✅ Dapat Dihitung | `text` di `indobert_9_emosi_fixed.csv` (1.349 duplikat) | Tersedia secara langsung |
| `hashtag_frequency` | ✅ Dapat Diekstrak | Regex `#\w+` pada kolom `text` | Tersedia di teks mentah |
| `URL_frequency` | ✅ Dapat Diekstrak | Regex `https?://\S+` pada kolom `text` | Tersedia di teks mentah (`text`), hilang di `clean_text` |
| `repost_ratio` | ⚠️ Parsial | `retweet_count` adalah jumlah RT yang *diterima*, bukan tipe apakah tweet itu RT | Perlu cek prefix `RT @` pada `text` atau tipe edge di NodeXL |
| `follower_count` | ❌ **Tidak Tersedia** | — | **Gap Kritis:** metadata profil akun tidak terkumpul |
| `following_count` | ❌ **Tidak Tersedia** | — | **Gap Kritis:** metadata profil akun tidak terkumpul |
| `engagement_rate` | ✅ Dapat Dihitung | `like_count`, `retweet_count`, `reply_count`, `quote_count`, `view_count` | Lengkap pada `mbg_tweets_master_clean.csv` & `indobert_9_emosi_fixed.csv` |
| `interaction_network` | ✅ Tersedia | `data/sna/network_edges.csv` (692 edges) & `actor_centrality_typology.csv` (971 nodes) | Siap pakai untuk graf mention/reply |
| `temporal_activity` | ✅ Tersedia | `reports/anomaly_events.csv` (83 hari) & timestamp posting | Tersedia |
| `bot_label` | ❌ **Tidak Tersedia** | — | **Gap Utama:** tidak ada ground truth bot/human |

---

## 2. Kesimpulan Kecukupan Dataset
- **Cukup untuk:** Deteksi anomali perilaku *unsupervised*, deteksi kemiripan teks/koordinasi, dan analisis topologi jaringan aktor (`Layer 2, 3, 4`).
- **Belum cukup untuk:** Klasifikasi *supervised* bot vs human secara langsung karena **ketiadaan `bot_label`**, **`follower_count`/`following_count`**, dan **`account_created_at`**.
- **Tindakan Wajib:** (1) Lakukan pelabelan manual 300–500 akun oleh 2 coder ($\kappa \ge 0.70$), dan (2) lengkapi metadata profil akun pada pengumpulan data berikutnya.
