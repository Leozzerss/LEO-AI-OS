"""
JARVIS — Konum bulma aracı
Cihaz, kişi veya adres konumunu bulur, harita koordinatlarını ve mesafe/adres bilgilerini döner.
"""

from __future__ import annotations

import json
import urllib.parse
import requests
import subprocess


def find_location(query: str = "", target: str = "device", open_maps: bool = False) -> str:
    """
    Konum bilgisi sorgular.
    query: Adres, yer veya kişi sorgusu. Boşsa cihazın mevcut konumu tespit edilir.
    target: 'device' (cihazın konumu), 'address' (adres veya mekan arama), 'person' (kişi konumu)
    open_maps: true ise harita uygulamasında konumu açar.
    """
    query = (query or "").strip()
    target = (target or "device").strip().lower()

    if not query or target == "device":
        # Cihaz konumu (IP tabanlı hızlı ve güvenilir tespit)
        try:
            resp = requests.get("https://ipapi.co/json/", timeout=4)
            if resp.status_code == 200:
                data = resp.json()
                city = data.get("city", "Bilinmiyor")
                region = data.get("region", "")
                country = data.get("country_name", "Türkiye")
                lat = data.get("latitude")
                lon = data.get("longitude")
                ip = data.get("ip", "")

                info = (
                    f"📍 Cihaz Konumu: {city}, {region} ({country})\n"
                    f"Koordinatlar: {lat}, {lon} (IP: {ip})"
                )

                if open_maps and lat and lon:
                    subprocess.run(["open", f"https://maps.apple.com/?ll={lat},{lon}&q=Konumum"], check=False)
                    info += "\n(Apple Haritalar'da açıldı)"
                return info
        except Exception:
            pass

        # Fallback ip-api
        try:
            resp = requests.get("http://ip-api.com/json/", timeout=4)
            if resp.status_code == 200:
                data = resp.json()
                city = data.get("city", "İstanbul")
                country = data.get("country", "Türkiye")
                lat, lon = data.get("lat"), data.get("lon")
                return f"📍 Cihaz Konumu: {city}, {country} (Koordinat: {lat}, {lon})"
        except Exception as e:
            return f"Cihaz konumu tespit edilemedi: {e}"

    # Adres veya mekan araması (OpenStreetMap Nominatim)
    try:
        headers = {"User-Agent": "JARVIS-Assistant/3.0"}
        url = f"https://nominatim.openstreetmap.org/search?format=json&q={urllib.parse.quote(query)}&limit=1"
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code == 200:
            results = resp.json()
            if results:
                place = results[0]
                display_name = place.get("display_name", query)
                lat = place.get("lat")
                lon = place.get("lon")
                res = f"📍 Konum Bulundu: {display_name}\nKoordinatlar: {lat}, {lon}"

                if open_maps:
                    map_url = f"https://maps.apple.com/?q={urllib.parse.quote(display_name)}"
                    subprocess.run(["open", map_url], check=False)
                    res += "\n(Haritalar uygulamasında açıldı)"
                return res
            else:
                return f"'{query}' için bir konum sonucu bulunamadı."
        else:
            return f"Konum servisi yanıt vermedi (kod {resp.status_code})."
    except Exception as e:
        return f"Konum arama hatası: {e}"
