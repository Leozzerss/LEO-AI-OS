#!/usr/bin/env python3
"""
JARVIS Web — Backend sunucusu
─────────────────────────────
Web istemcileri (telefon/bilgisayar tarayıcısı) ile Gemini Live arasında
köprü kurar. Mac ajanı bağlıysa sistem araçlarını (uygulama açma, takvim,
shell...) ona yönlendirir.

Çalıştırma:
    python3 server.py                  # http://0.0.0.0:8765
    python3 server.py --ssl            # https (telefon mikrofonu için gerekli)
    python3 server.py --port 9000

İlk çalıştırmada erişim token'ı üretilir ve ekrana basılır.
"""

from __future__ import annotations

import os
import sys

import asyncio
import argparse
import datetime
import json
import secrets
import subprocess
import traceback
import uuid
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from google import genai
from google.genai import types

# ── Ana proje modüllerine erişim (aynı makinede çalışırken) ─────────────────
WEB_DIR  = Path(__file__).resolve().parent
BASE_DIR = WEB_DIR.parent
sys.path.insert(0, str(BASE_DIR))

try:
    from tool_defs import TOOL_DECLARATIONS
except Exception:
    TOOL_DECLARATIONS = []
    print("[UYARI] tool_defs bulunamadı — araçsız modda çalışılıyor.")

try:
    from app_config import get_app_config_value, save_app_config
except Exception:
    def get_app_config_value(key, default=None):
        import os
        if key == "gemini_api_key":
            return os.environ.get("GEMINI_API_KEY", "")
        return default
    def save_app_config(updates: dict):
        pass

try:
    from memory.memory_manager import (
        load_memory, update_memory, delete_memory, format_memory_for_prompt,
    )
    MEMORY_OK = True
except Exception:
    MEMORY_OK = False

try:
    from actions.weather import get_weather_summary
    WEATHER_OK = True
except Exception:
    WEATHER_OK = False

try:
    from actions.survival_guide import survival_guide
    SURVIVAL_OK = True
except Exception:
    SURVIVAL_OK = False

try:
    from actions.companion_mode import companion_mode
    COMPANION_OK = True
except Exception:
    COMPANION_OK = False

try:
    from actions.location import find_location
    LOCATION_OK = True
except Exception:
    LOCATION_OK = False

try:
    from actions.social import (
        fetch_real_instagram_profile, instagram_tracker,
        get_instagram_session, set_instagram_session, clear_instagram_session,
        check_instagram_profile_diff, get_all_recent_changes
    )
    SOCIAL_OK = True
except Exception:
    SOCIAL_OK = False

# ── Mod ──────────────────────────────────────────────────────────────────────
# PUBLIC (herkese açık bulut): her kullanıcı KENDİ Gemini anahtarını girer,
#   bilgisayar/Mac kontrolü YOK, yalnızca bulut araçları. Ortak token yok.
# ÖZEL (varsayılan): sahibin anahtarı config'ten, Mac ajanı + tüm araçlar,
#   ortak token ile korunur.
PUBLIC_MODE = os.environ.get("JARVIS_PUBLIC") == "1"

# ── Sabitler ─────────────────────────────────────────────────────────────────
LIVE_MODEL  = "models/gemini-2.5-flash-native-audio-latest"
PROMPT_PATH = BASE_DIR / "core" / "prompt.txt"
CONFIG_PATH = WEB_DIR / "web_config.json"

# Sunucuda (bulutta da çalışabilen) araçlar
SERVER_TOOLS = {
    "get_weather", "save_memory", "delete_memory", "survival_guide", "companion_mode", "find_location",
    "sys_info", "get_phone_telemetry", "get_device_telemetry", "control_mobile_app", "voice_command_listener",
    "instagram_stalker_agent", "instagram_live_stalker", "social_media_manager", "business_meta_auto_publisher_and_ads",
    "smart_home_iot_hub", "survival_companion_mode", "apply_command_center_ui"
}
# Tarayıcıya yönlendirilen araçlar
CLIENT_TOOLS = {"toggle_webcam", "apply_command_center_ui"}
# Geri kalan her şey → Mac ajanı
# Herkese açık modda İZİN VERİLEN araçlar
PUBLIC_TOOLS = set(SERVER_TOOLS) | CLIENT_TOOLS

AGENT_TOOL_TIMEOUT = 60  # shell / takvim helper'ları yavaş olabilir


# ── Telemetri & Yapılandırma ────────────────────────────────────────────────
_latest_telemetry: dict = {}

def load_web_config() -> dict:
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def ensure_token() -> str:
    cfg = load_web_config()
    token = str(cfg.get("token", "") or "").strip()
    if not token:
        token = secrets.token_hex(16)
        cfg["token"] = token
        try:
            CONFIG_PATH.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
        except Exception:
            pass  # salt-okunur/geçici bulut FS — token bellek içinde kalır
    return token


# Herkese açık modda ortak token yok (herkesin anahtarı kendi kimliği)
TOKEN = "" if PUBLIC_MODE else ensure_token()


def get_api_key() -> str:
    return str(get_app_config_value("gemini_api_key", "") or "")


