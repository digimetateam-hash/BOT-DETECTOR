"""
Operasi CRUD Database SQLAlchemy untuk 11 tabel PRD (Bagian 12 & 12a).
Semua username asli wajib di-hash menggunakan SHA-256 + salt sebelum disimpan.
"""
import json
from datetime import date
from typing import Any, Dict, List, Optional

import pandas as pd
from sqlalchemy.orm import Session

from db.schema import (
    Akun,
    AnggotaKlaster,
    KlasterKoordinasi,
    Korpus,
    LabelManual,
    Posting,
    RunModel,
    SkorAkun,
    hash_handle,
)


def simpan_korpus(
    session: Session,
    nama_isu: str,
    query: str,
    sumber: str,
    periode_mulai: date,
    periode_akhir: date,
) -> Korpus:
    """Menyimpan metadata korpus baru ke database."""
    korpus = Korpus(
        nama_isu=nama_isu,
        query=query,
        sumber=sumber,
        periode_mulai=periode_mulai,
        periode_akhir=periode_akhir,
    )
    session.add(korpus)
    session.commit()
    session.refresh(korpus)
    return korpus


def simpan_postings_dan_akun(
    session: Session,
    korpus_id: int,
    df_postings: pd.DataFrame,
    salt: Optional[str] = None,
) -> Dict[str, int]:
    """
    Menyimpan akun (dengan handle_hash SHA-256) dan postingan ke database.
    Melakukan deduplikasi id_platform per korpus.
    """
    akun_cache: Dict[str, int] = {}
    akun_baru = 0
    posting_baru = 0

    for _, row in df_postings.iterrows():
        raw_user = str(row["author_username"])
        h_hash = hash_handle(raw_user, salt=salt)

        if h_hash not in akun_cache:
            akun = session.query(Akun).filter(Akun.handle_hash == h_hash).first()
            if akun is None:
                akun = Akun(
                    handle_hash=h_hash,
                    platform="x",
                    followers=int(row.get("followers", 0) or 0),
                    following=int(row.get("following", 0) or 0),
                    avatar_default=bool(row.get("is_default_avatar", False)),
                    bio_kosong=bool(row.get("is_empty_bio", False)),
                )
                session.add(akun)
                session.flush()
                akun_baru += 1
            akun_cache[h_hash] = akun.id

        id_plat = str(row["id_platform"])
        exists = (
            session.query(Posting)
            .filter(Posting.korpus_id == korpus_id, Posting.id_platform == id_plat)
            .first()
        )
        if exists is None:
            posting = Posting(
                id_platform=id_plat,
                korpus_id=korpus_id,
                akun_id=akun_cache[h_hash],
                tipe=str(row.get("interaction_type", "post")),
                waktu=row["created_at"],
                teks=str(row.get("text", "")),
            )
            session.add(posting)
            posting_baru += 1

    session.commit()
    return {"akun_baru": akun_baru, "posting_baru": posting_baru}


def simpan_run_model(
    session: Session,
    versi_model: str,
    parameter: Dict[str, Any],
    seed: int,
    catatan: Optional[str] = None,
) -> RunModel:
    """Mencatat metadata eksekusi model untuk reprodusibilitas (PRD 13b)."""
    run = RunModel(
        versi_model=versi_model,
        parameter=json.dumps(parameter),
        seed=seed,
        catatan=catatan,
    )
    session.add(run)
    session.commit()
    session.refresh(run)
    return run


def simpan_skor_akun(
    session: Session,
    run_id: int,
    korpus_id: int,
    df_scores: pd.DataFrame,
    salt: Optional[str] = None,
) -> int:
    """Menyimpan hasil skor akun dan top-5 fitur pemicu ke tabel skor_akun."""
    saved = 0
    for _, row in df_scores.iterrows():
        h_hash = hash_handle(str(row["author_username"]), salt=salt)
        akun = session.query(Akun).filter(Akun.handle_hash == h_hash).first()
        if akun is None:
            continue

        skor_obj = SkorAkun(
            run_id=run_id,
            akun_id=akun.id,
            korpus_id=korpus_id,
            skor=float(row["skor"]),
            kategori=str(row["kategori"]),
            fitur_pemicu=str(row.get("top_features", "[]")),
        )
        session.add(skor_obj)
        saved += 1

    session.commit()
    return saved


def simpan_label_manual(
    session: Session,
    akun_id: int,
    korpus_id: int,
    coder: str,
    label: str,
    catatan: Optional[str] = None,
) -> LabelManual:
    """Menyimpan label manual dari coder (manusia, bot, ragu)."""
    lbl = LabelManual(
        akun_id=akun_id,
        korpus_id=korpus_id,
        coder=coder,
        label=label,
        catatan=catatan,
    )
    session.add(lbl)
    session.commit()
    session.refresh(lbl)
    return lbl


def simpan_klaster(
    session: Session,
    run_id: int,
    korpus_id: int,
    clusters: List[Dict[str, Any]],
    jendela_waktu: int = 60,
    salt: Optional[str] = None,
) -> int:
    """Menyimpan klaster koordinasi beserta anggotanya ke database."""
    saved = 0
    for c in clusters:
        lapisan = "multiplex" if len(c.get("layers", [])) > 1 else c.get("layers", ["retweet"])[0]
        klaster = KlasterKoordinasi(
            run_id=run_id,
            korpus_id=korpus_id,
            lapisan=lapisan,
            jumlah_akun=int(c["size"]),
            densitas=float(c.get("density", 0.0)),
            jendela_waktu=jendela_waktu,
        )
        session.add(klaster)
        session.flush()

        for member in c.get("members", []):
            h_hash = hash_handle(str(member), salt=salt)
            akun = session.query(Akun).filter(Akun.handle_hash == h_hash).first()
            if akun:
                anggota = AnggotaKlaster(
                    klaster_id=klaster.id,
                    akun_id=akun.id,
                    peran=c.get("roles", {}).get(member, "pinggir"),
                )
                session.add(anggota)
        saved += 1

    session.commit()
    return saved
