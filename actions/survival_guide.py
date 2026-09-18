"""
JARVIS — Çevrimdışı Acil Durum ve Hayatta Kalma Rehberi (Survival Guide)
İlk yardım, afet protokolleri, deprem rehberi ve acil durum numaraları sunar.
"""

from __future__ import annotations

SURVIVAL_DATABASE = {
    "emergency_numbers": (
        "🚨 ACİL DURUM NUMARALARI (TÜRKİYE):\n"
        "• 112: Tek Acil Çağrı Merkezi (Ambulans, Polis, Jandarma, İtfaiye, Sahil Güvenlik, Orman)\n"
        "• 122: AFAD (Afet ve Acil Durum)\n"
        "• 114: Zehir Danışma Merkezi (UZEM)\n"
        "• 153: Belediye Beyaz Masa / Zabıta\n"
        "• 186: Elektrik Arıza | 185: Su Arıza | 187: Doğalgaz Acil"
    ),
    "earthquake": (
        "🏚️ DEPREM PROTOKOLÜ:\n"
        "1. Deprem Anı: Panik yapmayın, ÇÖK - KAPAN - TUTUN pozisyonu alın. Başınızı ve boynunuzu koruyun.\n"
        "2. Pencerelerden, devrilebilecek ağır mobilyalardan ve balkonlardan uzak durun.\n"
        "3. Sarsıntı bittiğinde: Gaz, elektrik ve su vanalarını kapatın.\n"
        "4. Asansör kesinlikle kullanmayın, merdivenleri dikkatle kullanarak acil toplanma alanına gidin.\n"
        "5. Acil Durum Çantası: Su, düdük, fener, ilk yardım kiti, önemli evraklar, kuru gıda, powerbank."
    ),
    "first_aid": (
        "🩹 TEMEL İLK YARDIM ADIMLARI:\n"
        "• Şiddetli Kanama: Temiz bir bezle yaranın üzerine doğrudan baskı uygulayın. Gerekirse yaralı bölgeyi kalp seviyesinden yukarı kaldırın.\n"
        "• Tıkanma (Heimlich Manevrası): Kişi nefes alamıyorsa arkasına geçin, göbek deliğinin 2 parmak üzerine yumruk yapıp içe ve yukarı doğru kuvvetle bastırın.\n"
        "• Yanıklar: Bölgeyi en az 10-15 dakika soğuk (buz değil, ılık/serin) akar su altında tutun. Asla diş macunu, yoğurt sürmeyin.\n"
        "• Bayılma: Kişiyi sırt üstü yatırın, bacaklarını 30 cm yukarı kaldırın (şok pozisyonu). Rahat nefes almasını sağlayın."
    ),
    "fire": (
        "🔥 YANGIN GÜVENLİK REHBERİ:\n"
        "1. Duman Varsa: Emekleyerek ilerleyin — duman ve zehirli gazlar yukarı yükselir, zemin seviyesinde hava daha temizdir.\n"
        "2. Isınmış Kapıları Açmayın: Kapı kolunu elinizin tersiyle kontrol edin; sıcaksa açmayın.\n"
        "3. Elbiseniz Tutuşursa: DUR, YAT, YUVARLAN taktiğini uygulayın.\n"
        "4. Tahliye sonrasında binaya asla geri dönmeyin, 112'yi arayın."
    ),
    "outage": (
        "⚡ UZUN SÜRELİ ELEKTRİK / ŞEBEKE KESİNTİSİ:\n"
        "• Buzdolabı kapağını mümkün olduğunca az açın (içerideki soğukluğu 24-48 saat korur).\n"
        "• Cihazları pil tasarruf moduna alın, fener ve pilleri hazır tutun.\n"
        "• Su kesintisine karşı her zaman kişi başı günlük en az 3 litre temiz içme suyu stoku bulundurun."
    )
}


def survival_guide(topic: str = "emergency_numbers", query: str = "") -> str:
    """
    Çevrimdışı ilk yardım, afet rehberi ve acil durum protokollerini sunar.
    topic: 'emergency_numbers' (numaralar) | 'earthquake' (deprem) | 'first_aid' (ilk yardım) | 'fire' (yangın) | 'outage' (kesinti)
    query: Arama sorgusu (örn: 'yanık', 'deprem çantası', 'zehirlenme')
    """
    topic_clean = (topic or "").strip().lower()
    q = (query or "").strip().lower()

    # Konu eşleştirme
    if any(k in topic_clean or k in q for k in ["numara", "tel", "acil", "112", "police", "ambulans", "itfaiye"]):
        return SURVIVAL_DATABASE["emergency_numbers"]
    if any(k in topic_clean or k in q for k in ["deprem", "afet", "sarsinti", "toplanma", "canta"]):
        return SURVIVAL_DATABASE["earthquake"]
    if any(k in topic_clean or k in q for k in ["ilk yardim", "kanama", "heimlich", "yanik", "bayilma", "cpr"]):
        return SURVIVAL_DATABASE["first_aid"]
    if any(k in topic_clean or k in q for k in ["yangin", "duman", "alev", "itfaiye"]):
        return SURVIVAL_DATABASE["fire"]
    if any(k in topic_clean or k in q for k in ["kesinti", "elektrik", "su kesintisi", "jenerator"]):
        return SURVIVAL_DATABASE["outage"]

    # Varsayılan veya genel arama
    return (
        SURVIVAL_DATABASE.get(topic_clean) or
        f"🚨 ÇEVRİMDIŞI ACİL DURUM REHBERİ:\n\n{SURVIVAL_DATABASE['emergency_numbers']}\n\n{SURVIVAL_DATABASE['earthquake']}"
    )