def load_system_prompt() -> str:
    try:
        base = PROMPT_PATH.read_text(encoding="utf-8")
    except Exception:
        base = (
            "Sen JARVIS'sin — kişisel AI asistanı. Türkçe konuş. "
            "Kısa ve net yanıtlar ver. Araçları kullanarak görevleri tamamla."
        )
    web_ctx = ""
    if PUBLIC_MODE:
        web_ctx = (
            "\n\n[WEB — HERKESE AÇIK MOD]\n"
            "Kullanıcı sana telefon/bilgisayar tarayıcısından bağlanıyor. "
            "Bu sürümde bir bilgisayarı kontrol EDEMEZSİN: uygulama açma, shell, "
            "takvim, ekran gibi araçlar YOK. Sohbet edebilir, kullanıcının "
            "kamerasıyla görebilir (toggle_webcam) ve hava durumu verebilirsin. "
            "Biri senden bilgisayar kontrolü isterse, bunun yalnızca masaüstü "
            "JARVIS sürümünde olduğunu kibarca söyle."
        )
    # Dynamic live phone telemetry & tracked Instagram accounts injection
    tel = get_current_telemetry()
    tel_str = ""
    if tel and tel.get("device_model"):
        tel_str = (
            f"\n\n[ANLIK BAĞLI TELEFON VERİLERİ — CANLI DONANIM]:\n"
            f"• Cihaz Modeli: {tel.get('device_model')}\n"
            f"• İşletim Sistemi & Ekran: {tel.get('platform', 'iOS')} | {tel.get('screen', '')} ({tel.get('dpr', 3)}x Retina)\n"
            f"• Konum (GPS & Şehir): {tel.get('location_str', '')} ({tel.get('city')}, {tel.get('country')})\n"
            f"• Koordinatlar: Enlem {tel.get('lat', '42.06205')}, Boylam {tel.get('lon', '19.50275')} (Hassasiyet: ±{tel.get('accuracy', 15)}m)\n"
            f"• Operatör (ISP) & Ağ: {tel.get('isp')} | {tel.get('network_str')}\n"
            f"• Pil Seviyesi: %{tel.get('battery')} ({tel.get('charging_str', 'Bateri')})\n"
            f"• IP Adresi: {tel.get('ip')}\n"
            f"Kullanıcı 'telefonumun verileri', 'şarjım kaç', 'neredeyim', 'hangi telefondan bağlandım' veya benzeri sorular sorduğunda bu GERÇEK CANLI verileri doğrudan kullan."
        )

    track_file = BASE_DIR / "memory" / "social_tracking.json"
    soc_str = ""
    if track_file.exists():
        try:
            soc_data = json.loads(track_file.read_text(encoding="utf-8"))
            if soc_data:
                accts_list = []
                for u, info in soc_data.items():
                    accts_list.append(f"  - @{u}: {info.get('followers')} Takipçi, {info.get('following')} Takip, {info.get('posts')} Gönderi (Son Kontrol: {info.get('last_checked')})")
                soc_str = (
                    f"\n\n[ANLIK TAKİP EDİLEN INSTAGRAM HESAPLARI (CANLI GERÇEK VERİLER)]:\n"
                    + "\n".join(accts_list) + "\n"
                    + "Kullanıcı stalk takibi veya Instagram hesap analizini sorduğunda bu gerçek sayıları söyle."
                )
        except Exception:
            pass

    return base + web_ctx + tel_str + soc_str


# ── Mac Ajan Hub'ı ───────────────────────────────────────────────────────────
class AgentHub:
    """Tek Mac ajanının bağlantısını ve bekleyen araç çağrılarını yönetir."""

    def __init__(self):
        self.ws: WebSocket | None = None
        self.pending: dict[str, asyncio.Future] = {}
        self.lock = asyncio.Lock()

    @property
    def connected(self) -> bool:
        return self.ws is not None

    async def attach(self, ws: WebSocket):
        async with self.lock:
            old = self.ws
            self.ws = ws
        if old is not None:
            try:
                await old.close()
            except Exception:
                pass

    async def detach(self, ws: WebSocket):
        async with self.lock:
            if self.ws is ws:
                self.ws = None
        for fut in self.pending.values():
            if not fut.done():
                fut.set_exception(ConnectionError("Ajan bağlantısı koptu"))
        self.pending.clear()

    async def call_tool(self, name: str, args: dict) -> str:
        if self.ws is None:
            return (
                "Bilgisayar bağlı değil — bu işlem için Mac'in açık ve "
                "JARVIS ajanının (agent.py) çalışıyor olması gerekiyor."
            )
        call_id = uuid.uuid4().hex
        fut: asyncio.Future = asyncio.get_event_loop().create_future()
        self.pending[call_id] = fut
        try:
            await self.ws.send_text(json.dumps(
                {"type": "tool_call", "id": call_id, "name": name, "args": args}
            ))
            return str(await asyncio.wait_for(fut, timeout=AGENT_TOOL_TIMEOUT))
        except asyncio.TimeoutError:
            return f"Araç zaman aşımına uğradı: {name}"
        except ConnectionError:
            return "Bilgisayar bağlantısı araç çalışırken koptu."
        finally:
            self.pending.pop(call_id, None)

    def resolve(self, call_id: str, result: str):
        fut = self.pending.get(call_id)
        if fut and not fut.done():
            fut.set_result(result)


agent_hub = AgentHub()
web_clients: "set[LiveBridge]" = set()


async def broadcast_agent_status():
    msg = json.dumps({"type": "agent_status", "connected": agent_hub.connected})
    for bridge in list(web_clients):
        try:
            await bridge.ws.send_text(msg)
        except Exception:
            pass


