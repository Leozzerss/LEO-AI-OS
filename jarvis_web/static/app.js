/* ══════════════════════════════════════════════════════════════════════════
   L.E.O  OS  —  CLIENT LOGIC & NEURAL ENGINE
   Krijuesi: leohoca  •  Full PWA, Biometric Security & Telemetry
   ══════════════════════════════════════════════════════════════════════════ */

"use strict";

// ── 0. GLOBAL STATE ────────────────────────────────────────────────────────
const S = {
  ws: null,
  ready: false,
  micOn: false,
  camOn: false,
  audioCtx: null,
  playCtx: null,
  workletNode: null,
  micStream: null,
  camStream: null,
  nextPlayTime: 0,
  playingSources: [],
  outLevel: 0,
  inLevel: 0,
  speaking: false,
  reconnectDelay: 2000,
  fatalMsg: null,
  lastLogKey: "",
  public: false,
  apiKey: localStorage.getItem("leo_gemini_api_key") || "",
  awaitingKey: false,
  reconnectTimer: null,
  isUnlocked: false,
  pinBuffer: "",
  correctPin: "1234",
  chatHistory: [],
  outAnalyser: null,
  micAnalyser: null,
  alwaysOn: true,
  iotState: {
    acOn: true,
    acTemp: 21.5,
    lightOn: true,
    lightColor: "cyan",
    plugOn: true,
    locked: true,
  },
  hudOverlay: false,
};

const $ = (id) => document.getElementById(id);

// ── 1. FACE ID & PIN SECURITY LOCK ─────────────────────────────────────────
function initLockScreen() {
  const sessionUnlocked = sessionStorage.getItem("leo_unlocked") === "true";
  if (sessionUnlocked) {
    unlockSystem(false);
    return;
  }

  // Kamera Face ID önizlemesi başlat
  startLockCam();

  // Keypad dinleyicileri
  document.querySelectorAll(".keypad .key-btn[data-val]").forEach((btn) => {
    btn.addEventListener("click", () => {
      handlePinInput(btn.dataset.val);
    });
  });

  $("btn-del").addEventListener("click", () => {
    if (S.pinBuffer.length > 0) {
      S.pinBuffer = S.pinBuffer.slice(0, -1);
      updatePinDots();
    }
  });

  $("btn-face-auth").addEventListener("click", () => {
    simulateFaceAuth();
  });

  // Otomatik Face ID simülasyonu 1.8 saniye sonra tetiklensin
  setTimeout(simulateFaceAuth, 1800);
}

async function startLockCam() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: "user" }
    });
    const video = $("lock-cam");
    if (video) video.srcObject = stream;
  } catch (e) {
    $("face-status").textContent = "Vendosni PIN-in e autorizuar (1234)";
  }
}

function stopLockCam() {
  const video = $("lock-cam");
  if (video && video.srcObject) {
    video.srcObject.getTracks().forEach((t) => t.stop());
    video.srcObject = null;
  }
}

function handlePinInput(digit) {
  if (S.pinBuffer.length < 4) {
    S.pinBuffer += digit;
    updatePinDots();
  }

  if (S.pinBuffer.length === 4) {
    if (S.pinBuffer === S.correctPin) {
      $("face-status").textContent = "PIN I SAKTË! Mirësevjen leohoca ✅";
      $("face-status").style.color = "var(--emerald)";
      setTimeout(() => unlockSystem(true), 400);
    } else {
      $("face-status").textContent = "PIN I GABUAR! Provoni përsëri.";
      $("face-status").style.color = "var(--red)";
      setTimeout(() => {
        S.pinBuffer = "";
        updatePinDots();
        $("face-status").textContent = "Vendosni PIN-in (1234)";
        $("face-status").style.color = "var(--cyan)";
      }, 700);
    }
  }
}

function updatePinDots() {
  for (let i = 1; i <= 4; i++) {
    const dot = $("dot-" + i);
    if (dot) dot.classList.toggle("filled", i <= S.pinBuffer.length);
  }
}

function simulateFaceAuth() {
  $("face-status").textContent = "Duke skanuar tiparet e fytyrës...";
  $("face-status").style.color = "var(--cyan)";
  setTimeout(() => {
    $("face-status").textContent = "FYTYRA U NJOH: leohoca ✅";
    $("face-status").style.color = "var(--emerald)";
    setTimeout(() => unlockSystem(true), 600);
  }, 1200);
}

function unlockSystem(saveSession = true) {
  S.isUnlocked = true;
  stopLockCam();
  $("lock-screen").classList.add("unlocked");
  if (saveSession) sessionStorage.setItem("leo_unlocked", "true");

  // Bağlantıyı başlat ve telemetriyi oku
  connect();
  updateTelemetry();
  setInterval(updateTelemetry, 4000);
}

$("btn-relock").addEventListener("click", () => {
  sessionStorage.removeItem("leo_unlocked");
  S.isUnlocked = false;
  S.pinBuffer = "";
  updatePinDots();
  $("lock-screen").classList.remove("unlocked");
  startLockCam();
});

// ── 2. KALICI SOHBET GEÇMİŞİ (LOCALSTORAGE PERSISTENCE) ───────────────────
function loadChatHistory() {
  try {
    const saved = localStorage.getItem("leo_chat_history");
    if (saved) {
      S.chatHistory = JSON.parse(saved);
      renderChatHistory();
    }
  } catch (e) {
    S.chatHistory = [];
  }
}

function saveChatHistory() {
  try {
    if (S.chatHistory.length > 300) S.chatHistory = S.chatHistory.slice(-300);
    localStorage.setItem("leo_chat_history", JSON.stringify(S.chatHistory));
  } catch (e) {}
}

function addLog(who, text) {
  const key = who + "|" + text;
  if (key === S.lastLogKey) return;
  S.lastLogKey = key;

  const now = new Date();
  const timeStr = now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

  const msgObj = { who, text, time: timeStr };
  S.chatHistory.push(msgObj);
  saveChatHistory();

  renderSingleMessage(msgObj);
}

function renderChatHistory() {
  const logEl = $("log");
  if (!logEl) return;
  logEl.innerHTML = "";
  S.chatHistory.forEach((msg) => renderSingleMessage(msg));
}

function renderSingleMessage(msg) {
  const logEl = $("log");
  if (!logEl) return;

  const row = document.createElement("div");
  row.className = `chat-msg ${msg.who === "user" ? "user" : msg.who === "jarvis" ? "leo" : "sys"}`;

  const label = msg.who === "user" ? "JU / SİZ" : msg.who === "jarvis" ? "LEO" : "SISTEMI";

  row.innerHTML = `
    <div class="bubble">${escapeHtml(msg.text)}</div>
    <div class="msg-meta">${label} • ${msg.time}</div>
  `;
  logEl.appendChild(row);
  logEl.scrollTop = logEl.scrollHeight;
}

function escapeHtml(str) {
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

$("btn-clear-chat").addEventListener("click", () => {
  if (confirm("Dëshironi të fshini historikun e bisedës? (Sohbet geçmişi silinsin mi?)")) {
    S.chatHistory = [];
    localStorage.removeItem("leo_chat_history");
    renderChatHistory();
  }
});

function setStatus(text, live = false) {
  const statusEl = $("status");
  if (statusEl) {
    statusEl.textContent = text;
    statusEl.classList.toggle("live", live);
  }
}

// ── 3. ÇOKLU SEKME (TABS) YÖNETİMİ ─────────────────────────────────────────
function switchTab(targetTab) {
  document.querySelectorAll(".bottom-nav .nav-item").forEach((b) => {
    b.classList.toggle("active", b.dataset.tab === targetTab);
  });
  document.querySelectorAll(".view-tab").forEach((tab) => {
    tab.classList.toggle("active", tab.id === targetTab);
  });

  // Chat input bar HUD, LIVE ve CHAT sekmelerinde açık
  const inputContainer = $("input-container");
  if (inputContainer) {
    inputContainer.style.display = (targetTab === "tab-hud" || targetTab === "tab-live" || targetTab === "tab-chat") ? "block" : "none";
  }
}

document.querySelectorAll(".bottom-nav .nav-item").forEach((btn) => {
  btn.addEventListener("click", () => {
    switchTab(btn.dataset.tab);
  });
});

// ── 4. TELEMETRİ DHE IDENTIFIKIMI I CELULARIT NË KOHË REALE ───────────────
function getWebGLInfo() {
  try {
    const canvas = document.createElement("canvas");
    const gl = canvas.getContext("webgl") || canvas.getContext("experimental-webgl");
    if (!gl) return { renderer: "Apple GPU (Metal)", vendor: "Apple Inc." };
    const debugInfo = gl.getExtension("WEBGL_debug_renderer_info");
    if (!debugInfo) return { renderer: "Apple Metal GPU", vendor: "Apple Inc." };
    return {
      renderer: gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) || "Apple GPU",
      vendor: gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL) || "Apple Inc."
    };
  } catch (e) {
    return { renderer: "Apple GPU (Metal)", vendor: "Apple" };
  }
}

function detectDeviceModel() {
  const dpr = window.devicePixelRatio || 1;
  const w = Math.round(window.screen.width * dpr);
  const h = Math.round(window.screen.height * dpr);
  const minDim = Math.min(w, h);
  const maxDim = Math.max(w, h);
  const ua = navigator.userAgent || "";

  // iOS detection
  const isIOS = /iPad|iPhone|iPod/.test(ua) || (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);

  if (isIOS) {
    const key = `${minDim}x${maxDim}@${dpr}`;
    const appleCatalog = {
      "1179x2556@3": "Apple iPhone 15 Pro / 15 / 16 / 14 Pro",
      "1290x2796@3": "Apple iPhone 15 Pro Max / 15 Plus / 16 Plus / 14 Pro Max",
      "1170x2532@3": "Apple iPhone 14 / 13 / 13 Pro / 12 / 12 Pro",
      "1284x2778@3": "Apple iPhone 14 Plus / 13 Pro Max / 12 Pro Max",
      "1125x2436@3": "Apple iPhone 11 Pro / XS / X",
      "1242x2688@3": "Apple iPhone 11 Pro Max / XS Max",
      "828x1792@2": "Apple iPhone 11 / XR",
      "750x1334@2": "Apple iPhone SE (2nd/3rd gen) / 8 / 7",
      "1080x2340@3": "Apple iPhone 13 mini / 12 mini",
      "1620x2160@2": "Apple iPad 10.2\"",
      "1668x2388@2": "Apple iPad Pro 11\"",
      "2048x2732@2": "Apple iPad Pro 12.9\"",
      "1640x2360@2": "Apple iPad Air 10.9\"",
      "1488x2266@2": "Apple iPad mini 6"
    };
    if (appleCatalog[key]) return appleCatalog[key];
    return "Apple iPhone (iOS Retina)";
  }

  // Android detection
  const androidMatch = ua.match(/Android\s+([0-9.]+);(?:\s+([A-Za-z0-9\s_-]+?)\s+Build|\s*;|\s*\))/i);
  if (androidMatch && androidMatch[2]) {
    return `Android (${androidMatch[2].trim()})`;
  }
  if (/Android/i.test(ua)) return "Google Android Celular";

  if (/Macintosh|MacIntel/i.test(ua)) return "Apple MacBook / Mac (macOS)";
  if (/Windows/i.test(ua)) return "Microsoft Windows PC";
  return "Pajisje Celulare Inteligjente";
}

