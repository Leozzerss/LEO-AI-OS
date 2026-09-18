"""
Tarayıcı kontrolü — macOS 'open' komutu ile çalışır.
"""

import re
import subprocess
import urllib.parse

import requests


YOUTUBE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def _open(url: str) -> None:
    subprocess.run(["open", url], check=False)


def _find_first_youtube_video(query: str) -> str | None:
    search_url = "https://www.youtube.com/results"
    response = requests.get(
        search_url,
        params={"search_query": query},
        headers=YOUTUBE_HEADERS,
        timeout=10,
    )
    response.raise_for_status()
    html = response.text

    matches = re.findall(r'"videoId":"([A-Za-z0-9_-]{11})"', html)
    seen = set()
    for video_id in matches:
        if video_id not in seen:
            seen.add(video_id)
            return video_id

    matches = re.findall(r'/watch\?v=([A-Za-z0-9_-]{11})', html)
    for video_id in matches:
        if video_id not in seen:
            seen.add(video_id)
            return video_id

    return None


def browser_control(action: str, url: str = None, query: str = None) -> str:
    if action == "open_url":
        if not url:
            return "URL belirtilmedi."
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        _open(url)
        return f"Açıldı: {url}"

    elif action == "search":
        if not query:
            return "Arama sorgusu belirtilmedi."
        encoded = urllib.parse.quote(query)
        search_url = f"https://www.google.com/search?q={encoded}"
        _open(search_url)
        return f"'{query}' için arama açıldı."

    elif action in ("play_youtube", "youtube_play", "play_music"):
        if not query:
            return "YouTube için arama sorgusu belirtilmedi."

        try:
            video_id = _find_first_youtube_video(query)
        except Exception as exc:
            encoded = urllib.parse.quote(query)
            fallback_url = f"https://www.youtube.com/results?search_query={encoded}"
            _open(fallback_url)
            return (
                f"YouTube ilk sonucu alınamadı ({exc}). "
                f"Arama sonuçları açıldı: {query}"
            )

        if not video_id:
            encoded = urllib.parse.quote(query)
            fallback_url = f"https://www.youtube.com/results?search_query={encoded}"
            _open(fallback_url)
            return f"YouTube'da doğrudan video bulunamadı. Arama sonuçları açıldı: {query}"

        watch_url = f"https://www.youtube.com/watch?v={video_id}&autoplay=1"
        _open(watch_url)
        return f"YouTube'da oynatılıyor: {query}"

    return f"Bilinmeyen eylem: {action}"