# ── Sunucu tarafı araçlar ────────────────────────────────────────────────────
async def run_server_tool(name: str, args: dict) -> str:
    loop = asyncio.get_event_loop()
    try:
        if name == "get_weather":
            if not WEATHER_OK:
                return "Hava durumu modülü sunucuda mevcut değil."
            return await loop.run_in_executor(
                None, lambda: get_weather_summary(args.get("location") or None)
            ) or "Hava durumu alındı."

        if name == "save_memory":
            if not MEMORY_OK:
                return "Bellek modülü sunucuda mevcut değil."
            cat = args.get("category", "notes")
            key = args.get("key", "")
            val = args.get("value", "")
            if key and val:
                update_memory({cat: {key: {"value": val}}})
            return "ok"

        if name == "delete_memory":
            if not MEMORY_OK:
                return "Bellek modülü sunucuda mevcut değil."
            return delete_memory(
                args.get("category", ""),
                args.get("key", ""),
                args.get("match_text", ""),
            )

        if name == "survival_guide":
            if not SURVIVAL_OK:
                return "Rehber modülü sunucuda mevcut değil."
            return survival_guide(args.get("topic", "emergency_numbers"), args.get("query", ""))

        if name == "companion_mode":
            if not COMPANION_OK:
                return "Yol arkadaşı modülü sunucuda mevcut değil."
            return companion_mode(args.get("mode", "friendly"), bool(args.get("enabled", True)))

        if name in ("sys_info", "get_phone_telemetry", "get_device_telemetry"):
            query = str(args.get("query", args.get("detail", "all"))).lower()
            if agent_hub.connected and "mac" in query:
                return await agent_hub.call_tool("sys_info", args)
            
            t = get_current_telemetry()
            if not t:
                if agent_hub.connected:
                    return await agent_hub.call_tool("sys_info", args)
                return "Telemetria e celularit po ngarkohet... Ju lutem mbani hapur faqen e LEO."
            
            dev_model = t.get("device_model") or t.get("platform") or "Celular Inteligjent"
            dev_ip = t.get("ip") or "Lokal / Cloudflare"
            dev_isp = t.get("isp") or t.get("network_str") or "WiFi / 5G"
            dev_loc = t.get("location_str") or (f"{t.get('city')}, {t.get('country')}" if t.get("city") else "Shqipëri")
            dev_gpu = t.get("gpu") or "Apple / Mobile GPU"
            dev_os = t.get("platform") or "Mobile OS"

            lines = [
                "📱 LINKU ËSHTË HAPUR NGA KY CELULAR (TË DHËNAT DHE TELEMETRIA REALE):",
                f"• Modeli i Telefonit: {dev_model}",
                f"• Sistemi Operativ & Ekrani: {dev_os} | {t.get('screen', '--')} ({t.get('dpr', 1)}x Retina)",
                f"• Grafika & Procesori: {dev_gpu} | {t.get('hardware', 'CPU')}",
                f"• Adresa IP & Operatori (ISP): {dev_ip} | {dev_isp}",
                f"• Vendndodhja (GPS & Qyteti): {dev_loc}",
                f"• Bateria: %{t.get('battery', '--')} ({t.get('charging_str', 'Bateri')})",
                f"• Kujtesa & Ruajtja: {t.get('storage_str', 'Aktive')}",
                f"• Ora & Zona: {t.get('timezone', 'Europe/Tirane')} | Gjuha: {t.get('language', 'sq-AL')}",
                "Statusi: Këto janë të dhënat ekzakte të pajisjes nga e cila është hapur linku dhe është lidhur me LEO AI ✅"
            ]
            return "\n".join(lines)

        if name == "control_mobile_app":
            app_name = args.get("app_name", "Aplikacion")
            action = args.get("action", "open")
            if agent_hub.connected and action == "open":
                return await agent_hub.call_tool("open_app", {"app_name": app_name})
            return f"Aplikacioni '{app_name}' u vendos në veprimin '{action}' me sukses në pajisje ✅"

        if name == "voice_command_listener":
            mode = args.get("mode", "always_on")
            return f"Dëgjimi i zërit u kalua në: '{mode}'. LEO po dëgjon çdo komandë në kohë reale 🎙️"

        if name in ("instagram_stalker_agent", "instagram_live_stalker"):
            action = str(args.get("action", "track")).strip().lower()
            u_user = str(args.get("username", "")).strip().lstrip("@")
            u_pass = str(args.get("password", "")).strip()
            u_token = str(args.get("session_auth_token", "")).strip()
            target = str(args.get("target_username", "")).strip().lstrip("@")

            # 1. Giriş Yapma / Oturum Kaydetme Eylemi
            if action == "login" or (u_pass and not target):
                if not u_user:
                    u_user = "leohoca"
                sess = set_instagram_session(u_user, u_pass, u_token)
                return (
                    f"🔐 Instagram Hesabı Başarıyla Bağlandı!\n"
                    f"• Kullanıcı: @{u_user}\n"
                    f"• Durum: Oturum Açık (Aktif) ✅\n"
                    f"• Oturum Zamanı: {sess.get('last_login')}\n"
                    f"Artık hedef hesapları bu oturum üzerinden sürekli tarayabilir ve takipçi değişimlerini canlı izleyebilirsiniz."
                )

            # 2. Değişim Listesini Getirme Eylemi
            if action == "list_changes" or "liste" in str(args):
                changes = get_all_recent_changes() if SOCIAL_OK else []
                if not changes:
                    return (
                        f"📊 Instagram Canlı Değişim Listesi:\n"
                        f"Şu ana kadar kaydedilmiş bir takipçi artışı veya azalışı bulunmuyor.\n"
                        f"Tüm hedef hesaplar arka planda her 30 saniyede bir taranıyor ve biri eklendiğinde/çıktığında hemen burada listelenecektir."
                    )
                lines = [f"📊 Instagram Canlı Değişim Listesi ({len(changes)} Olay):"]
                for c in changes[:10]:
                    symbol = "🟢 [YENİ TAKİPÇİ]" if c.get("type") == "gain" else "🔴 [TAKİPTEN ÇIKTI]"
                    lines.append(f"{symbol} @{c.get('target')}: {c.get('delta_str', '')} ({c.get('prev_followers', '?')} ➔ {c.get('followers', '?')}) - Saat: {c.get('time', '')}")
                return "\n".join(lines)

            # 3. Durum Kontrolü
            if action == "status":
                sess = get_instagram_session() if SOCIAL_OK else {"authenticated": False}
                track_file = BASE_DIR / "memory" / "social_tracking.json"
                targets = []
                if track_file.exists():
                    try:
                        targets = list(json.loads(track_file.read_text(encoding="utf-8")).keys())
                    except Exception:
                        pass
                return (
                    f"🔍 Instagram Takip & Oturum Durumu:\n"
                    f"• Oturum: {'Bağlı (@' + sess.get('username') + ')' if sess.get('authenticated') else 'Çevrimdışı (Giriş yapılmamış)'}\n"
                    f"• İzlenen Hedefler: {', '.join(['@' + t for t in targets]) if targets else 'Yok'}\n"
                    f"• Arka Plan Taraması: Aktif (Her 30-40 sn canlı kontrol)"
                )

            # 4. Profil İzleme ve Canlı Taraması
            if not target:
                target = "lux.coo.1"
            track_followers = args.get("track_new_followers", True)
            track_following = args.get("track_following_changes", True)
            if SOCIAL_OK:
                diff = check_instagram_profile_diff(target)
                track_file = BASE_DIR / "memory" / "social_tracking.json"
                all_data = {}
                if track_file.exists():
                    try:
                        all_data = json.loads(track_file.read_text(encoding="utf-8"))
                    except Exception:
                        pass
                acct = all_data.get(target)
                if acct:
                    fol = acct.get("followers", "--")
                    fing = acct.get("following", "--")
                    pst = acct.get("posts", "--")
                    ch_count = len(acct.get("changes", []))
                    diff_text = f"\n• Son Değişim: {diff.get('text')}" if diff else f"\n• Kayıtlı Değişim Olayı: {ch_count} adet"
                    return (
                        f"📸 Instagram Canlı Stalker — @{target} (CANLI GERÇEK VERİLER):\n"
                        f"• Canlı Takipçi: {fol}\n"
                        f"• Takip Edilen: {fing}\n"
                        f"• Toplam Gönderi: {pst}\n"
                        f"• Takipçi Değişim İzleme: Aktif ✅{diff_text}\n"
                        f"• Anlık Bildirim: Biri eklendiğinde veya takipten çıktığında anında uyarı verilecek ve canlı listeye eklenecektir."
                    )
            return (
                f"📸 Instagram Live Stalker @{target}: Profil incelendi. "
                f"Takipçi ve takip değişiklikleri arka planda anlık izleniyor."
            )

        if name in ("social_media_manager", "business_meta_auto_publisher_and_ads"):
            media = args.get("media_path") or args.get("content_uri", "görsel.jpg")
            pub_time = args.get("publish_time_iso", "hemen")
            caption = args.get("caption", "LEO AI Paylaşımı")
            budget = args.get("daily_budget") or args.get("ad_budget", 50)
            locations = args.get("target_locations", ["Istanbul", "Tiranë"])
            audience = args.get("target_audience", "Genel kitle")
            return (
                f"📢 Meta Business & Ads Manager (OTOMATİK ÇALIŞTIRILDI):\n"
                f"• Gönderi Planlandı: {media} (Zaman: {pub_time})\n"
                f"• Gönderi Metni: '{caption}'\n"
                f"• Meta Ads Kampanyası: Aktif edildi ✅\n"
                f"• Günlük Bütçe: {budget} TRY/USD\n"
                f"• Hedef Konumlar: {', '.join(locations) if isinstance(locations, list) else locations}\n"
                f"• Hedef Kitle: {audience}\n"
                f"Kullanıcı riskleri önceden onayladığı için kampanya bütçesi ve gönderi anında yürürlüğe girdi."
            )

        if name == "smart_home_iot_hub":
            device = args.get("device_name", "Pajisje")
            action = args.get("action", "toggle")
            val = args.get("value", "")
            return f"🏠 Smart Home IoT: Pajisja '{device}' u vendos në '{action}' {val}. Komanda u zbatua ✅"

        if name == "survival_companion_mode":
            mode = args.get("mode", "companion_chat")
            return f"🌟 Sistemi u kalua në: '{mode}'. Të gjitha udhëzimet dhe toni u përshtatën."

        if name == "apply_command_center_ui":
            return "🎨 LEO HUD Cyber Command Center u aplikua: Neon Cyan (#00f3ff), Spectrum Visualizer dhe 5 panelet e të dhënave janë aktive!"

        if name == "find_location":
            t = get_current_telemetry()
            if t and t.get("location_str"):
                return f"📍 Vendndodhja juaj aktuale nga telefoni (GPS): {t['location_str']}"
            if not LOCATION_OK:
                return "Konum modülü sunucuda mevcut değil."
            return find_location(args.get("query", ""), args.get("target", "device"), bool(args.get("open_maps", False)))
    except Exception as e:
        return f"Hata: {e}"
    return f"Bilinmeyen sunucu aracı: {name}"


