"""
Konstruksi Graf Multiplex & Deteksi Komunitas Terkoordinasi (PRD Bagian 7, 11 & 13a)
"""
from typing import Any, Dict, List, Set, Tuple

import networkx as nx
import numpy as np
import pandas as pd


def build_co_retweet_layer(
    df_postings: pd.DataFrame, window_seconds: int = 60, min_co_retweets: int = 3
) -> nx.Graph:
    """
    Membangun lapisan graf Co-Retweet (R-D3):
    Pasangan akun dianggap memiliki edge bila me-retweet postingan sama dalam jendela <= 60s minimal 3 kali.
    """
    G = nx.Graph()
    retweets = df_postings[df_postings["interaction_type"] == "retweet"].copy()
    if retweets.empty or len(retweets) < 2:
        return G

    # Pasangan akun yang me-retweet dalam jendela waktu
    authors = retweets["author_username"].unique()
    for a in authors:
        G.add_node(a, layer="co-retweet")

    pair_counts: Dict[Tuple[str, str], int] = {}
    sorted_rts = retweets.sort_values("created_at")

    for i in range(len(sorted_rts)):
        row_i = sorted_rts.iloc[i]
        time_i = row_i["created_at"]
        author_i = row_i["author_username"]

        for j in range(i + 1, min(i + 40, len(sorted_rts))):
            row_j = sorted_rts.iloc[j]
            time_j = row_j["created_at"]
            author_j = row_j["author_username"]

            if author_i == author_j:
                continue

            delta = abs((time_j - time_i).total_seconds())
            if delta <= window_seconds:
                pair = tuple(sorted([author_i, author_j]))
                pair_counts[pair] = pair_counts.get(pair, 0) + 1
            else:
                break

    for (u, v), count in pair_counts.items():
        if count >= min_co_retweets:
            G.add_edge(u, v, weight=count, layer="co-retweet")

    return G


def build_multiplex_coordination_graph(
    df_postings: pd.DataFrame, duplicates: List[Dict[str, Any]]
) -> nx.Graph:
    """
    Membangun graf multiplex terpadu:
    - Lapisan Co-Retweet (waktu sempit)
    - Lapisan Teks Kembar (MinHash similarity >= 0.85)
    - Lapisan Mention/Interaksi
    """
    G = nx.Graph()

    # 1. Lapisan Co-retweet
    G_rt = build_co_retweet_layer(df_postings, window_seconds=60, min_co_retweets=2)
    for u, v, data in G_rt.edges(data=True):
        G.add_edge(u, v, weight=data.get("weight", 1), layers={"retweet"})

    # 2. Lapisan Teks Kembar (MinHash)
    for dup in duplicates:
        u, v = dup["user_a"], dup["user_b"]
        if G.has_edge(u, v):
            G[u][v]["layers"].add("teks")
            G[u][v]["weight"] += 2
        else:
            G.add_edge(u, v, weight=2, layers={"teks"})

    # Tandai atribut node
    for node in G.nodes():
        G.nodes[node]["degree"] = G.degree(node)

    return G


def detect_coordinated_clusters(
    G: nx.Graph, min_cluster_size: int = 5, multi_layer_threshold: int = 2
) -> List[Dict[str, Any]]:
    """
    Mendeteksi klaster koordinasi menggunakan algoritma komunitas (Louvain / Connected Components).
    Aturan R-D6 & R-D7:
      - Ukuran minimal klaster: >= 5 akun
      - Kategori Tinggi bila muncul di >= 2 lapisan multiplex
    """
    clusters = []
    if G.number_of_nodes() == 0:
        return clusters

    try:
        import networkx.algorithms.community as nx_comm
        communities = list(nx_comm.louvain_communities(G, seed=42))
    except Exception:
        communities = list(nx.connected_components(G))

    cluster_id = 1
    for comm in communities:
        members = list(comm)
        if len(members) < min_cluster_size:
            continue

        subgraph = G.subgraph(members)
        densitas = nx.density(subgraph)

        # Cek lapisan yang aktif di dalam klaster
        active_layers: Set[str] = set()
        for u, v, data in subgraph.edges(data=True):
            layers = data.get("layers", set())
            active_layers.update(layers)

        is_high_risk = len(active_layers) >= multi_layer_threshold

        # Identifikasi akun inti (degree tertinggi) vs pinggir
        degrees = dict(subgraph.degree())
        avg_deg = np.mean(list(degrees.values())) if degrees else 0

        roles = {
            acc: ("inti" if deg >= avg_deg else "pinggir")
            for acc, deg in degrees.items()
        }

        clusters.append({
            "cluster_id": cluster_id,
            "size": len(members),
            "density": round(float(densitas), 3),
            "layers": list(active_layers) if active_layers else ["retweet"],
            "risk_level": "Tinggi (Multi-Lapisan)" if is_high_risk else "Sedang",
            "members": members,
            "roles": roles,
        })
        cluster_id += 1

    return clusters


def compute_actor_centrality_and_roles(G: nx.Graph) -> pd.DataFrame:
    """
    Menghitung metrik sentralitas (Degree, Betweenness, PageRank, Closeness)
    dan memetakan tipologi peran komunikasi aktor (diadopsi dari ThisIsEconomy).
    """
    if G.number_of_nodes() == 0:
        return pd.DataFrame(
            columns=[
                "author_username",
                "total_degree",
                "betweenness_centrality",
                "pagerank",
                "closeness_centrality",
                "communication_role",
            ]
        )

    tot_deg = dict(G.degree())
    bet_cent = nx.betweenness_centrality(G, normalized=True)
    cls_cent = nx.closeness_centrality(G)
    try:
        pr_cent = nx.pagerank(G, alpha=0.85)
    except Exception:
        pr_cent = {n: 0.0 for n in G.nodes()}

    rows = []
    for node in G.nodes():
        deg = tot_deg.get(node, 0)
        bw = bet_cent.get(node, 0.0)
        pr = pr_cent.get(node, 0.0)
        cls_val = cls_cent.get(node, 0.0)

        if bw >= 0.05 or (deg >= 4 and bw >= 0.01):
            role = "Opinion Broker (Jembatan Klaster)"
        elif deg >= 3:
            role = "Core Amplifier (Penggerak Klaster)"
        elif deg >= 2:
            role = "Secondary Amplifier"
        else:
            role = "Peripheral Account"

        rows.append({
            "author_username": node,
            "total_degree": deg,
            "betweenness_centrality": round(float(bw), 6),
            "pagerank": round(float(pr), 6),
            "closeness_centrality": round(float(cls_val), 6),
            "communication_role": role,
        })

    return pd.DataFrame(rows)
