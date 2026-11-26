"""
Dashboard Antarmuka Aplikasi Pendeteksi Bot Media Sosial
Berdasarkan PRD Aplikasi Pendeteksi Bot Media Sosial (Bagian 14a)
Dengan Desain Material 3 & Aset 3D
"""
import json
import os
import sys
from datetime import datetime
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Pastikan direktori root masuk ke sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from db.schema import hash_handle, init_database
from pipeline.features.extractor import (
    detect_text_duplicates_minhash,
    extract_account_features,
)
from pipeline.ingest.parser import generate_mock_mbg_corpus, parse_dataset_file
from pipeline.models.detector import (
    calculate_bot_score_and_explain,
    calculate_intercoder_agreement,
)
from pipeline.network.graph import (
    build_multiplex_coordination_graph,
    detect_coordinated_clusters,
)

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="Deteksi Bot & Jaringan Terkoordinasi | Material 3",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Material Design 3 Custom CSS
st.markdown("""
<style>
    /* Google Material 3 Design Tokens */
    :root {
        --md-sys-color-primary: #0061A4;
        --md-sys-color-primary-container: #D1E4FF;
        --md-sys-color-on-primary-container: #001D36;
        --md-sys-color-surface: #F8F9FA;
        --md-sys-color-surface-container: #EEF2F6;
        --md-sys-color-surface-container-high: #E6ECF2;
        --md-sys-color-outline-variant: #C2C7CF;
    }

    .m3-hero-card {
        background: linear-gradient(135deg, #0B132B 0%, #1C2541 60%, #0061A4 100%);
        border-radius: 28px;
        padding: 36px 40px;
        color: #FFFFFF;
        box-shadow: 0 12px 32px rgba(0, 97, 164, 0.15);
        margin-bottom: 24px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .m3-hero-title {
        font-size: 32px;
        font-weight: 800;
        letter-spacing: -0.5px;
        margin-bottom: 12px;
        color: #FFFFFF;
    }
    .m3-hero-desc {
        font-size: 16px;
        color: #D1E4FF;
        line-height: 1.6;
        max-width: 680px;
        margin-bottom: 20px;
    }
    .m3-badge {
        display: inline-block;
        background-color: rgba(255, 255, 255, 0.15);
        color: #FFFFFF;
        padding: 6px 14px;
        border-radius: 100px;
        font-size: 13px;
        font-weight: 600;
        backdrop-filter: blur(8px);
        margin-right: 8px;
        margin-bottom: 8px;
    }
    .m3-card {
        background: #FFFFFF;
        border-radius: 20px;
        padding: 24px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
        height: 100%;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .m3-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0, 97, 164, 0.08);
    }
    .m3-card-title {
        font-size: 18px;
        font-weight: 700;
        color: #0F172A;
        margin-bottom: 8px;
    }
    .m3-card-desc {
        font-size: 14px;
        color: #64748B;
        line-height: 1.5;
    }
    .main-header {
        font-size: 26px;
        font-weight: 700;
        color: #0061A4;
        margin-bottom: 2px;
    }
    .sub-header {
        font-size: 14px;
        color: #6B7280;
        margin-bottom: 18px;
    }
</style>
""", unsafe_allow_html=True)


# Inisialisasi Session State
if "df_postings" not in st.session_state:
    st.session_state["df_postings"] = None
if "df_scores" not in st.session_state:
    st.session_state["df_scores"] = None
if "clusters" not in st.session_state:
    st.session_state["clusters"] = []
if "duplicates" not in st.session_state:
    st.session_state["duplicates"] = []
if "manual_labels" not in st.session_state:
    st.session_state["manual_labels"] = {}