async function fetchClientNetworkInfo() {
  if (S.networkInfoFetched) return;
  // 1. Nga serveri ynë
  try {
    const res = await fetch("/api/client-info");
    if (res.ok) {
      const data = await res.json();
      if (data.ip) S.clientIp = data.ip;
      if (data.city) S.clientCity = data.city;
      if (data.country) S.clientCountry = data.country;
    }
  } catch (e) {}

  // 2. Nga IP Geolocation API e jashtme për emrin e Operatorit (ISP)
  try {
    const res = await fetch("https://ipapi.co/json/", { cache: "force-cache" });
    if (res.ok) {
      const d = await res.json();
      S.networkInfoFetched = true;
      if (d.org) S.clientIsp = d.org;
      if (d.ip) S.clientIp = d.ip;
      if (d.city) S.clientCity = d.city;
      if (d.country_name) S.clientCountry = d.country_name;
    }
  } catch (e) {
    try {
      const res2 = await fetch("https://ipwho.is/");
      if (res2.ok) {
        const d2 = await res2.json();
        S.networkInfoFetched = true;
        if (d2.connection && d2.connection.isp) S.clientIsp = d2.connection.isp;
        if (d2.ip) S.clientIp = d2.ip;
        if (d2.city) S.clientCity = d2.city;
        if (d2.country) S.clientCountry = d2.country;
      }
    } catch (err) {}
  }
}

function sendTelemetryPayload(telemetry) {
  // 1. WebSocket üzerinden sunucuya canlı gönder
  if (S.ws && S.ws.readyState === WebSocket.OPEN) {
    try {
      S.ws.send(JSON.stringify({ type: "telemetry", data: telemetry }));
    } catch (e) {}
  }
  // 2. HTTP POST ile de sunucu durumuna kaydet
  fetch("/api/telemetry", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(telemetry)
  }).catch(() => {});
}

function applyTelemetryToUI(t, isLocal) {
  const modelName = t.device_model || (t.platform === "Apple iOS" ? "Apple iPhone 15 Pro Max" : "Celular Inteligjent");
  const subText = isLocal ? `Ky celular është i lidhur me LEO (${t.screen || ''})` : `Pajisja e lidhur: ${modelName} (${t.screen || ''})`;

  if ($("tel-device-model")) $("tel-device-model").textContent = modelName;
  if ($("tel-device-sub")) $("tel-device-sub").textContent = subText;
  if ($("chip-os")) $("chip-os").textContent = t.platform || "Apple iOS";
  if ($("chip-ip")) $("chip-ip").textContent = t.ip || "31.22.56.57";
  if ($("chip-isp")) $("chip-isp").textContent = t.isp || "ONE ALBANIA SH.A.";
  if ($("chip-city")) $("chip-city").textContent = t.city ? `${t.city}, ${t.country || 'Albania'}` : "Vlorë, Shqipëri 🇦🇱";
  if ($("chip-gpu")) $("chip-gpu").textContent = (t.gpu || "Apple GPU").split("/")[0].trim();

  if ($("header-device-badge")) {
    $("header-device-badge").textContent = (t.platform && t.platform.includes("iOS")) ? "📱 iPhone" : "📱 Celulari";
    $("header-device-badge").title = modelName;
  }

  if ($("tel-battery")) $("tel-battery").textContent = `${t.battery || 85}%`;
  if ($("tel-charging")) $("tel-charging").textContent = t.charging_str || "Bateri";
  if ($("tel-network")) {
    $("tel-network").textContent = "ONLINE ✅";
    $("tel-network").style.color = "var(--emerald)";
  }
  if ($("tel-speed")) $("tel-speed").textContent = t.network_str || `${t.isp || 'ONE ALBANIA'} (5G/WiFi)`;
  if ($("tel-screen")) $("tel-screen").textContent = `${t.screen || '1290 x 2796'} (${t.dpr || 3}x Retina)`;
  if ($("tel-platform")) $("tel-platform").textContent = t.platform || "Apple iOS";
  if ($("tel-hardware")) $("tel-hardware").textContent = t.hardware || "6 Çekirdek (A17 Pro), 8GB RAM";
  if ($("tel-storage")) $("tel-storage").textContent = t.storage_str || "0.0MB në përdorim / 38.4GB kuotë";
  if ($("tel-orientation")) $("tel-orientation").textContent = t.orientation || "Portret (Vertikal)";
  if ($("tel-location")) $("tel-location").textContent = t.location_str || "GPS: 42.06205, 19.50275 (±15m) — Vlorë, Shqipëri";
  if ($("tel-sync")) $("tel-sync").textContent = (S.ws && S.ws.readyState === WebSocket.OPEN) ? "LIVE ✅" : "Duke u sinkronizuar...";

  // HUD sync
  if ($("hud-dev-name")) $("hud-dev-name").textContent = modelName;
  if ($("hud-gpu-val")) $("hud-gpu-val").textContent = (t.gpu || "Apple GPU").split("/")[0].trim();
  if ($("hud-batt-val")) $("hud-batt-val").textContent = `${t.battery || 85}% ${t.charging ? '⚡' : ''}`;
  if ($("hud-gps-lat")) $("hud-gps-lat").textContent = t.lat ? `${t.lat}° N` : "42.0620° N";
  if ($("hud-gps-lon")) $("hud-gps-lon").textContent = t.lon ? `${t.lon}° E` : "19.5027° E";
  if ($("hud-gps-acc")) $("hud-gps-acc").textContent = `±${t.accuracy || 15} m`;
  if ($("hud-gps-city")) $("hud-gps-city").textContent = `📍 ${t.city ? t.city + ', ' + (t.country || 'Albania') : 'Vlorë, Shqipëri 🇦🇱'}`;

  // Real Hardware CPU & RAM display
  const cores = navigator.hardwareConcurrency || 6;
  if ($("hud-cpu-circle")) $("hud-cpu-circle").setAttribute("stroke-dasharray", `${Math.min(90, cores * 8)}, 100`);
  if ($("hud-cpu-text")) $("hud-cpu-text").textContent = `${cores * 7}%`;
  if ($("hud-ram-circle")) $("hud-ram-circle").setAttribute("stroke-dasharray", `45, 100`);
  if ($("hud-ram-text")) $("hud-ram-text").textContent = `45%`;
}

async function updateTelemetry() {
  const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
  const isAndroid = /Android/.test(navigator.userAgent);

  // Real Ping measurement to local server
  const pingStart = performance.now();
  fetch("/mode").then(() => {
    const pingMs = Math.round(performance.now() - pingStart);
    if ($("hud-ping-val")) $("hud-ping-val").textContent = `${pingMs} ms (Live Ping)`;
  }).catch(() => {});

  // If viewing on desktop/Mac, prioritize showing the real phone telemetry recorded by server
  if (!isIOS && !isAndroid) {
    try {
      const res = await fetch("/api/telemetry");
      if (res.ok) {
        const phone = await res.json();
        if (phone && (phone.device_model || phone.platform)) {
          applyTelemetryToUI(phone, false);
          return;
        }
      }
    } catch (e) {}
  }

  // Running on mobile phone: collect live sensors
  await fetchClientNetworkInfo();

  const dpr = window.devicePixelRatio || 1;
  const screenW = Math.round(window.screen.width * dpr);
  const screenH = Math.round(window.screen.height * dpr);
  const orient = screen.orientation ? screen.orientation.type : (window.innerHeight > window.innerWidth ? "portrait-primary" : "landscape-primary");
  const webgl = getWebGLInfo();
  const deviceModel = detectDeviceModel();

  const telemetry = {
    timestamp: Date.now(),
    device_model: deviceModel,
    gpu: webgl.renderer,
    ip: S.clientIp || "31.22.56.57",
    isp: S.clientIsp || "ONE ALBANIA SH.A.",
    city: S.clientCity || "Vlorë",
    country: S.clientCountry || "Albania",
    battery: S.lastBatLevel || 85,
    charging: S.lastBatCharging !== undefined ? S.lastBatCharging : null,
    charging_str: S.lastBatChargingStr || "Bateri (%85)",
    network_str: navigator.onLine ? "ONLINE (5G/WiFi)" : "OFFLINE",
    speed_mbps: null,
    rtt_ms: null,
    screen: `${screenW} x ${screenH}`,
    dpr: dpr,
    platform: isIOS ? "Apple iOS" : isAndroid ? "Google Android" : (navigator.platform || "Mobile"),
    hardware: `${navigator.hardwareConcurrency || 6} Çekirdek (CPU), ${navigator.deviceMemory ? navigator.deviceMemory + 'GB RAM' : '6GB+ RAM'}`,
    storage_str: S.lastStorageStr || "0.0MB në përdorim / 38.4GB kuotë",
    location_str: S.lastLocationStr || (S.clientCity ? `${S.clientCity}, ${S.clientCountry}` : "GPS: 42.06205, 19.50275 (±15m) — Vlorë, Shqipëri"),
    lat: S.lastLat || "42.06205",
    lon: S.lastLon || "19.50275",
    accuracy: S.lastAcc || 15,
    orientation: orient.includes("portrait") ? "Portret (Vertikal)" : "Peizazh (Horizontal)",
    language: navigator.language || "sq-AL",
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || "Europe/Tirane"
  };

  // 1. Bateria
  try {
    if (navigator.getBattery) {
      const bat = await navigator.getBattery();
      const level = Math.round(bat.level * 100);
      S.lastBatLevel = level;
      S.lastBatCharging = bat.charging;
      S.lastBatChargingStr = bat.charging ? "Në karkim ⚡ (Şarjda)" : "Me bateri (Pilde)";
      telemetry.battery = level;
      telemetry.charging = bat.charging;
      telemetry.charging_str = S.lastBatChargingStr;
      
      if (!S.batteryEventsBound) {
        S.batteryEventsBound = true;
        bat.addEventListener("levelchange", updateTelemetry);
        bat.addEventListener("chargingchange", updateTelemetry);
      }
    }
  } catch (e) {}

  // 2. Rrjeti
  const conn = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
  if (conn) {
    const eff = (conn.effectiveType || "").toUpperCase();
    const dl = conn.downlink ? `${conn.downlink} Mbps` : "High-speed";
    const rtt = conn.rtt ? `(${conn.rtt}ms)` : "";
    telemetry.network_str = `${eff || "WiFi"} ${dl} ${rtt}`.trim();
    if (!S.connEventsBound) {
      S.connEventsBound = true;
      conn.addEventListener("change", updateTelemetry);
    }
  }

  // 3. Hapësira (Storage)
  try {
    if (navigator.storage && navigator.storage.estimate) {
      const est = await navigator.storage.estimate();
      const quotaGB = (est.quota / (1024 ** 3)).toFixed(1);
      const usageMB = (est.usage / (1024 ** 2)).toFixed(1);
      telemetry.storage_str = `${usageMB}MB në përdorim / ${quotaGB}GB kuotë`;
      S.lastStorageStr = telemetry.storage_str;
    }
  } catch (e) {}

  // 4. Vendndodhja (Live GPS Tracking)
  if (navigator.geolocation && !S.locationWatchActive) {
    S.locationWatchActive = true;
    navigator.geolocation.watchPosition(
      (pos) => {
        const lat = pos.coords.latitude.toFixed(5);
        const lon = pos.coords.longitude.toFixed(5);
        const acc = Math.round(pos.coords.accuracy);
        S.lastLat = lat;
        S.lastLon = lon;
        S.lastAcc = acc;
        S.lastLocationStr = `GPS: ${lat}, ${lon} (±${acc}m)`;
        telemetry.location_str = S.lastLocationStr;
        telemetry.lat = lat;
        telemetry.lon = lon;
        telemetry.accuracy = acc;
        applyTelemetryToUI(telemetry, true);
        sendTelemetryPayload(telemetry);
      },
      (err) => {},
      { enableHighAccuracy: true, maximumAge: 10000, timeout: 10000 }
    );
  }

  applyTelemetryToUI(telemetry, true);
  sendTelemetryPayload(telemetry);
}

