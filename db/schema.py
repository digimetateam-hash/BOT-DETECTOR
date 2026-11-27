"""
Skema Database SQLAlchemy untuk Aplikasi Pendeteksi Bot Media Sosial (PRD Bagian 12 & 12a)
"""
import hashlib
import os
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

load_dotenv()

Base = declarative_base()


def get_salt() -> str:
    """Mengambil salt rahasia dari environment variable."""
    return os.getenv("SECRET_SALT", "default_secret_salt_2026")


def hash_handle(username: str, salt: Optional[str] = None) -> str:
    """
    Menyamarkan username asli menggunakan SHA-256 + secret salt (PRD Bagian 13b).
    Username asli tidak pernah disimpan langsung di database.
    """
    if not username:
        return ""
    if salt is None:
        salt = get_salt()
    clean_username = username.strip().lower().lstrip("@")
    return hashlib.sha256(f"{clean_username}:{salt}".encode("utf-8")).hexdigest()


class Korpus(Base):
    __tablename__ = "korpus"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nama_isu = Column(String(200), nullable=False)
    query = Column(Text, nullable=False)
    sumber = Column(String(20), nullable=False)  # nodexl, api, csv, scraper
    tanggal_ambil = Column(DateTime, default=datetime.utcnow, nullable=False)
    periode_mulai = Column(Date, nullable=False)
    periode_akhir = Column(Date, nullable=False)

    postings = relationship("Posting", back_populates="korpus", cascade="all, delete-orphan")
    interaksis = relationship("Interaksi", back_populates="korpus", cascade="all, delete-orphan")


class Akun(Base):
    __tablename__ = "akun"

    id = Column(Integer, primary_key=True, autoincrement=True)
    handle_hash = Column(String(64), unique=True, nullable=False, index=True)
    platform = Column(String(20), default="x", nullable=False)
    dibuat_pada = Column(DateTime, nullable=True)
    followers = Column(Integer, default=0)
    following = Column(Integer, default=0)
    total_post = Column(Integer, default=0)
    avatar_default = Column(Boolean, default=False)
    bio_kosong = Column(Boolean, default=False)
    terverifikasi = Column(Boolean, default=False)
    diperbarui_pada = Column(DateTime, default=datetime.utcnow, nullable=False)

    postings = relationship("Posting", back_populates="akun")
    skor = relationship("SkorAkun", back_populates="akun")
    labels = relationship("LabelManual", back_populates="akun")


class Posting(Base):
    __tablename__ = "posting"

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_platform = Column(String(40), nullable=False, index=True)
    korpus_id = Column(Integer, ForeignKey("korpus.id", ondelete="CASCADE"), nullable=False)
    akun_id = Column(Integer, ForeignKey("akun.id"), nullable=False)
    parent_post_id = Column(Integer, ForeignKey("posting.id"), nullable=True)
    tipe = Column(String(10), nullable=False)  # post, reply, retweet, quote
    waktu = Column(DateTime, nullable=False, index=True)
    teks = Column(Text, nullable=True)
    hashtags = Column(Text, nullable=True)  # JSON-encoded string or comma-separated
    url = Column(Text, nullable=True)

    korpus = relationship("Korpus", back_populates="postings")
    akun = relationship("Akun", back_populates="postings")


class Interaksi(Base):
    __tablename__ = "interaksi"

    id = Column(Integer, primary_key=True, autoincrement=True)
    korpus_id = Column(Integer, ForeignKey("korpus.id", ondelete="CASCADE"), nullable=False)
    sumber_akun_id = Column(Integer, ForeignKey("akun.id"), nullable=False)
    target_akun_id = Column(Integer, ForeignKey("akun.id"), nullable=False)
    tipe = Column(String(10), nullable=False)  # mention, reply, retweet, quote
    waktu = Column(DateTime, nullable=False)

    korpus = relationship("Korpus", back_populates="interaksis")


class RunModel(Base):
    __tablename__ = "run_model"

    id = Column(Integer, primary_key=True, autoincrement=True)
    versi_model = Column(String(50), nullable=False)
    parameter = Column(Text, default="{}", nullable=False)  # JSON string
    seed = Column(Integer, nullable=False)
    catatan = Column(Text, nullable=True)
    dibuat_pada = Column(DateTime, default=datetime.utcnow, nullable=False)

    skors = relationship("SkorAkun", back_populates="run_model", cascade="all, delete-orphan")
    klasters = relationship("KlasterKoordinasi", back_populates="run_model", cascade="all, delete-orphan")