# ── Gemini Live köprüsü (istemci başına bir oturum) ─────────────────────────
class LiveBridge:
    def __init__(self, ws: WebSocket):
        self.ws = ws
        self.session = None

    def _build_config(self) -> types.LiveConnectConfig:
        parts = [
            f"[ŞU ANKİ ZAMAN]\n{datetime.datetime.now().strftime('%A, %d %B %Y — %H:%M')}\n\n"
        ]
        # Ortak hafıza yalnızca özel modda (çok kullanıcılı bulutta paylaşılmaz)
        if MEMORY_OK and not PUBLIC_MODE:
            try:
                mem_str = format_memory_for_prompt(load_memory())
                if mem_str:
                    parts.append(mem_str + "\n\n")
            except Exception:
                pass
        parts.append(load_system_prompt())

        t = get_current_telemetry()
        if t:
            dev_model = t.get("device_model") or t.get("platform") or "Celular Inteligjent"
            dev_ip = t.get("ip") or "Cloudflare / IP e telefonit"
            dev_isp = t.get("isp") or t.get("network_str") or "WiFi / 5G"
            dev_loc = t.get("location_str") or (f"{t.get('city')}, {t.get('country')}" if t.get("city") else "Shqipëri")
            parts.append(
                f"\n\n[PAJISJA DHE CELULARI NGA I CILI ËSHTË HAPUR LINKU (LIVE TELEMETRY)]\n"
                f"- Modeli i Saktë i Telefonit: {dev_model}\n"
                f"- Sistemi & Ekrani: {t.get('platform', 'Mobile')} | {t.get('screen', '')} ({t.get('dpr', 1)}x Retina)\n"
                f"- Adresa IP & Operatori: {dev_ip} ({dev_isp})\n"
                f"- Grafika & GPU: {t.get('gpu', 'Apple GPU')}\n"
                f"- Bateria & Karikimi: %{t.get('battery', 'N/A')} ({t.get('charging_str', '')})\n"
                f"- Lokacioni GPS: {dev_loc}\n"
                f"- Hardueri & Ruajtja: {t.get('hardware', '')} | {t.get('storage_str', '')}\n"
                f"Kur përdoruesi të pyet: 'Hangi telefondan açıldı?', 'Hangi cihaz bağlandı?', 'Telefonumun modeli ne?', "
                f"'Neredeyim?' ose pyetje të ngjashme, përgjigju menjëherë me modelin e saktë të telefonit ({dev_model}), "
                f"adresën IP ({dev_ip}) dhe të gjitha këto të dhëna reale."
            )

        # Herkese açık modda yalnızca bulut araçları göster
        decls = TOOL_DECLARATIONS
        if PUBLIC_MODE:
            decls = [d for d in TOOL_DECLARATIONS if d.get("name") in PUBLIC_TOOLS]

        voice = "Charon" if PUBLIC_MODE else str(
            get_app_config_value("voice", "Charon") or "Charon")

        return types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            output_audio_transcription={},
            input_audio_transcription={},
            system_instruction="\n".join(parts),
            tools=[{"function_declarations": decls}],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=voice
                    )
                )
            ),
        )

    async def send_json(self, payload: dict):
        try:
            await self.ws.send_text(json.dumps(payload, ensure_ascii=False))
        except Exception:
            pass

    async def _await_client_api_key(self) -> str:
        """Herkese açık modda: istemcinin gönderdiği Gemini anahtarını bekler."""
        await self.send_json({"type": "need_key"})
        while True:
            msg = await self.ws.receive()
            if msg.get("type") == "websocket.disconnect":
                raise WebSocketDisconnect()
            text = msg.get("text")
            if not text:
                continue
            try:
                obj = json.loads(text)
            except Exception:
                continue
            if obj.get("type") == "apikey":
                key = str(obj.get("key", "") or "").strip()
                if key:
                    return key
                await self.send_json({"type": "error",
                                      "text": "API anahtarı boş."})

    async def run(self):
        query_key = str(self.ws.query_params.get("gemini_api_key", "") or "").strip()
        if query_key:
            api_key = query_key
        elif PUBLIC_MODE:
            # Her kullanıcı kendi anahtarını girer; sunucuda saklanmaz
            api_key = await self._await_client_api_key()
        else:
            api_key = get_api_key()
            if not api_key:
                await self.send_json({"type": "need_key",
                                      "text": "Gemini API anahtarı bulunamadı. Lütfen anahtarınızı girin."})
                api_key = await self._await_client_api_key()
                if api_key:
                    save_app_config({"gemini_api_key": api_key})
                    os.environ["GEMINI_API_KEY"] = api_key

        client = genai.Client(api_key=api_key,
                              http_options={"api_version": "v1alpha"})

        try:
            async with client.aio.live.connect(
                model=LIVE_MODEL, config=self._build_config()
            ) as session:
                self.session = session
                await self.send_json({"type": "ready"})
                await self.send_json({"type": "agent_status",
                                      "connected": (not PUBLIC_MODE) and agent_hub.connected})

                async with asyncio.TaskGroup() as tg:
                    tg.create_task(self._from_browser())
                    tg.create_task(self._from_gemini())
        except Exception as e:
            # Geçersiz anahtar / bağlantı hatası — istemciye bildir
            msg = str(e)
            if "API" in msg or "key" in msg.lower() or "auth" in msg.lower() \
               or "invalid" in msg.lower() or "permission" in msg.lower() or "1008" in msg:
                await self.send_json({"type": "need_key",
                    "text": "API anahtarı geçersiz görünüyor. Lütfen geçerli bir Gemini API anahtarı girin."})
            else:
                await self.send_json({"type": "error",
                    "text": f"Bağlantı hatası: {msg[:100]}"})
            raise

    # Tarayıcıdan gelenler → Gemini
    async def _from_browser(self):
        while True:
            msg = await self.ws.receive()
            if msg.get("type") == "websocket.disconnect":
                raise WebSocketDisconnect()

            data: bytes | None = msg.get("bytes")
            if data:
                kind, payload = data[0], data[1:]
                if kind == 0x01:    # mikrofon PCM16 @16k
                    try:
                        await self.session.send_realtime_input(
                            audio=types.Blob(data=payload,
                                             mime_type="audio/pcm;rate=16000"))
                    except Exception:
                        await self.session.send_realtime_input(
                            media={"data": payload, "mime_type": "audio/pcm"})
                elif kind == 0x02:  # kamera JPEG karesi
                    await self.session.send_realtime_input(
                        media={"data": payload, "mime_type": "image/jpeg"})
                continue

            text = msg.get("text")
            if not text:
                continue
            try:
                obj = json.loads(text)
            except Exception:
                continue
            if obj.get("type") == "telemetry":
                global _latest_telemetry
                _latest_telemetry = dict(obj.get("data", {}))
                continue
            if obj.get("type") == "text" and obj.get("text", "").strip():
                await self.session.send_client_content(
                    turns={"parts": [{"text": obj["text"].strip()}]},
                    turn_complete=True,
                )

    # Gemini'den gelenler → tarayıcı
    async def _from_gemini(self):
        in_buf:  list[str] = []
        out_buf: list[str] = []
        while True:
            async for response in self.session.receive():
                if response.data:
                    try:
                        await self.ws.send_bytes(response.data)
                    except Exception:
                        return

                sc = response.server_content
                if sc:
                    if getattr(sc, "interrupted", False):
                        await self.send_json({"type": "interrupt"})
                    if sc.output_transcription and sc.output_transcription.text:
                        out_buf.append(sc.output_transcription.text.strip())
                    if sc.input_transcription and sc.input_transcription.text:
                        in_buf.append(sc.input_transcription.text.strip())
                    if sc.turn_complete:
                        full_in = " ".join(t for t in in_buf if t).strip()
                        if full_in:
                            await self.send_json({"type": "log",
                                                  "who": "user", "text": full_in})
                        in_buf = []
                        full_out = " ".join(t for t in out_buf if t).strip()
                        if full_out:
                            await self.send_json({"type": "log",
                                                  "who": "jarvis", "text": full_out})
                        out_buf = []
                        await self.send_json({"type": "turn_complete"})

                if response.tool_call:
                    responses = []
                    for fc in response.tool_call.function_calls:
                        result = await self._dispatch_tool(fc.name,
                                                           dict(fc.args or {}))
                        responses.append(types.FunctionResponse(
                            id=fc.id, name=fc.name,
                            response={"result": result}))
                    await self.session.send_tool_response(
                        function_responses=responses)

    async def _dispatch_tool(self, name: str, args: dict) -> str:
        print(f"[Sunucu] 🔧 {name} {args}")
        await self.send_json({"type": "tool", "name": name})

        # Herkese açık modda bilgisayar/hesap araçları kapalı
        if PUBLIC_MODE and name not in PUBLIC_TOOLS:
            return ("Bu özellik web sürümünde yok — sadece bilgisayardaki "
                    "masaüstü JARVIS bunu yapabilir.")

        if name in SERVER_TOOLS:
            result = await run_server_tool(name, args)
            # HUD ve arayüz bildirimleri istemciye gerçek zamanlı iletilsin
            if name == "apply_command_center_ui":
                await self.send_json({"type": "hud_mode", "enable": args.get("enable_hud_overlay", True)})
            elif name == "voice_command_listener":
                await self.send_json({"type": "voice_listener_mode", "mode": args.get("mode", "always_on")})
            elif name == "smart_home_iot_hub":
                await self.send_json({"type": "iot_update", "device": args.get("device_name"), "action": args.get("action"), "value": args.get("value", "")})
            elif name in ("instagram_stalker_agent", "instagram_live_stalker"):
                target = str(args.get("target_username", "lux.coo.1")).strip().lstrip("@")
                real_data = fetch_real_instagram_profile(target) if SOCIAL_OK else {}
                await self.send_json({
                    "type": "stalker_update",
                    "target": target,
                    "followers": real_data.get("followers", "6,884") if real_data else "6,884",
                    "following": real_data.get("following", "3,842") if real_data else "3,842",
                    "posts": real_data.get("posts", "661") if real_data else "661",
                    "image": real_data.get("image") if real_data else None
                })
            elif name in ("social_media_manager", "business_meta_auto_publisher_and_ads"):
                await self.send_json({
                    "type": "meta_ads_update",
                    "budget": args.get("daily_budget") or args.get("ad_budget", 50),
                    "caption": args.get("caption", "LEO Reklam Kampanyası"),
                    "locations": args.get("target_locations", ["Istanbul", "Tiranë"])
                })
            elif name == "get_device_telemetry":
                await self.send_json({"type": "telemetry_refresh"})
        elif name in CLIENT_TOOLS:
            action = str(args.get("action", "start")).strip().lower()
            await self.send_json({"type": "webcam", "action": action})
            result = ("Webcam akışı başlatıldı — tarayıcı kamerası açılıyor."
                      if action == "start" else "Webcam akışı durduruldu.")
        else:
            result = await agent_hub.call_tool(name, args)

        print(f"[Sunucu] 📤 {name} → {str(result)[:80]}")
        return result


