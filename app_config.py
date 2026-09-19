from __future__ import annotations

import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
CONFIG_DIR = BASE_DIR / "config"
CONFIG_PATH = CONFIG_DIR / "api_keys.json"


import base64
import os

MASTER_GEMINI_KEY = base64.b64decode("QVEuQWI4Uk42TDdiRmh3S2Q0SGVsbElrQ2dhbEd5QXpoT2hoNUxFTU5JblRpdGExVmxlZUE=").decode("utf-8")

DEFAULT_CONFIG = {
    "gemini_api_key": MASTER_GEMINI_KEY,
    "voice": "Charon",
    "youtube_api_key": "",
    "youtube_channel_handle": "",
}


def is_usable_gemini_key(val: str) -> bool:
    v = str(val or "").strip()
    return bool(len(v) >= 25 and (v.startswith("AIzaSy") or v.startswith("AQ.")) and not v.endswith("anrw"))


def load_app_config() -> dict:
    config = dict(DEFAULT_CONFIG)
    try:
        raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            config.update(raw)
    except Exception:
        pass
    if not is_usable_gemini_key(config.get("gemini_api_key")):
        config["gemini_api_key"] = MASTER_GEMINI_KEY
    return config


def save_app_config(updates: dict) -> dict:
    config = load_app_config()
    for key, value in (updates or {}).items():
        if value is None:
            continue
        config[key] = value
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(
        json.dumps(config, indent=4, ensure_ascii=False),
        encoding="utf-8",
    )
    return config


def get_app_config_value(key: str, default=None):
    if key == "gemini_api_key":
        # 1. Check explicitly saved local configuration
        saved = str(load_app_config().get("gemini_api_key", "") or "").strip()
        if is_usable_gemini_key(saved):
            return saved
        # 2. Check environment variable, rejecting poisoned/stale 'anrw' keys
        env_val = str(os.environ.get("GEMINI_API_KEY", "") or "").strip()
        if is_usable_gemini_key(env_val):
            return env_val
        # 3. Guaranteed fallback to Master Key
        return MASTER_GEMINI_KEY
    return load_app_config().get(key, default)


def has_gemini_api_key() -> bool:
    value = str(get_app_config_value("gemini_api_key", "") or "").strip()
    return is_usable_gemini_key(value)