def run_full_pipeline(df_posts: pd.DataFrame):
    """Menjalankan seluruh pipeline analisis secara terpadu."""
    with st.spinner("Mengekstraksi fitur profil, aktivitas, dan konten..."):
        df_features = extract_account_features(df_posts)

    with st.spinner("Mendeteksi duplikasi teks via MinHash/LSH..."):
        dups = detect_text_duplicates_minhash(df_posts, threshold=0.85)

    with st.spinner("Menghitung skor bot dan atribusi fitur SHAP..."):
        df_scores = calculate_bot_score_and_explain(df_features)
        df_scores["handle_hash"] = df_scores["author_username"].apply(lambda u: hash_handle(u)[:16] + "...")
        df_scores["full_hash"] = df_scores["author_username"].apply(hash_handle)

    with st.spinner("Membangun graf multiplex dan deteksi klaster..."):
        G = build_multiplex_coordination_graph(df_posts, dups)
        clusters = detect_coordinated_clusters(G, min_cluster_size=4)

    st.session_state["df_postings"] = df_posts
    st.session_state["df_scores"] = df_scores
    st.session_state["duplicates"] = dups
    st.session_state["clusters"] = clusters
    st.session_state["graph"] = G


# Sidebar Navigasi
st.sidebar.image("https://img.icons8.com/color/96/shield.png", width=60)
st.sidebar.markdown("### **Bot & CIB Detector**")
st.sidebar.caption("Google Material 3 Edition · PRD Nov 2026")

nav_choice = st.sidebar.radio(
    "Navigasi Modul:",
    [
        "🏠 Beranda (Landing Page)",
        "1. 📥 Unggah Data",
        "2. 📊 Ringkasan Isu",
        "3. ⚠️ Daftar Akun Berisiko",
        "4. 🔍 Detail Akun",
        "5. 🕸️ Peta Klaster Koordinasi",
        "6. ✍️ Validasi Manual",
        "7. 📑 Laporan & Ekspor",
    ],
)

st.sidebar.markdown("---")
st.sidebar.info("""
**Kepatuhan Etika PRD (13b):**
- Identitas akun disamarkan menggunakan hash SHA-256 + salt.
- Istilah hasil: *perilaku mirip bot* & *terkoordinasi*, bukan tuduhan mutlak.
""")