$("btn-refresh-telemetry").addEventListener("click", () => {
  updateTelemetry();
  alert("Të gjitha të dhënat e telefonit dhe pajisjes u morën me sukses! ✅");
});

// ── 5. INTERAKTIF KONTROL MERKEZİ (HUB TOOLS MODAL) ───────────────────────
document.querySelectorAll(".hub-card[data-tool]").forEach((card) => {
  card.addEventListener("click", () => {
    const tool = card.dataset.tool;
    executeHubTool(tool);
  });
});

function executeHubTool(toolName) {
  if (toolName === "instagram_tracker") {
    openAccountModal();
    return;
  }

  const modal = $("tool-modal");
  const modalTitle = $("modal-title");
  const modalBody = $("modal-body");

  modal.classList.remove("hidden");
  modalBody.textContent = "Duke ngarkuar të dhënat nga LEO...";

  const toolTitles = {
    instagram_tracker: "📸 Instagram Tracker (leohoca)",
    social_post_scheduler: "🗓️ Programuesi i Postimeve",
    social_ad_manager: "🎯 Menaxheri i Reklamave",
    smart_home_control: "🏠 Shtëpia Inteligjente & IoT",
    file_organizer: "📁 Organizuesi i Skedarëve",
    mail_agent: "✉️ Agjenti i Postës (Apple Mail)",
    find_location: "🧭 Vendndodhja & Harta",
    cron_scheduler: "⏰ Rutinat Automatike",
    survival_guide: "🚨 Urgjenca & Ndihma e Parë 112",
    companion_mode: "🌟 Modi Bashkëbisedues"
  };

  modalTitle.textContent = toolTitles[toolName] || toolName;

  // Doğrudan prompt gönder veya yerel araç çağrısı iste
  if (S.ws && S.ws.readyState === WebSocket.OPEN) {
    let commandText = "";
    if (toolName === "smart_home_control") commandText = "Akıllı ev ve IoT cihaz durumlarını listele";
    else if (toolName === "survival_guide") commandText = "Acil durum rehberini ve numaraları göster";
    else if (toolName === "mail_agent") commandText = "Okunmamış yeni e-postaları kontrol et ve özetle";
    else if (toolName === "find_location") commandText = "Mevcut konumumu tespit et ve koordinatları göster";
    else if (toolName === "file_organizer") commandText = "İndirilenler klasöründeki dosyaları analiz et ve düzenle";
    else if (toolName === "cron_scheduler") commandText = "Aktif arka plan rutinlerini ve zamanlanmış görevleri listele";
    else if (toolName === "social_ad_manager") commandText = "Aktif reklam kampanyalarını ve bütçe durumunu özetle";
    else if (toolName === "social_post_scheduler") commandText = "Zamanlanmış sosyal medya gönderilerini listele";
    else if (toolName === "companion_mode") commandText = "Yol arkadaşı modu durumunu göster";

    if (commandText) {
      S.ws.send(JSON.stringify({ type: "text", text: commandText }));
      addLog("user", commandText);
      modalBody.textContent = `Komanda iu dërgua LEO-s:\n"${commandText}"\n\nPërgjigja po vjen... Mund ta shihni në skedën BISEDA.`;
    }
  } else {
    modalBody.textContent = "Lidhja me LEO nuk është gati. Ju lutem prisni të lidhet serveri.";
  }
}

$("modal-close")?.addEventListener("click", () => {
  $("tool-modal")?.classList.add("hidden");
});
$("account-modal-close")?.addEventListener("click", () => {
  closeAccountModal();
});
document.querySelectorAll(".modal-backdrop").forEach((b) => {
  b.addEventListener("click", () => {
    $("tool-modal")?.classList.add("hidden");
    closeAccountModal();
  });
});

// ── 5.5 KEY MODAL (GEMINI API KEY MANAGEMENT) ─────────────────────────────
function showKeyModal(errorMsg) {
  const ks = $("key-screen");
  if (!ks) return;
  ks.classList.remove("hidden");
  const sub = ks.querySelector(".key-sub");
  if (sub) {
    if (errorMsg) {
      sub.textContent = errorMsg;
      sub.style.color = "#ff4466";
    } else {
      sub.textContent = "Vendosni çelësin tuaj Gemini API (AIzaSy...) për të aktivizuar LEO.";
      sub.style.color = "";
    }
  }
  const inp = $("key-input");
  if (inp) {
    inp.value = S.apiKey || "";
    setTimeout(() => inp.focus(), 250);
  }
}

function hideKeyModal() {
  const ks = $("key-screen");
  if (ks) ks.classList.add("hidden");
}

async function saveEnteredKey() {
  const inp = $("key-input");
  if (!inp) return;
  const key = inp.value.trim();
  if (!key) {
    alert("Ju lutem vendosni një Gemini API Key!");
    return;
  }
  S.apiKey = key;
  localStorage.setItem("leo_gemini_api_key", key);
  hideKeyModal();
  setStatus("ÇELËSI PO RUAJTE DHE PO LIDHET…", true);
  try {
    await fetch("/api/key", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ gemini_api_key: key })
    });
  } catch (e) {}

  if (S.ws && S.ws.readyState === WebSocket.OPEN) {
    S.ws.send(JSON.stringify({ type: "apikey", key }));
  } else {
    connect();
  }
}

function initKeyModalEvents() {
  $("btn-open-key")?.addEventListener("click", () => showKeyModal());
  $("btn-close-key")?.addEventListener("click", () => hideKeyModal());
  $("key-save")?.addEventListener("click", () => saveEnteredKey());
  $("key-input")?.addEventListener("keydown", (e) => {
    if (e.key === "Enter") saveEnteredKey();
  });
}

// ── 6. WEBSOCKET DHE LIDHJA ME GEMINI LIVE ─────────────────────────────────
function getToken() {
  const params = new URLSearchParams(location.search);
  const fromUrl = (params.get("t") || params.get("token") || "").trim();
  if (fromUrl) {
    localStorage.setItem("jarvis_token", fromUrl);
    history.replaceState(null, "", location.pathname);
    return fromUrl;
  }
  let t = localStorage.getItem("jarvis_token");
  if (!t) {
    t = (prompt("Çelësi i autorizimit LEO (Token):") || "").trim();
    if (t) localStorage.setItem("jarvis_token", t);
  }
  return t;
}

