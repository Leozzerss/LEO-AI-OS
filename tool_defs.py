"""
JARVIS — Gemini Live araç (tool) tanımları
Masaüstü (main.py) ve web sunucusu (jarvis_web/server.py) ortak kullanır.
"""

TOOL_DECLARATIONS = [
    {
        "name": "open_app",
        "description": "macOS'ta herhangi bir uygulamayı açar. Spotify, Safari, Terminal, Finder, VS Code vb.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "app_name": {
                    "type": "STRING",
                    "description": "Uygulama adı (örn. 'Spotify', 'Safari', 'Terminal')"
                }
            },
            "required": ["app_name"]
        }
    },
    {
        "name": "sys_info",
        "description": "Sistem bilgisi alır: pil durumu, CPU, RAM, disk, saat, tarih, ağ bağlantısı.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "query": {
                    "type": "STRING",
                    "description": "battery | cpu | ram | disk | time | date | network | all"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_phone_telemetry",
        "description": "Telefoni / celularit të përdoruesit: bateria (%), karikimi, shpejtësia e internetit, ekrani, lokacioni GPS, memoria dhe gjendja live në kohë reale.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "detail": {
                    "type": "STRING",
                    "description": "all | battery | network | location | storage | screen"
                }
            }
        }
    },
    {
        "name": "get_weather",
        "description": (
            "Anlik hava durumunu ozetler. Varsayilan konum Istanbul'dur. "
            "Kullanici hava durumunu, sicakligi veya yagmur durumunu sordugunda kullan."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "location": {
                    "type": "STRING",
                    "description": "Sehir veya konum. Bos birakilirsa Istanbul kullanilir."
                }
            }
        }
    },
    {
        "name": "get_calendar_events",
        "description": (
            "Apple Calendar takvimini okur. "
            "Bugun, yarin, siradaki etkinlik veya yaklasan ajandayi ozetler. "
            "Kullanici toplanti, takvim, ajanda, etkinlik veya gunluk programini sordugunda kullan."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "query": {
                    "type": "STRING",
                    "description": (
                        "today | tomorrow | next | agenda | week veya dogal dilde "
                        "'onumuzdeki 30 gun', '2 hafta', 'bu ay', 'gelecek ay'"
                    )
                },
                "limit": {
                    "type": "NUMBER",
                    "description": "Maksimum etkinlik sayisi"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "add_calendar_event",
        "description": (
            "Apple Calendar takvimine yeni etkinlik ekler. "
            "Kullanici toplanti, randevu, takvime ekleme veya etkinlik olusturma isterse kullan. "
            "Baslangic tarihini gercek tarih/saat olarak ver; bitis verilmezse varsayilan sure kullanilir."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "title": {
                    "type": "STRING",
                    "description": "Etkinlik basligi. Ornek: 'Disci Randevusu'"
                },
                "start_iso": {
                    "type": "STRING",
                    "description": "Baslangic tarih/saat. ISO veya yyyy-MM-dd HH:mm formatinda."
                },
                "end_iso": {
                    "type": "STRING",
                    "description": "Bitis tarih/saat. Opsiyonel."
                },
                "location": {
                    "type": "STRING",
                    "description": "Etkinlik konumu. Opsiyonel."
                },
                "notes": {
                    "type": "STRING",
                    "description": "Etkinlik notlari. Opsiyonel."
                },
                "calendar_name": {
                    "type": "STRING",
                    "description": "Eklenecek takvim adi. Opsiyonel."
                },
                "all_day": {
                    "type": "BOOLEAN",
                    "description": "true ise tum gun etkinligi olusturur."
                }
            },
            "required": ["title", "start_iso"]
        }
    },
    {
        "name": "delete_calendar_event",
        "description": (
            "Apple Calendar takviminden etkinlik siler. "
            "Kullanici bir toplantiyi, randevuyu veya takvim kaydini silmek istediginde kullan. "
            "Ayni ada birden fazla etkinlik varsa dogru kaydi bulmak icin baslangic tarihini gercek tarih/saat olarak ver."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "title": {
                    "type": "STRING",
                    "description": "Silinecek etkinlik basligi. Ornek: 'Disci Randevusu'"
                },
                "start_iso": {
                    "type": "STRING",
                    "description": "Opsiyonel tarih/saat. Ayni isimli birden fazla etkinligi ayirt etmek icin kullan."
                },
                "calendar_name": {
                    "type": "STRING",
                    "description": "Opsiyonel takvim adi"
                },
                "delete_all_matches": {
                    "type": "BOOLEAN",
                    "description": "true ise eslesen tum etkinlikleri siler"
                }
            },
            "required": ["title"]
        }
    },
    {
        "name": "get_reminders",
        "description": (
            "Apple Animsaticilar listesini okur. "
            "Bugunku, yaklasan, geciken veya tum acik animsaticilari ozetler. "
            "Kullanici hatirlatma, animsatici, reminder veya yapilacaklar listesini sordugunda kullan."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "query": {
                    "type": "STRING",
                    "description": "today | upcoming | overdue | all | next"
                },
                "limit": {
                    "type": "NUMBER",
                    "description": "Maksimum animsatici sayisi"
                },
                "list_name": {
                    "type": "STRING",
                    "description": "Istenirse belirli bir animsatici listesi adi"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "add_reminder",
        "description": (
            "Apple Animsaticilar uygulamasina yeni bir animsatici ekler. "
            "Kullanici 'hatirlat', 'animsatici ekle', 'reminder kur' dediginde kullan. "
            "Goreli zaman ifadelerini bugunku tarih baglamina gore due_iso alanina ISO formatinda cevir."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "title": {
                    "type": "STRING",
                    "description": "Animsatici basligi"
                },
                "due_iso": {
                    "type": "STRING",
                    "description": "Opsiyonel tarih/saat. Ornek: 2026-04-13T09:00 veya tum gun icin 2026-04-13"
                },
                "notes": {
                    "type": "STRING",
                    "description": "Opsiyonel not"
                },
                "list_name": {
                    "type": "STRING",
                    "description": "Opsiyonel animsatici listesi"
                },
                "priority": {
                    "type": "STRING",
                    "description": "low | medium | high"
                },
                "all_day": {
                    "type": "BOOLEAN",
                    "description": "Tum gun animsatici ise true"
                }
            },
            "required": ["title"]
        }
    },
    {
        "name": "browser_control",
        "description": "Tarayıcıda URL açar, Google'da arama yapar veya YouTube'da ilk sonucu doğrudan oynatır.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "open_url | search | play_youtube"},
                "url":    {"type": "STRING", "description": "Açılacak URL (open_url için)"},
                "query":  {"type": "STRING", "description": "Arama sorgusu (search veya play_youtube için)"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "shell_run",
        "description": "macOS terminal komutu çalıştırır. Dosya işlemleri, sistem yönetimi.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "command": {
                    "type": "STRING",
                    "description": "Çalıştırılacak bash komutu"
                }
            },
            "required": ["command"]
        }
    },
    {
        "name": "toggle_webcam",
        "description": (
            "Gerçek zamanlı webcam akışını başlatır veya durdurur. "
            "Akış aktifken model sürekli kamera görüntüsü alır — 'bak', 'gör', 'göster', "
            "'kameraya bak', 'önümdekileri anlat', 'ne görüyorsun' gibi komutlarda 'start' kullan. "
            "'kamerayı kapat', 'artık bakma' gibi durumlarda 'stop' kullan."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {
                    "type": "STRING",
                    "description": "start — akışı başlat  |  stop — akışı durdur"
                }
            },
            "required": ["action"]
        }
    },
    {
        "name": "play_media",
        "description": (
            "YouTube, Spotify veya Apple Music/Music uygulamasında şarkı, müzik veya video açar. "
            "Kullanıcı belirli bir platform söylerse onu kullan. "
            "Belirtmezse uygun olanı dene. "
            "Kullanıcı 'çal', 'oynat', 'aç' diyorsa autoplay=true kullan."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "query": {
                    "type": "STRING",
                    "description": "Şarkı, sanatçı, albüm veya video arama ifadesi"
                },
                "provider": {
                    "type": "STRING",
                    "description": "auto | youtube | spotify | apple_music"
                },
                "autoplay": {
                    "type": "BOOLEAN",
                    "description": "true ise mümkünse doğrudan oynatır"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_youtube_channel_report",
        "description": (
            "YouTube kanalinin public istatistiklerini ve son videolarin performansini raporlar. "
            "Kullanici kanal istatistiklerini, abone sayisini, son videolarini, buyume hizini "
            "veya YouTube analizini sordugunda kullan. Bu arac Studio yerine public YouTube Data API verisini kullanir."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "query": {
                    "type": "STRING",
                    "description": (
                        "Dogal dilde analiz istegi. Ornek: "
                        "'YouTube istatistiklerim nasil', 'son videolarimi analiz et', "
                        "'kanal buyumemi ozetle'"
                    )
                },
                "handle": {
                    "type": "STRING",
                    "description": (
                        "Opsiyonel kanal handle'i, kanal linki veya kanal ID'si. "
                        "Bos birakilirsa ayarlardaki youtube_channel_handle kullanilir."
                    )
                },
                "video_limit": {
                    "type": "NUMBER",
                    "description": "Analize dahil edilecek son video sayisi. Varsayilan 6."
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "analyze_screen",
        "description": (
            "Aktif pencerenin ekran goruntusunu alip Gemini vision ile analiz eder. "
            "Kullanici ekranda ne oldugunu, bir hatayi, gorunen metni, butonlari veya pencere icerigini sordugunda kullan. "
            "Bu surum yalnizca aktif pencereyi destekler."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "query": {
                    "type": "STRING",
                    "description": "Kullanicinin ekranla ilgili sorusu. Ornek: 'Bu hatayi oku', 'Ekranda ne var?'"
                },
                "target": {
                    "type": "STRING",
                    "description": "Su an sadece active_window desteklenir."
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "save_memory",
        "description": "Kullanıcı hakkında önemli bilgiyi kalıcı belleğe kaydeder. İsim, tercihler, projeler vb. duyunca sessizce çağır.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "category": {
                    "type": "STRING",
                    "description": "identity | preferences | projects | notes"
                },
                "key":   {"type": "STRING", "description": "Kısa anahtar (örn. 'name')"},
                "value": {"type": "STRING", "description": "Değer (İngilizce)"}
            },
            "required": ["category", "key", "value"]
        }
    },
    {
        "name": "delete_memory",
        "description": (
            "Kalici hafizadaki bir kaydi siler. "
            "Kullanici 'bunu hafizandan kaldir', 'unut', 'sil' gibi bir sey derse kullan. "
            "Mumkunse category ve key ile sil; emin degilsen match_text ile ilgili kaydi bulup kaldir."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "category": {
                    "type": "STRING",
                    "description": "Kaydin kategorisi. Ornek: notes | identity | preferences | projects"
                },
                "key": {
                    "type": "STRING",
                    "description": "Silinecek anahtar. Ornek: claude_limit_refresh"
                },
                "match_text": {
                    "type": "STRING",
                    "description": "Kaydi bulmak icin kullanilacak dogal dil parcasi. Ornek: 'claude ai limit yenilenmesi'"
                }
            }
        }
    },
    {
        "name": "send_whatsapp_message",
        "description": (
            "WhatsApp Desktop veya WhatsApp Web üzerinden mesaj taslağı açar veya mesajı gönderir. "
            "Kişi adı veya telefon numarasıyla çalışabilir. "
            "Telefon numarası verilmemişse kişi adını önce kayıtlı WhatsApp kişileri ve içe aktarılan telefon rehberinde ara. "
            "Kullanıcı 'gönder', 'yolla', 'ile', 'hemen gönder' gibi açık bir gönderme niyeti söylüyorsa "
            "ekstra onay istemeden send_now=true kullan. "
            "Yalnızca 'hazırla', 'taslak aç', 'yaz ama gönderme' diyorsa send_now=false kullan."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "recipient_name": {
                    "type": "STRING",
                    "description": "Kişi adı. Örn: 'Anne', 'Ahmet', 'Ece'"
                },
                "phone_number": {
                    "type": "STRING",
                    "description": "Uluslararası telefon numarası. Örn: +905551112233"
                },
                "message": {
                    "type": "STRING",
                    "description": "Gönderilecek mesaj içeriği"
                },
                "app_target": {
                    "type": "STRING",
                    "description": "desktop | web | auto. Varsayılan auto, tercihen desktop."
                },
                "send_now": {
                    "type": "BOOLEAN",
                    "description": "true ise sohbet açıldıktan sonra mesajı otomatik gönderir"
                }
            },
            "required": ["message"]
        }
    },
    {
        "name": "create_whatsapp_sales_campaign",
        "description": (
            "WhatsApp üzerinden müşteriye veya kişiye özel indirimli teklif, ikna edici mesaj ve canlı sesli görüşme odası hazırlar. "
            "Kullanıcı 'Ahmet'e bu teklifi yap', 'Leo'yu WhatsApp'tan ara, şu kadar indirim yap', "
            "'Müşteriye WhatsApp'tan ulaş ve özellikleri anlat' dediğinde kullan."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "recipient_name": {
                    "type": "STRING",
                    "description": "Müşterinin veya teklif verilecek kişinin adı (Örn: 'Leo', 'Ahmet Bey')"
                },
                "phone_number": {
                    "type": "STRING",
                    "description": "Varsa telefon numarası (Örn: +905551234567)"
                },
                "product_name": {
                    "type": "STRING",
                    "description": "Sunulan ürün, paket veya hizmetin adı"
                },
                "discount": {
                    "type": "STRING",
                    "description": "Müşteriye özel tanımlanan indirim oranı veya fiyat avantajı (Örn: '%25 İndirim', '750 TL')"
                },
                "features": {
                    "type": "STRING",
                    "description": "Ürünün/paketin öne çıkan özellikleri (virgülle ayrılmış)"
                },
                "custom_notes": {
                    "type": "STRING",
                    "description": "Varsa ek talimatlar, pazarlık kuralları veya kişiye özel notlar"
                }
            },
            "required": ["recipient_name", "discount"]
        }
    },
    {
        "name": "save_whatsapp_contact",
        "description": (
            "Sık kullanılan bir WhatsApp kişisini adı ve telefon numarasıyla kalıcı belleğe kaydeder. "
            "Kullanıcı bir kişiyi 'annem', 'Ahmet', 'iş ortağım' gibi tekrar kullanılacak şekilde tanımladığında kullan."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "display_name": {
                    "type": "STRING",
                    "description": "Kaydedilecek kişi adı. Örn: 'Annem', 'Ahmet'"
                },
                "phone_number": {
                    "type": "STRING",
                    "description": "Uluslararası telefon numarası. Örn: +905551112233"
                },
                "aliases": {
                    "type": "STRING",
                    "description": "Virgülle ayrılmış alternatif hitaplar. Örn: 'anne, annem, mom'"
                }
            },
            "required": ["display_name", "phone_number"]
        }
    },
    {
        "name": "whatsapp_broadcast",
        "description": "Birden fazla kişiye toplu WhatsApp mesajı gönderir veya taslak oluşturur.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "recipients": {
                    "type": "STRING",
                    "description": "Virgülle ayrılmış alıcı isimleri veya telefon numaraları. Örn: 'Ahmet, Mehmet, +905551112233'"
                },
                "message": {
                    "type": "STRING",
                    "description": "Gönderilecek mesaj metni"
                },
                "send_now": {
                    "type": "BOOLEAN",
                    "description": "true ise onay beklemeden doğrudan gönderir"
                }
            },
            "required": ["recipients", "message"]
        }
    },
    {
        "name": "find_location",
        "description": "Cihaz, kişi veya adres konumunu bulur. Harita koordinatları ve adres bilgisi döner.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "query": {
                    "type": "STRING",
                    "description": "Adres, yer veya mekan sorgusu. Boş bırakılırsa cihazın mevcut konumu bulunur."
                },
                "target": {
                    "type": "STRING",
                    "description": "device (cihaz) | address (adres/mekan) | person (kişi)"
                },
                "open_maps": {
                    "type": "BOOLEAN",
                    "description": "true ise harita uygulamasında konumu gösterir"
                }
            }
        }
    },
    {
        "name": "instagram_tracker",
        "description": "Belirtilen Instagram profilindeki takip, takipçi ve aktivite değişikliklerini izler.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "username": {
                    "type": "STRING",
                    "description": "Instagram kullanıcı adı (örn: 'elonmusk')"
                },
                "action": {
                    "type": "STRING",
                    "description": "check (durum kontrolü) | track (takip listesine ekle) | history (geçmiş değişimler)"
                }
            },
            "required": ["username"]
        }
    },
    {
        "name": "social_post_scheduler",
        "description": "Sosyal medyada belirli saatte içerik veya hikaye paylaşımını zamanlar.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "platform": {
                    "type": "STRING",
                    "description": "instagram | twitter | linkedin | all"
                },
                "content": {
                    "type": "STRING",
                    "description": "Paylaşılacak metin veya gönderi açıklaması"
                },
                "scheduled_time": {
                    "type": "STRING",
                    "description": "Planlanan tarih ve saat. Örn: '2026-04-15 14:00' veya 'yarın 10:00'"
                },
                "media_url": {
                    "type": "STRING",
                    "description": "Opsiyonel görsel veya medya yolu/URL'i"
                }
            },
            "required": ["platform", "content", "scheduled_time"]
        }
    },
    {
        "name": "social_ad_manager",
        "description": "Bütçe ve hedef kitleye göre sosyal medya reklam kampanyası planlar ve yönetir.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {
                    "type": "STRING",
                    "description": "create (oluştur) | list (listele) | optimize (optimizasyon önerisi) | status (durum)"
                },
                "campaign_name": {
                    "type": "STRING",
                    "description": "Kampanya adı"
                },
                "budget": {
                    "type": "NUMBER",
                    "description": "Toplam bütçe tutarı (TL)"
                },
                "target_audience": {
                    "type": "STRING",
                    "description": "Hedef kitle tanımı (örn: '18-35 yaş, Teknoloji, İstanbul')"
                }
            },
            "required": ["action"]
        }
    },
    {
        "name": "smart_home_control",
        "description": "WiFi ve IoT akıllı ev cihazlarını (klima, ışık, priz, kilit vb.) kontrol eder. Kritik işlemlerde (kilit açma) onay zorunludur.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "device_type": {
                    "type": "STRING",
                    "description": "light (ışık) | climate (klima) | plug (priz) | lock (kilit) | all (tümü)"
                },
                "action": {
                    "type": "STRING",
                    "description": "turn_on (aç) | turn_off (kapat) | set_temp (ısı ayarla) | status (durum)"
                },
                "room": {
                    "type": "STRING",
                    "description": "Oda adı (örn: 'Salon', 'Yatak Odası', 'Mutfak')"
                },
                "value": {
                    "type": "STRING",
                    "description": "Sıcaklık veya parlaklık değeri (örn: '22', '%80')"
                },
                "confirmed": {
                    "type": "BOOLEAN",
                    "description": "Kritik güvenlik işlemlerinde (kilit açma) kullanıcı onayı verilmişse true"
                }
            },
            "required": ["device_type", "action"]
        }
    },
    {
        "name": "file_organizer",
        "description": "İndirilenler, Masaüstü veya hedef klasördeki dağınık dosyaları türlerine ve tarihlerine göre düzenler.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "directory_path": {
                    "type": "STRING",
                    "description": "Düzenlenecek klasör yolu. Varsayılan '~/Downloads'"
                },
                "dry_run": {
                    "type": "BOOLEAN",
                    "description": "true ise dosyaları taşımadan sadece planı gösterir"
                },
                "group_by": {
                    "type": "STRING",
                    "description": "type (türe göre) | date (tarihe göre)"
                }
            }
        }
    },
    {
        "name": "mail_agent",
        "description": "macOS Apple Mail üzerinden e-postaları okur, özetler, arar ve taslak yanıt hazırlar.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {
                    "type": "STRING",
                    "description": "unread (okunmamışları özetle) | search (arama yap) | draft (taslak aç) | send (gönder)"
                },
                "query": {
                    "type": "STRING",
                    "description": "Arama sorgusu (gönderen adı veya konu)"
                },
                "recipient": {
                    "type": "STRING",
                    "description": "Alıcı e-posta adresi (taslak için)"
                },
                "subject": {
                    "type": "STRING",
                    "description": "E-posta konusu"
                },
                "body": {
                    "type": "STRING",
                    "description": "E-posta gövde metni"
                }
            },
            "required": ["action"]
        }
    },
    {
        "name": "cron_scheduler",
        "description": "Arka plan rutinleri, periyodik görevler ve zamanlanmış hatırlatıcılar ayarlar.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {
                    "type": "STRING",
                    "description": "list (listele) | add (yeni rutin ekle) | remove (sil)"
                },
                "task_name": {
                    "type": "STRING",
                    "description": "Rutin veya görev adı"
                },
                "cron_expression": {
                    "type": "STRING",
                    "description": "Zaman ifadesi (örn: 'her gün 09:00', '0 9 * * *')"
                },
                "command": {
                    "type": "STRING",
                    "description": "Çalıştırılacak eylem veya komut"
                }
            },
            "required": ["action"]
        }
    },
    {
        "name": "survival_guide",
        "description": "Çevrimdışı ilk yardım, deprem/afet rehberi ve acil durum numaraları sunar.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "topic": {
                    "type": "STRING",
                    "description": "emergency_numbers (acil numaralar) | earthquake (deprem) | first_aid (ilk yardım) | fire (yangın) | outage (kesinti)"
                },
                "query": {
                    "type": "STRING",
                    "description": "Özel arama terimi (örn: 'Heimlich', 'yanık', 'deprem çantası')"
                }
            }
        }
    },
    {
        "name": "companion_mode",
        "description": "JARVIS'in sohbet tonunu ve arkadaş canlısı yol arkadaşı modunu yönetir.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "mode": {
                    "type": "STRING",
                    "description": "friendly (arkadaş canlısı, dinamik) | formal (resmi, asistan) | concise (ultra kısa) | coach (yaşam koçu)"
                },
                "enabled": {
                    "type": "BOOLEAN",
                    "description": "true ise aktif eder, false ise standart asistan moduna döner"
                }
            }
        }
    },
    {
        "name": "get_device_telemetry",
        "description": "Cihazın anlık GPS konumunu, pil seviyesini, sensör verilerini ve bağlı ağ bilgilerini alır.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "include_location": { "type": "BOOLEAN", "description": "Konum dahil edilsin mi" },
                "include_network": { "type": "BOOLEAN", "description": "Ağ bilgisi dahil edilsin mi" }
            }
        }
    },
    {
        "name": "control_mobile_app",
        "description": "Mobil cihazda veya macOS'ta yüklü her türlü uygulamayı başlatır, kapatır veya arka planda çalıştırır.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "app_name": { "type": "STRING", "description": "Uygulama adı" },
                "action": { "type": "STRING", "description": "open | close | restart | background" }
            },
            "required": ["app_name", "action"]
        }
    },
    {
        "name": "voice_command_listener",
        "description": "Sürekli sesli dinleme modunu yönetir, alınan sesli girdileri doğrudan komut dizisine dönüştürür.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "mode": { "type": "STRING", "description": "always_on | push_to_talk | disabled" }
            },
            "required": ["mode"]
        }
    },
    {
        "name": "instagram_live_stalker",
        "description": "Kullanıcının Instagram hesabı ve şifresi/oturumunu yönetir, hedef profilleri (ör. sevgili) sürekli izler, takipçi/takip listesindeki artış ve azalışları (yeni eklenenler/çıkanlar) anlık tespit edip bildirim ve canlı liste oluşturur.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": { "type": "STRING", "description": "track (hedefi izle/tara) | list_changes (tüm eklenen/çıkan değişim listesini getir) | login (kullanıcı hesabına şifreyle giriş yap) | status (oturum ve izleme durumu)" },
                "target_username": { "type": "STRING", "description": "İzlenecek hedef profilin kullanıcı adı (ör. sevgili veya rakip hesap)" },
                "username": { "type": "STRING", "description": "Kullanıcının kendi Instagram kullanıcı adı (giriş için)" },
                "password": { "type": "STRING", "description": "Kullanıcının kendi Instagram şifresi (hesaba doğrudan giriş için)" },
                "session_auth_token": { "type": "STRING", "description": "Kullanıcının giriş oturum token'ı veya cookie" },
                "track_new_followers": { "type": "BOOLEAN", "description": "Yeni takipçileri takip et" },
                "track_following_changes": { "type": "BOOLEAN", "description": "Takip edilen değişikliklerini izle" },
                "alert_immediately": { "type": "BOOLEAN", "description": "Anında uyar" }
            }
        }
    },
    {
        "name": "business_meta_auto_publisher_and_ads",
        "description": "İşletme hesabında belirlenen saatte görsel/video paylaşır ve ardından Meta Ads Manager üzerinden belirlenen günlük bütçe ve coğrafi bölgeye doğrudan reklam kampanyası başlatır.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "media_path": { "type": "STRING", "description": "Paylaşılacak görsel veya videonun yolu" },
                "publish_time_iso": { "type": "STRING", "description": "Paylaşımın yapılacağı ISO tarih/saat" },
                "caption": { "type": "STRING", "description": "Gönderi metni" },
                "enable_meta_ad": { "type": "BOOLEAN", "description": "Meta reklamı aktif et" },
                "daily_budget": { "type": "NUMBER", "description": "Günlük reklam bütçesi (TRY/USD)" },
                "target_locations": {
                    "type": "ARRAY",
                    "items": { "type": "STRING" },
                    "description": "Hedef şehirler veya ülkeler (ör. ['Istanbul', 'Izmir'])"
                },
                "target_audience": { "type": "STRING", "description": "Hedef kitle detayları (yaş, ilgi alanları vb.)" }
            },
            "required": ["media_path", "daily_budget", "target_locations"]
        }
    },
    {
        "name": "instagram_stalker_agent",
        "description": "Hedef Instagram profilinin takip ettiği/çıkardığı kişileri, paylaşımlarını ve hikayelerini periyodik izler.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "target_username": { "type": "STRING", "description": "Hedef kullanıcı adı" },
                "track_following_changes": { "type": "BOOLEAN", "description": "Takipçi/takip edilen değişikliklerini izle" },
                "notify_interval_minutes": { "type": "INTEGER", "description": "Bildirim aralığı dakika" }
            },
            "required": ["target_username"]
        }
    },
    {
        "name": "social_media_manager",
        "description": "Sosyal medya hesaplarında hikaye/gönderi paylaşır ve belirlenen bütçe/kitleyle otomatik reklam kampanyası yürütür.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "platform": { "type": "STRING", "description": "instagram | facebook | tiktok | x" },
                "action": { "type": "STRING", "description": "post_story | post_feed | create_ad" },
                "content_uri": { "type": "STRING", "description": "Görsel veya video URL / dosya yolu" },
                "ad_budget": { "type": "NUMBER", "description": "Reklam bütçesi tutarı" },
                "target_audience": { "type": "STRING", "description": "Hedef kitle tanımı" }
            },
            "required": ["platform", "action"]
        }
    },
    {
        "name": "smart_home_iot_hub",
        "description": "WiFi/Local ağdaki tüm akıllı ev (HomeKit, Tuya vb.) cihazlarını (klima, priz, ışık) yönetir.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "device_name": { "type": "STRING", "description": "Cihaz adı (klima, lamba, priz, kilit)" },
                "action": { "type": "STRING", "description": "Aç, kapat, sıcaklık ayarla vb." },
                "value": { "type": "STRING", "description": "Değer veya parametre" }
            },
            "required": ["device_name", "action"]
        }
    },
    {
        "name": "survival_companion_mode",
        "description": "Çevrimdışı acil durum/hayatta kalma modunu veya arkadaş canlısı sohbet modunu tetikler.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "mode": { "type": "STRING", "description": "companion_chat | offline_survival" }
            },
            "required": ["mode"]
        }
    },
    {
        "name": "apply_command_center_ui",
        "description": "Mobil ve macOS arayüzünü LEO Command Center HUD temasına dönüştürür.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "enable_hud_overlay": { "type": "BOOLEAN", "description": "HUD modunu aç" },
                "theme_style": { "type": "STRING", "description": "HUD_CYBER_COMMAND_CENTER" }
            }
        }
    }
]