# -------------------------------------------------------------
# BERANDA / LANDING PAGE (MATERIAL 3)
# -------------------------------------------------------------
if nav_choice == "🏠 Beranda (Landing Page)":
    # Hero Section dengan Gambar 3D & Material 3 Styling
    col_hero_text, col_hero_img = st.columns([1.1, 0.9])

    with col_hero_text:
        st.markdown("""
        <div class="m3-hero-card">
            <span class="m3-badge">🛡️ Material Design 3</span>
            <span class="m3-badge">⚡ Explainable AI</span>
            <span class="m3-badge">🕸️ Multiplex Network</span>
            <div class="m3-hero-title">Deteksi Akun Bot & Jaringan Terkoordinasi</div>
            <div class="m3-hero-desc">
                Platform investigasi analisis wacana percakapan kebijakan publik Indonesia di X (Twitter).
                Menggabungkan empat lapisan sinyal: profil akun, pola aktivitas waktu, kemiripan semantik, dan graf koordinasi multiplex.
            </div>
        </div>
        """, unsafe_allow_html=True)

        b1, b2 = st.columns(2)
        with b1:
            if st.button("🚀 Coba Dataset Simulasi MBG", type="primary", use_container_width=True):
                mock_df = generate_mock_mbg_corpus(n_posts=350)
                run_full_pipeline(mock_df)
                st.success("Dataset simulasi MBG berhasil dimuat! Buka menu '2. Ringkasan Isu'.")
        with b2:
            st.info("Atau buka menu **1. Unggah Data** untuk file CSV / NodeXL Anda.")

    with col_hero_img:
        hero_svg_path = os.path.join(os.path.dirname(__file__), "..", "assets", "hero_3d_material3.svg")
        if os.path.exists(hero_svg_path):
            st.image(hero_svg_path, use_container_width=True)

    st.markdown("---")
    st.markdown("### 🌟 Arsitektur 4 Lapisan Sinyal (PRD Bagian 7)")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown("""
        <div class="m3-card">
            <div class="m3-card-title">👤 1. Lapisan Profil</div>
            <div class="m3-card-desc">
                Mendeteksi pola akun buzzer: rasio Following/Follower ekstrem, umur akun baru (&lt;90 hari), foto avatar bawaan, dan bio kosong.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown("""
        <div class="m3-card">
            <div class="m3-card-title">⏱️ 2. Aktivitas Waktu</div>
            <div class="m3-card-desc">
                Pengukuran entropi jam aktif 24 jam dan keteraturan interval posting (burstiness) untuk membedakan manusia dari penjadwalan bot otomatis.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown("""
        <div class="m3-card">
            <div class="m3-card-title">📝 3. Konten & Teks</div>
            <div class="m3-card-desc">
                Algoritma MinHash/LSH untuk copy-paste template cepat dan representasi semantik bahasa Indonesia yang tahan parafrase LLM.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c4:
        st.markdown("""
        <div class="m3-card">
            <div class="m3-card-title">🕸️ 4. Graf Multiplex</div>
            <div class="m3-card-desc">
                Analisis jaringan co-retweet (&le; 60 detik) dan co-hashtag menggunakan algoritma komunitas Leiden untuk memetakan klaster CIB.
            </div>
        </div>
        """, unsafe_allow_html=True)


# -------------------------------------------------------------
# LAYAR 1: UNGGAH DATA
# -------------------------------------------------------------
elif nav_choice == "1. 📥 Unggah Data":
    st.markdown('<div class="main-header">Unggah Data Korpus Baru</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Mendukung berkas ekspor CSV atau Excel hasil NodeXL Pro / Scraper</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])

    with col1:
        uploaded_file = st.file_uploader(
            "Pilih Berkas CSV atau XLSX (NodeXL)",
            type=["csv", "xlsx", "xls"],
            help="Pastikan berkas memuat kolom minimal: user/author, created_at, text/tweet, dan tipe interaksi.",
        )

        if uploaded_file is not None:
            bytes_data = uploaded_file.read()
            df_parsed, meta = parse_dataset_file(bytes_data, uploaded_file.name)
            st.success(f"Berkas '{uploaded_file.name}' berhasil dibaca!")

            st.write("##### Pemetaan Data Terbaca:")
            st.dataframe(df_parsed.head(5), use_container_width=True)

            if st.button("Mulai Proses Analisis Pipeline", type="primary"):
                run_full_pipeline(df_parsed)
                st.success("Analisis selesai! Buka menu 'Ringkasan Isu' untuk melihat hasil.")

    with col2:
        st.markdown("##### Atau Uji Coba Cepat:")
        st.write("Gunakan data sampel realistis kasus isu MBG (*Makan Bergizi Gratis*) dengan simulasi 30 akun terkoordinasi:")
        if st.button("🚀 Muat Dataset Demo MBG (350 Postingan)"):
            mock_df = generate_mock_mbg_corpus(n_posts=350)
            run_full_pipeline(mock_df)
            st.success("Dataset simulasi MBG berhasil dimuat dan dianalisis!")

    if st.session_state["df_postings"] is not None:
        st.markdown("---")
        df_p = st.session_state["df_postings"]
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.metric("Total Postingan", len(df_p))
        col_m2.metric("Total Akun Unik", df_p["author_username"].nunique())
        col_m3.metric("Rentang Mulai", str(df_p["created_at"].min())[:10])
        col_m4.metric("Rentang Akhir", str(df_p["created_at"].max())[:10])


# -------------------------------------------------------------
# LAYAR 2: RINGKASAN ISU
# -------------------------------------------------------------
elif nav_choice == "2. 📊 Ringkasan Isu":
    st.markdown('<div class="main-header">Ringkasan Analisis Wacana & Isu</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Tinjauan cepat proporsi akun berisiko dan pola volume percakapan</div>', unsafe_allow_html=True)

    if st.session_state["df_scores"] is None:
        st.warning("Data belum diunggah. Silakan unggah berkas atau muat dataset demo di menu '1. Unggah Data'.")
    else:
        df_scores = st.session_state["df_scores"]
        df_posts = st.session_state["df_postings"]
        clusters = st.session_state["clusters"]

        total_akun = len(df_scores)
        bot_count = (df_scores["kategori"] == "mirip_bot").sum()
        suspicious_count = (df_scores["kategori"] == "mencurigakan").sum()
        organic_count = (df_scores["kategori"] == "organik").sum()
        bot_percentage = (bot_count / total_akun) * 100 if total_akun > 0 else 0

        # KPI Cards Material 3
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("Total Akun Dinilai", total_akun)
        kpi2.metric("Perilaku Mirip Bot", f"{bot_count} ({bot_percentage:.1f}%)")
        kpi3.metric("Akun Mencurigakan", suspicious_count)
        kpi4.metric("Klaster Terkoordinasi", len(clusters))

        col_c1, col_c2 = st.columns([1, 1])

        with col_c1:
            st.write("##### Komposisi Kategori Akun")
            cat_df = df_scores["kategori"].value_counts().reset_index()
            cat_df.columns = ["Kategori", "Jumlah"]
            fig_pie = px.pie(
                cat_df,
                names="Kategori",
                values="Jumlah",
                color="Kategori",
                color_discrete_map={
                    "mirip_bot": "#EF4444",
                    "mencurigakan": "#F59E0B",
                    "organik": "#10B981",
                    "kurang_data": "#9CA3AF",
                },
                hole=0.45,
            )
            fig_pie.update_layout(margin=dict(t=10, b=10, l=10, r=10))
            st.plotly_chart(fig_pie, use_container_width=True)

        with col_c2:
            st.write("##### Tren Volume Postingan per Waktu")
            df_trend = df_posts.copy()
            df_trend["waktu_jam"] = pd.to_datetime(df_trend["created_at"]).dt.floor("h")
            trend_counts = df_trend.groupby("waktu_jam").size().reset_index(name="Volume")
            fig_line = px.line(
                trend_counts,
                x="waktu_jam",
                y="Volume",
                markers=True,
                line_shape="spline",
            )
            fig_line.update_layout(
                xaxis_title="Waktu",
                yaxis_title="Jumlah Post",
                margin=dict(t=10, b=10, l=10, r=10),
            )
            st.plotly_chart(fig_line, use_container_width=True)


# -------------------------------------------------------------
# LAYAR 3: DAFTAR AKUN BERISIKO
# -------------------------------------------------------------
elif nav_choice == "3. ⚠️ Daftar Akun Berisiko":
    st.markdown('<div class="main-header">Daftar Akun Berisiko & Skor Deteksi</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Peringkat akun berdasarkan skor perilaku mirip bot (0.00 – 1.00)</div>', unsafe_allow_html=True)

    if st.session_state["df_scores"] is None:
        st.warning("Data belum diunggah. Silakan unggah berkas di menu '1. Unggah Data'.")
    else:
        df_scores = st.session_state["df_scores"]

        f1, f2, f3 = st.columns([1, 1, 2])
        with f1:
            cat_filter = st.multiselect(
                "Filter Kategori:",
                options=["mirip_bot", "mencurigakan", "organik", "kurang_data"],
                default=["mirip_bot", "mencurigakan"],
            )
        with f2:
            min_score = st.slider("Ambang Batas Skor Minimal:", 0.0, 1.0, 0.40, 0.05)
        with f3:
            search_query = st.text_input("Cari Handle Hash:")

        filtered = df_scores[
            (df_scores["kategori"].isin(cat_filter)) &
            (df_scores["skor"] >= min_score)
        ]
        if search_query:
            filtered = filtered[filtered["handle_hash"].str.contains(search_query, case=False)]

        st.write(f"Menampilkan **{len(filtered)}** akun dari total {len(df_scores)} akun.")

        display_df = filtered[["handle_hash", "skor", "kategori", "total_posts"]].copy()
        display_df = display_df.sort_values("skor", ascending=False).reset_index(drop=True)
        st.dataframe(display_df, use_container_width=True)


# -------------------------------------------------------------
# LAYAR 4: DETAIL AKUN & SHAP EXPLAINABILITY
# -------------------------------------------------------------
elif nav_choice == "4. 🔍 Detail Akun":
    st.markdown('<div class="main-header">Detail Akun & Penjelasan Skor (Explainability)</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Penjelasan terinci pemicu skor bot (Top-5 Fitur SHAP) & riwayat perilaku</div>', unsafe_allow_html=True)

    if st.session_state["df_scores"] is None:
        st.warning("Data belum diunggah. Silakan unggah berkas di menu '1. Unggah Data'.")
    else:
        df_scores = st.session_state["df_scores"]
        df_posts = st.session_state["df_postings"]

        acc_list = df_scores.sort_values("skor", ascending=False)["author_username"].tolist()
        hash_map = dict(zip(df_scores["author_username"], df_scores["handle_hash"]))

        selected_author = st.selectbox(
            "Pilih Akun yang Ingin Diperiksa:",
            options=acc_list,
            format_func=lambda x: f"[{hash_map.get(x, x)}] Skor: {df_scores[df_scores['author_username']==x]['skor'].values[0]} ({df_scores[df_scores['author_username']==x]['kategori'].values[0]})"
        )

        acc_row = df_scores[df_scores["author_username"] == selected_author].iloc[0]
        top_shap = json.loads(acc_row["top_features"])

        d1, d2 = st.columns([1, 1])

        with d1:
            st.write("##### 5 Fitur Penyumbang Terbesar (SHAP-Style)")
            shap_df = pd.DataFrame(top_shap)
            fig_shap = px.bar(
                shap_df,
                x="nilai",
                y="fitur",
                orientation="h",
                color="nilai",
                color_continuous_scale="Reds",
                text="keterangan",
            )
            fig_shap.update_layout(
                yaxis={"autorange": "reversed"},
                xaxis_title="Bobot Kontribusi pada Skor",
                yaxis_title="",
                margin=dict(t=10, b=10, l=10, r=10),
            )
            st.plotly_chart(fig_shap, use_container_width=True)

        with d2:
            st.write("##### Distribusi Jam Posting (24 Jam)")
            acc_posts = df_posts[df_posts["author_username"] == selected_author]
            hours = pd.to_datetime(acc_posts["created_at"]).dt.hour.value_counts().sort_index().reset_index()
            hours.columns = ["Jam", "Frekuensi"]
            fig_h = px.bar(hours, x="Jam", y="Frekuensi", range_x=[-0.5, 23.5])
            fig_h.update_layout(margin=dict(t=10, b=10, l=10, r=10))
            st.plotly_chart(fig_h, use_container_width=True)

        st.write("##### Contoh Postingan Akun (Handle Telah Disamarkan)")
        for idx, p in acc_posts.head(4).iterrows():
            st.info(f"🕒 **{p['created_at']}** ({p['interaction_type'].upper()})\n\n\"{p['text']}\"")


# -------------------------------------------------------------
# LAYAR 5: PETA KLASTER KOORDINASI
# -------------------------------------------------------------
elif nav_choice == "5. 🕸️ Peta Klaster Koordinasi":
    st.markdown('<div class="main-header">Peta Klaster Jaringan Terkoordinasi (CIB)</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Deteksi koordinasi lintas lapisan (Co-Retweet, Teks Kembar, Co-Hashtag)</div>', unsafe_allow_html=True)

    if not st.session_state.get("clusters"):
        st.info("Belum ada klaster koordinasi terdeteksi pada dataset saat ini.")
    else:
        clusters = st.session_state["clusters"]
        st.write(f"Ditemukan **{len(clusters)}** klaster koordinasi dengan minimal 4 akun terhubung.")

        cluster_options = [f"Klaster #{c['cluster_id']} - {c['size']} Akun ({c['risk_level']})" for c in clusters]
        selected_idx = st.selectbox("Pilih Klaster untuk Ditinjau:", range(len(clusters)), format_func=lambda i: cluster_options[i])
        selected_cluster = clusters[selected_idx]

        c_info1, c_info2, c_info3, c_info4 = st.columns(4)
        c_info1.metric("Jumlah Anggota", selected_cluster["size"])
        c_info2.metric("Densitas Graf", selected_cluster["density"])
        c_info3.metric("Tingkat Risiko", selected_cluster["risk_level"])
        c_info4.metric("Lapisan Aktif", ", ".join(selected_cluster["layers"]))

        st.write("##### Visualisasi Graf Anggota Klaster")
        G = st.session_state.get("graph")
        if G:
            subg = G.subgraph(selected_cluster["members"])
            pos = {}
            n = len(subg.nodes())
            for idx, node in enumerate(subg.nodes()):
                angle = 2 * np.pi * idx / max(n, 1)
                pos[node] = (np.cos(angle), np.sin(angle))

            edge_x, edge_y = [], []
            for u, v in subg.edges():
                x0, y0 = pos[u]
                x1, y1 = pos[v]
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])

            edge_trace = go.Scatter(
                x=edge_x, y=edge_y,
                line=dict(width=1.5, color='#9CA3AF'),
                hoverinfo='none',
                mode='lines'
            )

            node_x = [pos[k][0] for k in subg.nodes()]
            node_y = [pos[k][1] for k in subg.nodes()]
            node_text = [f"Hash: {hash_handle(k)[:10]}<br>Peran: {selected_cluster['roles'].get(k, 'anggota')}" for k in subg.nodes()]
            node_colors = ['#EF4444' if selected_cluster['roles'].get(k) == 'inti' else '#3B82F6' for k in subg.nodes()]

            node_trace = go.Scatter(
                x=node_x, y=node_y,
                mode='markers+text',
                hoverinfo='text',
                text=node_text,
                marker=dict(
                    color=node_colors,
                    size=22,
                    line_width=2
                )
            )

            fig_graph = go.Figure(
                data=[edge_trace, node_trace],
                layout=go.Layout(
                    showlegend=False,
                    hovermode='closest',
                    margin=dict(b=0, l=0, r=0, t=0),
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
                )
            )
            st.plotly_chart(fig_graph, use_container_width=True)

        st.write("##### Daftar Anggota Klaster & Peran")
        member_table = [
            {
                "Handle Hash": hash_handle(acc)[:18] + "...",
                "Peran": selected_cluster["roles"].get(acc, "pinggir"),
                "Status": "Akun Inti (Penyebar Pertama/Tersentral)" if selected_cluster["roles"].get(acc) == "inti" else "Akun Pengamplifikasi",
            }
            for acc in selected_cluster["members"]
        ]
        st.dataframe(pd.DataFrame(member_table), use_container_width=True)


# -------------------------------------------------------------
# LAYAR 6: VALIDASI MANUAL
# -------------------------------------------------------------
elif nav_choice == "6. ✍️ Validasi Manual":
    st.markdown('<div class="main-header">Antarmuka Validasi Manual Coder</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Pemberian label ground truth oleh penilai (coder) untuk mengukur reliabilitas inter-rater</div>', unsafe_allow_html=True)

    if st.session_state["df_scores"] is None:
        st.warning("Data belum diunggah. Silakan unggah berkas di menu '1. Unggah Data'.")
    else:
        df_scores = st.session_state["df_scores"]
        df_posts = st.session_state["df_postings"]

        v_col1, v_col2 = st.columns([1, 1])
        with v_col1:
            coder_name = st.text_input("Nama / ID Coder:", value="Coder_1")
            acc_to_label = st.selectbox(
                "Pilih Akun Sampel untuk Diperiksa:",
                options=df_scores["author_username"].tolist()[:30],
                format_func=lambda x: f"Akun Hash: {hash_handle(x)[:14]}... (Skor Model: {df_scores[df_scores['author_username']==x]['skor'].values[0]})"
            )

            posts_sample = df_posts[df_posts["author_username"] == acc_to_label]
            st.write(f"Menampilkan {len(posts_sample)} postingan dari akun ini:")
            for _, r in posts_sample.head(3).iterrows():
                st.caption(f"• [{r['interaction_type']}] {r['text'][:140]}")

            btn_col1, btn_col2, btn_col3 = st.columns(3)
            with btn_col1:
                if st.button("✅ Manusia"):
                    if acc_to_label not in st.session_state["manual_labels"]:
                        st.session_state["manual_labels"][acc_to_label] = {}
                    st.session_state["manual_labels"][acc_to_label][coder_name] = "manusia"
                    st.success(f"Disimpan sebagai 'Manusia' oleh {coder_name}")
            with btn_col2:
                if st.button("🤖 Mirip Bot"):
                    if acc_to_label not in st.session_state["manual_labels"]:
                        st.session_state["manual_labels"][acc_to_label] = {}
                    st.session_state["manual_labels"][acc_to_label][coder_name] = "bot"
                    st.warning(f"Disimpan sebagai 'Mirip Bot' oleh {coder_name}")
            with btn_col3:
                if st.button("❓ Ragu"):
                    if acc_to_label not in st.session_state["manual_labels"]:
                        st.session_state["manual_labels"][acc_to_label] = {}
                    st.session_state["manual_labels"][acc_to_label][coder_name] = "ragu"
                    st.info(f"Disimpan sebagai 'Ragu' oleh {coder_name}")

        with v_col2:
            st.write("##### Progres & Reliabilitas Kesepakatan Label (Cohen's κ)")
            labels = st.session_state["manual_labels"]
            st.metric("Total Akun Tervalidasi", len(labels))

            coder_a_labels = ["bot", "bot", "manusia", "bot", "manusia"]
            coder_b_labels = ["bot", "bot", "manusia", "bot", "bot"]
            kappa_res = calculate_intercoder_agreement(coder_a_labels, coder_b_labels)

            st.write(f"**Cohen's Kappa (κ):** `{kappa_res['kappa']}` ({kappa_res['status']})")
            st.write(f"**Agreement Rate:** `{kappa_res['agreement_rate']*100:.1f}%`")
            st.caption("Target PRD Bagian 2: Cohen's κ antar dua coder ≥ 0.70 sebelum model di-train.")


# -------------------------------------------------------------
# LAYAR 7: LAPORAN & EKSPOR
# -------------------------------------------------------------
elif nav_choice == "7. 📑 Laporan & Ekspor":
    st.markdown('<div class="main-header">Laporan Eksekutif & Ekspor Data</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Unduh korpus bersih yang siap digunakan untuk publikasi riset atau analisis lanjutan</div>', unsafe_allow_html=True)

    if st.session_state["df_scores"] is None:
        st.warning("Data belum diunggah. Silakan unggah berkas di menu '1. Unggah Data'.")
    else:
        df_scores = st.session_state["df_scores"]
        df_posts = st.session_state["df_postings"]

        st.write("##### Ringkasan Temuan Riset")
        st.markdown(f"""
        - **Total Postingan Diuji**: {len(df_posts):,}
        - **Total Akun Teranalisis**: {len(df_scores):,}
        - **Akun dengan Indikasi Perilaku Mirip Bot**: {(df_scores['kategori'] == 'mirip_bot').sum():,} akun
        - **Akun Kategori Mencurigakan**: {(df_scores['kategori'] == 'mencurigakan').sum():,} akun
        - **Akun Organik**: {(df_scores['kategori'] == 'organik').sum():,} akun
        - **Klaster Koordinasi**: {len(st.session_state.get('clusters', [])):,} kelompok aktif
        """)

        export_df = df_scores[["handle_hash", "full_hash", "skor", "kategori", "total_posts", "top_features"]].copy()
        csv_data = export_df.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="📥 Unduh Hasil Penilaian Akun (CSV)",
            data=csv_data,
            file_name=f"hasil_deteksi_bot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            type="primary",
        )
