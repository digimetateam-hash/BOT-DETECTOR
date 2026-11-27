# 8. DASHBOARD SPECIFICATION — Spesifikasi UI/UX `TOPENG`

**Basis:** Penyelarasan PRD Bagian 14a (`app/main.py`) dengan 13 kebutuhan fitur Phase 8.

---

## 1. Prinsip Desain & Etika Tampilan
- **Pemisahan Tiga Sinyal:** Dashboard **wajib memisahkan secara visual** antara:
  1. **Bot Probability / Confidence Score** (0.00–1.00, hanya jika model terlatih & jumlah post $\ge 5$).
  2. **Behavioral Anomaly Score** (skor *unsupervised* dari Isolation Forest / Z-score).
  3. **Coordinated Activity Evidence** (keanggotaan klaster graf multiplex $\ge 2$ lapisan).
- **Larangan Vonis Tunggal:** UI tidak boleh melabeli akun sebagai "bot" hanya berdasarkan satu indikator (misalnya frekuensi tinggi atau sentimen negatif).

---

## 2. Pemetaan 13 Fitur Dashboard ke Layar `app/main.py`

| # | Fitur Wajib (Phase 8) | Layar Target di `app/main.py` | Komponen Visualisasi |
| :---: | :--- | :--- | :--- |
| 1 | Total akun dianalisis | Layar 2: Ringkasan Isu | KPI Card `Total Akun Dinilai` |
| 2 | Jumlah akun terindikasi bot | Layar 2: Ringkasan Isu | KPI Card `Perilaku Mirip Bot` + persentase |
| 3 | Jumlah akun terindikasi human | Layar 2: Ringkasan Isu | KPI Card & Pie/Donut Chart `Organik` |
| 4 | Jumlah akun mencurigakan | Layar 2: Ringkasan Isu | KPI Card `Akun Mencurigakan` |
| 5 | Bot probability / confidence score | Layar 3 & Layar 4 | Tabel berurutan + Bar Chart Top-5 SHAP |
| 6 | Behavioral anomaly score | Layar 3 & Layar 4 *(Penambahan)* | Kolom `Anomaly Score` & badge `Outlier` |
| 7 | Network visualization | Layar 5: Peta Klaster Koordinasi | Graf interaktif Plotly (`Inti` vs `Pengamplifikasi`) |
| 8 | Community detection | Layar 5: Peta Klaster Koordinasi | Dropdown Klaster Leiden/Louvain + metrik Modularity & Densitas |
| 9 | Temporal activity chart | Layar 2 & Layar 4 | Line chart volume per jam + highlight *spike* Z-Score $\ge 2.0$ |
| 10 | Content similarity | Layar 5 & Tab Duplikasi *(Penambahan)* | Tabel pasangan teks kembar MinHash ($\ge 0.85$) & kosinus |
| 11 | Coordinated activity detection | Layar 5: Peta Klaster Koordinasi | Indikator lapisan aktif (`co-retweet`, `co-hashtag`, `co-URL`, `teks`) |
| 12 | Model performance | Layar 6 & Tab Evaluasi *(Penambahan)* | Metrik Cohen's $\kappa$, F1, PR-AUC, Confusion Matrix (saat label tersedia) |
| 13 | Export hasil analisis CSV & Excel | Layar 7: Laporan & Ekspor | Tombol `Unduh CSV` dan `Unduh Excel (.xlsx)` (teranonimkan) |
