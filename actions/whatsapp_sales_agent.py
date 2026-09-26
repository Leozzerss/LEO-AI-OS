"""
WhatsApp AI Satış, Pazarlık ve Canlı Sesli Arama Ajanı
─────────────────────────────────────────────────────
%100 Ücretsiz altyapı:
- İnsan gibi samimi ve ikna edici WhatsApp mesajları ve sesli konuşma senaryoları hazırlar.
- Müşteriye özel indirim ve özelliklerle WhatsApp linki (wa.me) üretir.
- Müşterinin tek tıkla yapay zeka ile canlı sesli konuşabileceği ücretsiz sesli görüşme odası (/call?room=...) sağlar.
- Yapılan tüm teklifleri ve görüşme geçmişini hafızaya (memory/whatsapp_campaigns.json) kaydeder.
"""

from __future__ import annotations

import json
import re
import time
import uuid
import urllib.parse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CAMPAIGNS_FILE = BASE_DIR / "memory" / "whatsapp_campaigns.json"


def _normalize_phone(phone: str) -> str:
    digits = re.sub(r"\D+", "", str(phone or ""))
    if len(digits) == 11 and digits.startswith("0"):
        digits = "90" + digits[1:]
    elif len(digits) == 10:
        digits = "90" + digits
    return digits


