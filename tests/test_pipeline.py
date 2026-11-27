"""
Unit tests untuk Fase 1 (DB & Ingest), Fase 2 (Features, Anomaly & Scoring),
dan Fase 3 (Multiplex Network & SNA Centrality Typology).
"""
from datetime import date

from db.crud import (
    simpan_klaster,
    simpan_korpus,
    simpan_postings_dan_akun,
    simpan_run_model,
    simpan_skor_akun,
)
from db.schema import Akun, hash_handle, init_database
from pipeline.config_loader import load_config
from pipeline.features.anomaly import (
    compute_behavioral_anomaly_scores,
    detect_temporal_spikes,
)
from pipeline.features.extractor import (
    detect_text_duplicates_minhash,
    extract_account_features,
)
from pipeline.ingest.parser import generate_mock_mbg_corpus, standardize_postings_df
from pipeline.models.detector import (
    calculate_bot_score_and_explain,
    calculate_intercoder_agreement,
)
from pipeline.network.graph import (
    build_multiplex_coordination_graph,
    compute_actor_centrality_and_roles,
    detect_coordinated_clusters,
)


def test_hash_handle_privacy():
    h1 = hash_handle("@UserTest", salt="salt_abc")
    h2 = hash_handle("usertest", salt="salt_abc")
    assert len(h1) == 64
    assert h1 == h2
    assert "usertest" not in h1


def test_config_loader():
    cfg = load_config()
    assert "detection" in cfg
    assert cfg["detection"]["score_thresholds"]["mirip_bot_min"] == 0.70


def test_fase1_db_and_ingest():
    engine, Session = init_database("sqlite:///:memory:")
    session = Session()

    df_mock = generate_mock_mbg_corpus(n_posts=40)
    df_std, meta = standardize_postings_df(df_mock)
    assert meta["valid_count"] > 0

    korpus = simpan_korpus(
        session,
        nama_isu="Uji MBG",
        query="MBG",
        sumber="csv",
        periode_mulai=date(2026, 3, 1),
        periode_akhir=date(2026, 3, 10),
    )
    res = simpan_postings_dan_akun(session, korpus.id, df_std, salt="test_salt")
    assert res["akun_baru"] > 0
    assert res["posting_baru"] == len(df_std)

    # Pastikan username asli tidak pernah tersimpan di kolom handle_hash
    akuns = session.query(Akun).all()
    for a in akuns:
        assert len(a.handle_hash) == 64
    session.close()


def test_fase2_features_anomaly_and_scoring():
    df_mock = generate_mock_mbg_corpus(n_posts=150)
    df_feat = extract_account_features(df_mock)
    assert not df_feat.empty
    assert "active_hours_entropy" in df_feat.columns

    df_anom = compute_behavioral_anomaly_scores(df_feat, random_state=42)
    assert "anomaly_score" in df_anom.columns
    assert df_anom["anomaly_score"].between(0.0, 1.0).all()

    df_spikes = detect_temporal_spikes(df_mock)
    assert "z_score" in df_spikes.columns

    df_scores = calculate_bot_score_and_explain(df_feat)
    assert "skor" in df_scores.columns
    assert "top_features" in df_scores.columns
    assert set(df_scores["kategori"].unique()).issubset(
        {"organik", "mencurigakan", "mirip_bot", "kurang_data"}
    )

    agreement = calculate_intercoder_agreement(
        ["bot", "bot", "manusia", "manusia"],
        ["bot", "bot", "manusia", "manusia"],
    )
    assert agreement["kappa"] == 1.0


def test_fase3_multiplex_network_and_centrality():
    df_mock = generate_mock_mbg_corpus(n_posts=250)
    dups = detect_text_duplicates_minhash(df_mock, threshold=0.85)
    G = build_multiplex_coordination_graph(df_mock, dups)
    assert G.number_of_nodes() > 0

    df_cent = compute_actor_centrality_and_roles(G)
    assert "pagerank" in df_cent.columns
    assert "communication_role" in df_cent.columns

    clusters = detect_coordinated_clusters(G, min_cluster_size=4)
    assert len(clusters) >= 1

    # Simpan ke DB in-memory
    _, Session = init_database("sqlite:///:memory:")
    session = Session()
    korpus = simpan_korpus(
        session, "MBG", "MBG", "csv", date(2026, 3, 1), date(2026, 3, 10)
    )
    simpan_postings_dan_akun(session, korpus.id, df_mock)
    run = simpan_run_model(session, "v0.1", {"seed": 42}, seed=42)
    df_scores = calculate_bot_score_and_explain(extract_account_features(df_mock))
    saved_scores = simpan_skor_akun(session, run.id, korpus.id, df_scores)
    saved_clusters = simpan_klaster(session, run.id, korpus.id, clusters)
    assert saved_scores > 0
    assert saved_clusters == len(clusters)
    session.close()
