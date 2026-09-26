const { default: makeWASocket, useMultiFileAuthState, DisconnectReason, fetchLatestBaileysVersion } = require('@whiskeysockets/baileys');
const pino = require('pino');
const QRCode = require('qrcode');
const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = 8769;
const AUTH_DIR = path.join(__dirname, 'auth_info');
const PY_API_URL = 'http://127.0.0.1:8765/api/whatsapp/chat';

let sock = null;
let currentQR = null;
let currentQRDataUrl = null;
let isConnected = false;
let connectedUser = null;

async function startWhatsApp() {
  const { state, saveCreds } = await useMultiFileAuthState(AUTH_DIR);
  const { version, isLatest } = await fetchLatestBaileysVersion();
  console.log(`[Baileys] WhatsApp Web version ${version.join('.')} (isLatest: ${isLatest})`);

  sock = makeWASocket({
    version,
    logger: pino({ level: 'silent' }),
    printQRInTerminal: true,
    auth: state,
    browser: ['LEO AI OS', 'Safari', '3.5.0'],
    syncFullHistory: false
  });

  sock.ev.on('creds.update', saveCreds);

  sock.ev.on('connection.update', async (update) => {
    const { connection, lastDisconnect, qr } = update;

    if (qr) {
      currentQR = qr;
      try {
        currentQRDataUrl = await QRCode.toDataURL(qr, { margin: 2, scale: 8 });
        console.log('\n╔════════════════════════════════════════════════════╗');
        console.log('║  📲 SKANO QR KODIN NGA WHATSAPP (LINKED DEVICES)   ║');
        console.log('╚════════════════════════════════════════════════════╝\n');
        const termQR = await QRCode.toString(qr, { type: 'terminal', small: true });
        console.log(termQR);
      } catch (err) {
        console.error('[Baileys] QR generation error:', err);
      }
    }

    if (connection === 'close') {
      isConnected = false;
      connectedUser = null;
      const shouldReconnect = lastDisconnect?.error?.output?.statusCode !== DisconnectReason.loggedOut;
      console.log(`[Baileys] Connection closed. Reconnecting: ${shouldReconnect}`);
      if (shouldReconnect) {
        setTimeout(startWhatsApp, 3000);
      } else {
        console.log('[Baileys] Logged out. Clearing credentials...');
        try {
          fs.rmSync(AUTH_DIR, { recursive: true, force: true });
        } catch (e) {}
        setTimeout(startWhatsApp, 2000);
      }
    } else if (connection === 'open') {
      isConnected = true;
      currentQR = null;
      currentQRDataUrl = null;
      connectedUser = sock.user;
      console.log('\n✅ [Baileys] WHATSAPP ME SUKSES U LIDH!');
      console.log(`👤 Përdoruesi: ${sock.user?.name || 'LEO OS'} (${sock.user?.id})`);
    }
  });

  // Gelen Mesajları Dinle ve LEO AI ile Otomatik Cevapla
  sock.ev.on('messages.upsert', async ({ messages, type }) => {
    if (type !== 'notify') return;

    for (const msg of messages) {
      // Kendi gönderdiğimiz mesajları atla
      if (msg.key.fromMe) continue;
      // Grup mesajlarını veya status güncellemelerini atla
      const jid = msg.key.remoteJid;
      if (!jid || jid.endsWith('@g.us') || jid === 'status@broadcast') continue;

      const messageContent =
        msg.message?.conversation ||
        msg.message?.extendedTextMessage?.text ||
        msg.message?.imageMessage?.caption ||
        '';

      if (!messageContent || !messageContent.trim()) continue;

      const senderPhone = jid.split('@')[0];
      const pushName = msg.pushName || 'Klient';

      console.log(`[WhatsApp Inbound] Nga: ${pushName} (${senderPhone}): "${messageContent}"`);

      // LEO Python API'sine gönder ve Shqip/TR yanıt üret
      try {
        const response = await fetch(PY_API_URL, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            room_id: `wa-${senderPhone}`,
            message: messageContent,
            sender_name: pushName
          })
        });
        const data = await response.json();
        if (data.ok && data.reply) {
          console.log(`[WhatsApp Outbound] LEO Përgjigjet te ${senderPhone}: "${data.reply}"`);
          // WhatsApp üzerinden otomatik yanıtı gönder
          await sock.sendMessage(jid, { text: data.reply });
        }
      } catch (err) {
        console.error('[Baileys] Error calling LEO Python backend:', err.message);
      }
    }
  });
}