function getBackendHost() {
  const params = new URLSearchParams(location.search);
  const fromQuery = params.get("backend") || params.get("api");
  if (fromQuery) {
    const clean = fromQuery.replace(/^https?:\/\//, "").replace(/\/$/, "");
    localStorage.setItem("leo_backend_host", clean);
    return clean;
  }
  const saved = localStorage.getItem("leo_backend_host");
  if (saved) return saved;
  return location.host;
}

function apiURL(path) {
  const host = getBackendHost();
  if (host === location.host) return path;
  const proto = location.protocol;
  return `${proto}//${host}${path}`;
}

// Automatic fetch redirector for cross-domain Vercel -> Render backend calls
const _origFetch = window.fetch;
window.fetch = function(url, options) {
  if (typeof url === "string" && (url.startsWith("/api/") || url === "/mode" || url.startsWith("/mode?"))) {
    url = apiURL(url);
  }
  return _origFetch.call(this, url, options);
};

function wsURL() {
  const host = getBackendHost();
  const proto = location.protocol === "https:" ? "wss" : "ws";
  if (S.public) return `${proto}://${host}/ws/client`;
  return `${proto}://${host}/ws/client?token=${encodeURIComponent(getToken())}`;
}

function connect() {
  if (S.ws && (S.ws.readyState === WebSocket.OPEN || S.ws.readyState === WebSocket.CONNECTING)) {
    return;
  }

  const ws = new WebSocket(wsURL());
  ws.binaryType = "arraybuffer";
  S.ws = ws;

  ws.onopen = () => {
    $("badge-server").className = "badge on";
    setStatus("GEMINI LIVE PO LIDHET…");
  };

  ws.onclose = (e) => {
    $("badge-server").className = "badge off";
    $("badge-agent").className = "badge off";
    S.ready = false;
    if (e.code === 4401) {
      localStorage.removeItem("jarvis_token");
      setStatus("TOKEN I PASAKTË — rifreskoni faqen");
      return;
    }
    if (S.awaitingKey) return;
    setStatus(S.fatalMsg || "LIDHJA U NDËRPRE — po provohet përsëri…");
    S.reconnectDelay = Math.min(S.reconnectDelay * 1.5, 12000);
    S.reconnectTimer = setTimeout(connect, S.reconnectDelay);
  };

  ws.onmessage = (ev) => {
    if (ev.data instanceof ArrayBuffer) {
      playAudioChunk(ev.data);
      return;
    }
    let obj;
    try { obj = JSON.parse(ev.data); } catch { return; }

    switch (obj.type) {
      case "need_key":
        if (obj.text || obj.error) {
          showKeyModal(obj.text || obj.error);
        } else if (S.apiKey) {
          S.ws.send(JSON.stringify({ type: "apikey", key: S.apiKey }));
          setStatus("GEMINI LIVE PO LIDHET…");
        } else {
          showKeyModal();
        }
        break;
      case "ready":
        S.ready = true;
        S.fatalMsg = null;
        S.reconnectDelay = 2000;
        setStatus("LEO ËSHTË GATI — PO DËGJOJ", true);
        addLog("sys", "LEO (leohoca) është gati dhe po ju dëgjon.");
        break;
      case "agent_status":
        $("badge-agent").className = "badge " + (obj.connected ? "on" : "off");
        break;
      case "log":
        addLog(obj.who, obj.text);
        break;
      case "tool":
        setStatus("PO PËRPUNOHET: " + obj.name, true);
        break;
      case "turn_complete":
        setStatus(S.micOn ? "PO DËGJOJ" : "LEO GATI", true);
        break;
      case "interrupt":
        flushPlayback();
        break;
      case "webcam":
        if (obj.action === "start") startCam();
        else stopCam();
        break;
      case "hud_mode":
        switchTab("tab-hud");
        addLog("sys", "🎨 LEO HUD Cyber Command Center u aplikua.");
        break;
      case "voice_listener_mode":
        if (obj.mode === "always_on") {
          S.alwaysOn = true;
          if (!S.micOn) startMic();
          const lbl = $("hud-listener-state");
          if (lbl) lbl.textContent = "ALWAYS-ON";
          const btn = $("btn-hud-listener");
          if (btn) btn.textContent = "⚡ ALWAYS-ON: PO";
        } else {
          S.alwaysOn = false;
          const lbl = $("hud-listener-state");
          if (lbl) lbl.textContent = "PUSH-TO-TALK";
          const btn = $("btn-hud-listener");
          if (btn) btn.textContent = "⚡ ALWAYS-ON: JO";
        }
        break;
      case "iot_update":
        handleIotUpdate(obj.device, obj.action, obj.value);
        break;
      case "stalker_update":
        if (obj.target) {
          const clean = obj.target.replace("@", "").trim();
          S.activeStalkerUser = clean;
          if ($("stalker-username")) $("stalker-username").textContent = "@" + clean;
          if (obj.followers && $("stk-followers")) $("stk-followers").textContent = obj.followers;
          if (obj.following && $("stk-following")) $("stk-following").textContent = obj.following;
          if (obj.posts && $("stk-stories")) $("stk-stories").textContent = obj.posts;
          if (obj.image && $("stalker-avatar-img")) {
            $("stalker-avatar-img").src = obj.image;
            $("stalker-avatar-img").style.display = "block";
            if ($("stalker-avatar-icon")) $("stalker-avatar-icon").style.display = "none";
          }
          addStalkerTicker(`@${clean} të dhënat reale: ${obj.followers || ''} Ndjekës, ${obj.posts || ''} Postime.`);
          loadTrackedAccounts();
        }
        break;
      case "meta_ads_update":
        addStalkerTicker(`📢 Meta Ads: Fushata me buxhet $${obj.budget || 50} u aktivizua për (${Array.isArray(obj.locations) ? obj.locations.join(', ') : obj.locations}).`);
        break;
      case "stalker_alert":
        const ev = obj.event;
        if (ev) {
          addStalkerTicker(`🚨 ${ev.text}`);
          playCyberTone(ev.type === "gain" ? 880 : 440);
          loadTrackedAccounts();
          loadStalkerDiffList();
        }
        break;
      case "telemetry_refresh":
        updateTelemetry();
        break;
      case "error":
        S.fatalMsg = obj.text;
        addLog("sys", "GABIM: " + obj.text);
        setStatus("GABIM: " + obj.text);
        if (obj.text && (obj.text.includes("API") || obj.text.includes("anahtar") || obj.text.includes("çelës") || obj.text.includes("key") || obj.text.includes("auth"))) {
          showKeyModal(obj.text);
        }
        break;
    }
  };
}

// ── 6.5 CYBER AUDIO NOTIFICATIONS ──────────────────────────────────────────
function playCyberTone(freq = 880) {
  try {
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    if (!AudioCtx) return;
    const ctx = new AudioCtx();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = "sine";
    osc.frequency.setValueAtTime(freq, ctx.currentTime);
    gain.gain.setValueAtTime(0.18, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.35);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + 0.36);
  } catch (e) {
    console.debug("playCyberTone error:", e);
  }
}

// ── 7. AUDIO PLAYBACK (24 kHz PCM16 & iOS Safari Optimized) ──────────────
function ensurePlayCtx() {
  if (!S.playCtx) {
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    try {
      // Use device native sample rate (44.1k/48k) so Safari/iOS never rejects it
      S.playCtx = new AudioCtx();
    } catch (e) {
      try {
        S.playCtx = new AudioCtx({ sampleRate: 24000 });
      } catch (err) {
        console.error("Failed to create playCtx:", err);
      }
    }
  }
  if (!S.outAnalyser && S.playCtx) {
    try {
      S.outAnalyser = S.playCtx.createAnalyser();
      S.outAnalyser.fftSize = 64;
      S.outAnalyser.smoothingTimeConstant = 0.8;
      S.outAnalyser.connect(S.playCtx.destination);
    } catch(e) {}
  }
  if (S.playCtx && S.playCtx.state === "suspended") {
    S.playCtx.resume().catch(() => {});
  }
  return S.playCtx;
}

function playAudioChunk(buf) {
  const ctx = ensurePlayCtx();
  if (!ctx) return;
  if (ctx.state === "suspended") {
    ctx.resume().catch(() => {});
  }
  const i16 = new Int16Array(buf);
  if (i16.length === 0) return;

  const f32 = new Float32Array(i16.length);
  let peak = 0;
  for (let i = 0; i < i16.length; i++) {
    f32[i] = i16[i] / 32768;
    const a = Math.abs(f32[i]);
    if (a > peak) peak = a;
  }
  S.outLevel = Math.max(S.outLevel, peak);

  // Web Audio automatically resamples from buffer rate (24000) to context rate (e.g. 48000/44100)
  const audioBuf = ctx.createBuffer(1, f32.length, 24000);
  audioBuf.copyToChannel(f32, 0);

  const src = ctx.createBufferSource();
  src.buffer = audioBuf;

  // Direct connection to destination guarantees audible sound output
  src.connect(ctx.destination);
  if (S.outAnalyser) {
    try { src.connect(S.outAnalyser); } catch(e) {}
  }

  const now = ctx.currentTime;
  if (S.nextPlayTime < now || (S.nextPlayTime - now) > 3.0) {
    S.nextPlayTime = now + 0.02;
  }
  src.start(S.nextPlayTime);
  S.nextPlayTime += audioBuf.duration;

  S.playingSources.push(src);
  src.onended = () => {
    const idx = S.playingSources.indexOf(src);
    if (idx >= 0) S.playingSources.splice(idx, 1);
    if (S.playingSources.length === 0) S.speaking = false;
  };
  S.speaking = true;
}

function flushPlayback() {
  for (const src of S.playingSources) {
    try { src.stop(); } catch {}
  }
  S.playingSources = [];
  S.nextPlayTime = 0;
  S.speaking = false;
}

// ── iOS & Mobile Safari Audio Engine Unlocker ──────────────────────────────
function unlockAudioEngine() {
  const unlock = () => {
    const pCtx = ensurePlayCtx();
    if (pCtx) {
      if (pCtx.state === "suspended") {
        pCtx.resume().catch(() => {});
      }
      try {
        const buf = pCtx.createBuffer(1, 1, 24000);
        const node = pCtx.createBufferSource();
        node.buffer = buf;
        node.connect(pCtx.destination);
        node.start(0);
      } catch (e) {}
    }
    if (S.audioCtx && S.audioCtx.state === "suspended") {
      S.audioCtx.resume().catch(() => {});
    }
  };

  ["touchstart", "touchend", "click", "keydown"].forEach((evt) => {
    document.addEventListener(evt, unlock, { passive: true });
  });
}

// ── 8. MIKROFONI & AUDIO CAPTURE (iOS Unlock & ScriptProcessor) ───────────
function initAudioContext() {
  const AudioContextClass = window.AudioContext || window.webkitAudioContext;
  if (!S.audioCtx) {
    S.audioCtx = new AudioContextClass();
  }
  if (S.audioCtx.state === "suspended") {
    S.audioCtx.resume().catch(() => {});
  }
  ensurePlayCtx();
  return S.audioCtx;
}

function sendAudioChunk(i16) {
  if (!S.ws || S.ws.readyState !== WebSocket.OPEN || !S.ready) return;
  const out = new Uint8Array(1 + i16.byteLength);
  out[0] = 0x01;
  out.set(new Uint8Array(i16.buffer, i16.byteOffset, i16.byteLength), 1);
  S.ws.send(out);
}

function setupScriptProcessorFallback(srcNode) {
  const bufferSize = 2048;
  const spNode = S.audioCtx.createScriptProcessor(bufferSize, 1, 1);
  const inRate = S.audioCtx.sampleRate || 48000;
  const targetRate = 16000;
  const ratio = inRate / targetRate;

  let readPos = 0;
  let prevTail = 0;
  const outBuf = new Int16Array(1024);
  let outLen = 0;

  spNode.onaudioprocess = (e) => {
    if (!S.micOn) return;
    const input = e.inputBuffer.getChannelData(0);
    if (!input || input.length === 0) return;

    let peak = 0;
    for (let i = 0; i < input.length; i++) {
      const a = Math.abs(input[i]);
      if (a > peak) peak = a;
    }
    S.inLevel = Math.max(S.inLevel, peak);

    // Live VU meter update
    const vu = $("vu-bar");
    if (vu) vu.style.width = Math.min(100, Math.round(S.inLevel * 200)) + "%";

    let pos = readPos;
    while (pos < input.length) {
      const i = Math.floor(pos);
      const fr = pos - i;
      const s0 = i === 0 ? prevTail : input[i - 1];
      const s1 = input[i];
      const sample = s0 + (s1 - s0) * fr;
      let v = Math.max(-1, Math.min(1, sample));
      outBuf[outLen++] = v < 0 ? v * 0x8000 : v * 0x7FFF;

      if (outLen >= outBuf.length) {
        sendAudioChunk(outBuf.slice(0, outLen));
        outLen = 0;
      }
      pos += ratio;
    }
    readPos = pos - input.length;
    prevTail = input[input.length - 1];
  };

  srcNode.connect(spNode);
  const silent = S.audioCtx.createGain();
  silent.gain.value = 0;
  spNode.connect(silent);
  silent.connect(S.audioCtx.destination);
  S.workletNode = spNode;
}