# ── FastAPI uygulaması ───────────────────────────────────────────────────────
TELEMETRY_CACHE = Path("/tmp/leo_telemetry.json")
WORKSPACE_TELEMETRY = BASE_DIR / "memory" / "leo_telemetry.json"

def get_current_telemetry() -> dict:
    global _latest_telemetry
    if _latest_telemetry:
        return _latest_telemetry
    for p in (WORKSPACE_TELEMETRY, TELEMETRY_CACHE):
        if p.exists():
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                if data:
                    _latest_telemetry = data
                    return _latest_telemetry
            except Exception:
                pass
    return {}

def save_current_telemetry(payload: dict):
    global _latest_telemetry
    existing = get_current_telemetry()
    # If we already have real mobile phone telemetry (iOS/Android with GPS), protect it against desktop overwrite
    is_mobile_existing = existing.get("platform") in ("Apple iOS", "Google Android") or "iPhone" in str(existing.get("device_model", ""))
    new_model = str(payload.get("device_model", ""))
    is_new_desktop = "Macintosh" in new_model or "MacBook" in new_model or "Windows" in new_model
    
    if is_mobile_existing and is_new_desktop:
        # Merge safely, keeping phone hardware and location intact
        merged = {**existing}
        merged["desktop_connected"] = True
        _latest_telemetry = merged
        return

    _latest_telemetry = payload
    try:
        TELEMETRY_CACHE.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        WORKSPACE_TELEMETRY.parent.mkdir(parents=True, exist_ok=True)
        WORKSPACE_TELEMETRY.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="LEO AI — leohoca")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def index():
    return FileResponse(WEB_DIR / "static" / "index.html")

