# LEO OS — Cyber Command Center & 7/24 Mobile AI
**Krijuesi:** `leohoca`  
**Tema:** `HUD_CYBER_COMMAND_CENTER` (#00f3ff, #0066ff, #050811)  
**Mimari:** Full Unrestricted Access — Voice & Vision & Social Stalker Live Diff Engine

---

## 🚀 1 Dakikada Buluta Dağıtım (Bilgisayar Kapalıyken 7/24 Çalışma)

Bilgisayarınız kapalıyken bile telefonunuzdan kesintisiz kullanabilmek için sistemi **Vercel** (Ücretsiz Domain & Hızlı Arayüz) ve **Render** (7/24 Arka Plan & WebSocket) üzerine bağlayabilirsiniz:

### Adım 1: Render.com Üzerine 7/24 Arka Plan Kurulumu (Ücretsiz)
1. [Render.com](https://render.com) hesabınıza giriş yapın.
2. **New +** ➡️ **Web Service** seçin.
3. GitHub deponuzu bağlayın: `Leozzerss/LEO-AI-OS`
4. Ayarlar:
   - **Environment:** `Docker` (Dockerfile kök dizinde hazırdır)
   - **Plan:** `Free`
   - **Environment Variables:**
     - `GEMINI_API_KEY`: *(Google Gemini API Anahtarınız)*
     - `PORT`: `8765`
5. **Create Web Service** butonuna basın. Birkaç dakika içinde size ücretsiz bir kalıcı adres verilecektir:  
   `https://leo-ai-backend.onrender.com`

---

### Adım 2: Vercel Üzerine Arayüz & Ücretsiz Domain Kurulumu (.vercel.app)
1. [Vercel.com](https://vercel.com) hesabınıza gidin.
2. **Add New...** ➡️ **Project** butonuna tıklayın.
3. GitHub deponuzu seçin (`Leozzerss/LEO-AI-OS`) ve **Deploy** deyin.
4. Vercel size anında kalıcı ve ücretsiz bir SSL alan adı verecektir:  
   `https://leo-ai-os.vercel.app`

---

### Adım 3: Telefonunuzda Tek Tıkla Bağlantı
Vercel adresinizi telefonunuzun Safari tarayıcısında Render backend adresinizle birlikte tek seferlik açın:
```text
https://leo-ai-os.vercel.app/?backend=https://leo-ai-backend.onrender.com
```
*(Sistem bu adresi telefonunuzun hafızasına kaydeder. Sonraki tüm girişlerinizde doğrudan Vercel adresinizi açmanız yeterlidir).*

---

## 📱 iPhone / Android Telefona Gerçek Uygulama Olarak Yükleme (PWA)
1. Telefonunuzun Safari (iOS) veya Chrome (Android) tarayıcısında Vercel adresinizi açın.
2. Alttaki **Paylaş (Share)** butonuna basın ➡️ **"Ana Ekrana Ekle" (Add to Home Screen)** deyin.
3. Artık Safari adres çubuğu olmadan tam ekran siyah-neon LEO simgesiyle gerçek bir iOS uygulaması gibi açılır!

---

## 🔐 Güvenlik ve Kimlik Doğrulama
- **Varsayılan PIN:** `1234`
- **Biyometrik Kilit:** Face ID tarama animasyonuyla otomatik yüz algılama.
- **Instagram Oturumu:** `🔐 GİRİŞ YAP & HESAPLAR` menüsünden şifrenizle giriş yapıp hedef hesapları canlı izleyebilirsiniz.