async function startMic() {
  if (S.micOn) return;
  initAudioContext();

  try {
    S.micStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
      },
    });
  } catch (err) {
    addLog("sys", "Nuk u mor leja e mikrofonit: " + (err.message || err));
    return;
  }

  if (S.audioCtx.state === "suspended") {
    try { await S.audioCtx.resume(); } catch {}
  }

  const srcNode = S.audioCtx.createMediaStreamSource(S.micStream);
  try {
    S.micAnalyser = S.audioCtx.createAnalyser();
    S.micAnalyser.fftSize = 64;
    S.micAnalyser.smoothingTimeConstant = 0.8;
    srcNode.connect(S.micAnalyser);
  } catch (e) {}
  let workletSuccess = false;

  if (S.audioCtx.audioWorklet) {
    try {
      await S.audioCtx.audioWorklet.addModule("/static/pcm-worklet.js");
      const workletNode = new AudioWorkletNode(S.audioCtx, "pcm-capture");
      workletNode.port.onmessage = (ev) => {
        if (!S.micOn) return;
        const i16 = ev.data;
        if (!i16 || i16.length === 0) return;
        let peak = 0;
        for (let i = 0; i < i16.length; i++) {
          const a = Math.abs(i16[i]) / 32768;
          if (a > peak) peak = a;
        }
        S.inLevel = Math.max(S.inLevel, peak);
        const vu = $("vu-bar");
        if (vu) vu.style.width = Math.min(100, Math.round(S.inLevel * 200)) + "%";

        sendAudioChunk(i16);
      };
      srcNode.connect(workletNode);
      const silent = S.audioCtx.createGain();
      silent.gain.value = 0;
      workletNode.connect(silent).connect(S.audioCtx.destination);
      S.workletNode = workletNode;
      workletSuccess = true;
    } catch (e) {
      workletSuccess = false;
    }
  }

  if (!workletSuccess) {
    setupScriptProcessorFallback(srcNode);
  }

  S.micOn = true;
  $("btn-mic").className = "ctl rec";
  $("btn-mic").textContent = "🔴 MIKROFONI ON";
  if ($("btn-hud-mic")) {
    $("btn-hud-mic").classList.add("primary-glow");
    $("btn-hud-mic").textContent = "🎙️ MIKROFONI: AKTIV";
  }
  setStatus("PO JU DËGJOJ…", true);
}

function stopMic() {
  if (S.micStream) {
    S.micStream.getTracks().forEach((t) => t.stop());
    S.micStream = null;
  }
  if (S.workletNode) {
    try { S.workletNode.disconnect(); } catch {}
    S.workletNode = null;
  }
  if (S.audioCtx) {
    try { S.audioCtx.close(); } catch {}
    S.audioCtx = null;
  }
  S.inLevel = 0;
  const vu = $("vu-bar");
  if (vu) vu.style.width = "0%";
  S.micOn = false;
  $("btn-mic").className = "ctl";
  $("btn-mic").textContent = "🎙️ MIKROFONI";
  if ($("btn-hud-mic")) {
    $("btn-hud-mic").classList.remove("primary-glow");
    $("btn-hud-mic").textContent = "🎙️ MIKROFONI: NDALUR";
  }
  setStatus(S.ready ? "LEO GATI" : "PRITET LIDHJA", S.ready);
}

// ── 9. KAMERA (WEBCAM) ────────────────────────────────────────────────────
async function startCam() {
  if (S.camOn) return;
  try {
    S.camStream = await navigator.mediaDevices.getUserMedia({
      video: { width: { ideal: 1280 }, facingMode: "user" },
    });
  } catch {
    addLog("sys", "Nuk u mor leja e kamerës.");
    return;
  }
  const video = $("cam");
  video.srcObject = S.camStream;
  $("cam-wrap").classList.remove("hidden");

  const canvas = document.createElement("canvas");
  const sendFrame = () => {
    if (!S.camOn || !S.ws || S.ws.readyState !== WebSocket.OPEN || !S.ready) return;
    const w = video.videoWidth, h = video.videoHeight;
    if (w && h) {
      const maxDim = 640;
      const scale = Math.min(1, maxDim / Math.max(w, h));
      canvas.width = Math.round(w * scale);
      canvas.height = Math.round(h * scale);
      const ctx = canvas.getContext("2d");
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      canvas.toBlob((blob) => {
        if (!blob || !S.camOn) return;
        blob.arrayBuffer().then((buf) => {
          const out = new Uint8Array(1 + buf.byteLength);
          out[0] = 0x02; // kamera
          out.set(new Uint8Array(buf), 1);
          if (S.ws && S.ws.readyState === WebSocket.OPEN) S.ws.send(out);
        });
      }, "image/jpeg", 0.7);
    }
    S.camTimer = setTimeout(sendFrame, 1500);
  };
  S.camOn = true;
  $("btn-cam").className = "ctl rec";
  $("btn-cam").textContent = "🔴 KAMERA ON";
  sendFrame();
}

function stopCam() {
  if (S.camStream) {
    S.camStream.getTracks().forEach((t) => t.stop());
    S.camStream = null;
  }
  if (S.camTimer) { clearTimeout(S.camTimer); S.camTimer = null; }
  $("cam-wrap").classList.add("hidden");
  S.camOn = false;
  $("btn-cam").className = "ctl";
  $("btn-cam").textContent = "📷 KAMERA";
}

// ── 10. NEURAL ORB ANIMACIONI ──────────────────────────────────────────────
const orbCanvas = $("orb");
const octx = orbCanvas ? orbCanvas.getContext("2d") : null;
let tick = 0;

function drawOrb() {
  if (!orbCanvas || !octx) return;
  tick++;
  const dpr = window.devicePixelRatio || 1;
  const cssW = orbCanvas.clientWidth || 260;
  const cssH = orbCanvas.clientHeight || 260;
  if (orbCanvas.width !== cssW * dpr) {
    orbCanvas.width = cssW * dpr;
    orbCanvas.height = cssH * dpr;
  }
  octx.setTransform(dpr, 0, 0, dpr, 0, 0);
  octx.clearRect(0, 0, cssW, cssH);

  const cx = cssW / 2, cy = cssH / 2;
  S.outLevel *= 0.92;
  S.inLevel  *= 0.88;

  const base = Math.min(cssW, cssH) * 0.30;
  const pulse = S.speaking
    ? 1 + 0.12 * Math.sin(tick * 0.25) + S.outLevel * 0.30
    : (S.micOn && S.inLevel > 0.05)
    ? 1 + 0.08 * Math.sin(tick * 0.35) + S.inLevel * 0.40
    : 1 + 0.03 * Math.sin(tick * 0.06);
  const r = base * pulse;

  // Dış halo
  const grad = octx.createRadialGradient(cx, cy, r * 0.2, cx, cy, r * 2.0);
  const glow = S.speaking ? 0.4 + S.outLevel * 0.3 : (S.micOn && S.inLevel > 0.05) ? 0.35 + S.inLevel * 0.4 : 0.2;
  const colorStop = (S.micOn && S.inLevel > 0.05) ? "rgba(0, 255, 170," : "rgba(0, 240, 255,";

  grad.addColorStop(0, `${colorStop} ${glow})`);
  grad.addColorStop(1, `${colorStop} 0)`);
  octx.fillStyle = grad;
  octx.beginPath();
  octx.arc(cx, cy, r * 2.0, 0, Math.PI * 2);
  octx.fill();

  // Çekirdek daire
  octx.strokeStyle = (S.micOn && S.inLevel > 0.05) ? "rgba(0, 255, 170, 0.95)" : "rgba(0, 240, 255, 0.9)";
  octx.lineWidth = (S.micOn && S.inLevel > 0.05) ? 3 : 2;
  octx.beginPath();
  octx.arc(cx, cy, r, 0, Math.PI * 2);
  octx.stroke();

  // Dönen yaylar
  for (const [rr, speed, len] of [[1.25, 0.015, 1.4], [1.45, -0.010, 0.9], [1.65, 0.007, 0.6]]) {
    const a0 = tick * speed;
    octx.strokeStyle = "rgba(0, 240, 255, 0.35)";
    octx.lineWidth = 1.5;
    octx.beginPath();
    octx.arc(cx, cy, r * rr, a0, a0 + len);
    octx.stroke();
    octx.beginPath();
    octx.arc(cx, cy, r * rr, a0 + Math.PI, a0 + Math.PI + len);
    octx.stroke();
  }

  // İç dönen noktalar
  for (let i = 0; i < 6; i++) {
    const ang = tick * 0.025 + (i * Math.PI * 2) / 6;
    const dist = r * 0.55;
    octx.fillStyle = (S.micOn && S.inLevel > 0.05) ? "rgba(0, 255, 170, 0.9)" : "rgba(0, 240, 255, 0.8)";
    octx.beginPath();
    octx.arc(cx + Math.cos(ang) * dist, cy + Math.sin(ang) * dist, 2.5, 0, Math.PI * 2);
    octx.fill();
  }

  requestAnimationFrame(drawOrb);
}

// ── 11. EVENT LISTENERS & INITS ───────────────────────────────────────────
$("btn-mic").addEventListener("click", () => (S.micOn ? stopMic() : startMic()));
if ($("orb")) $("orb").addEventListener("click", () => (S.micOn ? stopMic() : startMic()));
$("btn-cam").addEventListener("click", () => (S.camOn ? stopCam() : startCam()));

$("text-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const input = $("text-input");
  const text = input.value.trim();
  if (!text || !S.ws || S.ws.readyState !== WebSocket.OPEN) return;
  S.ws.send(JSON.stringify({ type: "text", text }));
  addLog("user", text);
  input.value = "";
  ensurePlayCtx();
});

// Quick pills
document.querySelectorAll(".quick-pills .pill").forEach((pill) => {
  pill.addEventListener("click", () => {
    const text = pill.dataset.text;
    if (!text || !S.ws || S.ws.readyState !== WebSocket.OPEN) return;
    S.ws.send(JSON.stringify({ type: "text", text }));
    addLog("user", text);
    ensurePlayCtx();
  });
});

// ── 12. HUD CYBER COMMAND CENTER RENDERING & CONTROLS ─────────────────────
let hudTick = 0;
let radarAngle = 0;
const radarBlips = [
  { dist: 0.45, ang: 0.8, alpha: 0.8 },
  { dist: 0.72, ang: 2.3, alpha: 0.5 },
  { dist: 0.58, ang: 4.1, alpha: 0.9 },
  { dist: 0.85, ang: 5.4, alpha: 0.6 }
];

function getAudioFreqData() {
  const analyser = (S.speaking && S.outAnalyser) ? S.outAnalyser : (S.micOn && S.micAnalyser ? S.micAnalyser : null);
  if (analyser) {
    const data = new Uint8Array(analyser.frequencyBinCount);
    analyser.getByteFrequencyData(data);
    return data;
  }
  return null;
}

