<p align="center">
  <img src="assets/hero_3d_material3.svg" width="100%" alt="Pendeteksi Bot & Jaringan Terkoordinasi 3D Hero" />
</p>

<p align="center">
  <a href="https://github.com/digimetateam-hash/BOT-DETECTOR/stargazers"><img src="https://img.shields.io/github/stars/digimetateam-hash/BOT-DETECTOR?style=for-the-badge&color=0061A4&logo=github" alt="Stars" /></a>
  <a href="https://github.com/digimetateam-hash/BOT-DETECTOR/network/members"><img src="https://img.shields.io/github/forks/digimetateam-hash/BOT-DETECTOR?style=for-the-badge&color=3873C4&logo=github" alt="Forks" /></a>
  <a href="https://streamlit.io"><img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white" alt="Streamlit" /></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.11" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-4ECCA3?style=for-the-badge" alt="License" /></a>
</p>

<h1 align="center">🛡️ Social Media Bot & CIB Network Detector</h1>

<p align="center">
  <strong>Aplikasi Deteksi Akun Bot dan Perilaku Tidak Autentik Terkoordinasi (Coordinated Inauthentic Behavior) di Media Sosial X (Twitter).</strong><br>
  Dirancang dengan pendekatan <em>Explainable AI</em> (SHAP) dan <em>Graf Koordinasi Multiplex</em> berbasis bahasa Indonesia.
</p>

---

## ✨ Fitur Utama (Material Design 3 Architecture)

<table>
  <tr>
    <td width="50%">
      <h3>🔍 1. Lapisan Fitur Profil & Aktivitas</h3>
      <ul>
        <li>Deteksi rasio Following/Follower yang timpang.</li>
        <li>Analisis entropi jam aktif 24 jam & keteraturan burstiness.</li>
        <li>Identifikasi pola akun baru dengan bio kosong dan avatar default.</li>
      </ul>
    </td>
    <td width="50%">
      <h3>📝 2. Deteksi Konten & Teks Kembar</h3>
      <ul>
        <li>Algoritma <strong>MinHash & LSH</strong> untuk copy-paste template.</li>
        <li>Embedding semantik IndoBERT untuk mengantisipasi parafrase AI.</li>
        <li>Filter teks Indonesia (penanganan slang, plesetan, dan hashtag).</li>
      </ul>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h3>🕸️ 3. Graf Koordinasi Multiplex</h3>
      <ul>
        <li>Co-Retweet dalam jendela waktu sempit (&le; 60 detik).</li>
        <li>Deteksi komunitas algoritma <strong>Leiden / Louvain</strong>.</li>
        <li>Klasifikasi peran akun: <em>Akun Inti</em> vs <em>Akun Pengamplifikasi</em>.</li>
      </ul>
    </td>
    <td width="50%">
      <h3>📊 4. Explainable AI & Etika Privasi</h3>
      <ul>
        <li><strong>Top-5 SHAP Attribution</strong>: alasan transparan di setiap skor.</li>
        <li><strong>Kepatuhan Privasi</strong>: Username asli di-hash kriptografis SHA-256 + secret salt.</li>
        <li>Output menggunakan istilah <em>"perilaku mirip bot"</em>, bukan vonis mutlak.</li>
      </ul>
    </td>
  </tr>
</table>

---

## 🚀 Panduan Memulai Cepat

### 1. Kloning Repositori & Masuk Direktori
```bash
git clone https://github.com/digimetateam-hash/BOT-DETECTOR.git
cd BOT-DETECTOR
```

### 2. Buat & Aktifkan Virtual Environment (Python 3.11)
```bash
python3.11 -m venv .venv
source .venv/bin/activate  # Untuk Linux/macOS
# .venv\Scripts\activate   # Untuk Windows
```

### 3. Instal Dependensi
```bash
pip install -r requirements.txt
```

### 4. Konfigurasi Lingkungan (`.env`)
Salin berkas template dan atur secret salt:
```bash
cp .env.example .env
```

### 5. Jalankan Dashboard Streamlit
```bash
streamlit run streamlit_app.py
```
Akses dashboard di browser Anda: `http://localhost:8501`

---

## 📂 Struktur Proyek

```text
├── assets/                  # Aset visual 3D & Material Design 3
│   └── hero_3d_material3.svg
├── app/                     # Antarmuka Dashboard Streamlit
│   └── main.py              # 7 Layar evaluasi UI/UX sesuai PRD
├── pipeline/
│   ├── ingest/              # Parser data NodeXL (XLSX) & CSV
│   ├── features/            # Ekstraksi fitur profil, aktivitas, MinHash
│   ├── models/              # Engine skoring model & kalkulasi SHAP
│   └── network/             # Graf multiplex & deteksi komunitas
├── db/                      # Skema SQLAlchemy 11 tabel & hashing privasi
├── tests/                   # Unit testing pytest & data dummy
├── config.yaml              # Konfigurasi ambang batas deteksi (R-D1 s.d R-D9)
├── requirements.txt         # Daftar pustaka Python teruji
├── streamlit_app.py         # Entry point utama Streamlit Cloud
└── AGENTS.md                # Panduan pengembangan & aturan AI coding agent
```

---

## 📜 Kepatuhan Aturan Bisnis & Etika (PRD 13b)
1. **Anonimitas**: Username pengguna tidak pernah disimpan atau ditampilkan secara mentah; sistem selalu memakai `handle_hash`.
2. **Keterjelasan (XAI)**: Setiap akun berisiko memiliki grafik kontribusi fitur pemicu agar peneliti atau jurnalis dapat memverifikasi faktanya.
3. **Validasi Ground Truth**: Dilengkapi antarmuka validasi manual ganda dengan kalkulasi kesepakatan *Cohen's Kappa* ($\kappa \ge 0.70$).

---

<p align="center">
  Dibuat dengan ❤️ untuk Riset Analisis Wacana & Kebijakan Publik Indonesia.
</p>
