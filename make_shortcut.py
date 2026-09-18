#!/usr/bin/env python3
"""
JARVIS — Masaüstü kısayolu (.app) oluşturucu
────────────────────────────────────────────
Masaüstüne çift tıklanabilir bir JARVIS.app üretir. Özel teal ikon ekler.
Hem BASLAT.command (ilk kurulum sonrası) hem de UI ayarlar butonu kullanır.

Çalıştırma:
    python3 make_shortcut.py
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def _resolve_python() -> str:
    """Kısayolun JARVIS'i çalıştıracağı Python — önce venv, yoksa mevcut."""
    venv_py = BASE_DIR / "venv" / "bin" / "python"
    if venv_py.exists():
        return str(venv_py)
    return sys.executable or "/usr/bin/python3"


def generate_icns() -> "Path | None":
    """JARVIS .icns ikonu üretir (PIL + iconutil). Pillow yoksa None döner."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception:
        return None
    try:
        SIZE = 1024
        img  = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
        d    = ImageDraw.Draw(img)

        BG   = (2,  12,  12, 255)
        TEAL = (0, 212, 192, 255)
        MID  = (0, 100,  90, 255)
        DIM  = (4,  40,  36, 255)

        d.rounded_rectangle([0, 0, SIZE - 1, SIZE - 1], radius=190, fill=BG)

        cx, cy, R = SIZE // 2, SIZE // 2 - 40, 300
        for i in range(12):
            alpha = max(0, 180 - i * 14)
            d.ellipse([cx - (R + i * 4), cy - (R + i * 4),
                       cx + (R + i * 4), cy + (R + i * 4)],
                      outline=(0, 212, 192, alpha), width=2)
        d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=DIM, outline=TEAL, width=6)

        font_path = BASE_DIR / "Fonts" / "Grift-ExtraBold.ttf"
        try:
            fnt = ImageFont.truetype(str(font_path), 380)
        except Exception:
            fnt = ImageFont.load_default()
        bb = d.textbbox((0, 0), "J", font=fnt)
        tx = cx - (bb[2] - bb[0]) // 2 - bb[0]
        ty = cy - (bb[3] - bb[1]) // 2 - bb[1] - 10
        d.text((tx, ty), "J", fill=TEAL, font=fnt)

        try:
            fnt2 = ImageFont.truetype(str(BASE_DIR / "Fonts" / "Grift-Bold.ttf"), 68)
        except Exception:
            fnt2 = ImageFont.load_default()
        sub = "J.A.R.V.I.S"
        bb2 = d.textbbox((0, 0), sub, font=fnt2)
        d.text((SIZE // 2 - (bb2[2] - bb2[0]) // 2 - bb2[0], SIZE - 170),
               sub, fill=MID, font=fnt2)

        BL, BW, P = 90, 9, 44
        for bx, by, sx, sy in [(P, P, 1, 1), (SIZE - P, P, -1, 1),
                               (P, SIZE - P, 1, -1), (SIZE - P, SIZE - P, -1, -1)]:
            d.line([bx, by, bx + sx * BL, by], fill=TEAL, width=BW)
            d.line([bx, by, bx, by + sy * BL], fill=TEAL, width=BW)

        tmp     = Path(tempfile.mkdtemp())
        iconset = tmp / "JARVIS.iconset"
        iconset.mkdir()
        specs = {
            "icon_16x16.png": 16,    "icon_16x16@2x.png": 32,
            "icon_32x32.png": 32,    "icon_32x32@2x.png": 64,
            "icon_128x128.png": 128, "icon_128x128@2x.png": 256,
            "icon_256x256.png": 256, "icon_256x256@2x.png": 512,
            "icon_512x512.png": 512, "icon_512x512@2x.png": 1024,
        }
        for fname, sz in specs.items():
            img.resize((sz, sz), Image.Resampling.LANCZOS).save(iconset / fname)

        icns = tmp / "JARVIS.icns"
        r = subprocess.run(["iconutil", "-c", "icns", str(iconset), "-o", str(icns)],
                           capture_output=True)
        return icns if r.returncode == 0 else None
    except Exception as exc:
        print(f"[Icon] {exc}")
        return None


def create_desktop_shortcut() -> Path:
    """Masaüstünde JARVIS.app oluşturur ve yolunu döner. Hata olursa yükseltir."""
    desktop = Path.home() / "Desktop"
    app_dst = desktop / "JARVIS.app"
    python  = _resolve_python()

    # Varsa eskisini temizle (yeniden üret)
    if app_dst.exists():
        subprocess.run(["rm", "-rf", str(app_dst)], check=False)

    # Kısayol, JARVIS'i Terminal üzerinden açar. Neden?
    # macOS, Downloads/Desktop/Documents klasörlerini korur (TCC). AppleScript'in
    # python'u doğrudan çağırması bu klasörlerde sessizce izin hatası verir.
    # Terminal ise gerekli izin penceresini gösterir → her yerde çalışır.
    # BASLAT.command dev'de yanımızda, paylaşım düzeninde bir üst klasörde olur.
    baslat = BASE_DIR / "BASLAT.command"
    if not baslat.exists():
        baslat = BASE_DIR.parent / "BASLAT.command"
    if baslat.exists():
        script = f'do shell script "open -a Terminal \'{baslat}\'"'
    else:
        script = (
            f'do shell script "\'{python}\' \'{BASE_DIR}/main.py\''
            f' > /tmp/jarvis_launch.log 2>&1 &"'
        )
    res = subprocess.run(["osacompile", "-o", str(app_dst), "-"],
                        input=script, text=True, capture_output=True)
    if res.returncode != 0:
        raise RuntimeError(res.stderr.strip() or "osacompile başarısız")

    icns = generate_icns()
    if icns and icns.exists():
        import shutil, plistlib
        res_dir = app_dst / "Contents" / "Resources"
        shutil.copy2(str(icns), str(res_dir / "JARVIS.icns"))
        plist_path = app_dst / "Contents" / "Info.plist"
        try:
            with open(plist_path, "rb") as f:
                pdata = plistlib.load(f)
            pdata["CFBundleIconFile"] = "JARVIS"
            pdata["CFBundleIconName"] = "JARVIS"
            with open(plist_path, "wb") as f:
                plistlib.dump(pdata, f)
        except Exception:
            pass

    return app_dst


if __name__ == "__main__":
    try:
        path = create_desktop_shortcut()
        print(f"✅ Masaüstü kısayolu oluşturuldu → {path}")
    except Exception as exc:
        print(f"⚠️  Kısayol oluşturulamadı: {exc}")
        sys.exit(1)