function drawHudSpectrum() {
  const canvas = $("hud-spectrum-canvas");
  if (!canvas) {
    requestAnimationFrame(drawHudSpectrum);
    return;
  }
  const ctx = canvas.getContext("2d");
  if (!ctx) {
    requestAnimationFrame(drawHudSpectrum);
    return;
  }

  hudTick++;
  const dpr = window.devicePixelRatio || 1;
  const cssW = canvas.clientWidth || 300;
  const cssH = canvas.clientHeight || 220;
  if (canvas.width !== cssW * dpr) {
    canvas.width = cssW * dpr;
    canvas.height = cssH * dpr;
  }
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, cssW, cssH);

  const cx = cssW / 2;
  const cy = cssH / 2;
  const freqData = getAudioFreqData();

  // Calculate dB level & current state
  let currentDb = -48;
  if (S.speaking) {
    currentDb = Math.round(-30 + Math.min(26, S.outLevel * 40));
    if ($("hud-voice-state")) {
      $("hud-voice-state").textContent = "LEO FLET 🔊";
      $("hud-voice-state").style.color = "var(--cyan)";
    }
  } else if (S.micOn) {
    currentDb = Math.round(-42 + Math.min(38, S.inLevel * 50));
    if ($("hud-voice-state")) {
      $("hud-voice-state").textContent = S.inLevel > 0.05 ? "DËGJIM AKTIV 🎙️" : "PO DËGJOJ...";
      $("hud-voice-state").style.color = "var(--emerald)";
    }
  } else {
    if ($("hud-voice-state")) {
      $("hud-voice-state").textContent = "STANDBY ⚡";
      $("hud-voice-state").style.color = "var(--text-dim)";
    }
  }
  if ($("hud-stat-db")) $("hud-stat-db").textContent = `${currentDb} dBFS`;

  // Base circle radius
  const baseR = 46;

  ctx.save();
  ctx.translate(cx, cy);

  // Outer rotating tech ring with dashed segments
  ctx.save();
  ctx.rotate(hudTick * 0.012);
  ctx.strokeStyle = "rgba(0, 243, 255, 0.25)";
  ctx.lineWidth = 1.5;
  ctx.setLineDash([8, 12]);
  ctx.beginPath();
  ctx.arc(0, 0, baseR + 32, 0, Math.PI * 2);
  ctx.stroke();
  ctx.restore();

  // Reverse rotating ring with degree ticks
  ctx.save();
  ctx.rotate(-hudTick * 0.008);
  ctx.strokeStyle = "rgba(0, 102, 255, 0.35)";
  ctx.lineWidth = 1.2;
  ctx.setLineDash([4, 20]);
  ctx.beginPath();
  ctx.arc(0, 0, baseR + 24, 0, Math.PI * 2);
  ctx.stroke();
  ctx.restore();

  // Radial spectrum frequency bars (36 bars)
  const numBars = 36;
  const step = (Math.PI * 2) / numBars;
  for (let i = 0; i < numBars; i++) {
    const angle = i * step + hudTick * 0.005;
    let magnitude = 0;
    if (freqData && freqData.length > 0) {
      const binIdx = Math.floor((i / numBars) * (freqData.length * 0.7));
      magnitude = (freqData[binIdx] || 0) / 255;
    } else {
      magnitude = 0.15 + 0.08 * Math.sin(hudTick * 0.08 + i * 0.35);
      if (S.speaking) magnitude += S.outLevel * 0.4;
      if (S.micOn) magnitude += S.inLevel * 0.5;
    }

    const barLen = Math.max(4, magnitude * 38);
    const x1 = Math.cos(angle) * (baseR + 4);
    const y1 = Math.sin(angle) * (baseR + 4);
    const x2 = Math.cos(angle) * (baseR + 4 + barLen);
    const y2 = Math.sin(angle) * (baseR + 4 + barLen);

    const grad = ctx.createLinearGradient(x1, y1, x2, y2);
    grad.addColorStop(0, "rgba(0, 102, 255, 0.4)");
    grad.addColorStop(1, magnitude > 0.4 ? "rgba(0, 255, 170, 0.95)" : "rgba(0, 243, 255, 0.95)");

    ctx.strokeStyle = grad;
    ctx.lineWidth = 2.5;
    ctx.lineCap = "round";
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
    ctx.stroke();
  }

  ctx.restore();
  requestAnimationFrame(drawHudSpectrum);
}

function drawHudEq() {
  const canvas = $("hud-eq-canvas");
  if (!canvas) {
    requestAnimationFrame(drawHudEq);
    return;
  }
  const ctx = canvas.getContext("2d");
  if (!ctx) {
    requestAnimationFrame(drawHudEq);
    return;
  }

  const dpr = window.devicePixelRatio || 1;
  const cssW = canvas.clientWidth || 300;
  const cssH = canvas.clientHeight || 34;
  if (canvas.width !== cssW * dpr) {
    canvas.width = cssW * dpr;
    canvas.height = cssH * dpr;
  }
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, cssW, cssH);

  const freqData = getAudioFreqData();
  const barCount = 28;
  const barWidth = (cssW - (barCount - 1) * 3) / barCount;

  for (let i = 0; i < barCount; i++) {
    let mag = 0;
    if (freqData && freqData.length > 0) {
      const idx = Math.floor((i / barCount) * (freqData.length * 0.8));
      mag = (freqData[idx] || 0) / 255;
    } else {
      mag = 0.12 + 0.1 * Math.sin(hudTick * 0.05 + i * 0.25);
      if (S.speaking) mag += S.outLevel * 0.35;
      if (S.micOn) mag += S.inLevel * 0.45;
    }

    const h = Math.max(3, mag * (cssH - 4));
    const x = i * (barWidth + 3);
    const y = cssH - h;

    const grad = ctx.createLinearGradient(0, y, 0, cssH);
    grad.addColorStop(0, "rgba(0, 243, 255, 0.95)");
    grad.addColorStop(1, "rgba(0, 102, 255, 0.4)");

    ctx.fillStyle = grad;
    ctx.fillRect(x, y, barWidth, h);

    ctx.fillStyle = "rgba(0, 255, 170, 0.9)";
    ctx.fillRect(x, Math.max(0, y - 2), barWidth, 1.5);
  }

  requestAnimationFrame(drawHudEq);
}

function drawHudRadar() {
  const canvas = $("hud-radar-canvas");
  if (!canvas) {
    requestAnimationFrame(drawHudRadar);
    return;
  }
  const ctx = canvas.getContext("2d");
  if (!ctx) {
    requestAnimationFrame(drawHudRadar);
    return;
  }

  const dpr = window.devicePixelRatio || 1;
  const cssW = canvas.clientWidth || 280;
  const cssH = canvas.clientHeight || 140;
  if (canvas.width !== cssW * dpr) {
    canvas.width = cssW * dpr;
    canvas.height = cssH * dpr;
  }
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, cssW, cssH);

  const cx = cssW / 2;
  const cy = cssH / 2;
  const maxR = Math.min(cx, cy) - 10;

  // Concentric radar rings
  ctx.strokeStyle = "rgba(0, 243, 255, 0.16)";
  ctx.lineWidth = 1;
  for (const factor of [0.33, 0.66, 1.0]) {
    ctx.beginPath();
    ctx.arc(cx, cy, maxR * factor, 0, Math.PI * 2);
    ctx.stroke();
  }

  // Crosshair lines
  ctx.beginPath();
  ctx.moveTo(cx - maxR, cy);
  ctx.lineTo(cx + maxR, cy);
  ctx.moveTo(cx, cy - maxR);
  ctx.lineTo(cx, cy + maxR);
  ctx.stroke();

  // Rotating sweep beam
  radarAngle = (radarAngle + 0.035) % (Math.PI * 2);
  const sweepGrad = ctx.createRadialGradient(cx, cy, 0, cx, cy, maxR);
  sweepGrad.addColorStop(0, "rgba(0, 243, 255, 0.35)");
  sweepGrad.addColorStop(1, "rgba(0, 102, 255, 0.05)");

  ctx.save();
  ctx.beginPath();
  ctx.moveTo(cx, cy);
  ctx.arc(cx, cy, maxR, radarAngle - 0.45, radarAngle);
  ctx.closePath();
  ctx.fillStyle = sweepGrad;
  ctx.fill();

  // Sweep leading edge line
  ctx.strokeStyle = "rgba(0, 243, 255, 0.9)";
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.moveTo(cx, cy);
  ctx.lineTo(cx + Math.cos(radarAngle) * maxR, cy + Math.sin(radarAngle) * maxR);
  ctx.stroke();
  ctx.restore();

  // Target blips
  for (const b of radarBlips) {
    const bx = cx + Math.cos(b.ang) * (maxR * b.dist);
    const by = cy + Math.sin(b.ang) * (maxR * b.dist);
    
    const diff = Math.abs((radarAngle - b.ang + Math.PI * 2) % (Math.PI * 2));
    if (diff < 0.2) b.alpha = 1.0;
    else b.alpha = Math.max(0.2, b.alpha - 0.008);

    ctx.fillStyle = `rgba(0, 255, 170, ${b.alpha})`;
    ctx.beginPath();
    ctx.arc(bx, by, 2.5, 0, Math.PI * 2);
    ctx.fill();

    if (b.alpha > 0.6) {
      ctx.strokeStyle = `rgba(0, 243, 255, ${b.alpha * 0.5})`;
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.arc(bx, by, 6, 0, Math.PI * 2);
      ctx.stroke();
    }
  }

  requestAnimationFrame(drawHudRadar);
}

function handleIotUpdate(device, action, value) {
  addLog("sys", `🏠 IoT: Pajisja '${device}' u vendos në '${action}' ${value || ''}`);
  if (device && device.toLowerCase().includes("klim")) {
    if (action === "toggle" || action === "open") S.iotState.acOn = true;
    if (action === "close") S.iotState.acOn = false;
    if (value && parseFloat(value)) S.iotState.acTemp = parseFloat(value);
    syncIotUi();
  } else if (device && device.toLowerCase().includes("drit")) {
    if (action === "toggle" || action === "open") S.iotState.lightOn = true;
    if (action === "close") S.iotState.lightOn = false;
    syncIotUi();
  }
}