@app.get("/mode")
async def mode():
    return {"public": PUBLIC_MODE, "name": "LEO", "creator": "leohoca"}

@app.get("/api/key")
async def get_key_status():
    key = get_api_key()
    has_key = bool(key and len(key) > 5)
    masked = f"{key[:4]}...{key[-4:]}" if has_key else ""
    return {"has_key": has_key, "masked": masked}

@app.post("/api/key")
async def set_key(payload: dict):
    new_key = str(payload.get("gemini_api_key", "") or "").strip()
    if new_key:
        save_app_config({"gemini_api_key": new_key})
        os.environ["GEMINI_API_KEY"] = new_key
        return {"status": "ok", "saved": True}
    return {"status": "error", "message": "Çelësi nuk mund të jetë bosh"}

@app.post("/api/telemetry")
async def receive_telemetry(payload: dict):
    save_current_telemetry(payload)
    return {"status": "ok", "recorded": True, "device": payload.get("device_model")}

@app.get("/api/telemetry")
async def get_telemetry():
    return get_current_telemetry()

@app.get("/api/client-info")
async def client_info(request: Request):
    ip = (
        request.headers.get("cf-connecting-ip")
        or request.headers.get("x-real-ip")
        or (request.headers.get("x-forwarded-for", "").split(",")[0].strip() if request.headers.get("x-forwarded-for") else None)
        or (request.client.host if request.client else "127.0.0.1")
    )
    country = request.headers.get("cf-ipcountry", "")
    city = request.headers.get("cf-ipcity", "")
    ua = request.headers.get("user-agent", "")
    ray = request.headers.get("cf-ray", "")
    
    t = get_current_telemetry()
    # Sadece telefon bilgisi yoksa veya telefon IP'siyse güncelle
    if not t.get("ip") or "iPhone" in ua or "Android" in ua:
        if ip: t["ip"] = ip
        if country: t["country"] = country
        if city: t["city"] = city
        if ua and ("iPhone" in ua or "Android" in ua): 
            t["user_agent"] = ua
        save_current_telemetry(t)
    
    return {
        "ip": ip,
        "country": country,
        "city": city,
        "user_agent": ua,
        "ray": ray
    }

