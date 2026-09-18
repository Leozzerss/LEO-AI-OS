"""
JARVIS — Akıllı Ev ve IoT Kontrolü
WiFi / IoT cihazlarını (klima, ışık, priz, kilit vb.) kontrol eder.
"""

from __future__ import annotations

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
STATE_FILE = BASE_DIR / "memory" / "smart_home_state.json"

DEFAULT_DEVICES = {
    "salon_isik": {"name": "Salon Işığı", "type": "light", "state": "off", "brightness": 80, "room": "Salon"},
    "calisma_isik": {"name": "Çalışma Odası Işığı", "type": "light", "state": "on", "brightness": 100, "room": "Çalışma Odası"},
    "salon_klima": {"name": "Salon Kliması", "type": "climate", "state": "on", "temp": 22, "mode": "cool", "room": "Salon"},
    "ana_kilit": {"name": "Dış Kapı Kilidi", "type": "lock", "state": "locked", "room": "Giriş"},
    "kahve_priz": {"name": "Kahve Makinesi Prizi", "type": "plug", "state": "off", "room": "Mutfak"}
}


def _load_devices() -> dict:
    try:
        if STATE_FILE.exists():
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return dict(DEFAULT_DEVICES)


def _save_devices(devices: dict):
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(devices, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def smart_home_control(device_type: str, action: str, room: str = "", value: str = "", confirmed: bool = False) -> str:
    """
    WiFi ve IoT akıllı ev cihazlarını kontrol eder.
    device_type: 'light' (ışık) | 'climate' (klima) | 'plug' (priz) | 'lock' (kilit) | 'all'
    action: 'turn_on' (aç) | 'turn_off' (kapat) | 'set_temp' (ısı ayarla) | 'status' (durum)
    room: Oda adı ('Salon', 'Yatak Odası', 'Çalışma Odası', 'Mutfak')
    value: Derece veya parlaklık değeri (örn: '24', '%70')
    confirmed: Kritik işlemlerde (kilit açma) onay verilmişse true.
    """
    device_type = (device_type or "all").strip().lower()
    action = (action or "status").strip().lower()
    room_filter = (room or "").strip().lower()

    # Kritik işlem kontrolü: Kilit açma için onay zorunluluğu
    if device_type == "lock" and action in {"turn_off", "unlock", "ac"}:
        if not confirmed:
            return "⚠️ Güvenlik Onayı Gerekli: Dış kapı kilidini açmak kritik bir işlemdir. Lütfen 'Kapıyı açmayı onaylıyorum' diyerek teyit edin."

    devices = _load_devices()

    if action == "status":
        lines = ["🏠 Akıllı Ev Cihaz Durumları:"]
        for dev_id, info in devices.items():
            if room_filter and room_filter not in info["room"].lower():
                continue
            if device_type != "all" and device_type not in info["type"].lower():
                continue
            state_text = "AÇIK" if info["state"] in {"on", "unlocked"} else "KAPALI"
            extra = f", Sıcaklık: {info.get('temp')}°C" if "temp" in info else ""
            lines.append(f"• {info['room']} - {info['name']}: [{state_text}]{extra}")
        return "\n".join(lines) if len(lines) > 1 else "Eşleşen akıllı ev cihazı bulunamadı."

    # Açma / Kapatma / Sıcaklık Ayarlama
    affected = []
    for dev_id, info in devices.items():
        if room_filter and room_filter not in info["room"].lower():
            continue
        if device_type != "all" and device_type not in info["type"].lower():
            continue

        if action in {"turn_on", "ac"}:
            info["state"] = "unlocked" if info["type"] == "lock" else "on"
            affected.append(f"{info['name']} açıldı")
        elif action in {"turn_off", "kapat"}:
            info["state"] = "locked" if info["type"] == "lock" else "off"
            affected.append(f"{info['name']} kapatıldı")
        elif action in {"set_temp", "derece"} and info["type"] == "climate":
            try:
                temp_val = int(value.replace("°", "").replace("C", "").strip())
                info["temp"] = temp_val
                info["state"] = "on"
                affected.append(f"{info['name']} sıcaklığı {temp_val}°C olarak ayarlandı")
            except Exception:
                affected.append(f"{info['name']} için geçerli bir sıcaklık belirtilmedi")

    _save_devices(devices)

    if affected:
        return "✅ " + ", ".join(affected) + "."
    return f"'{room or ''} {device_type}' için komut uygulanacak uygun cihaz bulunamadı."
