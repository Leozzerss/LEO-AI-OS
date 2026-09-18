# JARVIS — Windows Portu Devir Planı

> Bu dosya, projeyi Windows'a taşırken **Windows'ta açılan yeni Claude Code
> oturumunun** kaldığımız yerden devam etmesi için hazırlandı. macOS tarafında
> geliştirilen kod referans; Windows sürümünü buna göre yaz.

## Windows oturumunu şu talimatla başlat (kopyala-yapıştır)

> "Bu bir macOS için yazılmış JARVIS sesli asistanı. Onu **tam native bir
> Windows uygulamasına** taşıyoruz. `WINDOWS_PORT_PLAN.md` dosyasını oku ve
> plana göre ilerle. Her adımı Windows'ta test ederek yap. Hedef: takvim ve
> WhatsApp dahil TÜM özellikler Windows'ta çalışsın."

---

## Proje nedir?

macOS masaüstü sesli asistanı — Python + tkinter arayüz + Google **Gemini Live
API** (gerçek zamanlı ses). Ayrıca telefondan bağlanmak için web sürümü var.

**Ana dosyalar:**
- `main.py` — çekirdek: Gemini Live bağlantısı, ses (pyaudio), webcam, araç dağıtımı
- `ui.py` — tkinter arayüz (animasyonlu "orb", ayarlar, kısayol/autostart butonları)
- `tool_defs.py` — Gemini araç (function-calling) tanımları — PLATFORMDAN BAĞIMSIZ
- `app_config.py`, `memory/` — ayar + hafıza (JSON) — platformdan bağımsız
- `actions/` — sistem araçları (ÇOĞU macOS'a özel, port gerekiyor)
- `jarvis_web/` — telefon/web sürümü (server.py + agent.py + static/)
- `BASLAT.command`, `TELEFON.command`, `make_shortcut.py` — başlatıcılar (macOS)

## Mimari (3 katman — hepsi Windows'a taşınacak)
1. **Masaüstü**: bilgisayarda çalışan asistan
2. **Telefon → kendi PC** (`jarvis_web`, private mod): telefondan kendi PC'ni kontrol
3. **Herkese açık bulut** (`jarvis_web`, `JARVIS_PUBLIC=1`): platformdan bağımsız, port gerekmez

---

## Önerilen yaklaşım: TEK kod tabanı, platform dallanması

Ayrı bir Windows kopyası TUTMA. Her platforma-özel yerde `sys.platform` ile dallan:
```python
import sys
IS_WIN = sys.platform == "win32"
IS_MAC = sys.platform == "darwin"
```
Böylece macOS sürümü bozulmadan Windows desteği eklenir. Her `actions/*.py`
içine `_win()` / `_mac()` uygulamaları koy, üstte platforma göre çağır.

---

## Ne taşınır / ne yeniden yazılır

### ✅ Değişmeden çalışır (Python 3.11+ Windows'ta)
- Gemini Live çekirdeği (`asyncio.TaskGroup` → **Python 3.11+ ŞART**)
- `tool_defs.py`, `app_config.py`, `memory/`
- `actions/webcam_vision.py` (cv2 çapraz-platform)
- `actions/weather.py` (requests)
- Web istemci (`jarvis_web/static/`) — tarayıcı, tamamen çapraz-platform

### 🔧 Küçük dokunuş
- `ui.py` — tkinter çalışır; kontrol et: tam ekran (`-fullscreen` Windows'ta farklı),
  font yolları (`Fonts/`), pencere davranışı, ⌘ yerine Ctrl kısayolları
- `main.py` — pyaudio Windows'ta çalışır (cihaz indeksleri farkı olabilir);
  `WebcamStreamer` cv2 ile aynı
- `actions/sys_info.py` — psutil çapraz-platform; pil/CPU/RAM çalışır, ufak metin ayarı
- `actions/screen_vision.py` — ekran görüntüsü: `mss` veya `PIL.ImageGrab` (Windows destekli)

### ❌ Windows için YENİDEN yazılacak (platform dallanmasıyla)
| Dosya | macOS | Windows karşılığı |
|-------|-------|-------------------|
| `actions/shell.py` | bash | PowerShell / cmd |
| `actions/open_app.py` | `open -a` | `start` / `os.startfile` / bilinen yollar |
| `actions/browser.py` | `open` URL | `os.startfile` / `webbrowser` |
| `actions/media.py` | AppleScript | Windows media (SMTC / pywinauto / tuş simülasyonu) |
| `actions/tts.py` | macOS `say` | `pyttsx3` / SAPI |
| `actions/calendar.py` | Swift helper | **Outlook COM** (`win32com`) veya Windows Takvim |
| `actions/reminders.py` | Swift helper | **Outlook görevleri** / Microsoft To Do |
| `actions/whatsapp.py` | AppleScript+Erişilebilirlik | WhatsApp Desktop otomasyonu (`pywinauto`) veya `wa.me` derin bağlantı |
| `actions/health.py` | iCloud sağlık export | (opsiyonel) aynı JSON'u Windows yolundan oku |

### 🔧 Başlatıcı / kurulum / dağıtım (tamamen yeni)
| macOS | Windows |
|-------|---------|
| `BASLAT.command` (tek dosya: kur+başlat) | `BASLAT.bat` (veya `.ps1`) — aynı mantık |
| `TELEFON.command` | `TELEFON.bat` |
| `make_shortcut.py` (.icns + osacompile .app) | `.ico` ikon + Masaüstü `.lnk` kısayolu (`win32com` / PowerShell `WScript.Shell`) |
| Homebrew + portaudio | Windows'ta Python.org + `pip install pyaudio` (Windows wheel'leri var, portaudio gerekmez) |
| LaunchAgent (autostart) | `shell:startup` klasörü veya Görev Zamanlayıcı |
| Gatekeeper "Yine de Aç" | Windows SmartScreen "Yine de çalıştır" (rehbere yaz) |
| `hazirla_paylasim.sh` | `hazirla_paylasim.ps1` (veya .bat) — aynı hariç-tutma mantığı |

### `jarvis_web/agent.py` (telefon → PC)
Ajan, `actions/*` araçlarını çağırır → yukarıdaki portlar bittiğinde ajan da
Windows'ta çalışır. `server.py` çapraz-platform (fastapi/uvicorn/websockets).
Not: SSL/tünel kısmı (`WEB_BASLAT.command`) Windows'ta `cloudflared.exe` +
`.bat` olarak yeniden yazılır.

---

## Kritik notlar
- **Python 3.11+ ZORUNLU** (`asyncio.TaskGroup`). Windows kurulumu bunu garanti etmeli.
- Bu makinede API anahtarı `config/api_keys.json`'a girilir (boş gelir, kullanıcı girer).
- `main.py` ve `ui.py` 3.10+ sözdizimi kullanır (`str | None`, parantezli `async with`).
- Paylaşım paketinde kişisel dosyalar hariç tutulur (bkz. `hazirla_paylasim.sh` mantığı).

## Önerilen sıra (Windows oturumu için)
1. Python 3.11+ ile venv + `pip install -r requirements.txt` (pyaudio dahil) çalışıyor mu — doğrula
2. `main.py` + `ui.py`'yi çalıştır, tkinter arayüz + Gemini ses açılıyor mu
3. Kolay araçlar: `shell`, `open_app`, `browser`, `sys_info`, `screen_vision`, `webcam`
4. TTS, media
5. Zor kısımlar: `calendar`/`reminders` (Outlook COM), `whatsapp`
6. Başlatıcılar: `BASLAT.bat`, masaüstü `.lnk`, autostart
7. `jarvis_web` ajanını Windows'ta test et (telefon → PC)
8. `hazirla_paylasim.ps1` + Windows OKU_BENI (SmartScreen rehberi)