def _load_campaigns() -> dict:
    try:
        if CAMPAIGNS_FILE.exists():
            data = json.loads(CAMPAIGNS_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
    except Exception:
        pass
    return {}


def _save_campaigns(data: dict):
    CAMPAIGNS_FILE.parent.mkdir(parents=True, exist_ok=True)
    CAMPAIGNS_FILE.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def create_sales_campaign(
    recipient_name: str,
    phone_number: str = "",
    product_name: str = "",
    discount: str = "",
    features: str = "",
    custom_notes: str = "",
    language: str = "sq",
    base_url: str = "https://leo-ai-backend.onrender.com",
) -> dict:
    """Yeni bir WhatsApp satış/arama teklifi oluşturur (Shqip & Türkçe)."""
    name = (recipient_name or ("Klient i Nderuar" if language == "sq" else "Değerli Müşterimiz")).strip()
    norm_phone = _normalize_phone(phone_number)
    room_id = f"leo-{uuid.uuid4().hex[:8]}"

    call_url = f"{base_url.rstrip('/')}/call?room={room_id}"

    # Default vlera sipas gjuhës
    if language == "sq":
        product = (product_name or "Paketa e Sigurisë & Automatizimit LEO AI").strip()
        disc = (discount or "%25 Zbritje Ekskluzive").strip()
        feats = (features or "Mbrojtje Meta 24/7, Asistent Zëri Inteligjent, Suport Personal").strip()

        message_text = (
            f"Përshëndetje {name}! Shpresoj të jesh mirë.\n\n"
            f"Bashkë me @leohoca e diskutuam kërkesën tënde dhe përgatitëm "
            f"një ofertë ekskluzive për paketën '{product}'.\n\n"
            f"🎁 Oferta Speciale me Zbritje: {disc}\n"
            f"✨ Çfarë Përfshin Paketa:\n"
        )
        for feat in feats.split(","):
            f_clean = feat.strip()
            if f_clean:
                message_text += f" • {f_clean}\n"

        if custom_notes.strip():
            message_text += f"\n💡 Shënim: {custom_notes.strip()}\n"

        message_text += (
            f"\nNëse dëshiron t'i sqarojmë detajet drejtpërdrejt, të bësh pyetje ose të flasim live me zë (falas dhe pa asnjë shkarkim), "
            f"mund të lidhesh në këtë dhomë të sigurt:\n"
            f"📞 Dhoma e Thirrjes Live me Zë: {call_url}\n\n"
            f"Si mendon, a të pëlqen kjo ofertë? 😊"
        )
    else:
        product = (product_name or "LEO AI Akıllı Otomasyon Paketi").strip()
        disc = (discount or "%20 İndirim").strip()
        feats = (features or "7/24 Kesintisiz Takip, Meta Hesap Koruma, Otomatik Asistan").strip()

        message_text = (
            f"Selam {name}! Umarım günün harika geçiyordur.\n\n"
            f"leohoca ile senin durumunu ve konuştuklarımızı değerlendirdik; "
            f"senin için özel olarak '{product}' üzerinde bir kolaylık sağladık.\n\n"
            f"🎁 Sana Özel Teklifimiz: {disc}\n"
            f"✨ Pakette Neler Var:\n"
        )
        for feat in feats.split(","):
            f_clean = feat.strip()
            if f_clean:
                message_text += f" • {f_clean}\n"

        if custom_notes.strip():
            message_text += f"\n💡 Not: {custom_notes.strip()}\n"

        message_text += (
            f"\nDetayları doğrudan konuşmak, aklına takılanları sormak veya anında canlı sesli görüşmek istersen "
            f"hiçbir şey yüklemeden şu güvenli arama odasından hemen bağlanabilirsin:\n"
            f"📞 Canlı Sesli Görüşme Linki: {call_url}\n\n"
            f"Fikrin nedir, ne dersin?"
        )

    encoded_text = urllib.parse.quote(message_text)
    if norm_phone:
        whatsapp_web_url = f"https://web.whatsapp.com/send?phone={norm_phone}&text={encoded_text}"
        whatsapp_direct_url = f"https://wa.me/{norm_phone}?text={encoded_text}"
    else:
        whatsapp_web_url = f"https://web.whatsapp.com/send?text={encoded_text}"
        whatsapp_direct_url = f"https://wa.me/?text={encoded_text}"

    campaign_data = {
        "room_id": room_id,
        "recipient_name": name,
        "phone_number": norm_phone,
        "product_name": product,
        "discount": disc,
        "features": feats,
        "custom_notes": custom_notes,
        "language": language,
        "call_url": call_url,
        "message_text": message_text,
        "whatsapp_direct_url": whatsapp_direct_url,
        "whatsapp_web_url": whatsapp_web_url,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "status": "OFFER_READY",
        "call_duration_seconds": 0,
        "logs": [],
    }

    campaigns = _load_campaigns()
    campaigns[room_id] = campaign_data
    _save_campaigns(campaigns)

    return campaign_data


def get_sales_campaign(room_id: str) -> dict | None:
    """Belirtilen oda kimliğine sahip satış teklifini getirir."""
    campaigns = _load_campaigns()
    return campaigns.get(room_id)


def list_sales_campaigns() -> list[dict]:
    """Tüm kayıtlı satış kampanyalarını tarihe göre sıralı listeler."""
    campaigns = _load_campaigns()
    result = list(campaigns.values())
    result.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return result


def update_campaign_status(room_id: str, status: str, note: str = "") -> bool:
    """Kampanya durumunu günceller (Örn: NEGOTIATING, DEAL_CLOSED, CALLED)."""
    campaigns = _load_campaigns()
    if room_id in campaigns:
        campaigns[room_id]["status"] = status
        if note:
            campaigns[room_id].setdefault("logs", []).append({
                "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "note": note
            })
        _save_campaigns(campaigns)
        return True
    return False


def build_sales_system_prompt(campaign: dict) -> str:
    """Müşteri ile canlı konuşurken Gemini Live'a verilecek özel satış danışmanı promptu (Shqip & Türkçe)."""
    name = campaign.get("recipient_name", "Klient")
    product = campaign.get("product_name", "Paketa LEO AI")
    discount = campaign.get("discount", "%25 Zbritje")
    features = campaign.get("features", "Mbrojtje Meta 24/7, Asistent Zëri Inteligjent")
    notes = campaign.get("custom_notes", "")
    lang = campaign.get("language", "sq")

    return (
        f"Ti je LEO — Asistenti dhe Përfaqësuesi Zyrtar i Shitjeve për leohoca.\n"
        f"Aktualisht je në bisedë të drejtpërdrejtë me klientin {name}.\n\n"
        f"[DETAJET E OFERTËS / GÖREVİN VE TEKLİFİN]\n"
        f"- Klienti / Müşteri: {name}\n"
        f"- Produkti / Ürün: {product}\n"
        f"- Zbritja / İndirim: {discount}\n"
        f"- Karakteristikat / Özellikler: {features}\n"
        f"- Shënime Shtesë: {notes}\n\n"
        f"[RREGULLAT E BISEDËS DHE GJUHA / KONUŞMA KURALLARI]\n"
        f"1. GJUHA: Klienti flet në GJUHËN SHQIPE (Shqip). Nëse klienti flet/shkruan Shqip, ti përgjigju në GJUHËN SHQIPE me fjalë të ngrohta, të qarta, natyrale dhe bindëse! Nëse klienti flet Turqisht, përgjigju Turqisht.\n"
        f"2. Fol tërësisht si një njeri i vërtetë, mik i besueshëm dhe ekspert. Mos përdor kurrë fraza robotike apo shabllone të ftohta.\n"
        f"3. Dëgjo me kujdes. Nëse klienti thotë 'është shtrenjtë' ose kërkon më shumë zbritje, vër në dukje zbritjen ekskluzive ({discount}) të aprovuar nga leohoca dhe vlerën e lartë ({features}).\n"
        f"4. Krijo ndjenjën e urgjencës dhe mundësisë: 'leohoca e aprovoi këtë çmim vetëm për ty dhe për një kohë të kufizuar'.\n"
        f"5. Qëllimi yt është të krijosh miqësi, t'i heqësh çdo dyshim dhe ta mbyllësh marrëveshjen me sukses.\n"
        f"6. Fillo ngrohtë: 'Përshëndetje {name}! Unë jam LEO, asistenti i leohoca. Si je? Jam këtu që të diskutojmë të gjitha detajet e ofertës tënde speciale me {discount}.'"
    )


def append_chat_message(room_id: str, sender: str, text: str) -> dict:
    """Belirli bir kampanya/oda için sohbet geçmişine yeni mesaj ekler."""
    campaigns = _load_campaigns()
    camp = campaigns.get(room_id)
    if not camp:
        # Oda yoksa otomatik kampanya oluştur
        camp = create_sales_campaign(recipient_name="Klient")
        room_id = camp["room_id"]
        campaigns = _load_campaigns()

    msg_obj = {
        "id": f"msg_{int(time.time()*1000)}",
        "sender": sender,  # "customer" veya "leo"
        "text": text.strip(),
        "time": time.strftime("%H:%M"),
        "timestamp": time.time(),
    }
    camp.setdefault("chat_history", []).append(msg_obj)
    campaigns[room_id] = camp
    _save_campaigns(campaigns)
    return msg_obj


def get_campaign_chat_history(room_id: str) -> list[dict]:
    """Belirtilen odanın sohbet geçmişini döner."""
    camp = get_sales_campaign(room_id)
    if camp and "chat_history" in camp:
        return camp["chat_history"]
    return []


def _fallback_heuristic_sales_reply(
    incoming_message: str,
    name: str,
    product: str,
    discount: str,
    call_url: str,
    lang: str = "sq",
) -> str:
    """Yapay zeka API'sinde geçici yoğunluk olsa bile anında çalışan insan gibi Shqip & Türkçe ikna motoru."""
    msg = incoming_message.lower().strip()

    is_sq = (lang == "sq") or any(k in msg for k in [
        "ckemi", "pershendetje", "tung", "si je", "mire", "shtrenjt", "cmim", "zbritj", "ulje",
        "leke", "euro", "cfare", "ka", "paketa", "flasim", "telefon", "thirr", "u be", "dakord",
        "dua", "blej", "faleminderit", "shqip"
    ])

    if is_sq:
        if any(k in msg for k in ["shtrenjt", "cmim", "buxhet", "zbritj", "ulje", "leke", "euro", "shum"]):
            return (
                f"Të kuptoj plotësisht {name} 😊 Vlera reale e kësaj pakete është shumë më e lartë, por "
                f"bashkë me @leohoca aprovuam posaçërisht për ty {discount}! Kjo është një mundësi unike. "
                f"Nëse dëshiron t'i sqarojmë të gjitha me zë live, mund të më telefonosh me 1 klikim këtu: {call_url} 📞"
            )
        elif any(k in msg for k in ["cfare", "ka", "vecori", "paketa", "detaj", "funksion"]):
            return (
                f"{name}, kjo paketë përfshin {product} me mbrojtje llogarie 24/7, asistent inteligjent me zë dhe suport direkt. "
                f"Të gjitha rreziqet eliminohen plotësisht. "
                f"Hajde të lidhemi shpejt me zë që të t'i tregoj të gjitha: {call_url} 🚀"
            )
        elif any(k in msg for k in ["pershendetje", "ckemi", "tung", "mirmengjes", "mirdita", "si je", "heyo"]):
            return (
                f"Përshëndetje {name}! Shpresoj të kesh një ditë të shkëlqyer. "
                f"Bashkë me @leohoca kemi përgatitur një ofertë speciale me {discount} për ty! "
                f"Mund të më shkruash lirisht këtu ose të më telefonosh direkt pa pagesë: {call_url} 😊"
            )
        elif any(k in msg for k in ["dakord", "u be", "dua", "blej", "pagesa", "si ta marr", "ok"]):
            return (
                f"Vendim i shkëlqyer {name}! Po e njoftoj menjëherë @leohoca që të ta aktivizojë me prioritet maksimal. "
                f"Për konfirmimin e fundit lidhu për 1 minutë me zë këtu: {call_url} 🤝"
            )
        else:
            return (
                f"{name}, e mora mesazhin tënd! Oferta jote me {discount} për {product} është ende e hapur. "
                f"Që të gjejmë zgjidhjen më të mirë për ty, hajde flasim 1 minutë me zë këtu: {call_url} 🎙️"
            )
    else:
        # Türkçe Fallback
        if any(k in msg for k in ["pahali", "fiyat", "cok", "bütçe", "butce", "pahalı", "indirim"]):
            return (
                f"Seni çok iyi anlıyorum {name}. Normalde bu paketin değeri çok daha yüksek fakat leohoca ile konuştuk ve "
                f"sana özel {discount} tanımladık! Bu fırsatı kaçırmaman için açtık. "
                f"Dilersen aklındakileri sesli netleştirelim, şu linkten beni tek tıkla arayabilirsin: {call_url} 📞"
            )
        elif any(k in msg for k in ["neler var", "ozellik", "özellik", "ne ise yarar", "detay"]):
            return (
                f"{name}, bu pakette {product} kapsamında 7/24 kesintisiz koruma, otomatik asistan ve birebir destek var. "
                f"İşini ve hesabını tamamen güvenceye alıyor. "
                f"Hemen şu odadan canlı sesli görüşelim mi, tüm sorularını canlı yanıtlayayım: {call_url} 🚀"
            )
        elif any(k in msg for k in ["selam", "merhaba", "gunaydin", "iyi gunler", "iyi akşamlar", "heyo"]):
            return (
                f"Harika bir gün dilerim {name}! leohoca ile senin için hazırladığımız özel teklifi inceleyebildin mi? "
                f"Aklına takılan her şeyi buradan yazabilir veya tek tıkla canlı sesli arayabilirsin: {call_url} 😊"
            )
        elif any(k in msg for k in ["tamam", "olur", "anlastik", "anlaştık", "almak istiyorum", "nasil alirim"]):
            return (
                f"Harika bir karar {name}! leohoca'ya hemen iletiyorum, işlemlerini en ön sıraya alıyoruz. "
                f"Detayları hızlıca teyit etmek için şu linkten 1 dakika sesli bağlanabilirsin: {call_url} 🤝"
            )
        else:
            return (
                f"{name}, mesajını aldım! leohoca'nın onayıyla sana sunduğumuz {discount} avantajı devam ediyor. "
                f"Senin için en doğrusunu belirlemek adına şu canlı sesli görüşme odasından hemen bağlanabilirsin: {call_url} 🎙️"
            )


def generate_whatsapp_bot_reply(
    room_id: str,
    incoming_message: str,
    sender_name: str = "Klient",
) -> dict:
    """Müşteriden gelen WhatsApp mesajına insansı, ikna edici Shqip veya Türkçe yanıt üretir."""
    camp = get_sales_campaign(room_id)
    if not camp:
        # Eğer oda yoksa oluştur
        camp = create_sales_campaign(recipient_name=sender_name)
        room_id = camp["room_id"]

    name = camp.get("recipient_name", sender_name or "Klient")
    product = camp.get("product_name", "Paketa LEO AI")
    discount = camp.get("discount", "%25 Zbritje")
    features = camp.get("features", "Mbrojtje Meta 24/7, Asistent Zëri")
    call_url = camp.get("call_url", "https://leo-ai-backend.onrender.com/call")
    phone = camp.get("phone_number", "")
    lang = camp.get("language", "sq")

    # 1. Gelen mesajı geçmişe kaydet
    append_chat_message(room_id, "customer", incoming_message)

    # 2. Gemini ile doğal yanıt üretmeyi dene
    reply_text = ""
    try:
        from app_config import get_app_config_value, is_usable_gemini_key
        key = get_app_config_value("gemini_api_key")
        if key and is_usable_gemini_key(key):
            from google import genai
            client = genai.Client(api_key=key, http_options={"timeout": 6000})

            history = get_campaign_chat_history(room_id)
            history_text = "\n".join([f"{m.get('sender')}: {m.get('text')}" for m in history[-6:]])

            prompt = (
                f"Ti je LEO — Asistenti dhe Përfaqësuesi i Shitjeve për @leohoca.\n"
                f"Po komunikon me klientin në WhatsApp.\n"
                f"- Emri i Klientit: {name}\n"
                f"- Produkti: {product}\n"
                f"- Zbritja / Oferta: {discount}\n"
                f"- Veçoritë: {features}\n"
                f"- Dhoma e Thirrjes Live me Zë (%100 Falas): {call_url}\n\n"
                f"[HISTORIA E BISEDËS]\n{history_text}\n\n"
                f"[MESAZHI I FUNDIT I KLIENTIT]: \"{incoming_message}\"\n\n"
                f"[RREGULLAT E PËRGJIGJES]\n"
                f"1. GJUHA: Klienti flet në GJUHËN SHQIPE (ose Turqisht). Nëse klienti shkruan Shqip, ti duhet patjetër të përgjigjesh në SHQIP të pastër, miqësor, shumë bindës dhe njerëzor! Nëse shkruan Turqisht, përgjigju Turqisht.\n"
                f"2. Përgjigju si një person i vërtetë në WhatsApp (2-3 fjali të shkurtra, të ngrohta, me emojit e duhura 😊, 📞, 🤝, 🚀).\n"
                f"3. Nëse klienti ankohet për çmimin ('është shtrenjtë', etj.), përmend zbritjen speciale ({discount}) dhe vlerën e lartë ({features}).\n"
                f"4. Në fund ftoje gjithmonë të flasë me zë duke i bashkangjitur këtë link falas: {call_url}\n"
            )

            for model_candidate in ["models/gemini-flash-lite-latest", "models/gemini-3.1-flash-lite", "models/gemini-flash-latest"]:
                try:
                    resp = client.models.generate_content(model=model_candidate, contents=prompt)
                    if resp and resp.text:
                        reply_text = resp.text.strip()
                        break
                except Exception:
                    continue
    except Exception:
        pass

    # 3. Eğer API yoğun veya ulaşılamazsa akıllı ikna kurallarını işlet
    if not reply_text:
        reply_text = _fallback_heuristic_sales_reply(
            incoming_message=incoming_message,
            name=name,
            product=product,
            discount=discount,
            call_url=call_url,
            lang=lang,
        )

    # 4. LEO'nun cevabını geçmişe kaydet
    append_chat_message(room_id, "leo", reply_text)

    # 5. WhatsApp doğrudan yanıtlama linki oluştur
    encoded_reply = urllib.parse.quote(reply_text)
    if phone:
        wa_reply_url = f"https://wa.me/{phone}?text={encoded_reply}"
        wa_web_url = f"https://web.whatsapp.com/send?phone={phone}&text={encoded_reply}"
    else:
        wa_reply_url = f"https://wa.me/?text={encoded_reply}"
        wa_web_url = f"https://web.whatsapp.com/send?text={encoded_reply}"

    return {
        "ok": True,
        "reply": reply_text,
        "room_id": room_id,
        "recipient_name": name,
        "whatsapp_reply_url": wa_reply_url,
        "whatsapp_web_url": wa_web_url,
        "chat_history": get_campaign_chat_history(room_id),
    }


SCHEDULED_CALLS_FILE = BASE_DIR / "memory" / "scheduled_whatsapp_calls.json"


def send_baileys_direct_message(phone: str, message: str) -> dict:
    """Baileys WhatsApp servisi üzerinden doğrudan mesaj iletir."""
    import urllib.request
    clean_p = _normalize_phone(phone)
    payload = json.dumps({"phone": clean_p, "message": message}).encode("utf-8")
    try:
        req = urllib.request.Request(
            "http://127.0.0.1:8769/send",
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=5) as res:
            return json.loads(res.read().decode("utf-8"))
    except Exception as e:
        return {"ok": False, "error": str(e)}


def schedule_whatsapp_call_or_message(
    phone_number: str = "",
    recipient_name: str = "Leo",
    time_str: str = "18:00",
    message_or_offer: str = "",
    language: str = "sq",
) -> dict:
    """Belirtilen saatte müşteriyi aramak / WhatsApp'tan otomatik bağlamak için zamanlar."""
    clean_phone = _normalize_phone(phone_number)
    name = (recipient_name or "Leo").strip()

    if not clean_phone:
        try:
            from actions.whatsapp import get_whatsapp_contact
            contact = get_whatsapp_contact(name)
            if contact and contact.get("phone_number"):
                clean_phone = _normalize_phone(contact["phone_number"])
        except Exception:
            pass
        if not clean_phone:
            clean_phone = "13602996009"

    # Teklif kampanyasını hazırla
    camp = create_sales_campaign(
        recipient_name=name,
        phone_number=clean_phone,
        language=language,
        custom_notes=f"E planifikuar për në orën {time_str}"
    )

    outreach_text = message_or_offer.strip() or camp["message_text"]

    # Saat hesapla
    now = time.localtime()
    t_lower = (str(time_str) or "").strip().lower()

    if any(k in t_lower for k in ["hemen", "now", "tani", "derhal", "simdi", "şimdi", "direct", "menjehere", "menjëherë"]):
        delay_sec = 2
        h, m = now.tm_hour, now.tm_min
        time_display = f"{h:02d}:{m:02d} (Tani / Menjëherë)"
    else:
        rel_match = re.search(r"(\d+)\s*(?:dak|min|dakika|minuta)", t_lower)
        if rel_match:
            mins = int(rel_match.group(1))
            delay_sec = max(2, mins * 60)
            target_t = time.time() + delay_sec
            t_struct = time.localtime(target_t)
            h, m = t_struct.tm_hour, t_struct.tm_min
            time_display = f"{h:02d}:{m:02d} (+{mins} min)"
        else:
            try:
                parts = [int(p) for p in re.findall(r"\d+", time_str)[:2]]
                h = parts[0]
                m = parts[1] if len(parts) > 1 else 0
            except Exception:
                h, m = now.tm_hour, (now.tm_min + 5) % 60

            target_time = time.mktime((
                now.tm_year, now.tm_mon, now.tm_mday,
                h, m, 0,
                now.tm_wday, now.tm_yday, now.tm_isdst
            ))
            if target_time <= time.time():
                # Eğer bugün geçmişse yarın aynı saate planla
                target_time += 86400

            delay_sec = max(2, target_time - time.time())
            time_display = f"{h:02d}:{m:02d}"

    target_timestamp = time.time() + delay_sec

    task_id = f"call_{uuid.uuid4().hex[:6]}"
    task_entry = {
        "id": task_id,
        "phone": clean_phone,
        "recipient_name": name,
        "scheduled_time": time_display,
        "target_timestamp": target_timestamp,
        "status": "SCHEDULED",
        "room_id": camp["room_id"],
        "call_url": camp["call_url"],
        "message": outreach_text,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    # Dosyaya kaydet
    SCHEDULED_CALLS_FILE.parent.mkdir(parents=True, exist_ok=True)
    all_tasks = []
    try:
        if SCHEDULED_CALLS_FILE.exists():
            all_tasks = json.loads(SCHEDULED_CALLS_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    all_tasks.append(task_entry)
    SCHEDULED_CALLS_FILE.write_text(json.dumps(all_tasks, indent=2, ensure_ascii=False), encoding="utf-8")

    # Arka planda gecikmeli tetikleyici başlat
    import threading
    def _delayed_call_trigger():
        time.sleep(delay_sec)
        print(f"\n⏰ [L.E.O AUTOMATED CALL] Ora {time_display} — Po telefonohet/kontaktohet {name} (+{clean_phone}) në WhatsApp!")
        
        # 1. Baileys ile doğrudan WhatsApp mesajı gönder
        res = send_baileys_direct_message(clean_phone, outreach_text)
        print(f"[L.E.O AUTOMATED CALL] Rezultati i dërgimit: {res}")

        # 2. Görevi tamamlandı olarak işaretle
        try:
            tasks = json.loads(SCHEDULED_CALLS_FILE.read_text(encoding="utf-8"))
            for t in tasks:
                if t["id"] == task_id:
                    t["status"] = "EXECUTED"
                    t["executed_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
                    t["send_result"] = res
            SCHEDULED_CALLS_FILE.write_text(json.dumps(tasks, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass

    t = threading.Thread(target=_delayed_call_trigger, daemon=True)
    t.start()

    return {
        "ok": True,
        "task_id": task_id,
        "recipient": name,
        "phone": clean_phone,
        "time": time_display,
        "call_url": camp["call_url"],
        "message": (
            f"✅ U regjistrua me sukses! LEO do ta kontaktojë dhe thërrasë {name} (+{clean_phone}) "
            f"në orën {time_display} në WhatsApp me ofertën speciale dhe dhomën e zërit."
        )
    }