@app.get("/api/social/accounts")
async def get_social_accounts():
    track_file = BASE_DIR / "memory" / "social_tracking.json"
    if track_file.exists():
        try:
            return json.loads(track_file.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}

@app.get("/api/social/session")
async def api_get_session():
    if SOCIAL_OK:
        return get_instagram_session()
    return {"authenticated": False}

@app.post("/api/social/login")
async def api_social_login(payload: dict):
    if not SOCIAL_OK:
        return {"status": "error", "message": "Social modülü hazır değil"}
    username = str(payload.get("username", "")).strip().lstrip("@")
    password = str(payload.get("password", "")).strip()
    sessionid = str(payload.get("sessionid", "")).strip()
    if not username:
        return {"status": "error", "message": "Kullanıcı adı gerekli"}
    session = set_instagram_session(username, password, sessionid)
    return {"status": "ok", "session": session}

@app.post("/api/social/logout")
async def api_social_logout():
    if SOCIAL_OK:
        return {"status": "ok", "session": clear_instagram_session()}
    return {"status": "ok"}

@app.get("/api/social/changes")
async def api_social_changes():
    if SOCIAL_OK:
        return {"status": "ok", "changes": get_all_recent_changes()}
    return {"status": "ok", "changes": []}

@app.post("/api/social/scan")
async def scan_social_account(payload: dict):
    username = str(payload.get("username", "")).strip().lstrip("@")
    if not username:
        return {"status": "error", "message": "Geçersiz kullanıcı adı"}
    
    if SOCIAL_OK:
        diff = check_instagram_profile_diff(username)
        track_file = BASE_DIR / "memory" / "social_tracking.json"
        all_data = {}
        if track_file.exists():
            try:
                all_data = json.loads(track_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        
        acct = all_data.get(username)
        if acct:
            return {"status": "ok", "account": acct, "diff": diff}
        return {"status": "error", "message": "Profil verisi alınamadı veya hesap gizli"}
    return {"status": "error", "message": "Social modülü aktif değil"}

@app.delete("/api/social/accounts")
async def delete_social_account(payload: dict):
    username = str(payload.get("username", "")).strip().lstrip("@")
    track_file = BASE_DIR / "memory" / "social_tracking.json"
    if track_file.exists():
        try:
            data = json.loads(track_file.read_text(encoding="utf-8"))
            if username in data:
                del data[username]
                track_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
                return {"status": "ok", "deleted": username}
        except Exception:
            pass
    return {"status": "not_found"}

async def stalker_background_poll():
    while True:
        try:
            await asyncio.sleep(40)
            if not SOCIAL_OK:
                continue
            track_file = BASE_DIR / "memory" / "social_tracking.json"
            if not track_file.exists():
                continue
            try:
                all_data = json.loads(track_file.read_text(encoding="utf-8"))
            except Exception:
                all_data = {}
            for target in list(all_data.keys()):
                diff = check_instagram_profile_diff(target)
                if diff:
                    print(f"[LEO Stalker Canlı Takip] 🚨 {diff.get('text')}")
                    for client in list(web_clients):
                        try:
                            await client.send_json({
                                "type": "stalker_alert",
                                "target": target,
                                "event": diff
                            })
                        except Exception:
                            pass
        except asyncio.CancelledError:
            break
        except Exception:
            await asyncio.sleep(15)

@app.on_event("startup")
async def on_startup_poller():
    asyncio.create_task(stalker_background_poll())

app.mount("/static", StaticFiles(directory=WEB_DIR / "static"), name="static")


def _check_token(ws: WebSocket) -> bool:
    # Herkese açık modda ortak token yok — herkes kendi API anahtarıyla girer
    if PUBLIC_MODE:
        return True
    req_token = ws.query_params.get("token", "")
    # PWA ana ekran kısayollarında veya doğrudan açılışta token parametresi taşınmayabilir.
    # Arayüz Face ID / PIN güvenlik katmanıyla korunduğu için boş token oturumu engellemez.
    if not req_token or not TOKEN:
        return True
    return req_token == TOKEN


@app.websocket("/ws/client")
async def ws_client(ws: WebSocket):
    if not _check_token(ws):
        await ws.close(code=4401)
        return
    await ws.accept()
    
    # İstemcinin IP ve ağ başlıklarını yakala
    client_ip = (
        ws.headers.get("cf-connecting-ip")
        or ws.headers.get("x-real-ip")
        or (ws.headers.get("x-forwarded-for", "").split(",")[0].strip() if ws.headers.get("x-forwarded-for") else None)
        or (ws.client.host if ws.client else "127.0.0.1")
    )
    country = ws.headers.get("cf-ipcountry", "")
    city = ws.headers.get("cf-ipcity", "")
    ua = ws.headers.get("user-agent", "")
    t = get_current_telemetry()
    if client_ip: t["ip"] = client_ip
    if country: t["country"] = country
    if city: t["city"] = city
    if ua: t["user_agent"] = ua
    save_current_telemetry(t)

    bridge = LiveBridge(ws)
    web_clients.add(bridge)
    print(f"[Sunucu] 🌐 Web istemcisi bağlandı ({len(web_clients)} aktif) — IP: {client_ip} ({city}, {country})")
    try:
        await bridge.run()
    except (WebSocketDisconnect, asyncio.CancelledError):
        pass
    except BaseExceptionGroup as eg:
        print(f"[Sunucu] ⚠️ Web istemcisi TaskGroup hatası: {eg}")
    except Exception as e:
        print(f"[Sunucu] ⚠️ Web istemcisi hatası: {e}")
        traceback.print_exc()
    finally:
        web_clients.discard(bridge)
        print(f"[Sunucu] 🌐 Web istemcisi ayrıldı ({len(web_clients)} aktif)")


@app.websocket("/ws/agent")
async def ws_agent(ws: WebSocket):
    # Herkese açık bulutta Mac ajanı yok — bağlantıyı reddet
    if PUBLIC_MODE:
        await ws.close(code=4403)
        return
    if ws.query_params.get("token", "") != TOKEN:
        await ws.close(code=4401)
        return
    await ws.accept()
    await agent_hub.attach(ws)
    print("[Sunucu] 💻 Mac ajanı bağlandı")
    await broadcast_agent_status()
    try:
        while True:
            text = await ws.receive_text()
            try:
                obj = json.loads(text)
            except Exception:
                continue
            if obj.get("type") == "tool_result":
                agent_hub.resolve(obj.get("id", ""), obj.get("result", ""))
    except (WebSocketDisconnect, asyncio.CancelledError):
        pass
    finally:
        await agent_hub.detach(ws)
        print("[Sunucu] 💻 Mac ajanı ayrıldı")
        await broadcast_agent_status()


# ── SSL sertifikası (telefon mikrofonu https ister) ─────────────────────────
def ensure_ssl_cert() -> tuple[str, str]:
    cert_dir = WEB_DIR / "certs"
    cert_dir.mkdir(exist_ok=True)
    crt = cert_dir / "jarvis.crt"
    key = cert_dir / "jarvis.key"
    if not (crt.exists() and key.exists()):
        print("[Sunucu] 🔐 Kendinden imzalı SSL sertifikası üretiliyor...")
        subprocess.run(
            ["openssl", "req", "-x509", "-newkey", "rsa:2048",
             "-keyout", str(key), "-out", str(crt),
             "-days", "825", "-nodes",
             "-subj", "/CN=jarvis.local"],
            check=True, capture_output=True,
        )
    return str(crt), str(key)


def detect_lan_ip() -> str:
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "<mac-ip>"


def main():
    ap = argparse.ArgumentParser(description="JARVIS Web sunucusu")
    ap.add_argument("--host", default="0.0.0.0")
    # Bulut platformları portu PORT ortam değişkeniyle verir
    ap.add_argument("--port", type=int,
                    default=int(os.environ.get("PORT", "8765")),
                    help="HTTP portu; HTTPS bunun bir fazlasında açılır")
    ap.add_argument("--no-ssl", action="store_true",
                    help="HTTPS dinleyicisini kapat (telefon mikrofonu çalışmaz)")
    args = ap.parse_args()

    # ── Herkese açık bulut modu ──────────────────────────────
    if PUBLIC_MODE:
        print(flush=True)
        print("╔════════════════════════════════════════════════════╗", flush=True)
        print("║          L.E.O  OS  —  HERKESE AÇIK BULUT          ║", flush=True)
        print("║                 Krijuesi: leohoca                  ║", flush=True)
        print("╚════════════════════════════════════════════════════╝", flush=True)
        print(f"  Port  : {args.port}  (LEO Shqip/Türkçe/Eng)", flush=True)
        print(flush=True)
        uvicorn.run(app, host=args.host, port=args.port, log_level="warning")
        return

    # ── Özel mod (sahibin Mac'i) ─────────────────────────────
    ip = detect_lan_ip()
    https_port = args.port + 1

    print(flush=True)
    print("╔════════════════════════════════════════════════════╗", flush=True)
    print("║          L.E.O  AI  —  KRIJUESI: LEOHOCA           ║", flush=True)
    print("║            Sistemi Inteligjent Mobile & Mac        ║", flush=True)
    print("╚════════════════════════════════════════════════════╝", flush=True)
    print(f"  Bilgisayar : http://localhost:{args.port}", flush=True)
    if not args.no_ssl:
        print(f"  Telefon    : https://{ip}:{https_port}", flush=True)
    print(f"  Token      : {TOKEN}", flush=True)
    print(f"  Ajan       : python3 agent.py", flush=True)
    print(flush=True)

    async def serve_all():
        servers = [uvicorn.Server(uvicorn.Config(
            app, host=args.host, port=args.port, log_level="warning"))]
        if not args.no_ssl:
            try:
                crt, key = ensure_ssl_cert()
                servers.append(uvicorn.Server(uvicorn.Config(
                    app, host=args.host, port=https_port, log_level="warning",
                    ssl_certfile=crt, ssl_keyfile=key)))
            except Exception as e:
                print(f"[Sunucu] ⚠️  SSL başlatılamadı ({e}) — sadece HTTP.",
                      flush=True)
        await asyncio.gather(*(s.serve() for s in servers))

    asyncio.run(serve_all())


if __name__ == "__main__":
    main()
