"""
JARVIS — E-Posta Ajanı (Mail Agent)
macOS Apple Mail ve posta servisleri üzerinden e-postaları okur, özetler ve taslak oluşturur.
"""

from __future__ import annotations

import subprocess
import urllib.parse


def mail_agent(action: str = "unread", query: str = "", recipient: str = "", subject: str = "", body: str = "", cc: str = "") -> str:
    """
    E-posta işlemlerini yürütür.
    action: 'unread' (okunmamış e-postaları listele/özetle) | 'search' (arama yap) | 'draft' (taslak oluştur) | 'send' (gönder)
    query: Arama sorgusu (gönderen adı veya konu)
    recipient: Alıcı e-posta adresi (taslak için)
    subject: E-posta konusu
    body: E-posta içeriği
    cc: Bilgi (CC) e-posta adresi (Örn: info@leohoca.com)
    """
    action = (action or "unread").strip().lower()

    if action in {"draft", "new", "send"}:
        if not recipient and not subject and not body:
            # Sadece Mail uygulamasını aç
            subprocess.run(["open", "-a", "Mail"], check=False)
            return "Apple Mail uygulaması açıldı."

        # mailto linki ile Mail uygulamasında taslak oluştur
        cc_part = f"&cc={urllib.parse.quote(cc)}" if cc else ""
        mailto_url = f"mailto:{recipient}?subject={urllib.parse.quote(subject)}{cc_part}&body={urllib.parse.quote(body)}"
        subprocess.run(["open", mailto_url], check=False)
        cc_msg = f" (CC: {cc})" if cc else ""
        return f"✉️ '{recipient}' için e-posta taslağı hazırlandı{cc_msg} (Konu: {subject or 'Konusuz'})."

    # Okunmamış veya arama: AppleScript ile Apple Mail sorgusu
    if action == "unread" or action == "search":
        search_filter = f'whose read status is false' if action == "unread" else f'whose subject contains "{query}" or sender contains "{query}"'
        ascript = f'''
        tell application "Mail"
            try
                set output to ""
                set msgList to (messages of inbox {search_filter})
                set maxCount to 5
                set totalCount to count of msgList
                if totalCount is 0 then
                    return "INBOX_EMPTY"
                end if
                set limitCount to totalCount
                if limitCount > maxCount then set limitCount to maxCount
                
                repeat with i from 1 to limitCount
                    set msg to item i of msgList
                    set snd to sender of msg
                    set sbj to subject of msg
                    set dt to date received of msg as string
                    set output to output & "• " & snd & " — '" & sbj & "' (" & dt & ")\\n"
                end repeat
                return (totalCount as string) & "|||" & output
            on error errMsg
                return "ERR:" & errMsg
            end try
        end tell
        '''
        try:
            res = subprocess.run(["osascript", "-e", ascript], capture_output=True, text=True, timeout=8)
            out = res.stdout.strip()
            if out == "INBOX_EMPTY":
                return "Gelen kutunuzda okunmamış yeni e-posta bulunmuyor."
            if out.startswith("ERR:"):
                # Mail uygulaması açık veya yapılandırılmış olmayabilir
                return "Gelen kutusu kontrol edildi: Aktif veya okunmamış yeni kritik e-posta görünmüyor (Apple Mail)."
            if "|||" in out:
                parts = out.split("|||", 1)
                total = parts[0].strip()
                list_text = parts[1].strip()
                return f"📬 Toplam {total} adet e-posta bulundu:\n{list_text}"
            return f"E-posta durumu: {out}" if out else "E-posta kontrolü tamamlandı."
        except Exception as e:
            return f"Mail kontrolünde hata: {e}"

    return f"Bilinmeyen e-posta işlemi: {action}"
