"""
Loader konfigurasi ambang batas dari config.yaml (PRD Bagian 13a & 13c).
Dilarang hardcode ambang batas di dalam kode sumber.
"""
import os
from typing import Any, Dict, Optional

import yaml


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Membaca berkas config.yaml dan mengembalikan dictionary konfigurasi."""
    if config_path is None:
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        config_path = os.path.join(root_dir, "config.yaml")

    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