// ── HTTP API Sunucusu (FastAPI ve Frontend ile iletişim) ─────────────────────
const server = http.createServer((req, res) => {
  // CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.writeHead(200);
    return res.end();
  }

  const url = new URL(req.url, `http://localhost:${PORT}`);

  if (url.pathname === '/status') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    return res.end(JSON.stringify({
      connected: isConnected,
      user: connectedUser,
      hasQR: !!currentQRDataUrl
    }));
  }

  if (url.pathname === '/qr') {
    if (isConnected) {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      return res.end(JSON.stringify({ status: 'connected', user: connectedUser }));
    }
    if (!currentQRDataUrl) {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      return res.end(JSON.stringify({ status: 'waiting', message: 'QR kodi po gjenerohet...' }));
    }
    res.writeHead(200, { 'Content-Type': 'application/json' });
    return res.end(JSON.stringify({ status: 'qr_ready', qr: currentQRDataUrl }));
  }

  if (url.pathname === '/qr.html') {
    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
    return res.end(`
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="utf-8">
        <title>LEO AI — WhatsApp QR Lidhja</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
          body { background:#030c16; color:#fff; font-family:-apple-system, sans-serif; display:flex; flex-direction:column; align-items:center; justify-content:center; min-height:100vh; margin:0; text-align:center; padding:1.5rem; }
          .card { background:rgba(7,21,36,0.9); border:1px solid #00f3ff; border-radius:20px; padding:2rem; max-width:380px; box-shadow:0 0 40px rgba(0,243,255,0.25); }
          h2 { color:#25d366; margin-top:0; }
          #qr-img { width:260px; height:260px; border-radius:12px; background:#fff; padding:10px; margin:1rem 0; }
          .inst { font-size:0.85rem; color:#94a3b8; line-height:1.5; text-align:left; background:rgba(0,0,0,0.3); padding:10px; border-radius:8px; }
          .status { font-weight:700; margin-top:1rem; color:#00f3ff; }
        </style>
      </head>
      <body>
        <div class="card">
          <h2>📲 Lidh WhatsApp me LEO AI</h2>
          <div class="inst">
            1. Hap <b>WhatsApp</b> në telefonin tënd.<br>
            2. Shko te <b>Settings (Cilësimet)</b> ➔ <b>Linked Devices (Pajisjet e Lidhura)</b>.<br>
            3. Prek <b>Link a Device (Lidh një Pajisje)</b> dhe skano këtë kod.
          </div>
          <img id="qr-img" src="${currentQRDataUrl || ''}" alt="QR Kod">
          <div class="status" id="status-txt">${isConnected ? '✅ I LIDHUR ME SUKSES!' : 'Po pret skanimin...'}</div>
        </div>
        <script>
          setInterval(async () => {
            try {
              const res = await fetch('/status');
              const data = await res.json();
              if (data.connected) {
                document.getElementById('status-txt').innerHTML = '✅ I LIDHUR ME SUKSES! (' + (data.user?.id || '') + ')';
                document.getElementById('status-txt').style.color = '#25d366';
                document.getElementById('qr-img').style.display = 'none';
              } else {
                const qrRes = await fetch('/qr');
                const qrData = await qrRes.json();
                if (qrData.qr) {
                  document.getElementById('qr-img').src = qrData.qr;
                  document.getElementById('qr-img').style.display = 'block';
                }
              }
            } catch(e) {}
          }, 2500);
        </script>
      </body>
      </html>
    `);
  }

  // Mesaj Gönderme Endpoint'i (Python veya Web panelden tetiklenir)
  if (url.pathname === '/send' && req.method === 'POST') {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', async () => {
      try {
        const { phone, message } = JSON.parse(body);
        if (!isConnected || !sock) {
          res.writeHead(503, { 'Content-Type': 'application/json' });
          return res.end(JSON.stringify({ ok: false, error: 'WhatsApp nuk është i lidhur ende. Skano QR kodin.' }));
        }

        const cleanPhone = phone.replace(/\\D/g, '');
        const jid = `${cleanPhone}@s.whatsapp.net`;
        await sock.sendMessage(jid, { text: message });

        res.writeHead(200, { 'Content-Type': 'application/json' });
        return res.end(JSON.stringify({ ok: true, recipient: jid }));
      } catch (e) {
        res.writeHead(500, { 'Content-Type': 'application/json' });
        return res.end(JSON.stringify({ ok: false, error: e.message }));
      }
    });
    return;
  }

  res.writeHead(404);
  res.end('Not Found');
});

server.listen(PORT, () => {
  console.log(`[WhatsApp Service] Server running on http://127.0.0.1:${PORT}`);
  console.log(`[WhatsApp Service] Open http://127.0.0.1:${PORT}/qr.html to scan QR code`);
  startWhatsApp();
});
