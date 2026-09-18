"""
JARVIS — Yol Arkadaşı Modu (Companion Mode)
Dinamik, arkadaş canlısı ve kişiselleştirilmiş sohbet modunu yönetir.
"""

from __future__ import annotations

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = BASE_DIR / "memory" / "companion_settings.json"


def _load_settings() -> dict:
    try:
        if CONFIG_FILE.exists():
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {"enabled": True, "mode": "friendly", "tone": "samimi ve enerjik"}


def _save_settings(data: dict):
    try:
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def companion_mode(mode: str = "friendly", enabled: bool = True) -> str:
    """
    Dinamik ve arkadaş canlısı sohbet modunu aktif veya pasif eder.
    mode: 'friendly' (arkadaş canlısı, esprili, samimi) | 'formal' (resmi, profesyonel asistan) | 'concise' (ultra kısa ve doğrudan) | 'coach' (motive edici yaşam koçu)
    enabled: Modun açık veya kapalı olması
    """
    mode = (mode or "friendly").strip().lower()
    data = _load_settings()
    data["enabled"] = bool(enabled)
    data["mode"] = mode

    if not enabled:
        data["tone"] = "standart asistan"
        _save_settings(data)
        return "Standart asistan moduna dönüldü. Yanıtlar tarafsız ve doğrudan iletilecek."

    tones = {
        "friendly": "Arkadaş Canlısı ve Dinamik — Samimi, esprili ve içten bir yol arkadaşı.",
        "formal": "Resmi ve Profesyonel — Ciddi, kusursuz iş dili ve mesafeli asistan.",
        "concise": "Ultra Kısa — Sıfır gereksiz kelime, anında sonuç odaklı.",
        "coach": "Motivasyonel Koç — Hedef odaklı, teşvik edici ve yüksek enerjili."
    }

    selected_desc = tones.get(mode, tones["friendly"])
    data["tone"] = selected_desc
    _save_settings(data)

    return f"🌟 Yol Arkadaşı Modu Aktif!\nSeçilen Ton: {selected_desc}\nŞimdi nasıl yardımcı olabilirim?"
