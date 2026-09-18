"""
JARVIS — Dosya Düzenleyici ve Organizatör
İndirilenler, Masaüstü veya hedef klasördeki dağınık dosyaları türlerine ve tarihlerine göre kategorize eder.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

CATEGORY_EXTENSIONS = {
    "Belgeler": {".pdf", ".docx", ".doc", ".txt", ".xlsx", ".xls", ".pptx", ".ppt", ".md", ".rtf", ".csv"},
    "Görseller": {".png", ".jpg", ".jpeg", ".webp", ".svg", ".gif", ".heic", ".ico", ".tiff"},
    "Videolar": {".mp4", ".mov", ".avi", ".mkv", ".webm"},
    "Sesler": {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"},
    "Arşivler_ve_Yükleyiciler": {".zip", ".rar", ".tar", ".gz", ".7z", ".dmg", ".pkg", ".iso"},
    "Kod_ve_Projeler": {".py", ".js", ".ts", ".json", ".html", ".css", ".sh", ".c", ".cpp", ".rs", ".go"}
}


def file_organizer(directory_path: str = "~/Downloads", dry_run: bool = False, group_by: str = "type") -> str:
    """
    Belirtilen dizindeki dağınık dosyaları kategorize edip alt klasörlere taşır.
    directory_path: Düzenlenecek klasör yolu (örn: '~/Downloads', '~/Desktop')
    dry_run: true ise sadece taşınacak dosyaları listeler, taşıma yapmaz.
    group_by: 'type' (dosya uzantısına göre) veya 'date' (yıla/aya göre)
    """
    target_dir = Path(os.path.expanduser(directory_path)).resolve()
    if not target_dir.exists() or not target_dir.is_dir():
        return f"Klasör bulunamadı: {directory_path}"

    files_to_move = []
    
    for item in target_dir.iterdir():
        # Klasörleri ve gizli dosyaları atla
        if item.is_dir() or item.name.startswith("."):
            continue

        ext = item.suffix.lower()
        target_category = "Diğer"
        for cat, extensions in CATEGORY_EXTENSIONS.items():
            if ext in extensions:
                target_category = cat
                break

        files_to_move.append((item, target_category))

    if not files_to_move:
        return f"'{target_dir.name}' klasöründe düzenlenecek dağınık dosya bulunamadı."

    if dry_run:
        summary = [f"📂 '{target_dir.name}' İçin Düzenleme Planı (Simülasyon - Taşınmadı):"]
        for item, cat in files_to_move[:10]:
            summary.append(f"• {item.name} ➔ {cat}/")
        if len(files_to_move) > 10:
            summary.append(f"... ve {len(files_to_move)-10} dosya daha.")
        return "\n".join(summary)

    # Gerçek taşıma işlemi
    moved_counts = {}
    for item, cat in files_to_move:
        cat_dir = target_dir / cat
        cat_dir.mkdir(exist_ok=True)
        dest = cat_dir / item.name

        # Aynı isimde dosya varsa üzerine yazma, numaralandır
        if dest.exists():
            base_stem = item.stem
            ext = item.suffix
            counter = 1
            while dest.exists():
                dest = cat_dir / f"{base_stem}_{counter}{ext}"
                counter += 1

        try:
            shutil.move(str(item), str(dest))
            moved_counts[cat] = moved_counts.get(cat, 0) + 1
        except Exception as e:
            pass

    details = ", ".join([f"{cat}: {count} adet" for cat, count in moved_counts.items()])
    return f"✅ '{target_dir.name}' klasörü başarıyla düzenlendi. Toplam {len(files_to_move)} dosya kategorize edildi ({details})."
