"""
JARVIS — Zamanlanmış Görev ve Rutin Yöneticisi (Cron Scheduler)
Arka plan rutinleri, periyodik görevler ve hatırlatıcı zamanlayıcılar ayarlar.
"""

from __future__ import annotations

import json
import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ROUTINES_FILE = BASE_DIR / "memory" / "scheduled_routines.json"


def _load_routines() -> list:
    try:
        if ROUTINES_FILE.exists():
            return json.loads(ROUTINES_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return []


def _save_routines(routines: list):
    try:
        ROUTINES_FILE.parent.mkdir(parents=True, exist_ok=True)
        ROUTINES_FILE.write_text(json.dumps(routines, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def cron_scheduler(action: str = "list", task_name: str = "", cron_expression: str = "", command: str = "") -> str:
    """
    Arka plan rutinleri ve zamanlanmış görevleri yönetir.
    action: 'list' (listele) | 'add' (yeni rutin ekle) | 'remove' (görev sil)
    task_name: Görevin adı veya tanımı (örn: 'Sabah Haber Özeti', 'Yedekleme Rutini')
    cron_expression: Zaman ifadesi (örn: '0 09:00', 'her gün 09:00', '0 9 * * *')
    command: Çalıştırılacak eylem veya komut
    """
    action = (action or "list").strip().lower()
    routines = _load_routines()

    if action == "list":
        if not routines:
            return "Aktif planlanmış bir arka plan rutini bulunmuyor."
        lines = ["⏰ Planlanmış Rutinler ve Görevler:"]
        for r in routines:
            lines.append(f"• [{r.get('id')}] {r.get('name')}: Zaman: {r.get('schedule')} (Eylem: {r.get('command')})")
        return "\n".join(lines)

    if action in {"add", "create", "kur"}:
        if not task_name:
            return "Rutin oluşturmak için bir görev adı belirtilmeli."
        task_id = f"job_{len(routines)+1}"
        new_entry = {
            "id": task_id,
            "name": task_name,
            "schedule": cron_expression or "09:00 (Günlük)",
            "command": command or "JARVIS sistem kontrolü",
            "created_at": datetime.datetime.now().isoformat(),
            "status": "active"
        }
        routines.append(new_entry)
        _save_routines(routines)
        return (
            f"✅ Rutin Oluşturuldu!\n"
            f"• Görev: {task_name}\n"
            f"• Zamanlama: {new_entry['schedule']}\n"
            f"• Durum: Aktif (ID: {task_id})"
        )

    if action in {"remove", "delete", "sil"}:
        target = task_name.strip().lower()
        kept = [r for r in routines if r.get("name", "").lower() != target and r.get("id", "").lower() != target]
        if len(kept) == len(routines):
            return f"'{task_name}' adında bir rutin bulunamadı."
        _save_routines(kept)
        return f"'{task_name}' görevi zamanlanmış rutinlerden kaldırıldı."

    return f"Bilinmeyen cron işlemi: {action}"