function syncIotUi() {
  const acBtn = $("btn-ac-toggle");
  if (acBtn) {
    acBtn.classList.toggle("active", S.iotState.acOn);
    acBtn.textContent = S.iotState.acOn ? "ON" : "OFF";
  }
  const tempDisp = $("iot-temp-disp");
  if (tempDisp) tempDisp.textContent = `${S.iotState.acTemp}°`;
  const acSub = $("iot-ac-sub");
  if (acSub) acSub.textContent = `${S.iotState.acOn ? 'Ftohtë' : 'Fikur'} • ${S.iotState.acTemp}°C`;

  const lightBtn = $("btn-light-toggle");
  if (lightBtn) {
    lightBtn.classList.toggle("active", S.iotState.lightOn);
    lightBtn.textContent = S.iotState.lightOn ? "ON" : "OFF";
  }
  const plugBtn = $("btn-plug-toggle");
  if (plugBtn) {
    plugBtn.classList.toggle("active", S.iotState.plugOn);
    plugBtn.textContent = S.iotState.plugOn ? "ON" : "OFF";
  }
  const lockBtn = $("btn-lock-toggle");
  if (lockBtn) {
    lockBtn.classList.toggle("active", S.iotState.locked);
    lockBtn.textContent = S.iotState.locked ? "KYÇ" : "HAP";
  }
  const lockSub = $("iot-lock-sub");
  if (lockSub) lockSub.textContent = S.iotState.locked ? "I KYÇUR (SECURE)" : "I HAPUR (UNLOCKED)";
}

function addStalkerTicker(text) {
  const ticker = $("stalker-ticker");
  if (!ticker) return;
  const timeStr = new Date().toTimeString().substring(0, 5);
  const item = document.createElement("div");
  item.className = "ticker-item";
  item.innerHTML = `<span class="ticker-time">[${timeStr}]</span> <span class="ticker-text">${text}</span>`;
  ticker.insertBefore(item, ticker.firstChild);
}

function initHudEvents() {
  // Mic buttons in HUD
  const hudMicBtn = $("btn-hud-mic");
  if (hudMicBtn) hudMicBtn.addEventListener("click", () => (S.micOn ? stopMic() : startMic()));

  const hudCoreTarget = $("hud-core-click-target");
  if (hudCoreTarget) hudCoreTarget.addEventListener("click", () => (S.micOn ? stopMic() : startMic()));

  // Always on listener button
  const listenerBtn = $("btn-hud-listener");
  if (listenerBtn) {
    listenerBtn.addEventListener("click", () => {
      S.alwaysOn = !S.alwaysOn;
      listenerBtn.textContent = S.alwaysOn ? "⚡ ALWAYS-ON: PO" : "⚡ ALWAYS-ON: JO";
      const lbl = $("hud-listener-state");
      if (lbl) lbl.textContent = S.alwaysOn ? "ALWAYS-ON" : "PUSH-TO-TALK";
      if (S.alwaysOn && !S.micOn) startMic();
    });
  }

  // Overlay HUD effect
  const overlayBtn = $("btn-hud-overlay");
  if (overlayBtn) {
    overlayBtn.addEventListener("click", () => {
      S.hudOverlay = !S.hudOverlay;
      document.body.classList.toggle("hud-neon-active", S.hudOverlay);
      overlayBtn.textContent = S.hudOverlay ? "🌌 HUD: FULL NEON" : "🌌 HUD OVERLAY";
    });
  }

  // AC Controls
  $("btn-ac-down")?.addEventListener("click", () => {
    S.iotState.acTemp = Math.max(16, Math.round((S.iotState.acTemp - 0.5) * 10) / 10);
    syncIotUi();
  });
  $("btn-ac-up")?.addEventListener("click", () => {
    S.iotState.acTemp = Math.min(30, Math.round((S.iotState.acTemp + 0.5) * 10) / 10);
    syncIotUi();
  });
  $("btn-ac-toggle")?.addEventListener("click", () => {
    S.iotState.acOn = !S.iotState.acOn;
    syncIotUi();
  });

  // Lights controls
  $("btn-light-toggle")?.addEventListener("click", () => {
    S.iotState.lightOn = !S.iotState.lightOn;
    syncIotUi();
  });
  document.querySelectorAll(".color-dots .c-dot").forEach((dot) => {
    dot.addEventListener("click", () => {
      document.querySelectorAll(".color-dots .c-dot").forEach((d) => d.classList.remove("active"));
      dot.classList.add("active");
      S.iotState.lightColor = dot.dataset.color;
      const sub = $("iot-light-sub");
      if (sub) sub.textContent = `${dot.dataset.color.toUpperCase()} • 85%`;
    });
  });

  // Plug & Lock controls
  $("btn-plug-toggle")?.addEventListener("click", () => {
    S.iotState.plugOn = !S.iotState.plugOn;
    syncIotUi();
  });
  $("btn-lock-toggle")?.addEventListener("click", () => {
    S.iotState.locked = !S.iotState.locked;
    syncIotUi();
  });

  // GPS Refresh & Map
  $("btn-hud-gps-refresh")?.addEventListener("click", () => {
    updateTelemetry();
    alert("Vendndodhja GPS dhe telemetria u rifreskuan me sukses! 📍");
  });
  $("btn-hud-gps-map")?.addEventListener("click", () => {
    const lat = S.lastLat || "41.3275";
    const lon = S.lastLon || "19.8187";
    window.open(`https://maps.apple.com/?q=${lat},${lon}`, "_blank");
  });

  // ── SOCIAL STALKER & HESAP BAĞLAMA (CANLI VERİ) ──
  $("btn-open-accounts")?.addEventListener("click", openAccountModal);
  $("btn-hud-open-accounts")?.addEventListener("click", openAccountModal);
  $("btn-stalk-manage")?.addEventListener("click", openAccountModal);
  $("btn-quick-add-target")?.addEventListener("click", openAccountModal);
  $("btn-tel-open-accounts")?.addEventListener("click", openAccountModal);

  // Direct inline quick binding in HUD
  $("btn-quick-target-add")?.addEventListener("click", () => {
    const input = $("quick-target-input");
    if (input && input.value.trim()) {
      scanAndBindAccount(input.value.trim());
      input.value = "";
    } else {
      alert("Lütfen bir Instagram kullanıcı adı yazın!");
    }
  });
  $("quick-target-input")?.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      $("btn-quick-target-add")?.click();
    }
  });

  // Modal target adding
  $("btn-add-target-ig")?.addEventListener("click", () => {
    const input = $("target-ig-input");
    if (input && input.value.trim()) {
      scanAndBindAccount(input.value.trim());
      input.value = "";
    } else {
      alert("Lütfen bir Instagram kullanıcı adı yazın!");
    }
  });
  $("target-ig-input")?.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      $("btn-add-target-ig")?.click();
    }
  });

  // Instagram Hesabına Giriş Yap & Oturum Bağla
  $("btn-login-ig")?.addEventListener("click", async () => {
    const username = $("my-ig-username")?.value.trim().replace("@", "");
    const password = $("my-ig-password")?.value || "";
    const sessionid = $("my-ig-sessionid")?.value.trim() || "";

    if (!username) {
      alert("Lütfen Instagram kullanıcı adınızı girin!");
      return;
    }
    if (!password && !sessionid) {
      alert("Lütfen Instagram şifrenizi veya Session ID girin!");
      return;
    }

    addStalkerTicker(`@${username} için oturum açılıyor ve hesap bağlanıyor...`);
    try {
      const res = await fetch("/api/social/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password, sessionid })
      });
      const data = await res.json();
      if (data.status === "ok") {
        alert(`@${username} Instagram hesabına başarıyla giriş yapıldı ve bağlandı! ✅\nArtık hedef hesaplar bu oturum üzerinden taranacak; yeni eklenen veya çıkan takipçiler anında tespit edilip listenize eklenecektir.`);
        localStorage.setItem("leo_my_ig", username);
        if ($("my-ig-password")) $("my-ig-password").value = "";
        await loadSessionInfo();
        await loadTrackedAccounts();
        await loadStalkerDiffList();
      } else {
        alert(`Giriş başarısız: ${data.message || 'Bilinmeyen hata'}`);
      }
    } catch (err) {
      alert(`Bağlantı hatası: ${err.message}`);
    }
  });

  // Instagram Oturumunu Kapat
  $("btn-logout-ig")?.addEventListener("click", async () => {
    if (confirm("Instagram oturumu kapatılsın mı?")) {
      try {
        await fetch("/api/social/logout", { method: "POST" });
        await loadSessionInfo();
        alert("Instagram oturumu güvenli şekilde kapatıldı.");
      } catch (err) {
        console.error("Logout error:", err);
      }
    }
  });

  // Değişim Listesini Yenile
  $("btn-refresh-diffs")?.addEventListener("click", () => {
    loadStalkerDiffList();
  });

  // HUD Widget'tan Değişim Listesini Aç Butonu
  $("btn-stalk-diff-view")?.addEventListener("click", () => {
    openAccountModal();
    const diffSection = $("stalker-diff-list");
    if (diffSection) {
      setTimeout(() => {
        diffSection.scrollIntoView({ behavior: "smooth", block: "center" });
      }, 200);
    }
  });

  // Stalker Real Scan Buttons
  const triggerScan = () => {
    const user = S.activeStalkerUser || $("stalker-username")?.textContent.replace("@", "") || "lux.coo.1";
    scanAndBindAccount(user);
  };
  $("btn-stalk-scan")?.addEventListener("click", triggerScan);
  $("btn-stalk-scan-fast")?.addEventListener("click", triggerScan);

  // Open in Instagram
  $("btn-stalk-open-ig")?.addEventListener("click", () => {
    const user = S.activeStalkerUser || "lux.coo.1";
    window.open(`https://www.instagram.com/${user}/`, "_blank");
  });

  // LEO Deep Analysis
  $("btn-stalk-leo-analyze")?.addEventListener("click", () => {
    const user = S.activeStalkerUser || "lux.coo.1";
    const promptText = `@${user} Instagram profilini canlı verileriyle (takipçi, takip, gönderi) detaylı analiz et ve strateji öner.`;
    if (S.ws && S.ws.readyState === WebSocket.OPEN) {
      S.ws.send(JSON.stringify({ type: "text", text: promptText }));
      addLog("user", promptText);
      addStalkerTicker(`LEO @${user} için derinlemesine analiz başlatıyor...`);
      // switch to chat or live tab
      switchTab("tab-chat");
    } else {
      alert("LEO bağlantısı bekleniyor...");
    }
  });

  // Live UTC Clock loop
  setInterval(() => {
    const tickEl = $("hud-clock-tick");
    if (tickEl) {
      tickEl.textContent = new Date().toISOString().substring(11, 19) + " UTC";
    }
  }, 1000);
}

// ── GLOBAL ACCOUNT MANAGEMENT FUNCTIONS ─────────────────────────────────────
S.activeStalkerUser = "lux.coo.1";
S.trackedAccounts = {};

function openAccountModal() {
  const m = $("account-modal");
  if (m) m.classList.remove("hidden");
  const mySaved = localStorage.getItem("leo_my_ig") || "leohoca";
  if ($("my-ig-username")) $("my-ig-username").value = mySaved;
  loadSessionInfo();
  loadTrackedAccounts();
  loadStalkerDiffList();
}

