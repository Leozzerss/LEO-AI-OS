"""
LEO OS — Otomatik Yenilenen ve Kesintisiz Tünel Yöneticisi (Tunnel Keeper)
- Cloudflare trycloudflare tünelini başlatır.
- URL'i otomatik okur, web_config.json'daki token ile birleştirir.
- QR kodu (leo_phone_qr.png) anında üretir.
- Tünel düştüğünde ('Tunnel not found', bağlantı kopması vb.) beklemeden anında yenisini açar.
- Tüneli 7/24 canlı ve sağlıklı tutar.
"""
import subprocess
import re
import time
import json
from pathlib import Path
import qrcode

BASE_DIR = Path(__file__).resolve().parent.parent
WEB_DIR = Path(__file__).resolve().parent
TOKEN_FILE = WEB_DIR / "web_config.json"
QR_PATHS = [
    Path("/Users/Apple/.gemini/antigravity-ide/brain/d03795e9-88ab-476b-a0b5-974097b0dc2d/leo_phone_qr.png"),
    WEB_DIR / "static" / "leo_phone_qr.png",
    Path("/tmp/leo_phone_qr.png")
]
INFO_FILE = BASE_DIR / "memory" / "leo_tunnel_active.json"

def get_token() -> str:
    if TOKEN_FILE.exists():
        try:
            return json.loads(TOKEN_FILE.read_text()).get("token", "a63c0bea7e254d682646d9f11a8be55d")
        except Exception:
            pass
    return "a63c0bea7e254d682646d9f11a8be55d"

def update_qr(full_url: str):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=12,
        border=4,
    )
    qr.add_data(full_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#001833", back_color="#ffffff")
    for p in QR_PATHS:
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            img.save(str(p))
            print(f"[TunnelKeeper] QR Kod güncellendi: {p}", flush=True)
        except Exception as e:
            print(f"[TunnelKeeper] QR hata {p}: {e}", flush=True)

def run_tunnel():
    token = get_token()
    while True:
        print("[TunnelKeeper] 🚀 Cloudflare tüneli başlatılıyor...", flush=True)
        proc = subprocess.Popen(
            ["cloudflared", "tunnel", "--url", "http://localhost:8765"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        current_url = None

        try:
            for line in proc.stdout:
                if not current_url:
                    m = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
                    if m:
                        base_url = m.group(0)
                        current_url = f"{base_url}/?t={token}"
                        print(f"\n[TunnelKeeper] ✅ AKTİF TÜNEL BULUNDU:\n{current_url}\n", flush=True)
                        update_qr(current_url)
                        try:
                            INFO_FILE.parent.mkdir(parents=True, exist_ok=True)
                            INFO_FILE.write_text(json.dumps({
                                "url": current_url,
                                "base_url": base_url,
                                "token": token,
                                "started_at": time.strftime("%Y-%m-%d %H:%M:%S")
                            }, indent=2), encoding="utf-8")
                        except Exception:
                            pass

                # Hata tespiti — tünel geçersiz hale gelirse döngüyü kırıp hemen yeniden oluştur
                if "Tunnel not found" in line or "Unauthorized" in line:
                    print("\n[TunnelKeeper] ⚠️ Tünel koptu veya geçersiz hale geldi (Tunnel not found). Yeniden başlatılıyor...", flush=True)
                    break
        except Exception as err:
            print(f"[TunnelKeeper] Okuma hatası: {err}", flush=True)

        try:
            proc.terminate()
            proc.wait(timeout=4)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
        time.sleep(2)

if __name__ == "__main__":
    run_tunnel()
