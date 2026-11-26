# PRD — Aplikasi Pendeteksi Bot Media Sosial

Nov 25, 2026 · @Indri

Aplikasi ini mendeteksi akun bot dan perilaku tidak autentik terkoordinasi (coordinated inauthentic behavior, CIB) di X, lalu memberi skor yang bisa dijelaskan, bukan vonis. Target awal: percakapan kebijakan publik berbahasa Indonesia, misalnya isu MBG.

## 1. Latar belakang & problem statement

**Masalah.** Analisis wacana media sosial di Indonesia jarang memisahkan suara warga dari akun otomatis atau akun yang digerakkan bersama. Akibatnya, volume isu, sentimen, dan aktor sentral bisa terdistorsi oleh buzzer.

- Alat deteksi bot paling terkenal, Botometer, kini dalam mode arsip: Botometer X hanya memakai skor yang dihitung dari data sebelum Juni 2023, jadi tidak bisa menilai akun baru ([OSoMe](https://osome.iu.edu/research/blog/introducing-botometer-x)).
- Akses data X sejak 2023 berbayar per pemakaian, sehingga detektor yang mengandalkan API gratis berhenti bekerja ([Sorsa](https://api.sorsa.io/blog/twitter-bot-detection)).
- Model bahasa umum tidak dilatih untuk pola buzzer Indonesia: singkatan, plesetan, dan template copy-paste.

**Kenapa dibuat.**

1. Menyediakan detektor yang bekerja pada data yang sudah dikumpulkan sendiri (NodeXL, CSV, ekspor scraper), tanpa bergantung pada satu API.
2. Membersihkan korpus riset sebelum analisis sentimen dan jaringan, agar temuan tesis dan artikel lebih kuat.
3. Mendeteksi kampanye terkoordinasi di level jaringan, bukan hanya akun tunggal.
4. Menghasilkan artefak yang bisa dipublikasikan: dataset berlabel bahasa Indonesia dan metode yang dapat direplikasi.

**Open question:** baseline proporsi akun mencurigakan di korpus sendiri belum diukur; ini menjadi langkah pertama Fase 1.

## 2. Goals & success metrics

Target angka di bawah adalah usulan awal; sesuaikan setelah baseline Fase 1.

| Goal | Metric | Target |
| --- | --- | --- |
| Akurasi deteksi akun bot | F1 pada data uji berlabel manusia | ≥ 0,80 |
| Kesepakatan label manusia | Cohen's κ antar dua coder | ≥ 0,70 |
| Deteksi kampanye terkoordinasi | Precision klaster CIB yang dicek manual | ≥ 0,75 |
| Kecepatan analisis | Waktu proses 10.000 posting | < 5 menit |
| Keterjelasan | Setiap skor punya alasan (fitur pemicu) | 100% akun |
| Dampak riset | Korpus bersih dipakai di artikel | ≥ 1 artikel Scopus |

## 3. Target users & personas

- **Peneliti komunikasi / data scientist:** butuh korpus yang bersih dari bot sebelum analisis sentimen dan jaringan, plus skor yang bisa dilaporkan di bagian metode.
- **Analis isu / humas instansi:** butuh peringatan dini bila sebuah isu didorong akun terkoordinasi, bukan warga organik.
- **Jurnalis & pemeriksa fakta:** butuh bukti visual (klaster, pola waktu, teks kembar) untuk memverifikasi dugaan buzzer.
- **Admin sistem (Anda):** butuh pipeline murah, bisa jalan di laptop atau VPS kecil, dan mudah diperbarui.

## 4. Functional requirements (MoSCoW)

**Must have**

- Impor data dari CSV/XLSX hasil NodeXL, scraper, atau API (kolom minimal: user, waktu, teks, tipe interaksi).
- Skor bot per akun (0–1) dari fitur profil, aktivitas, dan konten, dengan daftar fitur pemicu.
- Deteksi teks kembar / hampir kembar antar akun (copy-paste template).
- Deteksi koordinasi: akun yang memposting atau me-retweet hal sama dalam jendela waktu sempit.
- Dashboard: daftar akun berisiko, klaster terkoordinasi, grafik waktu posting.
- Ekspor hasil (CSV) untuk dipakai di analisis lanjutan.
- Validasi manual: antarmuka untuk memberi label human/bot/ragu pada sampel.

**Should have**

- Visualisasi jaringan koordinasi (graf akun–akun).
- Klasifikasi gaya teks dengan model bahasa Indonesia (IndoBERT) atau LLM sebagai fitur tambahan.
- Laporan PDF per isu: ringkasan, klaster, contoh posting.

**Could have**

- Notifikasi Telegram bila klaster CIB baru muncul.
- Dukungan platform lain (TikTok, Instagram, YouTube comments).
- Active learning: label manual baru memperbaiki model otomatis.

**Won't have (fase awal)**

- Pelabelan publik "akun X adalah bot" atau doxing pemilik akun.
- Pelaporan otomatis ke platform.

## 5. Non-functional requirements

| Kategori | Requirement |
| --- | --- |
| Privasi | Handle disamarkan (hash) di laporan publik; data mentah disimpan terenkripsi |
| Explainability | Setiap skor menampilkan 3–5 fitur penyumbang terbesar |
| Performa | 10.000 posting diproses < 5 menit di laptop 8 GB RAM |
| Reprodusibilitas | Versi model, parameter, dan seed tercatat di setiap laporan |
| Biaya | Bisa jalan tanpa API berbayar; LLM opsional dan dibatasi kuota |
| Keandalan | False positive pada akun manusia aktif ditekan; ambang batas bisa diatur |
| Etika | Hasil disebut "perilaku mirip bot", bukan tuduhan |

## 6. Arsitektur & alur kerja

&#91;embedded content: arsitektur pendeteksi bot · 4 lapisan sinyal, 1 loop validasi\]

Data masuk lewat file atau API, dibersihkan, lalu dinilai oleh empat lapisan sinyal secara paralel. Lapisan jaringan multiplex menjadi pembeda utama (lihat bagian 11). Label dari validasi manual dipakai untuk melatih ulang model.

## 7. Metode deteksi

Skor akhir menggabungkan empat kelompok sinyal. Kekuatan utamanya ada di lapisan jaringan: satu akun bisa tampak normal, tetapi 50 akun yang bergerak serempak tidak.

| Lapisan | Contoh fitur | Teknik |
| --- | --- | --- |
| Profil | Umur akun, rasio following/follower, foto default, bio kosong, username berpola angka acak | Aturan + gradient boosting (XGBoost/LightGBM) |
| Aktivitas | Posting per hari, proporsi retweet, jam aktif 24 jam, jeda antar-posting yang terlalu teratur | Statistik waktu (entropi, burstiness) |
| Konten | Teks kembar/hampir kembar, hashtag template, link sama, gaya bahasa seragam | MinHash/SimHash, embedding IndoBERT, LLM opsional |
| Jaringan | Co-retweet dan co-hashtag dalam jendela waktu sempit, klaster padat yang terisolasi | Graf koordinasi + deteksi komunitas (Louvain/Leiden) |

**Data latih.** Mulai dari label manual 300–500 akun oleh dua coder (ukur κ), ditambah dataset publik berbahasa Inggris (misalnya TwiBot) hanya sebagai pembanding, bukan acuan utama.

**Keluaran per akun:** skor 0–1, kategori (organik / mencurigakan / sangat mirip bot), fitur pemicu, dan klaster koordinasi bila ada.

## 8. Tools & stack

| Kebutuhan | Pilihan |
| --- | --- |
| Pengumpulan data | NodeXL Pro, X API berbayar, atau penyedia API pihak ketiga; impor CSV manual |
| Bahasa & olah data | Python 3.11, pandas, polars |
| Model | scikit-learn, LightGBM/XGBoost, SHAP untuk penjelasan |
| NLP Indonesia | IndoBERT (Hugging Face), datasketch (MinHash) |
| Jaringan | NetworkX, python-igraph / leidenalg |
| LLM opsional | Claude API untuk menilai gaya teks dan merangkum klaster |
| Penyimpanan | SQLite/PostgreSQL; dataset berlabel di Hugging Face |
| Antarmuka | Streamlit (cepat untuk prototipe dan demo juri) |
| Notifikasi | Bot Telegram |
| Deploy | Docker + Streamlit Cloud atau VPS; GitHub Actions untuk tes |
| Pembanding | Botometer X via RapidAPI, hanya untuk akun lama (data < Juni 2023) |

### 8a. Library yang perlu diinstal

**Node.js tidak wajib.** Seluruh aplikasi (olah data, model, dashboard Streamlit, bot Telegram) berjalan di Python. Node.js baru dibutuhkan bila nanti antarmuka diganti ke Next.js/React atau memakai tooling JavaScript lain.

**Perangkat dasar**

| Software | Fungsi | Wajib? |
| --- | --- | --- |
| Python 3.11 | Bahasa utama | Ya |
| pip + venv (atau uv) | Instal library, lingkungan terisolasi | Ya |
| Git | Versi kode, push ke GitHub | Ya |
| Docker | Deploy ke VPS secara konsisten | Untuk deploy |
| NodeXL Pro (Excel, Windows) | Ambil data X | Bila pakai NodeXL |
| Node.js 20+ | Frontend JS alternatif | Tidak |

**Library Python per fungsi**

| Fungsi | Library |
| --- | --- |
| Baca/olah data | pandas, polars, numpy, openpyxl (baca XLSX NodeXL), pyarrow |
| Pembersihan teks | regex, emoji, Sastrawi (stemming bahasa Indonesia), unidecode |
| Machine learning | scikit-learn, lightgbm, xgboost, imbalanced-learn |
| Penjelasan model | shap |
| NLP bahasa Indonesia | transformers, torch, sentence-transformers (embedding IndoBERT), tokenizers |
| Teks kembar | datasketch (MinHash/LSH), rapidfuzz |
| Jaringan | networkx, python-igraph, leidenalg |
| Statistik waktu | scipy, statsmodels |
| Reliabilitas label | scikit-learn (cohen\_kappa\_score), krippendorff |
| LLM opsional | anthropic |
| Dashboard | streamlit, plotly, pyvis (graf interaktif) |
| Laporan | reportlab atau weasyprint (PDF), jinja2 |
| Database | sqlalchemy, psycopg2-binary (PostgreSQL); sqlite3 sudah bawaan Python |
| Notifikasi | python-telegram-bot |
| Rahasia/konfigurasi | python-dotenv |
| Dataset publik | datasets, huggingface\_hub |
| Testing & kualitas kode | pytest, ruff |

**Isi requirements.txt (tanpa versi, kunci versi setelah instal pertama dengan `pip freeze`)**

```text
pandas
polars
numpy
openpyxl
pyarrow
emoji
Sastrawi
unidecode
scikit-learn
lightgbm
xgboost
imbalanced-learn
shap
transformers
torch
sentence-transformers
datasketch
rapidfuzz
networkx
python-igraph
leidenalg
scipy
statsmodels
krippendorff
anthropic
streamlit
plotly
pyvis
reportlab
jinja2
sqlalchemy
psycopg2-binary
python-telegram-bot
python-dotenv
datasets
huggingface_hub
pytest
ruff
```

Catatan instalasi: torch berukuran besar; di laptop tanpa GPU pakai build CPU. Bila laptop terbatas, tahap awal cukup tanpa transformers/torch/sentence-transformers (fitur profil, aktivitas, MinHash, dan jaringan sudah jalan), lalu tambahkan IndoBERT di Fase 3.

## 9. Step-by-step implementasi

1. **Fase 1 — Data & baseline (minggu 1–2):** kumpulkan 2–3 korpus isu (misal MBG, satu isu non-politik sebagai kontrol, satu isu fandom). Sampel 500 akun, dua coder memberi label, hitung κ.
2. **Fase 2 — Fitur akun (minggu 3–4):** bangun fitur profil dan aktivitas; latih LightGBM; ukur F1; tambahkan SHAP untuk penjelasan.
3. **Fase 3 — Konten (minggu 5–6):** MinHash untuk teks kembar; embedding IndoBERT untuk kemiripan semantik; uji ketahanan terhadap parafrase LLM.
4. **Fase 4 — Jaringan koordinasi (minggu 7–8):** graf multiplex (co-retweet, co-hashtag, co-URL, kemiripan teks cepat); deteksi komunitas; validasi klaster manual.
5. **Fase 5 — Aplikasi (minggu 9–10):** Streamlit: unggah data → skor → dashboard → ekspor; notifikasi Telegram.
6. **Fase 6 — Evaluasi & publikasi (minggu 11–14):** uji pada korpus baru yang belum pernah dilihat model; tulis artikel; rilis dataset berlabel (anonim) di Hugging Face dan kode di GitHub.

## 10. Risiko & mitigasi

| Risiko | Mitigasi |
| --- | --- |
| Akun aktivis atau fandom dianggap bot (false positive) | Korpus kontrol fandom; ambang konservatif; label "mirip bot", bukan vonis |
| Bot berbasis LLM lolos dari fitur teks klasik | Fitur jaringan dan waktu sebagai sinyal utama; uji parafrase LLM |
| Label manual subjektif | Dua coder, pedoman coding tertulis, laporkan κ |
| Akses data X mahal atau berubah | Arsitektur berbasis impor file; tidak terikat satu API |
| Risiko hukum (UU ITE) dan etika | Tidak menyebut nama akun pribadi di publikasi; handle di-hash; fokus pada pola |
| Model usang karena taktik buzzer berubah | Evaluasi ulang per isu; active learning dari label baru |

## 11. Research gap & novelty

Novelty terkuat ada pada kombinasi, bukan satu algoritma: deteksi koordinasi multiplex yang tahan parafrase LLM, untuk bahasa Indonesia, divalidasi dengan ground truth eksternal, dan dikontrol terhadap aksi kolektif organik seperti fandom. Klaim "belum pernah ada" wajib dicek ulang lewat pencarian sistematis Scopus/WoS sebelum ditulis di naskah.

**Peta literatur saat ini**

| Arus riset | Yang sudah ada | Celahnya |
| --- | --- | --- |
| Deteksi buzzer Indonesia | Klasifikasi per akun dengan SVM dan seleksi fitur ([Jurnal RESTI](https://garuda.kemdiktisaintek.go.id/documents/detail/2996576); [JOSI Unand](https://josi.ft.unand.ac.id/index.php/josi/article/download/718/285/3314)), DNN-PSO ([INISTA](https://journal.ittelkom-pwt.ac.id/index.php/inista/article/view/1622)), ResNet ([tesis UGM 2025](https://etd.repository.ugm.ac.id/home/detail_pencarian_downloadfiles/1539531)), SNA sebagai fitur ([skripsi UPI 2024](https://repository.upi.edu/122920/)) | Unit analisis akun tunggal; fokus pemilu; belum menguji bot berbasis LLM; mayoritas jurnal nasional |
| Bot berbasis LLM (internasional) | Bot hasil LLM menurunkan kinerja detektor lama hingga 29,6% ([Feng et al.](https://arxiv.org/pdf/2402.00371v2.pdf)); detektor khusus LLM-bot seperti [TRACE-Bot](https://arxiv.org/abs/2604.02147) dan [BotDMM](https://openrepository.aut.ac.nz/bitstreams/c8173c93-a290-4145-9c9a-eabbf563cf09/download) | Dataset berbahasa Inggris/Mandarin; tidak ada benchmark bahasa Indonesia, termasuk slang dan campur kode |
| Deteksi koordinasi (CIB) | Kerangka jaringan koordinasi ([Pacheco et al.](https://arxiv.org/pdf/2001.05658.pdf)); co-tweet/co-retweet untuk astroturfing ([Schoch et al.](https://boris.unibe.ch/167650/1/s41598-022-08404-9.pdf)); jaringan multiplex ([arXiv 2507.12108](https://arxiv.org/html/2507.12108v3)) | Jarang dipakai di Asia Tenggara; ground truth biasanya dari rilis platform yang kini tidak tersedia; belum membedakan buzzer dari fandom |
| Arah riset yang diminta | Ferrara menyerukan agen generatif untuk data sintetis dan deteksi multimodal lintas platform ([arXiv 2610.02386](https://arxiv.org/pdf/2610.02386)) | Belum dijawab untuk konteks bahasa berdaya rendah (low-resource) |

**Lima kandidat novelty (urut dari yang paling kuat)**

1. **Benchmark buzzer LLM berbahasa Indonesia.** Bangun dataset sintetis: posting buzzer asli diparafrase oleh LLM (gaya slang, campur kode, plesetan akronim), lalu uji apakah detektor teks lama gagal dan detektor jaringan bertahan. Ini menjawab celah bahasa sekaligus celah LLM-bot.
2. **Koordinasi multiplex tahan parafrase.** Ganti "teks kembar" dengan kemiripan semantik IndoBERT dalam jendela waktu cepat, digabung co-retweet, co-hashtag, dan co-URL dalam satu graf multiplex. Ukur kontribusi tiap lapisan (ablation).
3. **Ground truth eksternal pengganti rilis platform.** Validasi klaster terkoordinasi dengan sumber independen: label hoaks Komdigi, cek fakta Mafindo/Cekfakta, dan kejadian resmi yang menyusul. Ini memperluas logika "corroboration ledger" dari artikel Grok–MBG.
4. **Kontrol aksi kolektif organik.** Uji false positive pada fandom dan aktivisme yang juga bergerak serempak; usulkan fitur pembeda (keragaman umur akun, interaksi dua arah, sejarah topik). Masalah tumpang-tindih akronim MBG dengan fandom di korpus tesis menjadi motivasi empiris.
5. **Modalitas baru: co-summoning AI oracle.** Akun yang serempak memanggil @grok pada posting yang sama sebagai bentuk koordinasi baru. Pencarian awal ini belum menemukan studi yang memperlakukannya sebagai sinyal koordinasi; data korpus MBG hanya memuat balasan Grok, jadi perlu pengumpulan data baru.

**Rekomendasi kombinasi untuk satu artikel:** kandidat 1 + 2 + 3 sebagai kontribusi inti (dataset, metode, validasi), kandidat 4 sebagai uji ketahanan. Kandidat 5 lebih cocok jadi artikel kedua.

**Judul terpilih:** *Human, Bot, or AI? Detecting Paraphrased Buzzer Networks in Indonesia's Free Meal (MBG) Debate on X*

Variasi dari usulan penulis (*Detecting Paraphrased Buzzer MBG Networks on X in Indonesia*): nama program ditulis lengkap dengan akronim di kurung agar dikenali pembaca internasional dan mesin pencari AI, dan tidak tertukar dengan pemakaian akronim MBG oleh fandom atau produk lain. Opsi lain dan hasil cek novelty ada di bagian 11a.

**Calon jurnal** (cek kuartil SJR terbaru sebelum submit): EPJ Data Science, Online Social Networks and Media, Information Processing & Management, Social Network Analysis and Mining, Journal of Computational Social Science.

**Langkah verifikasi gap sebelum menulis:**

- [ ] Query Scopus: (bot OR buzzer OR "coordinated inauthentic") AND (Indonesia\* OR "low-resource") AND (LLM OR "large language model")
- [ ] Query kedua: "coordination detection" AND (paraphrase OR semantic) AND multiplex
- [ ] Catat jumlah hasil dan 10 artikel terdekat ke tabel perbandingan untuk bagian Related Work

### 11a. Cek novelty terbaru (25 Nov 2026) dan opsi judul

**Hasil cek: dua klaim harus direvisi, tiga masih kuat.** Pencarian web cepat ini belum menggantikan pencarian sistematis Scopus.

| Klaim | Status | Bukti terdekat |
| --- | --- | --- |
| Graf koordinasi multiplex | **Sudah ada, bukan novelty.** Posisikan sebagai metode yang dipakai dan dikembangkan | Model multiplex time-aware dengan Leiden, diuji pada 26 dataset berlabel ([Iannucci et al., ICWSM 2026](https://ojs.aaai.org/index.php/ICWSM/article/view/42682)); perbandingan strategi multimodal ([arXiv 2507.12108](https://arxiv.org/html/2507.12108v3)) |
| Deteksi koordinasi tahan parafrase AI | **Sebagian sudah ada** untuk bahasa lain: data sintetis ChatGPT/DeepL untuk copy-pasta ([arXiv 2312.17338](https://arxiv.org/html/2312.17338v1)), digital twin Telegram untuk operasi informasi berbasis LLM ([TeleTwin](https://arxiv.org/pdf/2610.23944)) | Novelty bergeser ke **bahasa Indonesia, slang, campur kode, plesetan akronim** |
| Akun palsu terkoordinasi di Indonesia | **Sudah ada studi bereputasi**, tetapi tanpa detektor dan tanpa uji LLM: 8.102 posting dari 100 akun palsu di X dan Instagram ([Comunicar 2026](https://www.revistacomunicar.com/ojs/index.php/comunicar/article/download/116613/5249/30579)); koordinasi pada 100 hari pemerintahan Prabowo ([IJSECS 2026](https://journal.lembagakita.com/ijsecs/article/download/7524/5042/29625)) | Wajib dikutip dan dibedakan: mereka menganalisis akun yang sudah diketahui palsu, kita **mendeteksi** dari data mentah |
| Benchmark parafrase LLM bahasa Indonesia | **Belum ditemukan** | Kontribusi utama |
| Ground truth eksternal (Komdigi, cek fakta) + kontrol fandom pada isu kebijakan non-pemilu | **Belum ditemukan** sebagai kombinasi | Kontribusi pendukung |

**Hook empiris yang kuat untuk pendahuluan:** Maret 2026, Kepala Produk X menyelidiki satu orang yang menjalankan 30 akun dari IP Indonesia; dugaan awalnya AI, ternyata manusia ([detikInet](https://inet.detik.com/cyberlife/d-8418959/mengejutkan-bos-x-kaget-ai-ternyata-asli-indonesia)). Kasus ini menunjukkan bahwa membedakan buzzer manusia, bot, dan AI adalah masalah nyata yang lolos dari sistem X sendiri.

**Opsi judul** (hook sebelum titik dua, presisi sesudahnya; entitas kunci di depan agar mudah dikutip mesin pencari AI)

| # | Judul | Gaya | Catatan |
| --- | --- | --- | --- |
| 1 | **When Buzzers Learn to Paraphrase: Detecting LLM-Assisted Coordinated Inauthentic Behaviour on Indonesian X** | Hook naratif | **Rekomendasi utama.** Jelas, ada "tegangan", entitas lengkap |
| 2 | Human, Bot, or AI? Detecting Paraphrased Buzzer Networks on X in Indonesia | Pertanyaan | Paling GEO-friendly (berbentuk pertanyaan yang dijawab paper); selaras dengan hook kasus 30 akun |
| 3 | Same Message, Different Words: A Paraphrase-Robust Benchmark for Coordinated Account Detection in Indonesian | Kontras | Cocok bila fokus utama adalah rilis dataset/benchmark |
| 4 | Bot, Buzzer, or Fan? Separating Coordinated Inauthentic Behaviour from Organic Collective Action in Indonesia's Free Meal Debate | Pertanyaan + kasus | Menonjolkan kontrol fandom dan studi kasus MBG |
| 5 | Beyond Copy-Paste: Network Signals Expose AI-Paraphrased Influence Campaigns in a Low-Resource Language | Klaim temuan | Kuat bila hasil membuktikan lapisan jaringan bertahan saat teks diparafrase |

**Prinsip GEO (Generative Engine Optimization) untuk naskah:**

- Entitas eksplisit di judul dan kalimat pertama abstrak: *Indonesia, X (Twitter), buzzer, large language model, coordinated inauthentic behaviour*.
- Kalimat pertama abstrak berupa klaim yang bisa dikutip langsung, dengan angka (misal: "Parafrase LLM menurunkan F1 detektor teks sebesar X poin, sedangkan detektor jaringan hanya Y poin").
- Definisi istilah *buzzer* dalam satu kalimat mandiri di pendahuluan, karena istilah ini khas Indonesia.
- Kata kunci mencakup sinonim yang dipakai orang saat bertanya ke AI: *social bot detection, astroturfing, influence operations, AI-generated text*.
- Judul hindari klik-bait berlebihan ("shocking", "secret"); editor jurnal bereputasi menolak judul yang menjanjikan lebih dari temuannya.

**Cek judul:** penelusuran web atas frasa kunci kelima judul di atas belum menemukan judul yang sama. Sebelum submit, cek ulang judul pilihan di Google Scholar dan Scopus dengan tanda kutip.

## 12. ERD database

Database memakai 11 tabel. Tabel akun menjadi pusat: posting, interaksi, skor, label manual, dan keanggotaan klaster semuanya mengacu ke sana. Mulai dengan SQLite di laptop, lalu pindah ke PostgreSQL saat deploy (lewat SQLAlchemy, skemanya sama).

&#91;embedded content: ERD database · 11 tabel, akun sebagai pusat\]

Tiga keputusan desain penting untuk riset: **run\_model** menyimpan versi, parameter, dan seed agar setiap skor bisa direplikasi; **handle\_hash** menggantikan username asli demi privasi; **validasi\_eksternal** menyimpan bukti dari Komdigi dan cek fakta, yang menjadi ground truth eksternal untuk klaim novelty di bagian 11.

### 12a. Schema database (DDL)

Schema di bawah untuk PostgreSQL 14+ dan siap dijalankan berurutan. Untuk SQLite, ganti `BIGSERIAL` menjadi `INTEGER PRIMARY KEY AUTOINCREMENT`, `JSONB` menjadi `TEXT`, dan `TIMESTAMPTZ` menjadi `TEXT` (format ISO 8601).

```sql
-- 1. Korpus: satu kali pengambilan data untuk satu isu
CREATE TABLE korpus (
    id              BIGSERIAL PRIMARY KEY,
    nama_isu        VARCHAR(200) NOT NULL,
    query           TEXT         NOT NULL,
    sumber          VARCHAR(20)  NOT NULL
                    CHECK (sumber IN ('nodexl', 'api', 'csv', 'scraper')),
    tanggal_ambil   TIMESTAMPTZ  NOT NULL DEFAULT now(),
    periode_mulai   DATE         NOT NULL,
    periode_akhir   DATE         NOT NULL,
    CHECK (periode_akhir >= periode_mulai)
);

-- 2. Akun: handle asli tidak disimpan, hanya hash
CREATE TABLE akun (
    id              BIGSERIAL PRIMARY KEY,
    handle_hash     CHAR(64)     NOT NULL UNIQUE,   -- SHA-256 + salt
    platform        VARCHAR(20)  NOT NULL DEFAULT 'x',
    dibuat_pada     TIMESTAMPTZ,                    -- tanggal akun dibuat
    followers       INTEGER      CHECK (followers >= 0),
    following       INTEGER      CHECK (following >= 0),
    total_post      INTEGER      CHECK (total_post >= 0),
    avatar_default  BOOLEAN,
    bio_kosong      BOOLEAN,
    terverifikasi   BOOLEAN,
    diperbarui_pada TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- 3. Posting
CREATE TABLE posting (
    id              BIGSERIAL PRIMARY KEY,
    id_platform     VARCHAR(40)  NOT NULL,          -- ID posting asli di X
    korpus_id       BIGINT       NOT NULL REFERENCES korpus(id) ON DELETE CASCADE,
    akun_id         BIGINT       NOT NULL REFERENCES akun(id),
    parent_post_id  BIGINT       REFERENCES posting(id),
    tipe            VARCHAR(10)  NOT NULL
                    CHECK (tipe IN ('post', 'reply', 'retweet', 'quote')),
    waktu           TIMESTAMPTZ  NOT NULL,
    teks            TEXT,
    hashtags        TEXT[],
    url             TEXT[],
    UNIQUE (korpus_id, id_platform)
);

-- 4. Interaksi: edge list (mention, reply, retweet) dari NodeXL
CREATE TABLE interaksi (
    id              BIGSERIAL PRIMARY KEY,
    korpus_id       BIGINT       NOT NULL REFERENCES korpus(id) ON DELETE CASCADE,
    sumber_akun_id  BIGINT       NOT NULL REFERENCES akun(id),
    target_akun_id  BIGINT       NOT NULL REFERENCES akun(id),
    tipe            VARCHAR(10)  NOT NULL
                    CHECK (tipe IN ('mention', 'reply', 'retweet', 'quote')),
    waktu           TIMESTAMPTZ  NOT NULL
);

-- 5. Run model: syarat reprodusibilitas
CREATE TABLE run_model (
    id              BIGSERIAL PRIMARY KEY,
    versi_model     VARCHAR(50)  NOT NULL,
    parameter       JSONB        NOT NULL DEFAULT '{}'::jsonb,
    seed            INTEGER      NOT NULL,
    catatan         TEXT,
    dibuat_pada     TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- 6. Skor akun per run
CREATE TABLE skor_akun (
    id              BIGSERIAL PRIMARY KEY,
    run_id          BIGINT       NOT NULL REFERENCES run_model(id) ON DELETE CASCADE,
    akun_id         BIGINT       NOT NULL REFERENCES akun(id),
    korpus_id       BIGINT       NOT NULL REFERENCES korpus(id),
    skor            NUMERIC(5,4) NOT NULL CHECK (skor BETWEEN 0 AND 1),
    kategori        VARCHAR(20)  NOT NULL
                    CHECK (kategori IN ('organik', 'mencurigakan', 'mirip_bot')),
    fitur_pemicu    JSONB        NOT NULL DEFAULT '[]'::jsonb, -- top-5 SHAP
    UNIQUE (run_id, akun_id, korpus_id)
);

-- 7. Label manual dari coder (untuk data latih dan kappa)
CREATE TABLE label_manual (
    id              BIGSERIAL PRIMARY KEY,
    akun_id         BIGINT       NOT NULL REFERENCES akun(id),
    korpus_id       BIGINT       NOT NULL REFERENCES korpus(id),
    coder           VARCHAR(50)  NOT NULL,
    label           VARCHAR(10)  NOT NULL
                    CHECK (label IN ('manusia', 'bot', 'ragu')),
    catatan         TEXT,
    dibuat_pada     TIMESTAMPTZ  NOT NULL DEFAULT now(),
    UNIQUE (akun_id, korpus_id, coder)
);

-- 8. Klaster koordinasi hasil graf multiplex
CREATE TABLE klaster_koordinasi (
    id              BIGSERIAL PRIMARY KEY,
    run_id          BIGINT       NOT NULL REFERENCES run_model(id) ON DELETE CASCADE,
    korpus_id       BIGINT       NOT NULL REFERENCES korpus(id),
    lapisan         VARCHAR(20)  NOT NULL
                    CHECK (lapisan IN ('retweet', 'hashtag', 'url', 'teks', 'multiplex')),
    jumlah_akun     INTEGER      NOT NULL CHECK (jumlah_akun >= 2),
    densitas        NUMERIC(5,4) CHECK (densitas BETWEEN 0 AND 1),
    jendela_waktu   INTEGER      NOT NULL,          -- detik
    dibuat_pada     TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- 9. Relasi N:M akun <-> klaster
CREATE TABLE anggota_klaster (
    klaster_id      BIGINT       NOT NULL REFERENCES klaster_koordinasi(id) ON DELETE CASCADE,
    akun_id         BIGINT       NOT NULL REFERENCES akun(id),
    peran           VARCHAR(10)  CHECK (peran IN ('inti', 'pinggir')),
    PRIMARY KEY (klaster_id, akun_id)
);

-- 10. Validasi eksternal (ground truth: Komdigi, cek fakta)
CREATE TABLE validasi_eksternal (
    id              BIGSERIAL PRIMARY KEY,
    klaster_id      BIGINT       NOT NULL REFERENCES klaster_koordinasi(id) ON DELETE CASCADE,
    sumber          VARCHAR(30)  NOT NULL
                    CHECK (sumber IN ('komdigi', 'cekfakta', 'mafindo', 'media', 'resmi_lain')),
    url             TEXT         NOT NULL,
    status          VARCHAR(20)  NOT NULL
                    CHECK (status IN ('terkonfirmasi', 'dibantah', 'belum_jelas')),
    dicek_pada      TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- 11. Alert yang terkirim
CREATE TABLE alert (
    id              BIGSERIAL PRIMARY KEY,
    klaster_id      BIGINT       NOT NULL REFERENCES klaster_koordinasi(id) ON DELETE CASCADE,
    kanal           VARCHAR(20)  NOT NULL DEFAULT 'telegram',
    pesan           TEXT,
    dikirim_pada    TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- Index untuk query yang paling sering
CREATE INDEX idx_posting_korpus_waktu ON posting (korpus_id, waktu);
CREATE INDEX idx_posting_akun         ON posting (akun_id);
CREATE INDEX idx_posting_parent       ON posting (parent_post_id);
CREATE INDEX idx_posting_hashtags     ON posting USING GIN (hashtags);
CREATE INDEX idx_interaksi_sumber     ON interaksi (korpus_id, sumber_akun_id);
CREATE INDEX idx_interaksi_target     ON interaksi (korpus_id, target_akun_id);
CREATE INDEX idx_skor_kategori        ON skor_akun (run_id, kategori);
CREATE INDEX idx_anggota_akun         ON anggota_klaster (akun_id);
```

**Contoh query: 20 akun paling mirip bot pada run terbaru, beserta alasannya**

```sql
SELECT a.handle_hash, s.skor, s.kategori, s.fitur_pemicu
FROM skor_akun s
JOIN akun a ON a.id = s.akun_id
WHERE s.run_id = (SELECT max(id) FROM run_model)
ORDER BY s.skor DESC
LIMIT 20;
```

**Contoh query: pasangan akun co-retweet dalam jendela 60 detik (bahan graf koordinasi)**

```sql
SELECT p1.akun_id AS akun_a, p2.akun_id AS akun_b, count(*) AS bobot
FROM posting p1
JOIN posting p2
  ON p1.parent_post_id = p2.parent_post_id
 AND p1.akun_id < p2.akun_id
 AND abs(extract(epoch FROM p1.waktu - p2.waktu)) <= 60
WHERE p1.tipe = 'retweet' AND p2.tipe = 'retweet'
  AND p1.korpus_id = :korpus_id AND p2.korpus_id = :korpus_id
GROUP BY p1.akun_id, p2.akun_id
HAVING count(*) >= 3;
```

## 13. Rules

Aturan dibagi tiga: cara sistem memberi skor, aturan bisnis yang tidak boleh dilanggar, dan aturan pengembangan untuk Anda maupun AI coding agent. Semua ambang angka adalah nilai awal dan dikalibrasi ulang setelah label manual Fase 1.

### 13a. Rules deteksi dan skor

| Kode | Rule | Nilai awal |
| --- | --- | --- |
| R-D1 | Kategori dari skor: organik / mencurigakan / mirip\_bot | < 0,40 / 0,40–0,69 / ≥ 0,70 |
| R-D2 | Akun dengan < 5 posting di korpus tidak diberi kategori, hanya skor | min 5 posting |
| R-D3 | Pasangan akun dianggap co-retweet bila me-retweet posting sama dalam jendela waktu | ≤ 60 detik, ≥ 3 kali |
| R-D4 | Dua teks dianggap kembar bila kemiripan MinHash (Jaccard) melewati ambang | ≥ 0,85 |
| R-D5 | Dua teks dianggap parafrase bila kemiripan kosinus embedding IndoBERT melewati ambang dalam jendela waktu | ≥ 0,90, ≤ 10 menit |
| R-D6 | Klaster koordinasi minimal beranggotakan sejumlah akun | ≥ 5 akun |
| R-D7 | Klaster berlabel "tinggi" bila muncul di ≥ 2 lapisan multiplex sekaligus | 2 dari 4 lapisan |
| R-D8 | Fandom/aktivis: klaster dengan median umur akun > 2 tahun dan interaksi dua arah tinggi diturunkan satu tingkat | review manual |
| R-D9 | Setiap skor wajib menyimpan 5 fitur penyumbang terbesar (SHAP) | top-5 |

### 13b. Rules bisnis dan etika

1. Username asli tidak pernah disimpan di database; hanya `handle_hash` (SHA-256 + salt rahasia di `.env`).
2. Output publik (artikel, laporan, dashboard yang dibagikan) memakai istilah "perilaku mirip bot" atau "terkoordinasi", tidak pernah "akun X adalah bot".
3. Alert Telegram hanya dikirim untuk klaster kategori tinggi (R-D7) dan maksimal 1 alert per klaster per 24 jam.
4. Klaster baru boleh disebut "terkonfirmasi" hanya bila ada baris di `validasi_eksternal` dengan status `terkonfirmasi`.
5. Label manual wajib dari minimal 2 coder; akun dengan label berbeda masuk antrean ragu dan tidak dipakai sebagai data latih sampai disepakati.
6. Data mentah disimpan maksimal selama masa riset; dataset publik hanya versi teranonimkan.
7. Setiap angka di artikel harus bisa ditelusuri ke satu `run_model.id`.

### 13c. Rules pengembangan (juga untuk AI coding agent, simpan sebagai `AGENTS.md`)

- Bahasa: Python 3.11; format dan lint dengan `ruff`; type hint di semua fungsi publik.
- Struktur folder: `app/` (Streamlit), `pipeline/` (ingest, fitur, model, graf), `db/` (schema, migrasi), `tests/`, `data/` (diabaikan Git).
- Rahasia (API key, salt, token Telegram) hanya di `.env`; `.env` masuk `.gitignore`; sediakan `.env.example`.
- Ambang di 13a disimpan di satu berkas `config.yaml`, bukan ditulis langsung di kode.
- Setiap fitur baru wajib punya tes `pytest`; PR tidak di-merge bila tes gagal di GitHub Actions.
- Seed acak tetap (dicatat di `run_model`) untuk setiap pelatihan dan deteksi komunitas.
- Dilarang commit data mentah atau handle asli ke GitHub; hanya data dummy di `tests/fixtures/`.
- Perubahan schema lewat berkas migrasi bernomor, bukan edit tabel langsung.
- AI agent wajib membaca PRD ini sebelum membuat kode dan tidak boleh menambah library di luar bagian 8a tanpa mencatat alasannya.

## 14. Evaluasi desain UI/UX

UI dinilai lolos bila skor SUS rata-rata ≥ 68, minimal 80% tugas inti selesai tanpa bantuan, dan tidak ada temuan heuristik berkategori berat (severity 3–4) yang tersisa. Evaluasi dilakukan dua kali: pada prototipe (minggu 9) dan sebelum rilis (minggu 12).

### 14a. Layar yang dievaluasi

| Layar | Tujuan pengguna | Elemen kunci |
| --- | --- | --- |
| Unggah data | Memasukkan korpus baru | Drag-and-drop CSV/XLSX, pemetaan kolom, ringkasan baris valid/ditolak |
| Ringkasan isu | Melihat gambaran cepat | Jumlah akun, % mencurigakan, jumlah klaster, grafik volume per jam |
| Daftar akun berisiko | Memilih akun untuk dicek | Tabel bisa diurutkan dan difilter, skor, kategori, badge alasan |
| Detail akun | Memahami kenapa skor tinggi | Grafik SHAP top-5, pola jam posting, contoh posting (handle tersamar) |
| Peta klaster | Melihat koordinasi | Graf interaktif, warna per lapisan, panel anggota klaster |
| Validasi manual | Memberi label | Tombol manusia/bot/ragu, pintasan keyboard, progres dan κ sementara |
| Laporan | Membagikan hasil | Ekspor PDF/CSV, pilihan anonimisasi |

### 14b. Tugas uji usability (5–8 peserta per putaran)

Peserta: campuran peneliti komunikasi, mahasiswa S2, dan analis/jurnalis. Metode think-aloud, direkam layar.

1. Unggah berkas NodeXL dan mulai analisis.
2. Temukan 10 akun dengan skor tertinggi pada isu tertentu.
3. Jelaskan dengan kata sendiri kenapa satu akun diberi skor tinggi.
4. Temukan klaster koordinasi terbesar dan sebutkan lapisannya.
5. Beri label pada 20 akun di layar validasi.
6. Ekspor laporan PDF yang sudah teranonimkan.

### 14c. Metrik dan target

| Metrik | Cara ukur | Target |
| --- | --- | --- |
| Keberhasilan tugas | % tugas selesai tanpa bantuan | ≥ 80% |
| Waktu tugas | Detik per tugas, dibanding waktu ahli | ≤ 2× waktu ahli |
| Error | Jumlah langkah salah per tugas | ≤ 1 rata-rata |
| System Usability Scale (SUS) | Kuesioner 10 butir setelah sesi | ≥ 68 (di atas rata-rata) |
| Pemahaman penjelasan skor | Peserta bisa menyebut ≥ 2 alasan skor dengan benar (tugas 3) | ≥ 80% peserta |
| Kepercayaan | Skala Likert 1–5: "Saya percaya skor ini" | ≥ 3,5, tanpa over-trust pada skor ragu |
| Kecepatan validasi | Akun berlabel per menit | ≥ 4 akun/menit |

### 14d. Evaluasi heuristik (Nielsen, 10 heuristik)

Dua evaluator memeriksa tiap layar secara terpisah, memberi severity 0–4, lalu menggabungkan temuan. Fokus khusus untuk aplikasi ini:

- **Visibilitas status sistem:** progres proses data panjang (IndoBERT, graf) harus terlihat, bukan layar diam.
- **Kecocokan dengan dunia nyata:** istilah "mirip bot" dan "terkoordinasi", bukan "bot" atau istilah teknis seperti "Leiden modularity".
- **Pencegahan error:** pemetaan kolom divalidasi sebelum analisis berjalan.
- **Pengakuan, bukan ingatan:** filter dan ambang yang aktif selalu tampak di atas tabel.
- **Bantuan dan dokumentasi:** tooltip di setiap fitur SHAP yang menjelaskan arti fitur dalam bahasa awam.

### 14e. Aksesibilitas (WCAG 2.2 AA)

- [ ] Kontras teks ≥ 4,5:1; kategori skor tidak dibedakan dengan warna saja (pakai label teks dan ikon).
- [ ] Seluruh tabel dan tombol validasi bisa dioperasikan dengan keyboard.
- [ ] Graf jaringan punya alternatif tabel anggota klaster untuk pembaca layar.
- [ ] Ukuran teks minimal 14 px; tata letak tetap terbaca di layar 1366 × 768.

### 14f. Alat evaluasi

Figma (prototipe dan uji klik sebelum coding), Google Forms (SUS dan Likert), OBS atau Zoom (rekam sesi), Lighthouse dan axe DevTools (aksesibilitas), spreadsheet log temuan dengan kolom layar, heuristik, severity, rekomendasi, dan status perbaikan.

## 15. Dataset

Dataset inti sudah ada di repo tesis `digimetateam-hash/tesis`: 5.272 posting MBG (2 Maret–24 Mei 2026) dan graf mention NodeXL. Korpus ini cukup untuk lapisan konten, waktu, dan jaringan mention, tetapi belum memuat metadata profil akun dan ID posting induk retweet, sehingga keduanya perlu dikumpulkan ulang.

### 15a. Dataset milik sendiri (sudah ada di repo)

| Berkas | Isi | Ukuran | Dipakai untuk |
| --- | --- | --- | --- |
| `data/data_bersih_sudah_dicleaning_5272.csv` | id, created\_at, author\_username, teks bersih, teks siap IndoBERT, emosi, like, retweet | 5.272 baris × 9 kolom | Tabel posting; lapisan konten dan waktu |
| `data/data_mentah_belum_dicleaning_5272.csv` | Teks asli sebelum cleaning | 5.272 baris | Deteksi teks kembar (URL dan emoji masih utuh) |
| `NodeXL_MBG_Tesis_Indri_Anjar.xlsx` | Sheet Edges, Vertices, Groups, Overall Metrics, Edges P1 pra-krisis, Edges P2 puncak krisis | 971 akun, 666 tie unik | Tabel interaksi dan akun; lapisan jaringan |
| `NodeXL_Scraped_Tweets_MBG.xlsx` | Edges dengan teks tweet per relasi | — | Mencocokkan teks dengan edge |
| `anggota_klaster.csv` | akun, klaster, in/out/total degree | 971 baris | Pembanding klaster komunitas vs klaster koordinasi |
| `data/network_edges.csv` | Source, Target | 692 baris | Graf mention siap pakai |
| `data/dataset_sindiran_valid.csv` | id, text, label sindiran | 3.395 baris | Fitur sarkasme (pembeda buzzer vs kritik warga) |
| `bab45/Lembar_Pengodean_150_Unggahan.xlsx` | Koding manual 150 posting | 150 baris | Contoh pedoman coding; awal label manual |

**Kolom yang belum ada dan harus dikumpulkan:** tanggal pembuatan akun, followers, following, total posting, avatar default, bio (untuk lapisan profil); ID posting induk dan tipe (retweet/quote/reply) untuk co-retweet; URL lengkap per posting untuk co-URL.

### 15b. Dataset publik pembanding

| Dataset | Isi | Peran dalam riset |
| --- | --- | --- |
| [TwiBot-22](https://twibot22.github.io/) | Benchmark bot Twitter berbasis graf, dengan 35 baseline dievaluasi | Uji transfer: apakah model yang dilatih di data Inggris gagal di data Indonesia |
| [MGTAB](https://arxiv.org/pdf/2311.05079) | Benchmark multi-relasi untuk deteksi akun | Pembanding metode graf |
| TwiBot-20, Cresci-2015 | Benchmark lama yang sering dipakai lintas-dataset ([preprint 2026](https://www.preprints.org/manuscript/202610.0500/v1)) | Uji generalisasi lintas dataset |
| [twitter\_indonesia\_sarcastic](https://huggingface.co/datasets/w11wo/twitter_indonesia_sarcastic) | Tweet bahasa Indonesia berlabel sarkasme | Melatih fitur sarkasme tambahan |
| [Botometer X](https://botometer.osome.iu.edu) | Skor bot arsip untuk akun dengan data sebelum Juni 2023 | Pembanding untuk akun lama saja |

### 15c. Dataset yang dibangun (kontribusi novelty)

1. **Label manual akun:** 500 akun dari korpus MBG dan korpus kontrol, dua coder, label manusia/bot/ragu, laporkan κ.
2. **Benchmark parafrase LLM bahasa Indonesia:** posting dari klaster terkoordinasi diparafrase oleh LLM (formal, slang, campur kode, plesetan akronim) untuk menguji ketahanan detektor.
3. **Korpus kontrol:** satu isu fandom dan satu isu non-politik, untuk mengukur false positive pada aksi kolektif organik.
4. **Ground truth eksternal:** daftar hoaks Komdigi, artikel cek fakta, dan kejadian resmi yang dikaitkan ke klaster lewat tabel `validasi_eksternal`.

### 15d. Publikasi dataset

Versi teranonimkan (handle di-hash, teks dipotong sesuai ketentuan platform) dirilis di Hugging Face akun `1ndrikartika007`, kode di GitHub, dan diarsipkan di Zenodo dengan DOI agar bisa dikutip di artikel.

## 16. Quality assessment

Sistem dianggap layak rilis dan layak publikasi bila lolos lima gerbang kualitas: data, label, model, perangkat lunak, dan pelaporan riset. Gerbang yang gagal menahan fase berikutnya. Pelajaran dari korpus MBG menjadi dasar gerbang data: hanya 49 dari 150 posting sampel (32,7%) yang benar-benar membahas program, dan label emosi IndoBERT setara tebakan (κ = 0,05).

### 16a. Kualitas data

| Dimensi | Pemeriksaan | Ambang lolos |
| --- | --- | --- |
| Relevansi | Sampel acak 150 posting dikoding manual: relevan atau tidak | ≥ 90% relevan setelah filter; laporkan angkanya |
| Kelengkapan | % baris dengan kolom wajib terisi (akun, waktu, teks, tipe) | ≥ 98% |
| Duplikasi | Posting dengan `id_platform` sama | 0 setelah dedup |
| Konsistensi waktu | Waktu posting di dalam periode korpus, zona waktu seragam (UTC) | 100% |
| Cakupan metadata akun | % akun dengan data profil lengkap | ≥ 90% (sisanya ditandai, tidak diberi kategori) |
| Bias pengambilan | Distribusi posting per hari dibanding volume pencarian/tren | Dilaporkan sebagai keterbatasan |

### 16b. Kualitas label manual

- [ ] Pedoman coding tertulis dengan definisi dan contoh tiap label, diuji pada 30 akun sebelum koding penuh.
- [ ] Dua coder independen; Cohen's κ ≥ 0,70 (atau Krippendorff's α ≥ 0,667).
- [ ] Ketidaksepakatan diselesaikan lewat adjudikasi orang ketiga dan dicatat.
- [ ] Proporsi label "ragu" dilaporkan; akun ragu tidak masuk data latih.

### 16c. Kualitas model

| Aspek | Metrik | Target |
| --- | --- | --- |
| Kinerja klasifikasi akun | Macro-F1, precision, recall, PR-AUC (data tidak seimbang) | Macro-F1 ≥ 0,80 |
| Kalibrasi skor | Brier score, Expected Calibration Error (ECE), reliability diagram | ECE ≤ 0,05 |
| Stabilitas | Rata-rata ± SD dari 5-fold CV dengan 5 seed berbeda | SD F1 ≤ 0,03 |
| Generalisasi | Latih di MBG, uji di korpus isu lain yang belum dilihat | Penurunan F1 ≤ 10 poin |
| Ketahanan parafrase LLM | F1 sebelum vs sesudah teks diparafrase LLM | Penurunan ≤ 5 poin (lapisan jaringan) |
| Kualitas klaster koordinasi | Precision klaster dicek manual; modularitas; stabilitas klaster antar-seed (ARI) | Precision ≥ 0,75; ARI ≥ 0,80 |
| Keadilan terhadap aksi organik | False positive rate pada korpus kontrol fandom/aktivis | FPR ≤ 10% |
| Kontribusi lapisan | Ablation: buang satu lapisan, ukur penurunan F1 | Dilaporkan per lapisan |
| Signifikansi | Uji McNemar atau bootstrap 95% CI terhadap baseline | p < 0,05 / CI tidak memotong 0 |

**Baseline wajib:** model hanya fitur profil (gaya penelitian buzzer Indonesia sebelumnya), Botometer X untuk akun lama, dan satu detektor graf dari framework TwiBot-22.

### 16d. Kualitas perangkat lunak

| Aspek | Ukuran | Target |
| --- | --- | --- |
| Test coverage | `pytest --cov` | ≥ 80% untuk `pipeline/` |
| Lint dan format | `ruff check`, `ruff format` | 0 error di CI |
| Integrasi berkelanjutan | GitHub Actions pada setiap push/PR | Semua job hijau sebelum merge |
| Performa | Waktu proses 10.000 posting di laptop 8 GB | < 5 menit |
| Keamanan | Tidak ada rahasia di repo (`gitleaks`), dependensi dicek (`pip-audit`) | 0 temuan kritis |
| Usability | SUS dan tugas uji (bagian 14) | SUS ≥ 68 |

### 16e. Kualitas pelaporan riset (kesiapan publikasi)

- [ ] **Datasheet for Datasets** untuk korpus dan benchmark parafrase (motivasi, komposisi, proses pengumpulan, anonimisasi, batas penggunaan).
- [ ] **Model card** untuk detektor (tujuan, data latih, metrik per subkelompok, keterbatasan, penggunaan yang tidak disarankan).
- [ ] Kode, konfigurasi ambang, dan seed dirilis; satu perintah untuk mereproduksi tabel utama.
- [ ] Dataset teranonimkan dengan DOI Zenodo dan tautan Hugging Face.
- [ ] Pernyataan etika: data publik, handle di-hash, tidak ada pelabelan individu di publikasi.
- [ ] Bagian keterbatasan: bias pengambilan data, satu platform, ambang yang dikalibrasi pada isu tertentu.
- [ ] Pernyataan penggunaan AI generatif dalam penulisan dan pembuatan data sintetis.
- [ ] Tabel perbandingan dengan studi terdekat hasil pencarian Scopus (bagian 11).

### 16f. Jadwal gerbang kualitas

| Gerbang | Kapan | Lolos bila |
| --- | --- | --- |
| G1 Data | Akhir Fase 1 | 16a terpenuhi |
| G2 Label | Akhir Fase 1 | κ ≥ 0,70 |
| G3 Model | Akhir Fase 4 | Target 16c terpenuhi atau selisihnya dijelaskan |
| G4 Aplikasi | Akhir Fase 5 | 16d dan SUS terpenuhi |
| G5 Publikasi | Sebelum submit | Seluruh checklist 16e dicentang |
