# LEO OS — 7/24 Bulut ve Telefon Kurulum Rehberi
**Krijuesi: leohoca**

Bu rehber, bilgisayarınız tamamen kapalı olsa bile LEO'nun telefonunuzda 7/24 çalışmasını ve telefonunuza gerçek bir mobil uygulama (App) gibi yüklenmesini sağlar.

---

## 1. Telefonunuza Gerçek Uygulama Olarak Yükleme (PWA)

LEO artık tam bir **Progressive Web App (PWA)** standartındadır.

### 📱 iPhone / iPad (iOS Safari):
1. Safari tarayıcısında LEO adresinizi (Cloudflare linkinizi veya bulut adresinizi) açın.
2. Ekranın altındaki **Paylaş (Share)** butonuna (yukarı oklu kare) dokunun.
3. Menüden **"Ana Ekrana Ekle" (Add to Home Screen)** seçeneğini seçin.
4. Sağ üstteki **"Ekle"**ye dokunun.
5. Artık telefonunuzun ana ekranında siyah-neon simgesiyle **LEO OS** belirecektir. Üzerine dokunduğunuzda Safari adres çubuğu olmadan, tam ekran gerçek bir iOS uygulaması gibi açılır!

### 🤖 Android (Google Chrome):
1. Chrome'da LEO linkinizi açın.
2. Sağ üstteki üç noktaya (**⋮**) dokunun.
3. **"Uygulamayı Yükle"** veya **"Ana Ekrana Ekle"** butonuna basın.
4. LEO artık Android menünüzde bağımsız bir uygulama olarak yüklenecektir.

---

## 2. Bilgisayar Kapalıyken LEO'nun 7/24 Açık Kalması (Always-On Cloud)

Şu anda Mac'inizden `WEB_BASLAT.command` veya JARVIS/LEO arayüzü ile başlattığınızda sunucu yerel Mac'inizde çalışır. Mac'inizi kapattığınızda yerel sunucu durur.

**Bilgisayarınız kapalıyken bile telefonunuzdan kesintisiz kullanmak için:**

### Seçenek A: Ücretsiz Render.com Dağıtımı (5 Dakika)
1. [Render.com](https://render.com) veya [Railway.app](https://railway.app) üzerinde ücretsiz bir hesap açın.
2. GitHub'a bu klasörü yükleyin veya Render'da **New Web Service > Docker** seçin.
3. Hazırladığımız `Dockerfile` ve `render.yaml` dosyaları sayesinde sistem otomatik olarak kurulur.
4. Environment Variables kısmına:
   - `GEMINI_API_KEY`: Sizin Gemini anahtarınız
5. Size verilen `https://leo-ai-xxxx.onrender.com` adresini telefonunuzda açın ve Ana Ekrana Ekleyin!
6. Artık Mac'iniz kapalı olsa dahi LEO telefonunuzda 7/24 aktiftir!

### Seçenek B: Mac Açıkken Cloudflare Tüneli (Mevcut Yöntem)
- Mac'iniz açıkken JARVIS ekranındaki **"JARVIS TELEFON"** panelinden **"▶ BAŞLAT"** butonuna bastığınızda Cloudflare tüneli açılır ve bilgisayarınız açık kaldığı sürece telefonunuzdan her yerden bağlanabilirsiniz.

---

## 3. Güvenlik: Face ID & PIN Kilidi
- Uygulama ilk açıldığında LEO güvenlik kalkanı devreye girer.
- **PIN:** `1234` (İstediğiniz zaman değiştirebilirsiniz).
- **Face ID:** Kameranız açıkken yüzünüzü tarar ve "FYTYRA U NJOH: leohoca ✅" onayıyla uygulamayı açar.
