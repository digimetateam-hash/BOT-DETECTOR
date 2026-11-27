# 9. SCIENTIFIC VALIDATION PLAN — Rencana Validasi Ilmiah

Mengacu pada temuan audit `ThisIsEconomy` (adanya 1.349 duplikat teks pada korpus emosi dan ketiadaan label bot/human) serta standar publikasi *Computational Social Science*.

---

## 1. Delapan Pilar Validasi Ilmiah

1. **Data Provenance:** Setiap dataset yang masuk dicatat sumber, tanggal pengambilan, dan versi transformasinya di tabel `korpus` (`db/schema.py`).
2. **Reproducibility:** Setiap eksekusi model mencatat `seed` tetap (mis. `42`), versi model, dan parameter JSON di tabel `run_model`.
3. **Train-Test Separation (Anti-Leakage):** Wajib menggunakan `GroupShuffleSplit` berdasarkan `handle_hash` (level akun) dan `clean_text` (mencegah teks copy-paste yang sama muncul di train dan test).
4. **Ablation Study:** Evaluasi kontribusi masing-masing lapisan secara terpisah dan gabungan:
   - *Layer 1 saja* (Profil & Aktivitas) vs *Layer 2* (Konten) vs *Layer 3* (Jaringan) vs *Hybrid (All Layers)*.
5. **Baseline Comparison:** Bandingkan model utama (`LightGBM`) terhadap baseline sederhana dari `ThisIsEconomy` (`TF-IDF + LogisticRegression`, `TF-IDF + LinearSVC`) dan baseline unsupervised (`IsolationForest`).
6. **Statistical Significance Testing:** Gunakan **McNemar's test** atau **Bootstrap 95% Confidence Interval** (seperti pada `ThisIsEconomy/results/mcnemar_results.csv` dan `ci_bootstrap_results.csv`) untuk membuktikan peningkatan F1/PR-AUC signifikan ($p < 0.05$).
7. **Error Analysis:** Audit manual terhadap sampel *False Positive* dan *False Negative* oleh 2 coder independen.
8. **External Validation:** Uji generalisasi lintas-isu (latih pada korpus MBG, uji pada korpus isu non-politik dan korpus kontrol fandom).

---

## 2. Identifikasi Potensi Bias & Mitigasi

| Jenis Bias | Sumber Masalah | Strategi Mitigasi |
| :--- | :--- | :--- |
| **False Positive (Fandom / Aktivis)** | Fans K-Pop atau aktivis bergerak serempak dengan hashtag yang sama | Terapkan aturan mitigasi R-D8: cek median umur akun ($>2$ tahun) dan resiprositas dialog tinggi |
| **False Positive (Akun Berita)** | Akun media massa memposting sangat sering dengan URL | Jangan klasifikasikan akun sebagai bot hanya dari frekuensi posting tinggi |
| **False Negative (LLM-Paraphrased Bot)** | Bot modern memparafrase teks dengan LLM sehingga lolos dari MinHash | Gunakan sinyal jaringan (co-retweet $\le 60$ detik) & embedding semantik IndoBERT |
| **Data Platform Tidak Lengkap** | Hilangnya 63,24% `author_username` di `mbg_tweets_master_clean.csv` | Pisahkan analisis level-posting vs level-akun; akun dengan $<5$ post ditandai `kurang_data` (R-D2) |
| **Perbedaan Pola Antarplatform** | Pola interaksi X (retweet/quote) berbeda dengan TikTok/Instagram | Gunakan adapter ingest per platform dan kalibrasi ulang ambang batas di `config.yaml` |
