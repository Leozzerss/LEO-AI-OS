#!/usr/bin/env python3
"""
JARVIS — Telefon köprüsü (uygulama içi)
────────────────────────────────────────
JARVIS arayüzündeki "JARVIS TELEFON" panelinin arka ucu. Telefon web
sunucusunu (jarvis_web/server.py), Mac ajanını (agent.py) ve Cloudflare
tünelini alt-süreç olarak başlatır; genel adres + token'ı verir; durdurur.

UI'dan bağımsız — tkinter'e dokunmaz. Durum callback'lerle bildirilir.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import threading
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
WEB_DIR  = BASE_DIR / "jarvis_web"

_URL_RE = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")


def _find_exe(name: str) -> str | None:
    """GUI uygulamalarında PATH eksik olabilir — bilinen yerlere de bak."""
    import shutil
    hit = shutil.which(name)
    if hit:
        return hit
    for p in (f"/opt/homebrew/bin/{name}", f"/usr/local/bin/{name}"):
        if Path(p).is_file():
            return p
    return None


class PhoneBridge:
    def __init__(self):
        self._procs: list[subprocess.Popen] = []
        self._tunnel_log = Path("/tmp/jarvis_phone_tunnel.log")
        self.url: str | None = None
        self.token: str | None = None
        self.running = False

    # ── Yardımcılar ──────────────────────────────────────────────────────────
    def _python(self) -> str:
        """Sunucu/ajanı çalıştıracak Python — bu uygulamanın yorumlayıcısı."""
        return sys.executable or "python3"

    def _read_token(self) -> str | None:
        try:
            cfg = json.loads((WEB_DIR / "web_config.json").read_text(encoding="utf-8"))
            return str(cfg.get("token", "") or "") or None
        except Exception:
            return None

    def cloudflared_available(self) -> bool:
        return _find_exe("cloudflared") is not None

    # ── Başlat ───────────────────────────────────────────────────────────────
    def start(self, on_ready, on_error, on_status=None):
        """Süreçleri başlatır; hazır olunca on_ready(url, token) çağrılır.
        Hepsi ayrı bir thread'de — UI donmaz."""
        if self.running:
            return
        threading.Thread(
            target=self._start_worker,
            args=(on_ready, on_error, on_status or (lambda s: None)),
            daemon=True,
        ).start()

    def _start_worker(self, on_ready, on_error, on_status):
        try:
            if not WEB_DIR.exists():
                on_error("Telefon dosyaları bulunamadı (jarvis_web).")
                return

            cf = _find_exe("cloudflared")
            if not cf:
                on_error("cloudflared kurulu değil. Terminal'de: brew install cloudflared")
                return

            py = self._python()
            env_note = {"PYTHONUNBUFFERED": "1"}
            import os
            env = {**os.environ, **env_note}

            on_status("Sunucu başlatılıyor...")
            self._procs.append(subprocess.Popen(
                [py, "-u", "server.py"], cwd=str(WEB_DIR),
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env))
            time.sleep(2)

            on_status("Mac ajanı başlatılıyor...")
            self._procs.append(subprocess.Popen(
                [py, "-u", "agent.py"], cwd=str(WEB_DIR),
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env))

            on_status("Genel adres alınıyor...")
            self._tunnel_log.write_text("", encoding="utf-8")
            with open(self._tunnel_log, "w") as logf:
                self._procs.append(subprocess.Popen(
                    [cf, "tunnel", "--url", "http://localhost:8765"],
                    stdout=logf, stderr=subprocess.STDOUT))

            # URL'i bekle (en çok ~30 sn)
            url = None
            for _ in range(60):
                try:
                    txt = self._tunnel_log.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    txt = ""
                m = _URL_RE.search(txt)
                if m:
                    url = m.group(0)
                    break
                time.sleep(0.5)

            self.token = self._read_token()
            if not url:
                # Tünel alınamadı — yerelden dene
                url = "http://localhost:8765"
            self.url = url
            self.running = True
            full = f"{url}/?t={self.token}" if self.token else url
            on_ready(full, self.token or "")
        except Exception as exc:
            self.stop()
            on_error(f"Başlatılamadı: {exc}")

    # ── Durdur ───────────────────────────────────────────────────────────────
    def stop(self):
        for p in self._procs:
            try:
                p.terminate()
            except Exception:
                pass
        # Kısa süre sonra hâlâ yaşayan varsa zorla kapat
        time.sleep(0.3)
        for p in self._procs:
            try:
                if p.poll() is None:
                    p.kill()
            except Exception:
                pass
        self._procs = []
        self.running = False
        self.url = None