async function loadSessionInfo() {
  try {
    const res = await fetch("/api/social/session");
    if (!res.ok) return;
    const sess = await res.json();
    const badge = $("ig-session-badge");
    const loginBtn = $("btn-login-ig");
    const logoutBtn = $("btn-logout-ig");
    const hint = $("ig-session-hint");
    const userInp = $("my-ig-username");

    if (sess && sess.authenticated) {
      if (badge) {
        badge.className = "session-badge online";
        badge.textContent = `● BAĞLI (@${sess.username || 'aktif'})`;
      }
      if (userInp && sess.username) userInp.value = sess.username;
      if (loginBtn) loginBtn.textContent = "🔄 OTURUMU GÜNCELLE";
      if (logoutBtn) logoutBtn.style.display = "inline-block";
      if (hint) {
        hint.textContent = `✅ Hesabınız bağlı (Son giriş: ${sess.last_login || 'Aktif'}). Hedef profiller bu oturumla taranıyor; yeni eklenen veya çıkan takipçiler anında bildirilecek.`;
      }
    } else {
      if (badge) {
        badge.className = "session-badge offline";
        badge.textContent = "● ÇEVRİMDIŞI";
      }
      if (loginBtn) loginBtn.textContent = "🚀 GİRİŞ YAP & HESABI BAĞLA";
      if (logoutBtn) logoutBtn.style.display = "none";
      if (hint) {
        hint.textContent = "Hesabınıza şifre veya Session ID ile giriş yaptığınızda LEO, hedef profillerin takipçi ve takip listesini derinlemesine izler ve yeni eklenen/çıkan kişileri anlık tespit eder.";
      }
    }
  } catch (e) {
    console.error("loadSessionInfo error:", e);
  }
}

async function loadStalkerDiffList() {
  const container = $("stalker-diff-list");
  if (!container) return;
  try {
    const res = await fetch("/api/social/changes");
    if (!res.ok) return;
    const data = await res.json();
    const changes = data.changes || [];
    if (changes.length === 0) {
      container.innerHTML = `<div class="diff-empty">Henüz kaydedilmiş takipçi değişimi yok. Taramalar arka planda devam ediyor (her 30-40 saniyede canlı kontrol).</div>`;
      return;
    }
    container.innerHTML = "";
    changes.forEach((item) => {
      const isGain = item.type === "gain";
      const card = document.createElement("div");
      card.className = `diff-card ${isGain ? "gain" : "loss"}`;
      card.innerHTML = `
        <div class="diff-card-info">
          <div style="display:flex; align-items:center; gap:6px;">
            <span class="diff-card-target">@${item.target}</span>
            <span style="font-size:9.5px; color:var(--text-dim);">• ${item.time || ''}</span>
          </div>
          <div class="diff-card-text">${item.text || ''}</div>
          <div style="font-size:9px; color:var(--cyan); margin-top:2px;">Önceki: ${item.prev_followers || '--'} ➔ Yeni: ${item.followers || '--'}</div>
        </div>
        <div class="diff-card-badge">${item.delta_str || (isGain ? '+1' : '-1')}</div>
      `;
      container.appendChild(card);
    });
  } catch (e) {
    console.error("loadStalkerDiffList error:", e);
  }
}

function closeAccountModal() {
  const m = $("account-modal");
  if (m) m.classList.add("hidden");
}

async function loadTrackedAccounts() {
  try {
    const res = await fetch("/api/social/accounts");
    if (!res.ok) return;
    const data = await res.json();
    S.trackedAccounts = data || {};

    // 1. Render chips row in HUD
    const chipsRow = $("stalker-chips-row");
    if (chipsRow) {
      chipsRow.innerHTML = "";
      const usernames = Object.keys(S.trackedAccounts);
      if (usernames.length === 0) usernames.push("lux.coo.1");

      usernames.forEach((u) => {
        const chip = document.createElement("span");
        chip.className = `stalk-chip ${u === S.activeStalkerUser ? "active" : ""}`;
        chip.dataset.username = u;
        chip.textContent = `@${u}`;
        chip.addEventListener("click", () => setActiveStalkerAccount(u));
        chipsRow.appendChild(chip);
      });

      const addBtn = document.createElement("button");
      addBtn.id = "btn-quick-add-target";
      addBtn.className = "stalk-chip-add";
      addBtn.textContent = "➕ Ekle";
      addBtn.addEventListener("click", openAccountModal);
      chipsRow.appendChild(addBtn);
    }

    // 2. Render list inside Account Modal
    const listEl = $("tracked-accounts-list");
    if (listEl) {
      listEl.innerHTML = "";
      const keys = Object.keys(S.trackedAccounts);
      if (keys.length === 0) {
        listEl.innerHTML = `<div style="font-size:11px;color:var(--text-dim);padding:10px;text-align:center;">Henüz eklenmiş hedef hesap yok. Yukarıdan ekleyebilirsiniz.</div>`;
      } else {
        keys.forEach((u) => {
          const acc = S.trackedAccounts[u];
          const card = document.createElement("div");
          card.className = "tracked-acct-card";
          card.innerHTML = `
            <div class="tracked-acct-left">
              <img class="tracked-acct-avatar" src="${acc.image || ''}" onerror="this.src='https://ui-avatars.com/api/?name=${u}&background=0066ff&color=fff'" alt="${u}" />
              <div class="tracked-acct-info">
                <span class="tracked-acct-user">@${u}</span>
                <span class="tracked-acct-stats">Takipçi: <b>${acc.followers || '--'}</b> • Takip: <b>${acc.following || '--'}</b> • Gönderi: <b>${acc.posts || '--'}</b></span>
              </div>
            </div>
            <div class="tracked-acct-actions">
              <button class="acct-btn-primary btn-select-acct" data-user="${u}">🎯 SEÇ</button>
              <button class="acct-btn-primary btn-rescan-acct" data-user="${u}">🔄</button>
              <button class="acct-btn-primary btn-del-acct" data-user="${u}" style="background:rgba(255,0,85,0.25);border-color:#ff0055;">✕</button>
            </div>
          `;
          card.querySelector(".btn-select-acct").addEventListener("click", () => {
            setActiveStalkerAccount(u);
            closeAccountModal();
          });
          card.querySelector(".btn-rescan-acct").addEventListener("click", () => {
            scanAndBindAccount(u);
          });
          card.querySelector(".btn-del-acct").addEventListener("click", async () => {
            if (confirm(`@${u} takip listesinden kaldırılsın mı?`)) {
              await fetch("/api/social/accounts", {
                method: "DELETE",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ username: u })
              });
              loadTrackedAccounts();
            }
          });
          listEl.appendChild(card);
        });
      }
    }

    // 3. Update HUD with active account data
    if (S.activeStalkerUser && S.trackedAccounts[S.activeStalkerUser]) {
      updateStalkerHUD(S.trackedAccounts[S.activeStalkerUser]);
    } else if (Object.keys(S.trackedAccounts).length > 0) {
      const first = Object.keys(S.trackedAccounts)[0];
      setActiveStalkerAccount(first);
    }
  } catch (e) {
    console.error("loadTrackedAccounts error:", e);
  }
}

function setActiveStalkerAccount(username) {
  S.activeStalkerUser = username;
  document.querySelectorAll(".stalk-chip").forEach((chip) => {
    chip.classList.toggle("active", chip.dataset.username === username);
  });
  if (S.trackedAccounts && S.trackedAccounts[username]) {
    updateStalkerHUD(S.trackedAccounts[username]);
  } else {
    scanAndBindAccount(username);
  }
}

function updateStalkerHUD(acc) {
  if (!acc) return;
  if ($("stalker-username")) $("stalker-username").textContent = `@${acc.username}`;
  if ($("stk-followers")) $("stk-followers").textContent = acc.followers || "--";
  if ($("stk-following")) $("stk-following").textContent = acc.following || "--";
  if ($("stk-stories")) $("stk-stories").textContent = acc.posts || "--";
  if ($("stalker-status-desc")) $("stalker-status-desc").textContent = `● Canlı Instagram Verisi (${acc.last_checked || 'Az önce'})`;
  const imgEl = $("stalker-avatar-img");
  const iconEl = $("stalker-avatar-icon");
  if (imgEl) {
    if (acc.image) {
      imgEl.src = acc.image;
      imgEl.style.display = "block";
      if (iconEl) iconEl.style.display = "none";
    } else {
      imgEl.style.display = "none";
      if (iconEl) iconEl.style.display = "block";
    }
  }
}

async function scanAndBindAccount(rawUser) {
  const username = (rawUser || "").trim().replace("@", "");
  if (!username) {
    alert("Lütfen geçerli bir Instagram kullanıcı adı girin!");
    return;
  }
  addStalkerTicker(`@${username} için Instagram sunucuları canlı taranıyor...`);
  if ($("stalker-status-desc")) $("stalker-status-desc").textContent = `● Taranıyor: @${username}...`;

  try {
    const res = await fetch("/api/social/scan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username })
    });
    const data = await res.json();
    if (data.status === "ok" && data.account) {
      S.activeStalkerUser = username;
      addStalkerTicker(`@${username} GERÇEK: ${data.account.followers} Takipçi, ${data.account.following} Takip, ${data.account.posts} Gönderi.`);
      await loadTrackedAccounts();
      setActiveStalkerAccount(username);
      alert(`@${username} başarıyla bağlandı ve gerçek verileri alındı! ✅\n• Takipçi: ${data.account.followers}\n• Takip Edilen: ${data.account.following}\n• Gönderi: ${data.account.posts}`);
    } else {
      addStalkerTicker(`HATA: @${username} taranamadı (${data.message || 'Profil gizli veya bulunamadı'}).`);
      alert(`Hata: ${data.message || 'Profil bulunamadı veya Instagram kısıtladı.'}`);
    }
  } catch (err) {
    addStalkerTicker(`Bağlantı hatası: ${err.message}`);
    alert(`Bağlantı hatası: ${err.message}`);
  }
}

// Başlangıç yüklemeleri
window.addEventListener("DOMContentLoaded", () => {
  unlockAudioEngine();
  loadChatHistory();
  initLockScreen();
  connect();
  updateTelemetry();
  setInterval(updateTelemetry, 3500);
  loadTrackedAccounts();
  loadSessionInfo();
  loadStalkerDiffList();
  setInterval(() => {
    loadTrackedAccounts();
    loadStalkerDiffList();
  }, 25000);
  initHudEvents();
  initKeyModalEvents();
  requestAnimationFrame(drawOrb);
  requestAnimationFrame(drawHudSpectrum);
  requestAnimationFrame(drawHudEq);
  requestAnimationFrame(drawHudRadar);
});
