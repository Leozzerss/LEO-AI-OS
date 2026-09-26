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
    product_name: str = "LEO AI Akıllı Otomasyon Paketi",
    discount: str = "%20 İndirim",
    features: str = "7/24 Kesintisiz Takip, Meta Hesap Koruma, Otomatik Asistan",
    custom_notes: str = "",
    base_url: str = "https://leo-ai-backend.onrender.com",
) -> dict:
    """Yeni bir WhatsApp satış/arama teklifi oluşturur."""
    name = (recipient_name or "Değerli Müşterimiz").strip()
    norm_phone = _normalize_phone(phone_number)
    room_id = f"leo-{uuid.uuid4().hex[:8]}"

    call_url = f"{base_url.rstrip('/')}/call?room={room_id}"

    # İnsan gibi, samimi, akıcı ve son derece ikna edici mesaj metni
    message_text = (
        f"Selam {name}! Umarım günün harika geçiyordur.\n\n"
        f"leohoca ile senin durumunu ve konuştuklarımızı değerlendirdik; "
        f"senin için özel olarak '{product_name}' üzerinde bir kolaylık sağladık.\n\n"
        f"🎁 Sana Özel Teklifimiz: {discount}\n"
        f"✨ Pakette Neler Var:\n"
    )
    for feat in features.split(","):
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
        "product_name": product_name,
        "discount": discount,
        "features": features,
        "custom_notes": custom_notes,
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
    """Müşteri ile canlı konuşurken Gemini Live'a verilecek özel satış danışmanı promptu."""
    name = campaign.get("recipient_name", "Müşteri")
    product = campaign.get("product_name", "Özel Paket")
    discount = campaign.get("discount", "%20 İndirim")
    features = campaign.get("features", "")
    notes = campaign.get("custom_notes", "")

    return (
        f"Sen leohoca adına hareket eden LEO AI Satış ve Müşteri İlişkileri Temsilcisisin.\n"
        f"Şu an {name} isimli müşterimizle doğrudan canlı sesli görüşmedesin.\n\n"
        f"[GÖREVİN VE TEKLİFİN]\n"
        f"- Müşterinin Adı: {name}\n"
        f"- Sunulan Ürün/Hizmet: {product}\n"
        f"- İndirim Oranı/Fiyat Avantajı: {discount}\n"
        f"- Önemli Özellikler: {features}\n"
        f"- Ek Notlar: {notes}\n\n"
        f"[KONUŞMA KURALLARI VE İKNA TARZI]\n"
        f"1. Tıpkı gerçek bir insan gibi konuş! Robotik, kalıp ve soğuk cümleler kurma. Samimi, saygılı, güven verici ve enerjik ol.\n"
        f"2. Karşı tarafı dikkatle dinle. Sorularına net ve ikna edici cevaplar ver.\n"
        f"3. Müşteri 'Fiyat çok pahalı' derse, indirim avantajını ({discount}) ve ürünün sağlayacağı değeri ({features}) hatırlat.\n"
        f"4. Gerekirse 'leohoca senin için bu özel fiyatı onayladı, bu fırsat sınırlı süre geçerli' diyerek aciliyet hissi oluştur.\n"
        f"5. Amacın müşteriyi rahatlatmak, tüm itirazlarını sevgiyle çözmek ve anlaşmayı (satışı) başarıyla kapatmaktır.\n"
        f"6. Görüşme başlarken sıcak bir şekilde 'Selam {name}! Ben leohoca'nın asistanı LEO. Nasılsın? Teklifimizle ilgili detayları konuşmak için buradayım' diyerek başla."
    )


def append_chat_message(room_id: str, sender: str, text: str) -> dict:
    """Belirli bir kampanya/oda için sohbet geçmişine yeni mesaj ekler."""
    campaigns = _load_campaigns()
    camp = campaigns.get(room_id)
    if not camp:
        # Oda yoksa otomatik kampanya oluştur
        camp = create_sales_campaign(recipient_name="Müşteri")
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
) -> str:
    """Yapay zeka API'sinde geçici yoğunluk olsa bile anında çalışan insan gibi Türkçe ikna motoru."""
    msg = incoming_message.lower().strip()

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
    sender_name: str = "Müşteri",
) -> dict:
    """Müşteriden gelen WhatsApp mesajına insansı, ikna edici ve samimi yanıt üretir."""
    camp = get_sales_campaign(room_id)
    if not camp:
        # Eğer oda yoksa oluştur
        camp = create_sales_campaign(recipient_name=sender_name)
        room_id = camp["room_id"]

    name = camp.get("recipient_name", sender_name or "Müşteri")
    product = camp.get("product_name", "LEO AI Otomasyon Paketi")
    discount = camp.get("discount", "%20 İndirim")
    features = camp.get("features", "7/24 Kesintisiz Takip")
    call_url = camp.get("call_url", "https://leo-ai-backend.onrender.com/call")
    phone = camp.get("phone_number", "")

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
                f"Sen leohoca adına hareket eden samimi, sıcakkanlı ve son derece ikna edici LEO AI Satış Asistanısın.\n"
                f"Şu an WhatsApp üzerinden müşteriyle yazışıyorsun.\n"
                f"- Müşterinin Adı: {name}\n"
                f"- Ürün/Hizmet: {product}\n"
                f"- İndirim Oranı/Teklif: {discount}\n"
                f"- Özellikler: {features}\n"
                f"- Ücretsiz Canlı Sesli Arama Linki: {call_url}\n\n"
                f"[ÖNCEKİ YAZIŞMALAR]\n{history_text}\n\n"
                f"[MÜŞTERİNİN SON MESAJI]: \"{incoming_message}\"\n\n"
                f"[KURALLAR]\n"
                f"1. Tıpkı WhatsApp'ta konuşan kibar, enerjik ve samimi bir insan gibi 2-3 cümleyle cevap ver. Asla robot gibi konuşma.\n"
                f"2. Fiyat itirazı varsa indirim fırsatını ({discount}) ve değerini açıkla.\n"
                f"3. Konuşmanın sonunda müşteriyi sesli konuşmaya davet ederek şu linki ekle: {call_url}\n"
                f"4. Uygun emojiler kullan (📞, ✨, 🤝, 😊)."
            )

            # Hızlı modelleri sırayla dene
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