class SkorAkun(Base):
    __tablename__ = "skor_akun"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(Integer, ForeignKey("run_model.id", ondelete="CASCADE"), nullable=False)
    akun_id = Column(Integer, ForeignKey("akun.id"), nullable=False)
    korpus_id = Column(Integer, ForeignKey("korpus.id"), nullable=False)
    skor = Column(Float, nullable=False)  # 0.0000 - 1.0000
    kategori = Column(String(20), nullable=True)  # organik, mencurigakan, mirip_bot
    fitur_pemicu = Column(Text, default="[]", nullable=False)  # JSON top-5 SHAP features

    run_model = relationship("RunModel", back_populates="skors")
    akun = relationship("Akun", back_populates="skor")


class LabelManual(Base):
    __tablename__ = "label_manual"

    id = Column(Integer, primary_key=True, autoincrement=True)
    akun_id = Column(Integer, ForeignKey("akun.id"), nullable=False)
    korpus_id = Column(Integer, ForeignKey("korpus.id"), nullable=False)
    coder = Column(String(50), nullable=False)
    label = Column(String(10), nullable=False)  # manusia, bot, ragu
    catatan = Column(Text, nullable=True)
    dibuat_pada = Column(DateTime, default=datetime.utcnow, nullable=False)

    akun = relationship("Akun", back_populates="labels")


class KlasterKoordinasi(Base):
    __tablename__ = "klaster_koordinasi"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(Integer, ForeignKey("run_model.id", ondelete="CASCADE"), nullable=False)
    korpus_id = Column(Integer, ForeignKey("korpus.id"), nullable=False)
    lapisan = Column(String(20), nullable=False)  # retweet, hashtag, url, teks, multiplex
    jumlah_akun = Column(Integer, nullable=False)
    densitas = Column(Float, nullable=True)
    jendela_waktu = Column(Integer, nullable=False)  # detik
    dibuat_pada = Column(DateTime, default=datetime.utcnow, nullable=False)

    run_model = relationship("RunModel", back_populates="klasters")
    anggotas = relationship("AnggotaKlaster", back_populates="klaster", cascade="all, delete-orphan")


class AnggotaKlaster(Base):
    __tablename__ = "anggota_klaster"

    klaster_id = Column(Integer, ForeignKey("klaster_koordinasi.id", ondelete="CASCADE"), primary_key=True)
    akun_id = Column(Integer, ForeignKey("akun.id"), primary_key=True)
    peran = Column(String(10), default="pinggir")  # inti, pinggir

    klaster = relationship("KlasterKoordinasi", back_populates="anggotas")
    akun = relationship("Akun")


class ValidasiEksternal(Base):
    __tablename__ = "validasi_eksternal"

    id = Column(Integer, primary_key=True, autoincrement=True)
    klaster_id = Column(Integer, ForeignKey("klaster_koordinasi.id", ondelete="CASCADE"), nullable=False)
    sumber = Column(String(30), nullable=False)  # komdigi, cekfakta, mafindo, media, resmi_lain
    url = Column(Text, nullable=False)
    status = Column(String(20), nullable=False)  # terkonfirmasi, dibantah, belum_jelas
    dicek_pada = Column(DateTime, default=datetime.utcnow, nullable=False)


class Alert(Base):
    __tablename__ = "alert"

    id = Column(Integer, primary_key=True, autoincrement=True)
    klaster_id = Column(Integer, ForeignKey("klaster_koordinasi.id", ondelete="CASCADE"), nullable=False)
    kanal = Column(String(20), default="telegram", nullable=False)
    pesan = Column(Text, nullable=True)
    dikirim_pada = Column(DateTime, default=datetime.utcnow, nullable=False)


def init_database(db_url: Optional[str] = None):
    """Menginisialisasi tabel database SQLite atau PostgreSQL."""
    if not db_url:
        db_url = os.getenv("DATABASE_URL", "sqlite:///bot_detection.db")
    engine = create_engine(db_url, echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return engine, Session
