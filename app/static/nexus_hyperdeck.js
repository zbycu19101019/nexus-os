(function nexusHyperDeckBoot() {
  "use strict";

  const esc = (value) => String(value ?? "").replace(/[&<>"']/g, ch => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]));
  const qs = (id) => document.getElementById(id);
  const token = () => localStorage.getItem("nexus_token") || "";
  const readableDetail = (value, depth = 0) => {
    if (value === null || value === undefined) return "";
    if (typeof value === "string") return value;
    if (typeof value === "number" || typeof value === "boolean") return String(value);
    if (Array.isArray(value)) return value.map(item => readableDetail(item, depth + 1)).filter(Boolean).join(" | ").slice(0, 1000);
    if (typeof value === "object") {
      for (const key of ["detail", "message", "error", "title", "status", "output"]) {
        if (value[key] !== undefined && value[key] !== value) {
          const text = readableDetail(value[key], depth + 1);
          if (text) return text;
        }
      }
      if (Array.isArray(value.errors)) return readableDetail(value.errors, depth + 1);
      if (Array.isArray(value.attempts)) {
        return value.attempts.slice(-4).map(row => {
          const mode = row.mode || row.operation || "attempt";
          const code = row.code !== undefined ? `code=${row.code}` : "";
          const output = row.output ? String(row.output).slice(0, 240) : "";
          return [mode, code, output].filter(Boolean).join(" ");
        }).join(" | ");
      }
      try { return JSON.stringify(value, null, depth ? 0 : 2).slice(0, 1000); } catch (_) { return String(value); }
    }
    return String(value);
  };
  const notify = (level, title, body, timeout) => {
    const text = readableDetail(body);
    if (typeof window.notifyNexus === "function") window.notifyNexus(level, title, text, timeout);
    else if (level === "error") alert(`${title}: ${text}`);
  };

  let currentBackend = "auto";
  let currentRfb = null;
  let noVncRfbClass = null;
  let osCatalog = [];
  let isoSources = [];
  let isoItems = [];
  let diskItems = [];
  let isoDownloads = [];
  let driverItems = [];
  let hyperVmItems = [];
  let selectedOsId = "debian";
  let isoPollTimer = null;
  let lastConsole = { vmId: "", backend: "auto", name: "" };
  let pointerAttached = true;
  const savedHyperCursorMode = localStorage.getItem("nexus_hyper_cursor_mode");
  let hyperCursorMode = savedHyperCursorMode || ((window.matchMedia && window.matchMedia("(pointer: coarse)").matches) ? "fallback" : "precise");
  let hyperAudioMuted = false;
  let hyperResizeObserver = null;
  let hyperAutoFitTimer = null;
  let hyperCustomScale = localStorage.getItem("nexus_hyper_custom_scale") === "1";
  let hyperCustomWidth = Number(localStorage.getItem("nexus_hyper_custom_w") || 1024);
  let hyperCustomHeight = Number(localStorage.getItem("nexus_hyper_custom_h") || 768);
  const hyperKeyboardRows = [
    [
      { label: "ESC", keysym: 0xff1b, code: "Escape", cls: "warn" },
      { label: "F1", keysym: 0xffbe, code: "F1" }, { label: "F2", keysym: 0xffbf, code: "F2" }, { label: "F3", keysym: 0xffc0, code: "F3" }, { label: "F4", keysym: 0xffc1, code: "F4" },
      { label: "F5", keysym: 0xffc2, code: "F5" }, { label: "F6", keysym: 0xffc3, code: "F6" }, { label: "F7", keysym: 0xffc4, code: "F7" }, { label: "F8", keysym: 0xffc5, code: "F8" },
      { label: "F9", keysym: 0xffc6, code: "F9" }, { label: "F10", keysym: 0xffc7, code: "F10" }, { label: "F11", keysym: 0xffc8, code: "F11" }, { label: "F12", keysym: 0xffc9, code: "F12" }
    ],
    [
      { label: "`", text: "`" }, { label: "1", text: "1" }, { label: "2", text: "2" }, { label: "3", text: "3" }, { label: "4", text: "4" }, { label: "5", text: "5" }, { label: "6", text: "6" }, { label: "7", text: "7" }, { label: "8", text: "8" }, { label: "9", text: "9" }, { label: "0", text: "0" }, { label: "-", text: "-" }, { label: "=", text: "=" },
      { label: "BKSP", keysym: 0xff08, code: "Backspace", cls: "wide warn" }
    ],
    [
      { label: "TAB", keysym: 0xff09, code: "Tab", cls: "wide" }, ...["q","w","e","r","t","y","u","i","o","p"].map(ch => ({ label: ch.toUpperCase(), text: ch })), { label: "[", text: "[" }, { label: "]", text: "]" }, { label: "\\", text: "\\" }
    ],
    [
      { label: "CAPS", keysym: 0xffe5, code: "CapsLock", cls: "wide" }, ...["a","s","d","f","g","h","j","k","l"].map(ch => ({ label: ch.toUpperCase(), text: ch })), { label: ";", text: ";" }, { label: "'", text: "'" }, { label: "ENTER", keysym: 0xff0d, code: "Enter", cls: "wide accent" }
    ],
    [
      { label: "SHIFT", keysym: 0xffe1, code: "ShiftLeft", cls: "wide" }, ...["z","x","c","v","b","n","m"].map(ch => ({ label: ch.toUpperCase(), text: ch })), { label: ",", text: "," }, { label: ".", text: "." }, { label: "/", text: "/" }, { label: "SHIFT", keysym: 0xffe2, code: "ShiftRight", cls: "wide" }
    ],
    [
      { label: "CTRL", keysym: 0xffe3, code: "ControlLeft" }, { label: "ALT", keysym: 0xffe9, code: "AltLeft" }, { label: "SPACJA", keysym: 0x20, code: "Space", cls: "wide accent" }, { label: "ALT", keysym: 0xffea, code: "AltRight" },
      { label: "DEL", keysym: 0xffff, code: "Delete", cls: "warn" }, { label: "HOME", keysym: 0xff50, code: "Home" }, { label: "END", keysym: 0xff57, code: "End" },
      { label: "LEWO", keysym: 0xff51, code: "ArrowLeft" }, { label: "GORA", keysym: 0xff52, code: "ArrowUp" }, { label: "DOL", keysym: 0xff54, code: "ArrowDown" }, { label: "PRAWO", keysym: 0xff53, code: "ArrowRight" },
      { label: "CTRL+ALT+DEL", combo: "ctrl-alt-del", cls: "wide warn" }
    ]
  ];

  function addStyles() {
    if (qs("nexus-hyperdeck-style")) return;
    const style = document.createElement("style");
    style.id = "nexus-hyperdeck-style";
    style.textContent = `
      .hyperdeck-shell{display:flex;flex-direction:column;gap:14px;min-height:100%}
      .hyperdeck-hero{display:grid;grid-template-columns:minmax(0,1fr) 330px;gap:12px}
      .hyperdeck-panel{background:linear-gradient(180deg,#101010,#060606);border:1px solid #26343a;border-radius:6px;box-shadow:0 0 22px rgba(0,255,255,.08)}
      .hyperdeck-main{padding:18px;border-left:4px solid var(--acc-purple);position:relative;overflow:hidden}
      .hyperdeck-main:before{content:"";position:absolute;inset:0;background:linear-gradient(120deg,rgba(176,0,255,.16),transparent 45%,rgba(0,255,255,.08));pointer-events:none}
      .hyperdeck-main>*{position:relative;z-index:1}
      .hyperdeck-main h2{margin:0 0 8px;color:#fff;font-size:clamp(24px,3vw,40px);letter-spacing:0;line-height:1.05}
      .hyperdeck-main p{margin:0;color:#aeb8ba;font-size:13px;line-height:1.55;max-width:850px}
      .hyperdeck-kicker{color:var(--acc-warn);font-size:11px;font-weight:bold;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px}
      .hyperdeck-status{padding:14px;display:grid;gap:10px;align-content:center}
      .hyperdeck-status span{color:#888;font-size:10px;text-transform:uppercase}
      .hyperdeck-status strong{color:#fff;font-size:22px;overflow-wrap:anywhere}
      .hyperdeck-toolbar{display:flex;gap:8px;flex-wrap:wrap;align-items:center;padding:10px}
      .hyperdeck-toolbar .nav-btn{margin:0}
      .hyperdeck-tabs{display:flex;gap:8px;flex-wrap:wrap;align-items:center;padding:10px;background:#050505;border:1px solid #26343a;border-radius:7px}
      .hyperdeck-tab{margin:0!important;border-color:#344!important;color:#9fb!important;background:#070707!important}
      .hyperdeck-tab.active{border-color:var(--acc-cyan)!important;color:var(--acc-cyan)!important;box-shadow:0 0 16px rgba(0,255,255,.14)}
      .hyperdeck-section{display:none}
      .hyperdeck-section.active{display:grid;gap:12px}
      .hyperdeck-section-head{display:flex;justify-content:space-between;gap:10px;align-items:center;padding:12px;border-bottom:1px solid #1f2b30}
      .hyperdeck-section-head strong{color:#fff;font-size:13px;text-transform:uppercase}
      .hyperdeck-section-head small{color:#888;line-height:1.45}
      .hyperdeck-section-body{padding:12px}
      .forge-layout{display:grid;grid-template-columns:minmax(280px,1.05fr) minmax(280px,.95fr);gap:12px}
      .forge-panel{padding:12px}
      .forge-title{display:flex;justify-content:space-between;gap:10px;align-items:center;color:#fff;font-weight:bold;font-size:13px;text-transform:uppercase;border-bottom:1px solid #253136;padding-bottom:8px;margin-bottom:10px}
      .forge-form{display:grid;grid-template-columns:repeat(3,minmax(120px,1fr));gap:8px}
      .forge-form .cyber-input,.forge-form select{margin:0}
      .forge-wide{grid-column:1/-1}
      .forge-os-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:8px;max-height:260px;overflow:auto;padding-right:4px}
      .forge-os-card{background:#070707;border:1px solid #242424;border-left:3px solid var(--acc-cyan);border-radius:5px;padding:10px;cursor:pointer}
      .forge-os-card.selected{border-left-color:var(--acc-warn);box-shadow:0 0 14px rgba(255,170,0,.12)}
      .forge-os-card strong{display:block;color:#fff;margin-bottom:5px}
      .forge-os-card small{display:block;color:#888;line-height:1.35}
      .iso-list{display:grid;gap:7px;max-height:230px;overflow:auto;padding-right:4px}
      .iso-row{display:grid;grid-template-columns:1fr auto;gap:8px;align-items:center;background:#070707;border:1px solid #242424;border-left:3px solid var(--acc-purple);border-radius:5px;padding:9px}
      .iso-row strong{display:block;color:#fff;overflow-wrap:anywhere}
      .iso-row small{display:block;color:#777;margin-top:3px;overflow-wrap:anywhere}
      .source-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:7px;margin-top:10px}
      .source-card{background:#070707;border:1px solid #222;border-left:3px solid #555;border-radius:5px;padding:9px}
      .source-card.direct{border-left-color:#00ff72}.source-card.manual{border-left-color:var(--acc-warn)}
      .source-card strong{display:block;color:#fff;font-size:12px;margin-bottom:5px}
      .source-card small{display:block;color:#888;font-size:10px;line-height:1.35;margin-bottom:7px}
      .download-row{background:#050505;border:1px solid #222;border-radius:5px;padding:8px;margin-top:7px;color:#aaa;font-size:11px}
      .driver-matrix{display:grid;grid-template-columns:repeat(auto-fill,minmax(145px,1fr));gap:6px;margin-top:8px}
      .driver-cat{display:flex;gap:7px;align-items:flex-start;background:#050505;border:1px solid #252525;border-left:3px solid #555;border-radius:5px;padding:7px;color:#bbb;font-size:10px;cursor:pointer}
      .driver-cat.recommended{border-left-color:#00ff72}.driver-cat.unknown{border-left-color:var(--acc-warn)}
      .driver-cat input{margin-top:2px}
      .driver-cat strong{display:block;color:#fff;font-size:10px;line-height:1.2}
      .driver-cat span{display:block;color:#777;font-size:9px;margin-top:2px}
      .hyperdeck-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));gap:12px}
      .hyperdeck-card{background:#080808;border:1px solid #222;border-left:4px solid #555;border-radius:7px;padding:14px;min-height:250px;display:flex;flex-direction:column;gap:10px;position:relative;overflow:hidden}
      .hyperdeck-card.running{border-left-color:#00ff72;box-shadow:inset 0 0 18px rgba(0,255,114,.06)}
      .hyperdeck-card.stopped{border-left-color:var(--acc-warn)}
      .hyperdeck-card:after{content:"";position:absolute;left:0;right:0;bottom:0;height:2px;background:linear-gradient(90deg,var(--acc-cyan),var(--acc-purple),var(--acc-warn));opacity:.45}
      .hyperdeck-meta{display:flex;justify-content:space-between;gap:8px;color:#888;font-size:10px;text-transform:uppercase}
      .hyperdeck-name{color:#fff;font-size:18px;font-weight:bold;line-height:1.2;overflow-wrap:anywhere}
      .hyperdeck-badge{display:inline-flex;width:max-content;max-width:100%;border:1px solid #444;background:#050505;color:#aaa;padding:3px 8px;border-radius:4px;font-size:10px;font-weight:bold}
      .hyperdeck-badge.online{color:#00ff72;border-color:#007a37}.hyperdeck-badge.offline{color:var(--acc-warn);border-color:#684900}
      .hyperdeck-telemetry{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}
      .hyperdeck-tile{background:#050505;border:1px solid #202b2f;border-radius:5px;padding:8px}
      .hyperdeck-tile span{display:block;color:#777;font-size:10px;margin-bottom:4px;text-transform:uppercase}
      .hyperdeck-tile strong{display:block;color:#fff;font-size:15px;overflow-wrap:anywhere}
      .hyperdeck-actions{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:7px;margin-top:auto}
      .hyperdeck-actions .nav-btn{margin:0;padding:8px;font-size:10px}
      body.hyper-console-open{overflow:hidden!important}
      body.hyper-console-open #identity-badge,body.hyper-console-open #skin-toggle,body.hyper-console-open #nx-bottom-drawer,body.hyper-console-open #nexus-floating-chat,body.hyper-console-open #nx-layout-tools{display:none!important}
      .hyperdeck-console{position:fixed;inset:0;z-index:42000;background:rgba(0,0,0,.94);display:none;flex-direction:column;padding:10px;box-sizing:border-box;pointer-events:none}
      .hyperdeck-console.active{display:flex}
      .hyperdeck-console.active{pointer-events:auto}
      .hyperdeck-console:fullscreen{background:#000;padding:8px}
      .hyperdeck-console-bar{display:grid;grid-template-columns:minmax(230px,1fr) minmax(0,auto);gap:10px;align-items:start;padding:10px;background:#080808;border:1px solid #26343a;border-bottom:none;border-radius:8px 8px 0 0}
      .hyperdeck-console-head{min-width:0;max-width:520px;padding-right:8px}
      .hyperdeck-console-controls{display:flex;gap:8px;flex-wrap:wrap;align-items:center;justify-content:flex-end;min-width:0;max-width:calc(100vw - 560px)}
      .hyperdeck-console-controls .nav-btn{margin:0;min-height:38px;white-space:nowrap;min-width:0}
      .hyperdeck-console-title{color:#fff;font-weight:bold;overflow-wrap:anywhere}
      .hyperdeck-console-status{color:var(--acc-cyan);font-size:11px}
      .hyperdeck-vnc-wrap{--hyper-stage-pad-x:0px;--hyper-stage-pad-y:0px;flex:1;min-height:0;background:#000;border:1px solid #26343a;display:flex;align-items:center;justify-content:center;overflow:hidden;overscroll-behavior:contain}
      .hyperdeck-vnc-wrap.custom-size{overflow:auto;align-items:stretch;justify-content:flex-start;padding:var(--hyper-stage-pad-y) var(--hyper-stage-pad-x)}
      #hyper-vnc-screen{width:100%;height:100%;display:flex;align-items:center;justify-content:center;background:#000;outline:none;touch-action:none;user-select:none;cursor:crosshair;overflow:hidden;position:relative}
      .hyperdeck-vnc-wrap.custom-size #hyper-vnc-screen{width:var(--hyper-custom-width,1024px);height:var(--hyper-custom-height,768px);flex:0 0 auto}
      #hyper-rfb-surface{width:100%;height:100%;min-width:0;min-height:0;display:flex;align-items:center;justify-content:center;background:#000;outline:none;touch-action:none;user-select:none;position:relative}
      #hyper-rfb-surface canvas{display:block;image-rendering:auto;touch-action:none;outline:none}
      #hyper-rfb-surface>*{flex:0 0 auto}
      #hyper-rfb-surface>div{width:100%!important;height:100%!important;display:flex!important;align-items:center;justify-content:center;background:#000!important}
      #hyper-vnc-screen.cursor-fallback,#hyper-vnc-screen.cursor-fallback canvas,#hyper-vnc-screen.cursor-fallback #hyper-rfb-surface{cursor:default!important}
      #hyper-vnc-screen.cursor-fallback{overflow:auto;align-items:flex-start;justify-content:flex-start}
      #hyper-vnc-screen.cursor-fallback #hyper-rfb-surface{width:max-content;height:max-content}
      #hyper-vnc-screen.cursor-fallback #hyper-rfb-surface>div{width:auto!important;height:auto!important}
      #hyper-vnc-screen.cursor-fallback canvas{max-width:none!important;max-height:none!important}
      .hyperdeck-osk{display:none;background:#050505;border:1px solid #26343a;border-top:none;border-radius:0 0 8px 8px;padding:10px;max-height:34vh;overflow:auto}
      .hyperdeck-osk.active{display:grid;gap:6px}
      .hyperdeck-osk-row{display:flex;gap:6px;justify-content:center;min-width:max-content}
      .hyperdeck-key{min-width:38px;height:34px;margin:0!important;padding:0 8px!important;border-color:#355!important;color:#cfe!important;background:#070707!important;font-size:10px!important;line-height:1!important;white-space:nowrap}
      .hyperdeck-key.wide{min-width:72px;flex:1 1 72px}
      .hyperdeck-key.accent{border-color:var(--acc-cyan)!important;color:var(--acc-cyan)!important}
      .hyperdeck-key.warn{border-color:var(--acc-warn)!important;color:var(--acc-warn)!important}
      .hyperdeck-password{width:180px!important;margin:0!important;padding:8px!important;min-height:34px!important}
      .hyperdeck-clip{width:min(260px,22vw)!important;margin:0!important;padding:8px!important;min-height:34px!important}
      .hyperdeck-size{width:78px!important;margin:0!important;padding:8px!important;min-height:34px!important;text-align:center}
      .hyperdeck-modal{position:fixed;inset:0;z-index:42500;background:rgba(0,0,0,.82);display:none;align-items:center;justify-content:center;padding:16px;box-sizing:border-box}
      .hyperdeck-modal.active{display:flex}
      .hyperdeck-modal-panel{width:min(980px,96vw);max-height:88vh;overflow:auto;background:#080808;border:1px solid #26343a;border-radius:8px;box-shadow:0 0 28px rgba(0,255,255,.12)}
      .hyperdeck-modal-head{display:flex;justify-content:space-between;gap:10px;align-items:center;padding:12px 14px;border-bottom:1px solid #222}
      .hyperdeck-modal-head strong{color:#fff;overflow-wrap:anywhere}
      .hyperdeck-modal-body{padding:14px;display:grid;gap:10px}
      .hyperdeck-form{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:8px;align-items:end}
      .hyperdeck-form .cyber-input,.hyperdeck-form select{margin:0}
      .hyperdeck-log{background:#020202;color:#0f0;border:1px solid #222;border-left:3px solid var(--acc-cyan);border-radius:5px;padding:12px;min-height:280px;max-height:60vh;overflow:auto;white-space:pre-wrap;font-size:12px}
      .hyperdeck-row{background:#050505;border:1px solid #222;border-left:3px solid var(--acc-purple);border-radius:5px;padding:9px;display:grid;grid-template-columns:1fr auto;gap:8px;align-items:center}
      .hyperdeck-row strong{color:#fff;display:block;overflow-wrap:anywhere}
      .hyperdeck-row small{color:#888;display:block;margin-top:3px;overflow-wrap:anywhere}
      @media(max-width:1280px){.hyperdeck-console-bar{grid-template-columns:1fr}.hyperdeck-console-controls{justify-content:flex-start;max-width:100%}.hyperdeck-password{flex:1 1 180px;width:auto!important}.hyperdeck-clip{flex:2 1 240px;width:auto!important}}
      @media(max-width:900px){.hyperdeck-hero,.forge-layout{grid-template-columns:1fr}.hyperdeck-section-head{display:grid}.forge-form{grid-template-columns:1fr}.hyperdeck-grid{grid-template-columns:1fr}.hyperdeck-actions{grid-template-columns:1fr}.hyperdeck-console{padding:8px}.hyperdeck-console-controls .nav-btn{flex:1 1 150px;padding-left:8px!important;padding-right:8px!important}.hyperdeck-key{min-width:34px;height:32px;padding:0 6px!important}}
      @media(max-width:560px){.hyperdeck-password,.hyperdeck-clip{flex:1 1 100%;width:100%!important}.hyperdeck-console-controls .nav-btn{flex:1 1 calc(50% - 8px);white-space:normal;font-size:9px!important;padding:8px 6px!important}.hyperdeck-console-bar{padding:8px;max-height:40vh;overflow:auto}.hyperdeck-vnc-wrap{min-height:220px}.hyperdeck-osk{max-height:42vh}.hyperdeck-key{min-width:32px;height:30px;font-size:9px!important}.hyperdeck-key.wide{min-width:62px;flex:1 1 62px}}
    `;
    document.head.appendChild(style);
  }

  function installPage() {
    if (!qs("content") || qs("hyper_deck")) return;
    const page = document.createElement("div");
    page.id = "hyper_deck";
    page.className = "page";
    page.innerHTML = `
      <div class="hyperdeck-shell">
        <section class="hyperdeck-hero">
          <div class="hyperdeck-panel hyperdeck-main">
            <div class="hyperdeck-kicker">V-MATRIX / HYPERVISOR</div>
            <h2>HYPER-DECK</h2>
            <p>Matryca maszyn KVM/QEMU z kontrola zasilania i graficzna konsola noVNC. Surowy VNC zostaje na localhost VPS-a, a NEXUS przepuszcza obraz przez autoryzowany websocket.</p>
          </div>
          <div class="hyperdeck-panel hyperdeck-status">
            <div><span>Silnik</span><strong id="hyper-backend">--</strong></div>
            <div><span>Stan</span><strong id="hyper-message">Oczekiwanie na skan</strong></div>
          </div>
        </section>
        <section class="hyperdeck-panel hyperdeck-toolbar">
          <button class="nav-btn" style="border-color:var(--acc-cyan);color:var(--acc-cyan);" onclick="loadHyperDeck()">SKANUJ HYPERVISOR</button>
          <button class="nav-btn" style="border-color:var(--acc-warn);color:var(--acc-warn);" onclick="loadVMs();loadHyperDeck()">SYNC Z VM CONTROL</button>
          <button class="nav-btn" style="border-color:var(--acc-purple);color:var(--acc-purple);" onclick="loadOsForge()">ODSWIEZ OS FORGE</button>
          <button class="nav-btn" style="border-color:#0f0;color:#0f0;" onclick="checkVmAlerts()">VM ALERT CHECK</button>
          <span class="proc-pill">Konsola: noVNC / WebSocket proxy</span>
          <span class="proc-pill">VNC publiczny: <b style="color:#0f0;">NIE</b></span>
        </section>
        <section class="hyperdeck-tabs">
          <button id="hyper-tab-vms" class="nav-btn hyperdeck-tab active" onclick="setHyperDeckTab('vms')">VM CONTROL</button>
          <button id="hyper-tab-forge" class="nav-btn hyperdeck-tab" onclick="setHyperDeckTab('forge')">TWORZENIE VM</button>
          <button id="hyper-tab-iso" class="nav-btn hyperdeck-tab" onclick="setHyperDeckTab('iso')">ISO / DYSKI</button>
          <button id="hyper-tab-drivers" class="nav-btn hyperdeck-tab" onclick="setHyperDeckTab('drivers')">STEROWNIKI</button>
        </section>
        <section id="hyper-section-vms" class="hyperdeck-section active">
          <div class="hyperdeck-panel">
            <div class="hyperdeck-section-head">
              <div><strong>Aktywne maszyny</strong><br><small>Najpierw kontrola VM, konsole i szybkie akcje. Tworzenie i vaulty sa w osobnych kartach.</small></div>
              <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;justify-content:flex-end;">
                <span id="hyper-vm-summary" class="proc-pill">VM: --</span>
                <input id="hyper-vm-filter" class="cyber-input" style="margin:0;min-height:34px;width:min(280px,42vw);" placeholder="filtr VM..." oninput="renderHyperVmGrid()">
                <button class="nav-btn" style="margin:0;border-color:var(--acc-cyan);color:var(--acc-cyan);" onclick="loadHyperDeck()">ODSWIEZ LISTE</button>
              </div>
            </div>
            <div id="hyper-vm-grid" class="hyperdeck-grid hyperdeck-section-body"></div>
          </div>
        </section>
        <section id="hyper-section-forge" class="hyperdeck-section">
          <div class="hyperdeck-panel forge-panel">
            <div class="forge-title">TWORZENIE VM / OS FORGE <span id="forge-tools" style="color:#888;font-size:10px;">ladowanie</span></div>
            <div class="forge-form">
              <select id="forge-os-select" class="cyber-input" onchange="selectForgePreset(this.value)"></select>
              <input id="forge-vm-name" class="cyber-input" placeholder="nazwa VM">
              <select id="forge-iso-select" class="cyber-input"></select>
              <select id="forge-driver-select" class="cyber-input forge-wide"></select>
              <input id="forge-opencore" class="cyber-input" list="forge-opencore-list" placeholder="OpenCore qcow2: opencore.qcow2">
              <datalist id="forge-opencore-list"></datalist>
              <input id="forge-ovmf-code" class="cyber-input" placeholder="OVMF_CODE opcj.">
              <input id="forge-ovmf-vars" class="cyber-input" placeholder="OVMF_VARS opcj.">
              <input id="forge-memory" class="cyber-input" type="number" min="128" step="128" placeholder="RAM MB">
              <input id="forge-vcpus" class="cyber-input" type="number" min="1" step="1" placeholder="vCPU">
              <input id="forge-disk" class="cyber-input" type="number" min="4" step="1" placeholder="Dysk GB">
              <label class="cyber-input forge-wide" style="display:flex;gap:8px;align-items:center;color:#9cf;">
                <input id="forge-byol" type="checkbox">
                BYOL: mam legalny obraz/licencje i wlasny bootloader OpenCore
              </label>
              <input id="forge-search" class="cyber-input forge-wide" placeholder="Filtruj systemy..." oninput="renderForgeCatalog()">
              <button class="nav-btn forge-wide" style="margin:0;border-color:#0f0;color:#0f0;" onclick="createForgeVm()">UTWORZ VM I OTWORZ KONSOLĘ</button>
              <button class="nav-btn forge-wide" style="margin:0;border-color:#9cf;color:#9cf;" onclick="cupertinoCheckForge()">CUPERTINO CHECK</button>
              <div id="forge-status" class="forge-wide" style="color:#888;font-size:11px;">Wybierz preset i ISO.</div>
            </div>
            <div id="forge-os-grid" class="forge-os-grid" style="margin-top:10px;"></div>
          </div>
        </section>
        <section id="hyper-section-iso" class="hyperdeck-section">
          <div class="hyperdeck-panel forge-panel">
            <div class="forge-title">ISO / DYSK VAULT <span id="iso-roots" style="color:#888;font-size:10px;">/var/lib/libvirt/images/nexus-isos</span></div>
            <div class="forge-form">
              <input id="iso-url" class="cyber-input forge-wide" placeholder="URL do .iso / .qcow2 / .raw / .img">
              <input id="iso-filename" class="cyber-input" placeholder="nazwa pliku opcj.">
              <button class="nav-btn" style="margin:0;border-color:var(--acc-cyan);color:var(--acc-cyan);" onclick="downloadIso()">POBIERZ DO VAULT</button>
              <button class="nav-btn" style="margin:0;border-color:var(--acc-warn);color:var(--acc-warn);" onclick="loadIsoVault()">ODSWIEZ</button>
              <input id="iso-upload-file" type="file" multiple class="cyber-input forge-wide" accept=".iso,.qcow2,.raw,.img">
              <button class="nav-btn forge-wide" style="margin:0;border-color:#0f0;color:#0f0;" onclick="turboUploadIsoVault()">TURBO UPLOAD ISO / OPENCORE</button>
            </div>
            <div id="iso-downloads"></div>
            <div id="iso-list" class="iso-list" style="margin-top:10px;"></div>
            <div id="disk-list" class="iso-list" style="margin-top:10px;"></div>
            <div class="forge-title" style="margin-top:12px;">SZYBKIE ZRODLA <span style="color:#888;font-size:10px;">oficjalne</span></div>
            <div id="iso-source-grid" class="source-grid"></div>
          </div>
        </section>
        <section id="hyper-section-drivers" class="hyperdeck-section">
          <div class="hyperdeck-panel forge-panel">
            <div class="forge-title">DRIVER VAULT <span id="driver-tools" style="color:#888;font-size:10px;">sterowniki VM</span></div>
            <div id="driver-list" class="iso-list"></div>
          </div>
        </section>
      </div>
      <section id="hyper-console" class="hyperdeck-console">
        <div class="hyperdeck-console-bar">
          <div class="hyperdeck-console-head">
            <div class="hyperdeck-console-title" id="hyper-console-title">KONSOLA VM</div>
            <div class="hyperdeck-console-status" id="hyper-console-status">Rozlaczona</div>
          </div>
          <div class="hyperdeck-console-controls">
            <input id="hyper-vnc-password" class="cyber-input hyperdeck-password" type="password" placeholder="VNC password opcj.">
            <input id="hyper-clipboard-text" class="cyber-input hyperdeck-clip" placeholder="tekst do wklejenia w VM">
            <button class="nav-btn" style="margin:0;border-color:#0f0;color:#0f0;" onclick="sendHyperClipboard()">WKLEJ</button>
            <button class="nav-btn" style="margin:0;border-color:#0f0;color:#0f0;" onclick="readSystemClipboardToHyper()">CZYTAJ PC</button>
            <button class="nav-btn" style="margin:0;border-color:var(--acc-cyan);color:var(--acc-cyan);" onclick="typeHyperClipboardToVm()">WPISZ</button>
            <button class="nav-btn" style="margin:0;border-color:var(--acc-warn);color:var(--acc-warn);" onclick="sendHyperCtrlAltDel()">CTRL+ALT+DEL</button>
            <button class="nav-btn" style="margin:0;border-color:var(--acc-purple);color:var(--acc-purple);" onclick="restartHyperConsoleView()">RESET PODGLADU</button>
            <button class="nav-btn" style="margin:0;border-color:var(--acc-warn);color:var(--acc-warn);" onclick="openConsoleIsoPicker()">ISO</button>
            <button class="nav-btn" style="margin:0;border-color:var(--acc-purple);color:var(--acc-purple);" onclick="fitHyperConsole()">FIT</button>
            <input id="hyper-size-w" class="cyber-input hyperdeck-size" type="number" min="320" max="7680" step="16" title="Szerokosc obrazu VM">
            <input id="hyper-size-h" class="cyber-input hyperdeck-size" type="number" min="240" max="4320" step="16" title="Wysokosc obrazu VM">
            <button class="nav-btn" id="hyper-custom-size-btn" style="margin:0;border-color:var(--acc-purple);color:var(--acc-purple);" onclick="setHyperCustomSize()">ROZMIAR</button>
            <button class="nav-btn" id="hyper-clear-size-btn" style="margin:0;border-color:#777;color:#aaa;" onclick="clearHyperCustomSize()">AUTO</button>
            <button class="nav-btn" id="hyper-center-btn" style="margin:0;border-color:var(--acc-cyan);color:var(--acc-cyan);" onclick="centerHyperConsoleView(true)">CENTRUJ</button>
            <button class="nav-btn" style="margin:0;border-color:var(--acc-warn);color:var(--acc-warn);" onclick="repairHyperMouse()">RESET MYSZY</button>
            <button class="nav-btn" id="hyper-fullscreen-btn" style="margin:0;border-color:var(--acc-cyan);color:var(--acc-cyan);" onclick="toggleHyperFullscreen()">FULLSCREEN</button>
            <button class="nav-btn" id="hyper-pointer-btn" style="margin:0;border-color:var(--acc-cyan);color:var(--acc-cyan);" onclick="toggleHyperPointer()">MYSZ ON</button>
            <button class="nav-btn" id="hyper-cursor-mode-btn" style="margin:0;border-color:var(--acc-cyan);color:var(--acc-cyan);" onclick="toggleHyperCursorMode()">KURSOR PRECYZYJNY</button>
            <button class="nav-btn" id="hyper-mute-btn" style="margin:0;border-color:#777;color:#aaa;" onclick="toggleHyperAudioMute()">MUTE</button>
            <button class="nav-btn" id="hyper-keyboard-btn" style="margin:0;border-color:var(--acc-cyan);color:var(--acc-cyan);" onclick="toggleHyperKeyboard()">KLAWIATURA</button>
            <button class="nav-btn" style="margin:0;border-color:var(--acc-cyan);color:var(--acc-cyan);" onclick="hyperConsoleFocus()">FOCUS</button>
            <button class="nav-btn" style="margin:0;border-color:var(--acc-crit);color:var(--acc-crit);" onclick="closeHyperConsole()">ZAMKNIJ</button>
          </div>
        </div>
        <div class="hyperdeck-vnc-wrap"><div id="hyper-vnc-screen"><span style="color:#456;">NO SIGNAL</span></div></div>
        <div id="hyper-osk" class="hyperdeck-osk"></div>
      </section>
      <section id="hyper-modal" class="hyperdeck-modal">
        <div class="hyperdeck-modal-panel">
          <div class="hyperdeck-modal-head">
            <strong id="hyper-modal-title">VM OPS</strong>
            <button class="nav-btn" style="margin:0;border-color:var(--acc-crit);color:var(--acc-crit);" onclick="closeHyperModal()">ZAMKNIJ</button>
          </div>
          <div id="hyper-modal-body" class="hyperdeck-modal-body"></div>
        </div>
      </section>
    `;
    qs("content").appendChild(page);
  }

  function addNavButton() {
    if (window.nexusAddNavButton) {
      window.nexusAddNavButton({ id: "hyper_deck", label: "HYPER-DECK", cls: "nx-btn-purp", group: "ops" });
      return true;
    }
    return false;
  }

  function setHyperDeckTab(tab) {
    const key = ["vms", "forge", "iso", "drivers"].includes(tab) ? tab : "vms";
    ["vms", "forge", "iso", "drivers"].forEach(name => {
      qs(`hyper-tab-${name}`)?.classList.toggle("active", name === key);
      qs(`hyper-section-${name}`)?.classList.toggle("active", name === key);
    });
    localStorage.setItem("nexus_hyperdeck_tab", key);
    if (key === "vms") setTimeout(loadHyperDeck, 40);
    if (key === "forge") setTimeout(loadOsForge, 40);
    if (key === "iso") setTimeout(loadIsoVault, 40);
    if (key === "drivers") setTimeout(loadDriverVault, 40);
  }

  async function loadNoVnc() {
    if (noVncRfbClass) return noVncRfbClass;
    const mod = await import("https://esm.sh/@novnc/novnc@1.5.0/lib/rfb.js");
    noVncRfbClass = mod.default;
    return noVncRfbClass;
  }

  async function loadHyperDeck() {
    installPage();
    const grid = qs("hyper-vm-grid");
    const backendLabel = qs("hyper-backend");
    const message = qs("hyper-message");
    if (!grid) return;
    grid.innerHTML = `<div class="hyperdeck-card"><strong style="color:var(--acc-cyan);">SKANOWANIE HYPERVISORA...</strong></div>`;
    if (message) message.textContent = "Skanowanie hosta...";
    try {
      const data = await (await apiFetch("/api/vms/list")).json();
      currentBackend = data.backend || "auto";
      if (backendLabel) backendLabel.textContent = currentBackend;
      if (message) message.textContent = data.message || "OK";
      const items = data.items || [];
      hyperVmItems = items;
      if (!items.length) {
        grid.innerHTML = `<div class="hyperdeck-card stopped"><div class="hyperdeck-name">BRAK MASZYN</div><p style="color:#888;font-size:12px;">${esc(data.message || "Nie znaleziono VM na hoscie.")}</p></div>`;
        updateHyperVmSummary(items);
        return;
      }
      updateHyperVmSummary(items);
      renderHyperVmGrid();
    } catch (err) {
      if (message) message.textContent = "Blad skanowania VM.";
      hyperVmItems = [];
      updateHyperVmSummary([]);
      grid.innerHTML = `<div class="hyperdeck-card stopped"><div class="hyperdeck-name" style="color:var(--acc-crit);">BLAD VM API</div><p style="color:#888;font-size:12px;">Nie udalo sie pobrac listy maszyn.</p></div>`;
    }
  }

  function updateHyperVmSummary(items) {
    const el = qs("hyper-vm-summary");
    if (!el) return;
    const rows = items || [];
    const running = rows.filter(vm => String(vm.status || "").toLowerCase().includes("running")).length;
    el.textContent = `VM: ${rows.length} / ONLINE: ${running}`;
  }

  function renderHyperVmGrid() {
    const grid = qs("hyper-vm-grid");
    if (!grid) return;
    const filter = String(qs("hyper-vm-filter")?.value || "").toLowerCase().trim();
    const items = hyperVmItems.filter(vm => {
      const blob = `${vm.id || ""} ${vm.name || ""} ${vm.status || ""} ${vm.type || ""}`.toLowerCase();
      return !filter || blob.includes(filter);
    });
    grid.innerHTML = items.length ? items.map(renderVmCard).join("") : `<div class="hyperdeck-card stopped"><div class="hyperdeck-name">BRAK WYNIKOW</div><p style="color:#888;font-size:12px;">Filtr nie pasuje do zadnej VM.</p></div>`;
  }

  function renderVmCard(vm) {
    const status = String(vm.status || "unknown").toLowerCase();
    const running = status.includes("running") || status.includes("uruch") || status === "running";
    const id = encodeURIComponent(String(vm.id || ""));
    const backend = encodeURIComponent(String(currentBackend || "auto"));
    const cpu = vm.cpu_percent == null ? "--" : `${vm.cpu_percent}%`;
    const mem = vm.mem_mb == null ? (vm.used_mem || vm.configured_mem || vm.configured_mem_mb || "--") : `${vm.mem_mb} MB`;
    const disk = vm.bootdisk_gb ? `${vm.bootdisk_gb} GB` : "--";
    const cores = vm.vcpus || "--";
    return `
      <article class="hyperdeck-card ${running ? "running" : "stopped"}">
        <div class="hyperdeck-meta"><span>${esc(vm.type || currentBackend)}</span><span>ID: ${esc(vm.id)}</span></div>
        <div class="hyperdeck-name">${esc(vm.name || vm.id)}</div>
        <span class="hyperdeck-badge ${running ? "online" : "offline"}">${running ? "ONLINE" : "OFFLINE"} / ${esc(vm.status || "unknown")}</span>
        <div class="hyperdeck-telemetry">
          <div class="hyperdeck-tile"><span>CPU procesu</span><strong>${esc(cpu)}</strong></div>
          <div class="hyperdeck-tile"><span>RAM procesu</span><strong>${esc(mem)}</strong></div>
          <div class="hyperdeck-tile"><span>vCPU</span><strong>${esc(cores)}</strong></div>
          <div class="hyperdeck-tile"><span>Dysk boot</span><strong>${esc(disk)}</strong></div>
        </div>
        <div class="hyperdeck-actions">
          <button class="nav-btn" style="border-color:#0f0;color:#0f0;" onclick="hyperVmAction(decodeURIComponent('${id}'),'start')">POWER ON</button>
          <button class="nav-btn" style="border-color:#9cf;color:#9cf;" onclick="hyperCupertinoStart(decodeURIComponent('${id}'))">MAC START</button>
          <button class="nav-btn" style="border-color:var(--acc-warn);color:var(--acc-warn);" onclick="hyperVmAction(decodeURIComponent('${id}'),'shutdown')">ACPI SHUTDOWN</button>
          <button class="nav-btn" style="border-color:var(--acc-crit);color:var(--acc-crit);" onclick="hyperVmAction(decodeURIComponent('${id}'),'stop')">HARD RESET</button>
          <button class="nav-btn" style="border-color:var(--acc-purple);color:var(--acc-purple);" onclick="openHyperConsole(decodeURIComponent('${id}'), decodeURIComponent('${backend}'), '${esc(String(vm.name || vm.id)).replaceAll("'", "\\'")}')">OTWORZ KONSOLE</button>
          <button class="nav-btn" style="border-color:var(--acc-warn);color:var(--acc-warn);" onclick="openVmIsoPicker(decodeURIComponent('${id}'))">ISO / CD-ROM</button>
          <button class="nav-btn" style="border-color:var(--acc-cyan);color:var(--acc-cyan);" onclick="openVmSnapshots(decodeURIComponent('${id}'))">SNAPSHOT</button>
          <button class="nav-btn" style="border-color:#aaa;color:#ddd;" onclick="openVmConfig(decodeURIComponent('${id}'))">CONFIG</button>
          <button class="nav-btn" style="border-color:var(--acc-cyan);color:var(--acc-cyan);" onclick="openVmDoctor(decodeURIComponent('${id}'))">DOCTOR</button>
          <button class="nav-btn" style="border-color:var(--acc-warn);color:var(--acc-warn);" onclick="openVmLogs(decodeURIComponent('${id}'))">LOGI</button>
          <button class="nav-btn" style="border-color:#0f0;color:#0f0;" onclick="openVmPorts(decodeURIComponent('${id}'))">PORTY</button>
          <button class="nav-btn" style="border-color:var(--acc-purple);color:var(--acc-purple);" onclick="openVmGuestAgent(decodeURIComponent('${id}'))">AGENT</button>
          <button class="nav-btn" style="border-color:var(--acc-crit);color:var(--acc-crit);" onclick="deleteVmPrompt(decodeURIComponent('${id}'))">USUN VM</button>
        </div>
      </article>
    `;
  }

  async function hyperVmAction(vmId, action) {
    const label = action === "stop" ? "HARD RESET" : action.toUpperCase();
    let confirmText = "";
    if (action === "stop") {
      confirmText = prompt(`HARD RESET odcina zasilanie VM ${vmId}. Wpisz nazwe VM, aby potwierdzic:`, "");
      if (confirmText !== vmId) return notify("warn", "Akcja VM", "Potwierdzenie nie pasuje do nazwy VM.");
    } else if (action !== "start" && !confirm(`${label} VM ${vmId}?`)) {
      return;
    }
    try {
      const response = await apiFetch("/api/vms/action", { method: "POST", body: JSON.stringify({ vm_id: vmId, action, backend: currentBackend || "auto", confirm: confirmText }) });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data.detail || "Akcja VM nie powiodla sie");
      }
      const status = data.status || "success";
      const tone = status === "success" ? "ok" : "warn";
      notify(tone, "Akcja VM", `${vmId}: ${status.replaceAll("_", " ")} / ${label}.`, 3600);
      if (typeof window.verifyVmActionEffect === "function") window.verifyVmActionEffect(vmId, action);
      setTimeout(loadHyperDeck, 800);
    } catch (err) {
      notify("error", "Akcja VM", err.message || "Akcja VM nie powiodla sie.");
    }
  }

  async function hyperCupertinoStart(vmId) {
    const ok = confirm("NEXUS dostarcza wylacznie infrastrukture BYOL. Potwierdzam legalna licencje macOS i wlasny OpenCore.");
    if (!ok) return;
    const bootloader = prompt("Bootloader OpenCore qcow2:", "opencore.qcow2") || "opencore.qcow2";
    const isoPath = prompt("Opcjonalnie BaseSystem.iso / installer ISO path (puste = aktualny CD-ROM):", "") || "";
    try {
      notify("info", "Cupertino", `${vmId}: sprawdzam prerequisites...`);
      const data = await apiJson("/api/vms/start", {
        method: "POST",
        body: JSON.stringify({ vm_name: vmId, legal_byol_ack: true, bootloader, iso_path: isoPath })
      });
      notify("ok", "Cupertino", `${vmId}: ${data.status || "booting"}.`, 6000);
      setTimeout(loadHyperDeck, 900);
    } catch (err) {
      notify("error", "Cupertino", err.message || "Start macOS nie powiodl sie.");
    }
  }

  function openHyperModal(title, html) {
    installPage();
    const modal = qs("hyper-modal");
    const head = qs("hyper-modal-title");
    const body = qs("hyper-modal-body");
    if (head) head.textContent = title || "VM OPS";
    if (body) body.innerHTML = html || "";
    if (modal) modal.classList.add("active");
  }

  function closeHyperModal() {
    const modal = qs("hyper-modal");
    if (modal) modal.classList.remove("active");
  }

  async function apiJson(url, options) {
    const response = await apiFetch(url, options);
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(readableDetail(data) || `Operacja nie powiodla sie. HTTP ${response.status}`);
    return data;
  }

  async function verifySnapshotVisible(vmId, snapshot, shouldExist) {
    try {
      await new Promise(resolve => setTimeout(resolve, 500));
      const data = await apiJson(`/api/vms/snapshots?vm_id=${encodeURIComponent(vmId)}`, { silent: true });
      const exists = (data.items || []).some(item => item.name === snapshot);
      if (exists === shouldExist) {
        notify("ok", "Weryfikacja snapshotu", `${snapshot}: ${shouldExist ? "widoczny" : "usuniety"} w libvirt.`);
        return true;
      }
      notify("warn", "Weryfikacja snapshotu", `${snapshot}: backend przyjal akcje, ale lista snapshotow jeszcze jej nie potwierdza.`, 8000);
    } catch (err) {
      notify("warn", "Weryfikacja snapshotu", err.message || "Nie udalo sie sprawdzic snapshotu.", 8000);
    }
    return false;
  }

  async function verifyVmConfigValues(vmId, memoryMb, vcpus) {
    try {
      await new Promise(resolve => setTimeout(resolve, 500));
      const data = await apiJson(`/api/vms/config?vm_id=${encodeURIComponent(vmId)}`, { silent: true });
      const persistentRam = data.memory_config?.current_memory_mb || data.memory_config?.memory_mb || data.max_memory_mb || data.used_memory_mb || 0;
      const liveRam = data.used_memory_mb || "--";
      const ramOk = Math.abs(Number(persistentRam || 0) - Number(memoryMb)) <= 1;
      const cpuOk = String(data.vcpus) === String(vcpus);
      notify(ramOk && cpuOk ? "ok" : "warn", "Weryfikacja configu VM", `RAM persistent ${persistentRam || "--"} MB, live ${liveRam} MB, vCPU ${data.vcpus || "--"}.`);
    } catch (err) {
      notify("warn", "Weryfikacja configu VM", err.message || "Nie udalo sie sprawdzic configu.", 8000);
    }
  }

  async function verifyVmPortRule(id, shouldExist) {
    try {
      await new Promise(resolve => setTimeout(resolve, 400));
      const data = await apiJson("/api/vms/ports", { silent: true });
      const exists = (data.items || []).some(item => item.id === id);
      notify(exists === shouldExist ? "ok" : "warn", "Weryfikacja portu VM", exists === shouldExist ? "Regula NAT potwierdzona." : "Lista reguł jeszcze nie potwierdza zmiany.", 8000);
    } catch (err) {
      notify("warn", "Weryfikacja portu VM", err.message || "Nie udalo sie sprawdzic reguly NAT.", 8000);
    }
  }

  async function openVmSnapshots(vmId) {
    openHyperModal(`SNAPSHOT: ${vmId}`, `<div style="color:#888;">Ladowanie migawek...</div>`);
    try {
      const data = await apiJson(`/api/vms/snapshots?vm_id=${encodeURIComponent(vmId)}`);
      const items = data.items || [];
      const rows = items.length ? items.map(item => `
        <div class="hyperdeck-row">
          <div>
            <strong>${esc(item.name)}</strong>
            <small>${esc(item.creation_time || item.state || "")}</small>
          </div>
          <div style="display:flex;gap:6px;flex-wrap:wrap;">
            <button class="nav-btn" style="margin:0;padding:7px;border-color:var(--acc-warn);color:var(--acc-warn);" onclick="revertVmSnapshot('${esc(vmId)}','${esc(item.name)}')">PRZYWROC</button>
            <button class="nav-btn" style="margin:0;padding:7px;border-color:var(--acc-crit);color:var(--acc-crit);" onclick="deleteVmSnapshot('${esc(vmId)}','${esc(item.name)}')">USUN</button>
          </div>
        </div>
      `).join("") : `<div class="download-row">Brak migawek dla tej VM.</div>`;
      openHyperModal(`SNAPSHOT: ${vmId}`, `
        <div class="hyperdeck-form">
          <input id="vm-snapshot-name" class="cyber-input" placeholder="nazwa migawki, opcjonalnie">
          <input id="vm-snapshot-desc" class="cyber-input" placeholder="opis, opcjonalnie">
          <button class="nav-btn" style="margin:0;border-color:var(--acc-cyan);color:var(--acc-cyan);" onclick="createVmSnapshot('${esc(vmId)}')">ZROB SNAPSHOT</button>
        </div>
        <div style="display:grid;gap:8px;">${rows}</div>
      `);
    } catch (err) {
      openHyperModal(`SNAPSHOT: ${vmId}`, `<div style="color:var(--acc-crit);">${esc(err.message)}</div>`);
    }
  }

  async function createVmSnapshot(vmId) {
    const name = qs("vm-snapshot-name")?.value || "";
    const description = qs("vm-snapshot-desc")?.value || "";
    if (!confirm(`Zrobic snapshot VM ${vmId}?`)) return;
    try {
      const data = await apiJson("/api/vms/snapshots/create", { method: "POST", body: JSON.stringify({ vm_id: vmId, name, description }) });
      await verifySnapshotVisible(vmId, data.snapshot || name, true);
      await openVmSnapshots(vmId);
    } catch (err) {
      notify("error", "Snapshot VM", err.message || "Snapshot nie powiodl sie.");
    }
  }

  async function revertVmSnapshot(vmId, snapshot) {
    const confirmText = prompt(`Przywrocenie cofnie stan VM ${vmId} do snapshotu ${snapshot}. Wpisz nazwe VM:`, "");
    if (confirmText !== vmId) return notify("warn", "Revert snapshotu", "Potwierdzenie nie pasuje do nazwy VM.");
    try {
      await apiJson("/api/vms/snapshots/revert", { method: "POST", body: JSON.stringify({ vm_id: vmId, snapshot, confirm: confirmText }) });
      notify("ok", "Weryfikacja snapshotu", `${snapshot}: polecenie przywrocenia przyjete przez libvirt.`);
      await openVmSnapshots(vmId);
      setTimeout(loadHyperDeck, 800);
    } catch (err) {
      notify("error", "Revert snapshotu", err.message || "Revert nie powiodl sie.");
    }
  }

  async function deleteVmSnapshot(vmId, snapshot) {
    const confirmText = prompt(`Usunac snapshot ${snapshot}? Wpisz nazwe snapshotu:`, "");
    if (confirmText !== snapshot) return notify("warn", "Snapshot VM", "Potwierdzenie nie pasuje do nazwy snapshotu.");
    try {
      await apiJson("/api/vms/snapshots/delete", { method: "POST", body: JSON.stringify({ vm_id: vmId, snapshot, confirm: confirmText }) });
      await verifySnapshotVisible(vmId, snapshot, false);
      await openVmSnapshots(vmId);
    } catch (err) {
      notify("error", "Snapshot VM", err.message || "Usuniecie snapshotu nie powiodlo sie.");
    }
  }

  async function openVmConfig(vmId) {
    openHyperModal(`CONFIG: ${vmId}`, `<div style="color:#888;">Pobieram konfiguracje...</div>`);
    try {
      const [data, isoData] = await Promise.all([
        apiJson(`/api/vms/config?vm_id=${encodeURIComponent(vmId)}`),
        apiJson("/api/vms/iso/list").catch(() => ({ items: [] })),
      ]);
      const memory = data.used_memory_mb || data.max_memory_mb || 1024;
      const vcpus = data.vcpus || 1;
      const persistentRam = data.memory_config?.current_memory_mb || data.max_memory_mb || memory;
      const maxRamSlider = Math.max(8192, Number(memory || 0), Number(persistentRam || 0), Number(data.memory_config?.memory_mb || 0), 262144);
      const cdromItems = isoData.cdrom_items || (isoData.items || []).filter(item => item.cdrom_attachable || String(item.kind || "").toLowerCase() === "iso");
      const vmDiskItems = isoData.disk_items || (isoData.items || []).filter(item => item.disk_attachable || ["qcow2", "raw", "img"].includes(String(item.kind || "").toLowerCase()));
      const isoOptions = cdromItems.map(item => `<option value="${esc(item.path)}">${esc(item.name)} / ${esc(item.size_label || "")}</option>`).join("");
      const diskOptions = vmDiskItems.map(item => `<option value="${esc(item.path)}">${esc(item.name)} / ${esc(item.size_label || "")}</option>`).join("");
      const cdroms = (data.cdroms || []).map(row => `${row.target}: ${row.source || "pusty"}`).join("\\n") || "--";
      const cdromTargetOptions = [`<option value="">AUTO: slot boot CD-ROM</option>`]
        .concat((data.cdroms || []).map(row => `<option value="${esc(row.target || "")}">${esc(row.target || "--")} / ${esc(row.source || "pusty")}</option>`))
        .join("");
      const interfaces = (data.interfaces || []).map(row => `${row.mac} ${row.model} ${row.source}`).join("\\n") || "--";
      const internetOn = (data.interfaces || []).length > 0;
      const maxVcpus = data.vcpu_counts?.maximum_config || data.vcpus || 1;
      openHyperModal(`CONFIG: ${vmId}`, `
        <div class="hyperdeck-form">
          <label style="color:#bbb;font-size:11px;">RAM MB <b id="vm-config-memory-label" style="color:var(--acc-cyan);">${esc(memory)}</b></label>
          <input id="vm-config-memory-range" class="cyber-input" type="range" min="128" max="${esc(maxRamSlider)}" step="128" value="${esc(memory)}" oninput="document.getElementById('vm-config-memory').value=this.value;document.getElementById('vm-config-memory-label').textContent=this.value">
          <input id="vm-config-memory" class="cyber-input" type="number" min="128" step="128" value="${esc(memory)}" placeholder="RAM MB" oninput="document.getElementById('vm-config-memory-range').value=this.value;document.getElementById('vm-config-memory-label').textContent=this.value">
          <label style="color:#bbb;font-size:11px;">vCPU <b id="vm-config-vcpus-label" style="color:var(--acc-cyan);">${esc(vcpus)}</b></label>
          <input id="vm-config-vcpus-range" class="cyber-input" type="range" min="1" max="8" step="1" value="${esc(vcpus)}" oninput="document.getElementById('vm-config-vcpus').value=this.value;document.getElementById('vm-config-vcpus-label').textContent=this.value">
          <input id="vm-config-vcpus" class="cyber-input" type="number" min="1" step="1" value="${esc(vcpus)}" placeholder="vCPU" oninput="document.getElementById('vm-config-vcpus-range').value=this.value;document.getElementById('vm-config-vcpus-label').textContent=this.value">
          <label style="display:flex;gap:8px;align-items:center;color:#bbb;font-size:11px;"><input id="vm-config-live" type="checkbox" checked> Zastosuj live, jesli VM dziala</label>
          <button class="nav-btn" style="margin:0;border-color:#0f0;color:#0f0;" onclick="saveVmConfig('${esc(vmId)}')">ZAPISZ CONFIG</button>
        </div>
        <div class="hyperdeck-form" style="margin-top:10px;border-left:3px solid var(--acc-warn);padding-left:10px;">
          <div class="forge-wide" style="color:var(--acc-warn);font-size:11px;font-weight:bold;">ISO / CD-ROM - tylko pliki .iso, zapisywane permanentnie osobno od dysku</div>
          <select id="vm-iso-select" class="cyber-input">${isoOptions || '<option value="">Brak ISO w vault</option>'}</select>
          <select id="vm-iso-target" class="cyber-input">${cdromTargetOptions}</select>
          <label style="display:flex;gap:8px;align-items:center;color:#bbb;font-size:11px;"><input id="vm-iso-live" type="checkbox" checked> LIVE jesli VM dziala</label>
          <label style="display:flex;gap:8px;align-items:center;color:#bbb;font-size:11px;"><input id="vm-iso-config" type="checkbox" checked> PERSISTENT po resecie</label>
          <label style="display:flex;gap:8px;align-items:center;color:#bbb;font-size:11px;"><input id="vm-iso-force" type="checkbox" checked> FORCE EJECT/INSERT</label>
          <button class="nav-btn" style="margin:0;border-color:var(--acc-warn);color:var(--acc-warn);" onclick="attachVmIso('${esc(vmId)}')">PODMIEN / DODAJ ISO</button>
        </div>
        <div class="hyperdeck-form" style="margin-top:10px;border-left:3px solid var(--acc-cyan);padding-left:10px;">
          <div class="forge-wide" style="color:var(--acc-cyan);font-size:11px;font-weight:bold;">DODATKOWY DYSK - .qcow2/.raw/.img, nigdy jako CD-ROM</div>
          <select id="vm-disk-select" class="cyber-input">${diskOptions || '<option value="">Brak plikow dyskow w vault</option>'}</select>
          <select id="vm-disk-bus" class="cyber-input">
            <option value="ide">IDE / legacy</option>
            <option value="sata">SATA</option>
            <option value="virtio">VirtIO</option>
            <option value="scsi">SCSI</option>
            <option value="usb">USB disk</option>
          </select>
          <input id="vm-disk-target" class="cyber-input" placeholder="target opcj. np. hdb/vdb">
          <label style="display:flex;gap:8px;align-items:center;color:#bbb;font-size:11px;"><input id="vm-disk-readonly" type="checkbox"> READONLY</label>
          <label style="display:flex;gap:8px;align-items:center;color:#bbb;font-size:11px;"><input id="vm-disk-live" type="checkbox" checked> LIVE</label>
          <label style="display:flex;gap:8px;align-items:center;color:#bbb;font-size:11px;"><input id="vm-disk-config" type="checkbox" checked> PERSISTENT</label>
          <button class="nav-btn" style="margin:0;border-color:var(--acc-cyan);color:var(--acc-cyan);" onclick="attachVmDisk('${esc(vmId)}')">PODPNIJ DYSK</button>
        </div>
        <div class="hyperdeck-form" style="margin-top:10px;border-left:3px solid #0f0;padding-left:10px;">
          <div class="forge-wide" style="color:#0f0;font-size:11px;font-weight:bold;">THIN STORAGE - qcow2 rośnie dynamicznie, TRIM/UNMAP odzyskuje miejsce po usuniętych plikach</div>
          <button class="nav-btn" style="margin:0;border-color:#0f0;color:#0f0;" onclick="openVmThinStatus('${esc(vmId)}')">THIN STATUS</button>
          <button class="nav-btn" style="margin:0;border-color:var(--acc-cyan);color:var(--acc-cyan);" onclick="applyVmThinPolicy('${esc(vmId)}')">APPLY THIN</button>
          <button class="nav-btn" style="margin:0;border-color:var(--acc-warn);color:var(--acc-warn);" onclick="openVmCompactPlan('${esc(vmId)}')">COMPACT PLAN</button>
          <span class="proc-pill">Linux: fstrim -av / Windows: ReTrim</span>
        </div>
        <div class="hyperdeck-form" style="margin-top:10px;">
          <button class="nav-btn" style="margin:0;border-color:#0f0;color:#0f0;" onclick="setVmInternet('${esc(vmId)}',true)">INTERNET ON</button>
          <button class="nav-btn" style="margin:0;border-color:var(--acc-cyan);color:var(--acc-cyan);" onclick="setVmInternet('${esc(vmId)}',true,'pcnet')">LEGACY NET PCNET</button>
          <button class="nav-btn" style="margin:0;border-color:var(--acc-cyan);color:var(--acc-cyan);" onclick="setVmInternet('${esc(vmId)}',true,'rtl8139')">LEGACY NET RTL8139</button>
          <button class="nav-btn" style="margin:0;border-color:var(--acc-crit);color:var(--acc-crit);" onclick="setVmInternet('${esc(vmId)}',false)">INTERNET OFF</button>
          <span class="proc-pill">Aktualnie: <b style="color:${internetOn ? "#0f0" : "var(--acc-warn)"}">${internetOn ? "ON" : "OFF"}</b></span>
        </div>
        <div class="hyperdeck-form" style="margin-top:10px;">
          <button class="nav-btn" style="margin:0;border-color:var(--acc-warn);color:var(--acc-warn);" onclick="applyVmCompatProfile('${esc(vmId)}','win95')">WIN95 NDIS FIX</button>
          <button class="nav-btn" style="margin:0;border-color:var(--acc-warn);color:var(--acc-warn);" onclick="applyVmCompatProfile('${esc(vmId)}','win98')">WIN98 SAFE FIX</button>
          <button class="nav-btn" style="margin:0;border-color:var(--acc-cyan);color:var(--acc-cyan);" onclick="applyVmCompatProfile('${esc(vmId)}','winxp')">XP IDE/e1000 FIX</button>
          <button class="nav-btn" style="margin:0;border-color:var(--acc-cyan);color:var(--acc-cyan);" onclick="applyVmCompatProfile('${esc(vmId)}','reactos')">REACTOS FIX</button>
          <button class="nav-btn" style="margin:0;border-color:var(--acc-crit);color:var(--acc-crit);" onclick="repairVmMedia('${esc(vmId)}')">NAPRAW MEDIA</button>
          <button class="nav-btn" style="margin:0;border-color:#fff;color:#fff;" onclick="openVmDoctor('${esc(vmId)}')">VM DOCTOR</button>
          <span class="proc-pill">Latki restartuja VM i zapisuja XML na stale</span>
        </div>
        <div class="hyperdeck-log" style="min-height:160px;color:#bbb;">Stan: ${esc(data.state || "--")}\nMax RAM live: ${esc(data.max_memory || "--")}\nUsed RAM live: ${esc(data.used_memory || "--")}\nRAM persistent: ${esc(persistentRam)} MB\nvCPU: ${esc(data.vcpus || "--")} / max config: ${esc(maxVcpus)}\nCDROM:\n${esc(cdroms)}\nSiec:\n${esc(interfaces)}\nStorage:\n${esc((data.storage || []).join("\\n") || "--")}</div>
      `);
    } catch (err) {
      openHyperModal(`CONFIG: ${vmId}`, `<div style="color:var(--acc-crit);">${esc(err.message)}</div>`);
    }
  }

  async function saveVmConfig(vmId) {
    const memory_mb = Number(qs("vm-config-memory")?.value || 0);
    const vcpus = Number(qs("vm-config-vcpus")?.value || 0);
    const live = !!qs("vm-config-live")?.checked;
    if (!memory_mb || !vcpus) return notify("warn", "Konfiguracja VM", "Podaj RAM i vCPU.");
    try {
      const data = await apiJson("/api/vms/config", { method: "POST", body: JSON.stringify({ vm_id: vmId, memory_mb, vcpus, live }) });
      const memory = data.memory || {};
      const tone = memory.requires_restart || data.status === "warning" || (data.warnings || []).length ? "warn" : "ok";
      const ramLine = memory.message || "RAM/vCPU zapisane.";
      const restartLine = memory.requires_restart ? ` Target RAM: ${memory.target_memory_mb} MB (wymaga restartu).` : "";
      const warningLine = (data.warnings || []).length ? ` ${data.warnings.join(" | ")}` : "";
      notify(tone, "Konfiguracja VM", `${ramLine}${restartLine}${warningLine}`, 10000);
      await verifyVmConfigValues(vmId, memory_mb, vcpus);
      await openVmConfig(vmId);
      setTimeout(loadHyperDeck, 700);
      if (typeof window.loadVMs === "function") setTimeout(window.loadVMs, 800);
    } catch (err) {
      notify("error", "Konfiguracja VM", err.message || "Zapis konfiguracji nie powiodl sie.");
    }
  }

  async function attachVmIso(vmId) {
    const iso_path = qs("vm-iso-select")?.value || "";
    if (!iso_path) return notify("warn", "ISO VM", "Wybierz ISO z listy.");
    if (!/\.iso$/i.test(iso_path)) return notify("warn", "ISO VM", "Do CD-ROM mozna podpiac tylko plik .iso. Dyski .qcow2/.raw/.img sa w osobnej sekcji.");
    const target = qs("vm-iso-target")?.value || "";
    const force = !!qs("vm-iso-force")?.checked;
    const live = !!qs("vm-iso-live")?.checked;
    const config = !!qs("vm-iso-config")?.checked;
    try {
      const data = await apiJson("/api/vms/iso/attach", { method: "POST", body: JSON.stringify({ vm_id: vmId, iso_path, target, force, live, config }) });
      const verify = (data.verify_cdroms || []).map(row => `${row.target}:${row.source || "pusty"}`).join(" | ");
      const warnings = data.validation?.warnings || [];
      const firmware = data.firmware?.firmware ? ` Firmware VM: ${data.firmware.firmware}.` : "";
      const warningLine = warnings.length ? ` UWAGA: ${warnings.slice(0, 3).join(" | ")}` : "";
      notify(warnings.length ? "warn" : "ok", "ISO VM", `${data.mode || "attach"} ${data.target || ""}: ISO zapisane${config ? " trwale" : ""}.${firmware} ${verify ? "CD-ROM: " + verify : ""}${warningLine}`, warnings.length ? 14000 : 8000);
      await openVmConfig(vmId);
    } catch (err) {
      notify("error", "ISO VM", err.message || "Podpiecie ISO nie powiodlo sie.");
    }
  }

  async function openVmIsoPicker(vmId = "") {
    vmId = vmId || lastConsole.vmId;
    if (!vmId) return notify("warn", "ISO VM", "Brak aktywnej konsoli VM.");
    openHyperModal(`ISO / CD-ROM: ${vmId}`, `<div style="color:#888;">Pobieram ISO Vault i sloty CD-ROM...</div>`);
    try {
      const [isoData, config, media] = await Promise.all([
        apiJson("/api/vms/iso/list"),
        apiJson(`/api/vms/config?vm_id=${encodeURIComponent(vmId)}`),
        apiJson(`/api/vms/media/status?vm_id=${encodeURIComponent(vmId)}`).catch(() => ({ cdrom_analysis: [], firmware: {} }))
      ]);
      const cdromItems = isoData.cdrom_items || (isoData.items || []).filter(item => item.cdrom_attachable || String(item.kind || "").toLowerCase() === "iso");
      const isoOptions = cdromItems.map(item => `<option value="${esc(item.path)}">${esc(item.name)} / ${esc(item.size_label || "")}</option>`).join("");
      const vmDiskItems = isoData.disk_items || (isoData.items || []).filter(item => item.disk_attachable || ["qcow2", "raw", "img"].includes(String(item.kind || "").toLowerCase()));
      const openCoreItems = openCoreItemsFrom(vmDiskItems);
      const openCoreOptions = openCoreItems.map(item => `<option value="${esc(item.path)}">${esc(item.name)} / ${esc(item.size_label || "")}</option>`).join("");
      const targetOptions = [`<option value="">AUTO: slot boot CD-ROM</option>`]
        .concat((config.cdroms || []).map(row => `<option value="${esc(row.target || "")}">${esc(row.target || "--")} / ${esc(row.source || "pusty")}</option>`))
        .join("");
      const cdroms = (config.cdroms || []).map(row => `${row.target}: ${row.source || "pusty"}`).join("\\n") || "--";
      const mediaWarnings = (media.cdrom_analysis || [])
        .map(row => {
          const boot = row.validation?.boot_profile || {};
          const tags = [
            boot.bios_boot_hint ? "BIOS-BOOT" : "",
            boot.uefi_boot_hint ? "UEFI-BOOT" : "",
            boot.apple_hint ? "APPLE/MACOS" : "",
          ].filter(Boolean).join(", ") || "NO-BOOT-HINT";
          const warn = (row.warnings || []).slice(0, 3).join(" | ");
          return `${row.target || "--"}: ${tags}${warn ? " / " + warn : ""}`;
        }).join("\\n") || "Brak analizy boot dla CD-ROM.";
      openHyperModal(`ISO / CD-ROM: ${vmId}`, `
        <div class="hyperdeck-form">
          <select id="console-iso-select" class="cyber-input">${isoOptions || '<option value="">Brak plikow .iso w vault</option>'}</select>
          <select id="console-iso-target" class="cyber-input">${targetOptions}</select>
          <label style="display:flex;gap:8px;align-items:center;color:#bbb;font-size:11px;"><input id="console-iso-live" type="checkbox" checked> LIVE</label>
          <label style="display:flex;gap:8px;align-items:center;color:#bbb;font-size:11px;"><input id="console-iso-config" type="checkbox" checked> PERSISTENT</label>
          <label style="display:flex;gap:8px;align-items:center;color:#bbb;font-size:11px;"><input id="console-iso-force" type="checkbox" checked> FORCE EJECT/INSERT</label>
          <button class="nav-btn" style="margin:0;border-color:var(--acc-warn);color:var(--acc-warn);" onclick="attachConsoleIso('${esc(vmId)}')">PODMIEN ISO TERAZ</button>
          <button class="nav-btn" style="margin:0;border-color:var(--acc-crit);color:var(--acc-crit);" onclick="ejectConsoleIso('${esc(vmId)}')">WYSUN ISO</button>
          <button class="nav-btn" style="margin:0;border-color:var(--acc-cyan);color:var(--acc-cyan);" onclick="repairConsoleMedia('${esc(vmId)}')">NAPRAW CD-ROM</button>
          <button class="nav-btn" style="margin:0;border-color:var(--acc-cyan);color:var(--acc-cyan);" onclick="openVmConfig('${esc(vmId)}')">PELNY CONFIG</button>
        </div>
        <div class="hyperdeck-form" style="margin-top:10px;border-top:1px solid #263238;padding-top:10px;">
          <div class="forge-wide" style="color:var(--acc-warn);font-size:11px;font-weight:bold;">OPENCORE / CUPERTINO - bootloader .qcow2, nie CD-ROM</div>
          <select id="console-opencore-select" class="cyber-input">${openCoreOptions || '<option value="">Brak OpenCore .qcow2 w vault</option>'}</select>
          <input id="console-opencore-manual" class="cyber-input" placeholder="albo wpisz recznie: opencore.qcow2">
          <button class="nav-btn" style="margin:0;border-color:var(--acc-warn);color:var(--acc-warn);" onclick="startConsoleCupertino('${esc(vmId)}')">START Z OPENCORE</button>
          <button class="nav-btn" style="margin:0;border-color:var(--acc-cyan);color:var(--acc-cyan);" onclick="copyConsoleOpenCoreToForge()">KOPIUJ DO OS FORGE</button>
        </div>
        <pre class="hyperdeck-log" style="min-height:140px;">AKTUALNE CD-ROM:
${esc(cdroms)}

FIRMWARE VM: ${esc(media.firmware?.firmware || "--")}
ANALIZA BOOT:
${esc(mediaWarnings)}

Uwaga: tutaj podpinasz tylko .iso. Dyski .qcow2/.raw/.img sa w VM CONFIG jako DODATKOWY DYSK.</pre>
      `);
    } catch (err) {
      openHyperModal(`ISO / CD-ROM: ${vmId}`, `<div style="color:var(--acc-crit);">${esc(err.message || "Nie udalo sie pobrac ISO.")}</div>`);
    }
  }

  async function openConsoleIsoPicker() {
    return openVmIsoPicker(lastConsole.vmId);
  }

  async function attachConsoleIso(vmId) {
    const iso_path = qs("console-iso-select")?.value || "";
    if (!iso_path) return notify("warn", "ISO VM", "Wybierz ISO.");
    const target = qs("console-iso-target")?.value || "";
    const live = !!qs("console-iso-live")?.checked;
    const config = !!qs("console-iso-config")?.checked;
    const force = !!qs("console-iso-force")?.checked;
    try {
      const data = await apiJson("/api/vms/iso/attach", { method: "POST", body: JSON.stringify({ vm_id: vmId, iso_path, target, live, config, force }) });
      const verify = (data.verify_cdroms || []).map(row => `${row.target}:${row.source || "pusty"}`).join(" | ");
      const warnings = data.validation?.warnings || [];
      const firmware = data.firmware?.firmware ? ` Firmware VM: ${data.firmware.firmware}.` : "";
      const warningLine = warnings.length ? ` UWAGA: ${warnings.slice(0, 3).join(" | ")}` : "";
      notify(warnings.length ? "warn" : "ok", "ISO VM", `${data.target || "AUTO"}: podmieniono ISO.${firmware} ${verify ? "CD-ROM: " + verify : ""}${warningLine}`, warnings.length ? 14000 : 8000);
      await openConsoleIsoPicker();
    } catch (err) {
      notify("error", "ISO VM", err.message || "Podmiana ISO nie powiodla sie.", 9000);
    }
  }

  function selectedConsoleOpenCore() {
    return qs("console-opencore-manual")?.value || qs("console-opencore-select")?.value || "opencore.qcow2";
  }

  function copyConsoleOpenCoreToForge() {
    const value = selectedConsoleOpenCore();
    const forgeInput = qs("forge-opencore");
    if (forgeInput) forgeInput.value = value;
    notify("ok", "OpenCore", `Skopiowano do OS Forge: ${value}`, 5000);
  }

  async function startConsoleCupertino(vmId) {
    const bootloader = selectedConsoleOpenCore();
    const isoPath = qs("console-iso-select")?.value || "";
    if (!bootloader) return notify("warn", "OpenCore", "Wybierz OpenCore .qcow2 albo wpisz sciezke recznie.");
    const ok = confirm("Cupertino Legal Shield: potwierdz BYOL. NEXUS nie dostarcza licencji, OSK ani chronionych komponentow Apple.");
    if (!ok) return;
    try {
      notify("info", "Cupertino", `${vmId}: start z OpenCore ${bootloader}...`, 7000);
      const data = await apiJson("/api/vms/start", {
        method: "POST",
        body: JSON.stringify({ vm_name: vmId, legal_byol_ack: true, bootloader, iso_path: isoPath })
      });
      notify("ok", "Cupertino", `${vmId}: ${data.status || "booting"}.`, 8000);
      await openConsoleIsoPicker();
      setTimeout(loadHyperDeck, 900);
    } catch (err) {
      notify("error", "Cupertino", err.message || "Start z OpenCore nie powiodl sie.", 12000);
    }
  }

  async function ejectConsoleIso(vmId) {
    const target = qs("console-iso-target")?.value || "";
    const live = !!qs("console-iso-live")?.checked;
    const config = !!qs("console-iso-config")?.checked;
    const force = !!qs("console-iso-force")?.checked;
    if (!target && !confirm(`Wysunac ISO ze wszystkich napedow CD-ROM w VM ${vmId}?`)) return;
    try {
      const data = await apiJson("/api/vms/iso/eject", { method: "POST", body: JSON.stringify({ vm_id: vmId, target, live, config, force }) });
      const verify = (data.verify_cdroms || []).map(row => `${row.target}:${row.source || "pusty"}`).join(" | ");
      notify("ok", "ISO VM", `${target || "ALL"}: wysunieto ISO. ${verify ? "CD-ROM: " + verify : ""}`, 8000);
      await openVmIsoPicker(vmId);
    } catch (err) {
      notify("error", "ISO VM", err.message || "Wysuniecie ISO nie powiodlo sie.", 9000);
    }
  }

  async function repairConsoleMedia(vmId) {
    if (!vmId) return notify("warn", "ISO VM", "Brak aktywnej VM.");
    const live = !!qs("console-iso-live")?.checked;
    const config = !!qs("console-iso-config")?.checked;
    try {
      const data = await apiJson("/api/vms/media/repair", { method: "POST", body: JSON.stringify({ vm_id: vmId, live, config }) });
      const cdroms = (data.media?.cdroms || data.media?.config_cdroms || []).map(row => `${row.target}:${row.source || "pusty"}`).join(" | ");
      notify("ok", "ISO VM", `CD-ROM sprawdzony. ${cdroms ? "Sloty: " + cdroms : "Brak slotow w raporcie."}`, 8000);
      await openVmIsoPicker(vmId);
    } catch (err) {
      notify("error", "ISO VM", err.message || "Naprawa CD-ROM nie powiodla sie.", 9000);
    }
  }

  async function attachVmDisk(vmId) {
    const disk_path = qs("vm-disk-select")?.value || "";
    if (!disk_path) return notify("warn", "Dysk VM", "Wybierz plik dysku z listy.");
    if (!/\.(qcow2|raw|img)$/i.test(disk_path)) return notify("warn", "Dysk VM", "Tu podpinasz tylko .qcow2/.raw/.img. ISO zostaje w sekcji CD-ROM.");
    const bus = qs("vm-disk-bus")?.value || "ide";
    const target = qs("vm-disk-target")?.value || "";
    const readonly = !!qs("vm-disk-readonly")?.checked;
    const live = !!qs("vm-disk-live")?.checked;
    const config = !!qs("vm-disk-config")?.checked;
    try {
      const data = await apiJson("/api/vms/disk/attach", { method: "POST", body: JSON.stringify({ vm_id: vmId, disk_path, bus, target, readonly, live, config }) });
      notify("ok", "Dysk VM", `${data.target || ""} / ${data.bus || bus}: dysk podpiety${config ? " permanentnie" : ""}.`);
      await openVmConfig(vmId);
      setTimeout(loadHyperDeck, 700);
    } catch (err) {
      notify("error", "Dysk VM", err.message || "Podpiecie dysku nie powiodlo sie.");
    }
  }

  function renderThinRows(data) {
    const rows = data.disks || [];
    if (!rows.length) return `<div class="download-row">Brak dyskow VM do sprawdzenia.</div>`;
    return rows.map(row => {
      const trim = row.trim || {};
      const trimOk = trim.trim_enabled ? "#0f0" : "var(--acc-warn)";
      return `
        <div class="download-row">
          <strong>${esc(row.name || row.path)}</strong>
          <small>${esc(row.path || "")}</small>
          <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:8px;margin-top:8px;">
            <span class="proc-pill">virtual: ${esc(row.virtual_size_label || "--")}</span>
            <span class="proc-pill">real: ${esc(row.actual_size_label || row.file_size_label || "--")}</span>
            <span class="proc-pill">used: ${row.thin_ratio === null || row.thin_ratio === undefined ? "--" : esc(row.thin_ratio) + "%"}</span>
            <span class="proc-pill" style="border-color:${trimOk};color:${trimOk};">TRIM: ${trim.trim_enabled ? "ON" : "CHECK"}</span>
            <span class="proc-pill">bus: ${esc(trim.bus || "--")} / ${esc(trim.target || "--")}</span>
          </div>
        </div>
      `;
    }).join("");
  }

  async function openVmThinStatus(vmId) {
    openHyperModal(`THIN STORAGE: ${vmId}`, `<div style="color:#888;">Sprawdzam qemu-img i XML discard/unmap...</div>`);
    try {
      const data = await apiJson(`/api/vms/storage/thin?vm_id=${encodeURIComponent(vmId)}`);
      openHyperModal(`THIN STORAGE: ${vmId}`, `
        <div style="display:grid;gap:8px;">${renderThinRows(data)}</div>
        <pre class="hyperdeck-log" style="min-height:130px;">${esc(data.policy || "")}

${esc(data.guest_trim?.linux || "")}
${esc(data.guest_trim?.windows || "")}</pre>
      `);
    } catch (err) {
      openHyperModal(`THIN STORAGE: ${vmId}`, `<div style="color:var(--acc-crit);">${esc(err.message || "Nie udalo sie sprawdzic dysku.")}</div>`);
    }
  }

  async function applyVmThinPolicy(vmId) {
    try {
      const data = await apiJson("/api/vms/storage/thin/apply", { method: "POST", body: JSON.stringify({ vm_id: vmId }) });
      const changed = (data.changed || []).length;
      notify("ok", "Thin Storage", `${vmId}: zaktualizowano ${changed} dyskow. ${data.requires_restart ? "Restart VM aktywuje live runtime." : "Polityka aktywna."}`, 9000);
      await openVmThinStatus(vmId);
    } catch (err) {
      notify("error", "Thin Storage", err.message || "Nie udalo sie zastosowac thin policy.", 10000);
    }
  }

  async function openVmCompactPlan(vmId) {
    openHyperModal(`COMPACT PLAN: ${vmId}`, `<div style="color:#888;">Buduje bezpieczny plan odzyskiwania miejsca...</div>`);
    try {
      const data = await apiJson("/api/vms/storage/compact", { method: "POST", body: JSON.stringify({ vm_id: vmId, dry_run: true }) });
      openHyperModal(`COMPACT PLAN: ${vmId}`, `
        <div class="hyperdeck-form">
          <div class="hyperdeck-tile"><span>Można wykonać</span><strong style="color:${data.can_execute ? "#0f0" : "var(--acc-warn)"}">${data.can_execute ? "TAK" : "NIE"}</strong></div>
          <div class="hyperdeck-tile"><span>Realnie teraz</span><strong>${esc(data.before?.actual_size_label || "--")}</strong></div>
          <div class="hyperdeck-tile"><span>Wirtualnie</span><strong>${esc(data.before?.virtual_size_label || "--")}</strong></div>
        </div>
        <pre class="hyperdeck-log" style="min-height:220px;">SOURCE: ${esc(data.source)}
OUTPUT: ${esc(data.output)}

1. W gosciu Linux: ${esc((data.commands?.guest_linux || []).join(" "))}
2. W gosciu Windows PowerShell: ${esc((data.commands?.guest_windows || []).join(" "))}
3. Host stopped copy: ${esc((data.commands?.host_stopped_copy || []).join(" "))}
4. Host stopped inplace: ${esc((data.commands?.host_stopped_inplace || []).join(" "))}

${esc(data.warning || "")}
RUNNING OWNERS: ${esc(readableDetail(data.running_owners || []))}</pre>
        <button class="nav-btn" style="margin:0;border-color:var(--acc-crit);color:var(--acc-crit);" onclick="executeVmCompact('${esc(vmId)}')">WYKONAJ IN-PLACE PO WYŁĄCZENIU VM</button>
      `);
    } catch (err) {
      openHyperModal(`COMPACT PLAN: ${vmId}`, `<div style="color:var(--acc-crit);">${esc(err.message || "Nie udalo sie zbudowac planu.")}</div>`);
    }
  }

  async function executeVmCompact(vmId) {
    const confirmText = prompt(`Kompaktowanie qcow2 wymaga wylaczonej VM ${vmId}. Wpisz COMPACT-QCOW2:`, "");
    if (confirmText !== "COMPACT-QCOW2") return notify("warn", "Thin Storage", "Anulowano compact.");
    try {
      const data = await apiJson("/api/vms/storage/compact", { method: "POST", body: JSON.stringify({ vm_id: vmId, dry_run: false, confirm: confirmText }) });
      notify("ok", "Thin Storage", `${data.source}: ${data.before?.actual_size_label || "--"} -> ${data.after?.actual_size_label || "--"}`, 9000);
      await openVmThinStatus(vmId);
    } catch (err) {
      notify("error", "Thin Storage", err.message || "Kompaktowanie nie powiodlo sie.", 10000);
    }
  }

  async function setVmInternet(vmId, enabled, model = "virtio") {
    try {
      await apiJson("/api/vms/network", { method: "POST", body: JSON.stringify({ vm_id: vmId, enabled, network: "default", model, live: true, config: true }) });
      notify("ok", "Internet VM", enabled ? `Internet podpiety live/config (${model}).` : "Internet odpiety live/config.");
      await openVmConfig(vmId);
      setTimeout(loadHyperDeck, 700);
      if (typeof window.loadVMs === "function") setTimeout(window.loadVMs, 800);
    } catch (err) {
      notify("error", "Internet VM", err.message || "Zmiana internetu nie powiodla sie.");
    }
  }

  async function applyVmCompatProfile(vmId, profile) {
    const label = String(profile || "").toUpperCase();
    const network = ["win95", "win98", "freedos"].includes(profile) ? "off" : "safe";
    if (!confirm(`Zastosowac latke ${label} dla VM ${vmId}? VM zostanie zrestartowana, konfiguracja XML zapisze sie na stale.`)) return;
    try {
      const data = await apiJson("/api/vms/compat/apply", { method: "POST", body: JSON.stringify({ vm_id: vmId, profile, restart: true, network }) });
      notify("ok", "Latka VM", `${data.label || label}: RAM ${data.memory_mb} MB, CPU ${data.cpu}, siec ${data.network?.mode || network}.`, 9000);
      await openVmConfig(vmId);
      setTimeout(loadHyperDeck, 1000);
      if (typeof window.loadVMs === "function") setTimeout(window.loadVMs, 1200);
    } catch (err) {
      notify("error", "Latka VM", err.message || "Nie udalo sie zastosowac latki kompatybilnosci.", 10000);
    }
  }

  function doctorSeverityStyle(severity) {
    if (severity === "critical") return "border-color:var(--acc-crit);color:var(--acc-crit);";
    if (severity === "warn") return "border-color:var(--acc-warn);color:var(--acc-warn);";
    return "border-color:var(--acc-cyan);color:var(--acc-cyan);";
  }

  async function openVmDoctor(vmId) {
    openHyperModal(`DOCTOR: ${vmId}`, `<div style="color:#888;">Skanuje XML, VNC, input, ISO i profil zgodnosci...</div>`);
    try {
      const data = await apiJson(`/api/vms/doctor?vm_id=${encodeURIComponent(vmId)}`);
      const issues = data.issues || [];
      const profile = data.recommended_profile || "";
      const config = data.config || {};
      const devices = config.devices || {};
      const issueRows = issues.length ? issues.map(item => `
        <div class="hyperdeck-row" style="border-left-color:${item.severity === "critical" ? "var(--acc-crit)" : item.severity === "warn" ? "var(--acc-warn)" : "var(--acc-cyan)"};">
          <div>
            <strong style="color:#fff;">${esc(item.title || item.id)}</strong>
            <div style="color:#888;font-size:11px;margin-top:4px;">${esc(item.detail || "")}</div>
          </div>
          <span class="proc-pill" style="${doctorSeverityStyle(item.severity)}">${esc(item.severity || "info")}</span>
        </div>
      `).join("") : `<div class="download-row"><strong style="color:#0f0;">CZYSTO</strong><small>Nie widze krytycznych problemow w konfiguracji VM.</small></div>`;
      const cdroms = (config.cdroms || []).map(row => `${row.target}: ${row.source || "pusty"}`).join("\\n") || "--";
      const ifaces = (config.interfaces || []).map(row => `${row.mac} ${row.model} ${row.source}`).join("\\n") || "--";
      const inputs = (devices.inputs || []).map(row => `${row.type}/${row.bus}`).join(", ") || "--";
      const controllers = (devices.controllers || []).map(row => `${row.type}/${row.model || "auto"}`).join(", ") || "--";
      openHyperModal(`DOCTOR: ${vmId}`, `
        <div class="hyperdeck-form">
          <div class="hyperdeck-tile"><span>Score</span><strong style="color:${data.state === "critical" ? "var(--acc-crit)" : data.state === "warn" ? "var(--acc-warn)" : "#0f0"}">${esc(data.score)} / 100</strong></div>
          <div class="hyperdeck-tile"><span>Stan</span><strong>${esc(data.state || "unknown")}</strong></div>
          <div class="hyperdeck-tile"><span>Profil</span><strong>${esc(data.detected_profile || "generic")}</strong></div>
          <div class="hyperdeck-tile"><span>QEMU PID</span><strong>${config.has_qemu_pid ? "OK" : "BRAK"}</strong></div>
        </div>
        <div style="display:flex;gap:8px;flex-wrap:wrap;">
          ${profile ? `<button class="nav-btn" style="margin:0;border-color:#0f0;color:#0f0;" onclick="runVmDoctorFix('${esc(vmId)}','${esc(profile)}')">AUTO FIX ${esc(profile.toUpperCase())}</button>` : ""}
          <button class="nav-btn" style="margin:0;border-color:var(--acc-crit);color:var(--acc-crit);" onclick="repairVmMedia('${esc(vmId)}')">NAPRAW MEDIA</button>
          <button class="nav-btn" style="margin:0;border-color:var(--acc-cyan);color:var(--acc-cyan);" onclick="repairVmInput('${esc(vmId)}')">NAPRAW INPUT</button>
          <button class="nav-btn" style="margin:0;border-color:var(--acc-purple);color:var(--acc-purple);" onclick="openVmDoctor('${esc(vmId)}')">ODSWIEZ DOCTOR</button>
          <button class="nav-btn" style="margin:0;border-color:#aaa;color:#ddd;" onclick="openVmConfig('${esc(vmId)}')">CONFIG</button>
          <button class="nav-btn" style="margin:0;border-color:var(--acc-warn);color:var(--acc-warn);" onclick="openVmLogs('${esc(vmId)}')">LOGI</button>
        </div>
        <div style="display:grid;gap:8px;">${issueRows}</div>
        <pre class="hyperdeck-log" style="min-height:190px;">STATE: ${esc(config.dominfo?.state || "--")}
RAM: ${esc(config.memory_mb || "--")} MB
CDROM:
${esc(cdroms)}

SIEC:
${esc(ifaces)}

INPUT:
${esc(inputs)}

CONTROLLERS:
${esc(controllers)}</pre>
      `);
    } catch (err) {
      openHyperModal(`DOCTOR: ${vmId}`, `<div style="color:var(--acc-crit);">${esc(err.message || "VM Doctor nie powiodl sie.")}</div>`);
    }
  }

  async function runVmDoctorFix(vmId, profile = "") {
    if (!confirm(`Uruchomic AUTO FIX dla ${vmId}${profile ? ` (${profile})` : ""}?`)) return;
    try {
      const data = await apiJson("/api/vms/doctor/fix", { method: "POST", body: JSON.stringify({ vm_id: vmId, profile, restart: true, fix_input: true }) });
      const after = data.diagnosis_after || {};
      notify(after.state === "ok" ? "ok" : "warn", "VM Doctor", `Naprawa wykonana. Score po: ${after.score ?? "--"}/100, stan: ${after.state || "--"}.`, 9000);
      await openVmDoctor(vmId);
      setTimeout(loadHyperDeck, 1000);
    } catch (err) {
      notify("error", "VM Doctor", err.message || "AUTO FIX nie powiodl sie.", 10000);
    }
  }

  async function repairVmInput(vmId) {
    try {
      const data = await apiJson("/api/vms/input/repair", { method: "POST", body: JSON.stringify({ vm_id: vmId, backend: currentBackend || "auto", live: true, config: true }) });
      notify("ok", "Input VM", `Sprawdzone: ${data.added || 0} dodane, ${data.skipped || 0} juz bylo.`, 5000);
      await openVmDoctor(vmId);
    } catch (err) {
      notify("error", "Input VM", err.message || "Nie udalo sie naprawic inputu.", 8000);
    }
  }

  async function repairVmMedia(vmId) {
    try {
      const data = await apiJson("/api/vms/media/repair", { method: "POST", body: JSON.stringify({ vm_id: vmId, live: true, config: true }) });
      notify("ok", "Media VM", `Odpieto bledne CD-ROM-y: ${(data.detached || []).length}.`, 6000);
      await openVmDoctor(vmId);
      setTimeout(loadHyperDeck, 700);
    } catch (err) {
      notify("error", "Media VM", err.message || "Nie udalo sie naprawic mediow VM.", 8000);
    }
  }

  async function openVmLogs(vmId) {
    openHyperModal(`LOGI: ${vmId}`, `<div style="color:#888;">Pobieram ostatnie 50 linii...</div>`);
    try {
      const data = await apiJson(`/api/vms/logs?vm_id=${encodeURIComponent(vmId)}&lines=50`);
      openHyperModal(`LOGI: ${vmId}`, `
        <div style="display:flex;gap:8px;flex-wrap:wrap;">
          <button class="nav-btn" style="margin:0;border-color:var(--acc-cyan);color:var(--acc-cyan);" onclick="openVmLogs('${esc(vmId)}')">ODSWIEZ</button>
          <span class="proc-pill">${esc(data.path || "")}</span>
        </div>
        <pre class="hyperdeck-log">${esc(data.logs || "Brak danych.")}</pre>
      `);
    } catch (err) {
      openHyperModal(`LOGI: ${vmId}`, `<div style="color:var(--acc-crit);">${esc(err.message)}</div>`);
    }
  }

  async function openVmPorts(vmId) {
    openHyperModal(`PORTY: ${vmId}`, `<div style="color:#888;">Pobieram reguly...</div>`);
    try {
      const data = await apiJson("/api/vms/ports");
      const items = (data.items || []).filter(item => item.vm_id === vmId);
      const rows = items.length ? items.map(item => `
        <div class="hyperdeck-row">
          <div>
            <strong>${esc(item.proto || "tcp").toUpperCase()} HOST:${esc(item.host_port)} -> ${esc(item.guest_ip)}:${esc(item.vm_port)}</strong>
            <small>${esc(item.comment || item.id)} | ${esc(item.created_at || "")}</small>
          </div>
          <button class="nav-btn" style="margin:0;padding:7px;border-color:var(--acc-crit);color:var(--acc-crit);" onclick="deleteVmPort('${esc(item.id)}','${esc(vmId)}')">USUN</button>
        </div>
      `).join("") : `<div class="download-row">Brak reguly port forwarding dla tej VM.</div>`;
      openHyperModal(`PORTY: ${vmId}`, `
        <div class="hyperdeck-form">
          <input id="vm-port-guest-ip" class="cyber-input" placeholder="IP VM, opcj. autodetect">
          <input id="vm-port-vm" class="cyber-input" type="number" min="1" max="65535" placeholder="port VM np. 80">
          <input id="vm-port-host" class="cyber-input" type="number" min="1" max="65535" placeholder="port host np. 8080">
          <select id="vm-port-proto" class="cyber-input"><option value="tcp">TCP</option><option value="udp">UDP</option></select>
          <button class="nav-btn" style="margin:0;border-color:#0f0;color:#0f0;" onclick="createVmPort('${esc(vmId)}')">DODAJ NAT</button>
        </div>
        <div style="display:grid;gap:8px;">${rows}</div>
      `);
    } catch (err) {
      openHyperModal(`PORTY: ${vmId}`, `<div style="color:var(--acc-crit);">${esc(err.message)}</div>`);
    }
  }

  async function createVmPort(vmId) {
    const payload = {
      vm_id: vmId,
      guest_ip: qs("vm-port-guest-ip")?.value || "",
      vm_port: Number(qs("vm-port-vm")?.value || 0),
      host_port: Number(qs("vm-port-host")?.value || 0),
      proto: qs("vm-port-proto")?.value || "tcp",
    };
    if (!payload.vm_port || !payload.host_port) return notify("warn", "Port forwarding VM", "Podaj port VM i port hosta.");
    try {
      const data = await apiJson("/api/vms/ports/create", { method: "POST", body: JSON.stringify(payload) });
      await verifyVmPortRule(data.id, true);
      await openVmPorts(vmId);
    } catch (err) {
      notify("error", "Port forwarding VM", err.message || "Nie udalo sie dodac port forwarding.");
    }
  }

  async function deleteVmPort(id, vmId) {
    if (!confirm("Usunac te regule port forwarding?")) return;
    try {
      await apiJson("/api/vms/ports/delete", { method: "POST", body: JSON.stringify({ id }) });
      await verifyVmPortRule(id, false);
      await openVmPorts(vmId);
    } catch (err) {
      notify("error", "Port forwarding VM", err.message || "Nie udalo sie usunac reguly.");
    }
  }

  async function deleteVmPrompt(vmId) {
    if (!confirm(`Usunac VM ${vmId}?`)) return;
    const removeStorage = confirm(`Usunac tez dysk qcow2/raw/img maszyny ${vmId}? OK = VM + dysk, Anuluj = sama definicja VM.`);
    try {
      await apiJson("/api/vms/delete", { method: "POST", body: JSON.stringify({ vm_id: vmId, backend: currentBackend || "auto", remove_storage: removeStorage, confirm: "" }) });
      if (typeof window.verifyVmActionEffect === "function") window.verifyVmActionEffect(vmId, "delete");
      closeHyperModal();
      await loadHyperDeck();
      if (typeof window.loadVMs === "function") window.loadVMs();
    } catch (err) {
      notify("error", "Usuwanie VM", err.message || "Nie udalo sie usunac VM.");
    }
  }

  function putCommandInClipboardBox(command, pasteNow) {
    const input = qs("hyper-clipboard-text");
    if (input) input.value = command || "";
    if (pasteNow) sendHyperClipboard();
    try { navigator.clipboard?.writeText(command || ""); } catch (_) {}
  }

  async function openVmGuestAgent(vmId) {
    openHyperModal(`AGENT: ${vmId}`, `<div style="color:#888;">Generuje token i komendy agenta...</div>`);
    try {
      const data = await apiJson("/api/vms/guest-agent", { method: "POST", body: JSON.stringify({ vm_id: vmId }) });
      const tel = data.telemetry || {};
      const linux = esc(data.linux_command || "");
      const win = esc(data.windows_command || "");
      openHyperModal(`AGENT: ${vmId}`, `
        <div class="download-row">Endpoint: ${esc(data.endpoint || "")} | token: ...${esc(data.token_tail || "")}</div>
        <div class="hyperdeck-form">
          <button class="nav-btn" style="margin:0;border-color:#0f0;color:#0f0;" onclick="putCommandInClipboardBox(document.getElementById('vm-agent-linux').value,true)">WKLEJ LINUX DO KONSOLI</button>
          <button class="nav-btn" style="margin:0;border-color:var(--acc-cyan);color:var(--acc-cyan);" onclick="putCommandInClipboardBox(document.getElementById('vm-agent-win').value,true)">WKLEJ WINDOWS DO KONSOLI</button>
          <button class="nav-btn" style="margin:0;border-color:var(--acc-warn);color:var(--acc-warn);" onclick="openVmGuestAgent('${esc(vmId)}')">ODSWIEZ STATUS</button>
        </div>
        <div class="hyperdeck-row">
          <div>
            <strong>OSTATNIA TELEMETRIA: ${tel.received_at ? esc(tel.received_at) : "BRAK"}</strong>
            <small>${tel.hostname ? esc(tel.hostname) + " | " : ""}${tel.os ? esc(tel.os) + " | " : ""}CPU ${esc(tel.cpu_percent ?? "--")}% | RAM ${esc(tel.memory_percent ?? "--")}% | DYSK ${esc(tel.disk_percent ?? "--")}%</small>
          </div>
        </div>
        <label style="color:#888;font-size:11px;">LINUX</label>
        <textarea id="vm-agent-linux" class="cyber-input" style="min-height:220px;">${linux}</textarea>
        <label style="color:#888;font-size:11px;">WINDOWS POWERSHELL</label>
        <textarea id="vm-agent-win" class="cyber-input" style="min-height:220px;">${win}</textarea>
      `);
    } catch (err) {
      openHyperModal(`AGENT: ${vmId}`, `<div style="color:var(--acc-crit);">${esc(err.message)}</div>`);
    }
  }

  async function checkVmAlerts() {
    try {
      const data = await apiJson("/api/vms/alerts/check", { method: "POST", body: JSON.stringify({}) });
      const count = (data.triggered || []).length;
      notify(count ? "warn" : "ok", "VM alert check", count ? `${count} alertow.` : "Czysto.");
    } catch (err) {
      notify("error", "VM alert check", err.message || "Alert check nie powiodl sie.");
    }
  }

  function ensureHyperRfbSurface() {
    const screen = qs("hyper-vnc-screen");
    if (!screen) return null;
    let surface = qs("hyper-rfb-surface");
    if (!surface || !screen.contains(surface)) {
      screen.innerHTML = `<div id="hyper-rfb-surface" tabindex="0"></div>`;
      surface = qs("hyper-rfb-surface");
    }
    return surface;
  }

  function hyperPointerTarget() {
    return qs("hyper-rfb-surface") || qs("hyper-vnc-screen");
  }

  async function openHyperConsole(vmId, backend, name) {
    installPage();
    const hyperPage = qs("hyper_deck");
    if (hyperPage && !hyperPage.classList.contains("active")) {
      try {
        if (typeof window.show === "function") window.show("hyper_deck");
        else {
          document.querySelectorAll(".page").forEach(page => page.classList.remove("active"));
          hyperPage.classList.add("active");
        }
      } catch (_) {
        document.querySelectorAll(".page").forEach(page => page.classList.remove("active"));
        hyperPage.classList.add("active");
      }
    }
    lastConsole = { vmId, backend: backend || currentBackend || "auto", name: name || vmId };
    const panel = qs("hyper-console");
    const screen = qs("hyper-vnc-screen");
    const title = qs("hyper-console-title");
    const status = qs("hyper-console-status");
    if (!panel || !screen) return;
    panel.classList.add("active");
    document.body.classList.add("hyper-console-open");
    title.textContent = `KONSOLA: ${name || vmId}`;
    status.textContent = "Pobieram endpoint VNC...";
    screen.innerHTML = `<span style="color:#678;">LADOWANIE noVNC...</span>`;
    applyHyperCustomSize();
    const sharedClip = localStorage.getItem("nexus_shared_clipboard") || "";
    const clipInput = qs("hyper-clipboard-text");
    if (clipInput && sharedClip && !clipInput.value) clipInput.value = sharedClip;
    try {
      if (currentRfb) {
        try { currentRfb.disconnect(); } catch (_) {}
        currentRfb = null;
      }
      const consoleResponse = await apiFetch(`/api/vms/console?vm_id=${encodeURIComponent(vmId)}&backend=${encodeURIComponent(backend || currentBackend || "auto")}`);
      const info = await consoleResponse.json().catch(() => ({}));
      if (!consoleResponse.ok) {
        throw new Error(info.detail || "Nie udalo sie znalezc lokalnego VNC dla tej VM.");
      }
      if (info.input_repair) {
        const repair = info.input_repair;
        const warnings = Array.isArray(repair.warnings) ? repair.warnings.filter(Boolean) : [];
        if (warnings.length) {
          notify("warn", "Input VM", warnings[0], 6200);
        } else if (Number(repair.added || 0) > 0) {
          notify("ok", "Input VM", `Dodano ${repair.added} urzadzen wejscia do konsoli.`, 3200);
        }
      }
      const RFB = await loadNoVnc();
      const wsProto = location.protocol === "https:" ? "wss:" : "ws:";
      let wsPath = info.ws_path || `/ws/vnc/${encodeURIComponent(vmId)}?backend=${encodeURIComponent(backend || currentBackend || "auto")}`;
      if (!/[?&]session=/.test(wsPath)) wsPath += `${wsPath.includes("?") ? "&" : "?"}token=${encodeURIComponent(token())}`;
      const wsUrl = `${wsProto}//${location.host}${wsPath}`;
      screen.innerHTML = "";
      delete screen.dataset.pointerReady;
      const surface = ensureHyperRfbSurface();
      prepareHyperPointerSurface();
      const password = qs("hyper-vnc-password")?.value || "";
      currentRfb = new RFB(surface || screen, wsUrl, { credentials: password ? { password } : {} });
      currentRfb.focusOnClick = true;
      currentRfb.viewOnly = false;
      currentRfb.showDotCursor = true;
      if ("qualityLevel" in currentRfb) currentRfb.qualityLevel = 6;
      if ("compressionLevel" in currentRfb) currentRfb.compressionLevel = 2;
      pointerAttached = true;
      updateHyperPointerButton();
      applyHyperCursorMode();
      bindHyperAutoFit();
      currentRfb.addEventListener("connect", () => {
        status.textContent = `POLACZONO / sesja noVNC ${info.session_ttl_seconds || 600}s / low-lag scale`;
        fitHyperConsole();
      });
      currentRfb.addEventListener("disconnect", event => {
        status.textContent = event.detail && event.detail.clean ? "Rozlaczono" : "Rozlaczono / blad VNC";
      });
      currentRfb.addEventListener("clipboard", event => {
        const text = event.detail?.text || "";
        if (!text) return;
        const input = qs("hyper-clipboard-text");
        if (input) input.value = text;
        localStorage.setItem("nexus_shared_clipboard", text);
        if (navigator.clipboard?.writeText) navigator.clipboard.writeText(text).catch(() => {});
        notify("ok", "Schowek VM", `Odebrano ${text.length} znakow z VM.`, 2600);
      });
      currentRfb.addEventListener("credentialsrequired", () => {
        const pass = prompt("VNC wymaga hasla:");
        currentRfb.sendCredentials({ password: pass || "" });
      });
      setTimeout(() => { fitHyperConsole(); try { currentRfb.focus(); } catch (_) {} }, 500);
    } catch (err) {
      status.textContent = "Brak sygnalu VNC";
      screen.innerHTML = `<div style="color:var(--acc-warn);padding:20px;text-align:center;max-width:760px;">${esc(err.message || "Nie udalo sie otworzyc konsoli. Sprawdz, czy VM ma lokalny VNC: listen=127.0.0.1.")}</div>`;
    }
  }

  async function openHyperConsoleFromDash(vmId, backend, name) {
    if (!vmId) {
      notify("error", "PODGLAD VM", "Brak identyfikatora maszyny.");
      return;
    }
    return openHyperConsole(vmId, backend || currentBackend || "auto", name || vmId);
  }

  function finishHyperConsoleClose(panel, screen, keyboard) {
    unbindHyperAutoFit();
    if (screen) {
      screen.innerHTML = `<span style="color:#456;">NO SIGNAL</span>`;
      delete screen.dataset.pointerReady;
      screen.style.pointerEvents = "";
    }
    if (panel) panel.classList.remove("active");
    if (keyboard) keyboard.classList.remove("active");
    document.body.classList.remove("hyper-console-open");
    pointerAttached = true;
    updateHyperPointerButton();
    updateHyperKeyboardButton();
    updateHyperFullscreenButton();
  }

  function closeHyperConsole() {
    if (currentRfb) {
      try { currentRfb.disconnect(); } catch (_) {}
      currentRfb = null;
    }
    const panel = qs("hyper-console");
    const screen = qs("hyper-vnc-screen");
    const keyboard = qs("hyper-osk");
    if (document.fullscreenElement === panel) {
      document.exitFullscreen()
        .catch(() => {})
        .finally(() => finishHyperConsoleClose(panel, screen, keyboard));
    } else {
      finishHyperConsoleClose(panel, screen, keyboard);
    }
  }

  function renderHyperKeyboard() {
    const panel = qs("hyper-osk");
    if (!panel || panel.dataset.rendered === "1") return;
    panel.innerHTML = hyperKeyboardRows.map((row, rowIndex) => `
      <div class="hyperdeck-osk-row">
        ${row.map((key, keyIndex) => `<button type="button" class="nav-btn hyperdeck-key ${esc(key.cls || "")}" data-row="${rowIndex}" data-key="${keyIndex}">${esc(key.label)}</button>`).join("")}
      </div>
    `).join("");
    panel.querySelectorAll(".hyperdeck-key").forEach(button => {
      button.addEventListener("click", () => {
        const row = Number(button.dataset.row || 0);
        const key = Number(button.dataset.key || 0);
        sendHyperVirtualKey(hyperKeyboardRows[row]?.[key]);
      });
    });
    panel.dataset.rendered = "1";
  }

  function updateHyperKeyboardButton() {
    const btn = qs("hyper-keyboard-btn");
    const panel = qs("hyper-osk");
    if (!btn) return;
    const active = !!panel?.classList.contains("active");
    btn.textContent = active ? "KLAWIATURA ON" : "KLAWIATURA";
    btn.style.borderColor = active ? "var(--acc-warn)" : "var(--acc-cyan)";
    btn.style.color = active ? "var(--acc-warn)" : "var(--acc-cyan)";
  }

  function toggleHyperKeyboard(force) {
    renderHyperKeyboard();
    const panel = qs("hyper-osk");
    if (!panel) return;
    const next = typeof force === "boolean" ? force : !panel.classList.contains("active");
    panel.classList.toggle("active", next);
    updateHyperKeyboardButton();
    try { if (currentRfb) currentRfb.focus(); } catch (_) {}
  }

  function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  function keysymForChar(ch) {
    const point = ch.codePointAt(0);
    if (point == null) return 0;
    return point <= 0xff ? point : (0x01000000 | point);
  }

  async function pressHyperKey(keysym, code = "", holdMs = 18) {
    currentRfb.sendKey(keysym, code || null, true);
    await sleep(holdMs);
    currentRfb.sendKey(keysym, code || null, false);
  }

  async function sendHyperVirtualKey(key) {
    if (!key) return;
    if (key.combo === "ctrl-alt-del") return sendHyperCtrlAltDel();
    if (!currentRfb) return alert("Konsola VNC nie jest polaczona.");
    try {
      if (key.text) {
        for (const ch of Array.from(String(key.text))) await pressHyperKey(keysymForChar(ch), "", 14);
      } else if (key.keysym) {
        await pressHyperKey(Number(key.keysym), key.code || key.label, 18);
      }
      try { currentRfb.focus(); } catch (_) {}
    } catch (err) {
      notify("error", "Klawiatura VM", err.message || "Nie udalo sie wyslac klawisza.");
    }
  }

  function sendHyperCtrlAltDel() {
    if (!currentRfb) return alert("Konsola VNC nie jest polaczona.");
    currentRfb.sendCtrlAltDel();
  }

  async function sendHyperCtrlV() {
    if (!currentRfb) return;
    currentRfb.sendKey(0xffe3, "ControlLeft", true);
    await sleep(18);
    currentRfb.sendKey(0x0076, "KeyV", true);
    await sleep(18);
    currentRfb.sendKey(0x0076, "KeyV", false);
    await sleep(18);
    currentRfb.sendKey(0xffe3, "ControlLeft", false);
  }

  async function sendHyperClipboard() {
    if (!currentRfb) return alert("Konsola VNC nie jest polaczona.");
    const text = qs("hyper-clipboard-text")?.value || "";
    if (!text) return;
    localStorage.setItem("nexus_shared_clipboard", text);
    if (typeof currentRfb.clipboardPasteFrom === "function") {
      currentRfb.clipboardPasteFrom(text);
      try { currentRfb.focus(); } catch (_) {}
      await sleep(90);
      try { await sendHyperCtrlV(); } catch (_) {}
      notify("ok", "Schowek VM", `Wyslano ${text.length} znakow i nacisnieto CTRL+V. Gdy legacy Windows nie przyjmie schowka, kliknij WPISZ.`, 5200);
    } else {
      await typeHyperClipboardToVm(text);
    }
  }

  async function typeHyperClipboardToVm(text = qs("hyper-clipboard-text")?.value || "") {
    if (!currentRfb) return alert("Konsola VNC nie jest polaczona.");
    const value = String(text || "");
    if (!value) return notify("warn", "Klawiatura VM", "Pole tekstowe jest puste.", 2600);
    localStorage.setItem("nexus_shared_clipboard", value);
    const normalized = value.replace(/\r\n/g, "\n").replace(/\r/g, "\n");
    try {
      try { currentRfb.focus(); } catch (_) {}
      notify("ok", "Klawiatura VM", `Wpisuje ${normalized.length} znakow jako klawisze...`, 2600);
      for (const ch of Array.from(normalized)) {
        if (ch === "\n") await pressHyperKey(0xff0d, "Enter", 20);
        else if (ch === "\t") await pressHyperKey(0xff09, "Tab", 20);
        else await pressHyperKey(keysymForChar(ch), "", 16);
        await sleep(22);
      }
      try { currentRfb.focus(); } catch (_) {}
      notify("ok", "Klawiatura VM", `Wpisano ${normalized.length} znakow do VM.`, 3200);
    } catch (err) {
      notify("error", "Klawiatura VM", err.message || "Nie udalo sie wpisac tekstu do VM.");
    }
  }

  function clampHyperSize(value, min, max, fallback) {
    const number = Number.parseInt(value, 10);
    if (!Number.isFinite(number)) return fallback;
    return Math.max(min, Math.min(max, number));
  }

  function applyHyperCustomSize() {
    const wrap = document.querySelector(".hyperdeck-vnc-wrap");
    const screen = qs("hyper-vnc-screen");
    const w = qs("hyper-size-w");
    const h = qs("hyper-size-h");
    if (w) w.value = String(hyperCustomWidth);
    if (h) h.value = String(hyperCustomHeight);
    if (wrap) {
      wrap.classList.toggle("custom-size", hyperCustomScale);
      wrap.style.setProperty("--hyper-custom-width", `${hyperCustomWidth}px`);
      wrap.style.setProperty("--hyper-custom-height", `${hyperCustomHeight}px`);
    }
    if (screen) {
      screen.style.setProperty("--hyper-custom-width", `${hyperCustomWidth}px`);
      screen.style.setProperty("--hyper-custom-height", `${hyperCustomHeight}px`);
    }
    const btn = qs("hyper-custom-size-btn");
    if (btn) {
      btn.textContent = hyperCustomScale ? `ROZMIAR ${hyperCustomWidth}x${hyperCustomHeight}` : "ROZMIAR";
      btn.style.borderColor = hyperCustomScale ? "var(--acc-warn)" : "var(--acc-purple)";
      btn.style.color = hyperCustomScale ? "var(--acc-warn)" : "var(--acc-purple)";
    }
    if (currentRfb && hyperCustomScale) {
      currentRfb.scaleViewport = true;
      currentRfb.resizeSession = false;
      currentRfb.clipViewport = false;
      currentRfb.dragViewport = false;
    }
    centerHyperConsoleView(false);
  }

  function getHyperStageSize() {
    const screen = hyperPointerTarget();
    const canvas = screen?.querySelector("canvas");
    if (hyperCustomScale) return { width: hyperCustomWidth, height: hyperCustomHeight };
    const rect = screen?.getBoundingClientRect();
    return {
      width: Math.max(1, Math.ceil(rect?.width || canvas?.offsetWidth || canvas?.width || 0)),
      height: Math.max(1, Math.ceil(rect?.height || canvas?.offsetHeight || canvas?.height || 0))
    };
  }

  function centerHyperConsoleView(forceScroll = false) {
    const wrap = document.querySelector(".hyperdeck-vnc-wrap");
    if (!wrap) return;
    if (!hyperCustomScale) {
      wrap.style.setProperty("--hyper-stage-pad-x", "0px");
      wrap.style.setProperty("--hyper-stage-pad-y", "0px");
      return;
    }
    const { width, height } = getHyperStageSize();
    const padX = Math.max(0, Math.floor((wrap.clientWidth - width) / 2));
    const padY = Math.max(0, Math.floor((wrap.clientHeight - height) / 2));
    wrap.style.setProperty("--hyper-stage-pad-x", `${padX}px`);
    wrap.style.setProperty("--hyper-stage-pad-y", `${padY}px`);
    if (forceScroll) {
      requestAnimationFrame(() => {
        wrap.scrollLeft = Math.max(0, Math.floor((wrap.scrollWidth - wrap.clientWidth) / 2));
        wrap.scrollTop = Math.max(0, Math.floor((wrap.scrollHeight - wrap.clientHeight) / 2));
        try { currentRfb?.focus(); } catch (_) {}
      });
      notify("ok", "Podglad VM", "Wycentrowano obraz w oknie konsoli.", 2200);
    }
  }

  function setHyperCustomSize() {
    hyperCustomWidth = clampHyperSize(qs("hyper-size-w")?.value, 320, 7680, hyperCustomWidth || 1024);
    hyperCustomHeight = clampHyperSize(qs("hyper-size-h")?.value, 240, 4320, hyperCustomHeight || 768);
    hyperCustomScale = true;
    hyperCursorMode = "precise";
    localStorage.setItem("nexus_hyper_custom_scale", "1");
    localStorage.setItem("nexus_hyper_custom_w", String(hyperCustomWidth));
    localStorage.setItem("nexus_hyper_custom_h", String(hyperCustomHeight));
    localStorage.setItem("nexus_hyper_cursor_mode", hyperCursorMode);
    applyHyperCustomSize();
    applyHyperCursorMode();
    queueHyperFit(60);
    notify("ok", "Rozmiar VM", `Ustawiono ${hyperCustomWidth}x${hyperCustomHeight}.`, 3200);
  }

  function clearHyperCustomSize() {
    hyperCustomScale = false;
    localStorage.setItem("nexus_hyper_custom_scale", "0");
    applyHyperCustomSize();
    applyHyperCursorMode();
    queueHyperFit(80);
    notify("ok", "Rozmiar VM", "Wrocono do automatycznego dopasowania.", 2600);
  }

  async function readSystemClipboardToHyper() {
    if (!navigator.clipboard?.readText) return alert("Przegladarka nie pozwala odczytac schowka.");
    try {
      const text = await navigator.clipboard.readText();
      const input = qs("hyper-clipboard-text");
      if (input) input.value = text || "";
      localStorage.setItem("nexus_shared_clipboard", text || "");
      notify("ok", "Schowek PC", `Odczytano ${String(text || "").length} znakow. Kliknij WPISZ, zeby wprowadzic tekst do VM.`, 3600);
    } catch (err) {
      notify("error", "Schowek VM", err.message || "Nie udalo sie odczytac schowka przegladarki.");
    }
  }

  function fitHyperConsole() {
    if (!currentRfb) return;
    try {
      applyHyperCustomSize();
      applyHyperCursorMode();
      if ("qualityLevel" in currentRfb) currentRfb.qualityLevel = 6;
      if ("compressionLevel" in currentRfb) currentRfb.compressionLevel = 2;
      const resize = () => {
        try {
          const box = hyperPointerTarget();
          if (box && currentRfb.scaleViewport && currentRfb._display && typeof currentRfb._display.autoscale === "function") {
            currentRfb._display.autoscale(Math.max(1, Math.round(box.clientWidth || 1)), Math.max(1, Math.round(box.clientHeight || 1)));
          }
        } catch (_) {}
        try { if (typeof currentRfb._windowResize === "function") currentRfb._windowResize(); } catch (_) {}
      };
      requestAnimationFrame(resize);
      setTimeout(resize, 120);
      setTimeout(resize, 420);
      setTimeout(() => centerHyperConsoleView(false), 40);
      setTimeout(() => centerHyperConsoleView(false), 180);
      setTimeout(() => centerHyperConsoleView(false), 460);
      currentRfb.focus();
    } catch (_) {}
  }

  function prepareHyperPointerSurface() {
    const screen = qs("hyper-vnc-screen");
    const surface = ensureHyperRfbSurface();
    const target = surface || screen;
    if (!screen || !target || screen.dataset.pointerReady === "1") return;
    screen.dataset.pointerReady = "1";
    screen.tabIndex = 0;
    target.tabIndex = 0;
    screen.addEventListener("contextmenu", event => event.preventDefault());
    target.addEventListener("contextmenu", event => event.preventDefault());
    const focusSurface = () => {
      try { screen.focus({ preventScroll: true }); } catch (_) { try { screen.focus(); } catch (_) {} }
      try { target.focus({ preventScroll: true }); } catch (_) { try { target.focus(); } catch (_) {} }
      try { currentRfb?.focus(); } catch (_) {}
    };
    screen.addEventListener("mouseenter", focusSurface, { passive: true });
    target.addEventListener("mouseenter", focusSurface, { passive: true });
    target.addEventListener("pointermove", () => { if (pointerAttached) focusSurface(); }, { passive: true });
    ["pointerdown", "mousedown", "touchstart"].forEach(type => {
      target.addEventListener(type, event => {
        if (!pointerAttached) return;
        focusSurface();
        if (type === "touchstart" && event.cancelable) event.preventDefault();
        if (event.pointerId !== undefined && typeof target.setPointerCapture === "function") {
          try { target.setPointerCapture(event.pointerId); } catch (_) {}
        }
      }, { capture: true, passive: type !== "touchstart" });
    });
  }

  function applyHyperCursorMode() {
    const screen = qs("hyper-vnc-screen");
    const surface = hyperPointerTarget();
    const btn = qs("hyper-cursor-mode-btn");
    const fallback = hyperCursorMode === "fallback";
    if (screen) screen.classList.toggle("cursor-fallback", fallback);
    if (surface) surface.classList.toggle("cursor-fallback", fallback);
    if (currentRfb) {
      currentRfb.scaleViewport = hyperCustomScale ? true : !fallback;
      currentRfb.resizeSession = false;
      currentRfb.clipViewport = !fallback || hyperCustomScale;
      currentRfb.dragViewport = false;
      currentRfb.showDotCursor = true;
    }
    if (btn) {
      btn.textContent = fallback ? "KURSOR 1:1" : "KURSOR PRECYZYJNY";
      btn.style.borderColor = fallback ? "var(--acc-warn)" : "var(--acc-cyan)";
      btn.style.color = fallback ? "var(--acc-warn)" : "var(--acc-cyan)";
    }
  }

  function toggleHyperCursorMode() {
    hyperCursorMode = hyperCursorMode === "fallback" ? "precise" : "fallback";
    localStorage.setItem("nexus_hyper_cursor_mode", hyperCursorMode);
    applyHyperCursorMode();
    queueHyperFit(80);
    try { currentRfb?.focus(); } catch (_) {}
    notify("ok", "Kursor VM", hyperCursorMode === "fallback" ? "Tryb 1:1 wlaczony. Uzyj go, gdy kursor rozjezdza sie ze skala." : "Tryb precyzyjny noVNC wlaczony.", 3600);
  }

  function queueHyperFit(delay = 80) {
    clearTimeout(hyperAutoFitTimer);
    hyperAutoFitTimer = setTimeout(fitHyperConsole, delay);
  }

  function bindHyperAutoFit() {
    if (hyperResizeObserver) {
      try { hyperResizeObserver.disconnect(); } catch (_) {}
      hyperResizeObserver = null;
    }
    const screen = qs("hyper-vnc-screen");
    if (screen && "ResizeObserver" in window) {
      hyperResizeObserver = new ResizeObserver(() => queueHyperFit(160));
      hyperResizeObserver.observe(screen);
    }
    window.removeEventListener("resize", queueHyperFit);
    window.addEventListener("resize", queueHyperFit);
    document.removeEventListener("fullscreenchange", updateHyperFullscreenButton);
    document.addEventListener("fullscreenchange", updateHyperFullscreenButton);
  }

  function unbindHyperAutoFit() {
    if (hyperResizeObserver) {
      try { hyperResizeObserver.disconnect(); } catch (_) {}
      hyperResizeObserver = null;
    }
    clearTimeout(hyperAutoFitTimer);
    window.removeEventListener("resize", queueHyperFit);
    document.removeEventListener("fullscreenchange", updateHyperFullscreenButton);
  }

  function updateHyperFullscreenButton() {
    const btn = qs("hyper-fullscreen-btn");
    if (!btn) return;
    const panel = qs("hyper-console");
    const active = document.fullscreenElement === panel;
    btn.textContent = active ? "EXIT FULL" : "FULLSCREEN";
    btn.style.borderColor = active ? "var(--acc-warn)" : "var(--acc-cyan)";
    btn.style.color = active ? "var(--acc-warn)" : "var(--acc-cyan)";
    if (panel?.classList.contains("active")) queueHyperFit(180);
  }

  async function toggleHyperFullscreen() {
    const panel = qs("hyper-console");
    if (!panel) return;
    try {
      if (document.fullscreenElement) await document.exitFullscreen();
      else await panel.requestFullscreen();
      updateHyperFullscreenButton();
    } catch (err) {
      notify("error", "Fullscreen VM", err.message || "Tryb pelnoekranowy niedostepny.");
    }
  }

  function restartHyperConsoleView() {
    if (!lastConsole.vmId) return alert("Nie ma aktywnej konsoli do restartu.");
    try { if (currentRfb) currentRfb.disconnect(); } catch (_) {}
    currentRfb = null;
    setTimeout(() => openHyperConsole(lastConsole.vmId, lastConsole.backend, lastConsole.name), 350);
  }

  function updateHyperPointerButton() {
    const btn = qs("hyper-pointer-btn");
    const screen = qs("hyper-vnc-screen");
    const surface = hyperPointerTarget();
    if (screen) screen.style.pointerEvents = pointerAttached ? "auto" : "none";
    if (surface) surface.style.pointerEvents = pointerAttached ? "auto" : "none";
    if (btn) {
      btn.textContent = pointerAttached ? "MYSZ ON" : "MYSZ OFF";
      btn.style.borderColor = pointerAttached ? "var(--acc-cyan)" : "var(--acc-warn)";
      btn.style.color = pointerAttached ? "var(--acc-cyan)" : "var(--acc-warn)";
    }
  }

  function toggleHyperPointer() {
    pointerAttached = !pointerAttached;
    updateHyperPointerButton();
    if (currentRfb) {
      try { currentRfb.focus(); } catch (_) {}
    }
  }

  function resetHyperMouse() {
    pointerAttached = false;
    updateHyperPointerButton();
    setTimeout(() => {
      pointerAttached = true;
      updateHyperPointerButton();
      fitHyperConsole();
      try { currentRfb?.focus(); } catch (_) {}
      notify("ok", "Mysz VM", "Zresetowano przechwytywanie kursora.");
    }, 160);
  }

  async function repairHyperMouse() {
    resetHyperMouse();
    if (!lastConsole.vmId) return;
    try {
      const data = await apiJson("/api/vms/input/repair", {
        method: "POST",
        body: JSON.stringify({ vm_id: lastConsole.vmId, backend: lastConsole.backend || currentBackend || "auto", live: true, config: true }),
        silent: true
      });
      notify("ok", "Mysz VM", `Wejscie VM sprawdzone: ${data.added || 0} dodane, ${data.skipped || 0} juz bylo.`);
      queueHyperFit(180);
    } catch (err) {
      notify("warn", "Mysz VM", err.message || "Nie udalo sie naprawic wejscia VM.", 7000);
    }
  }

  function toggleHyperAudioMute() {
    hyperAudioMuted = !hyperAudioMuted;
    document.querySelectorAll("audio,video").forEach(node => { node.muted = hyperAudioMuted; });
    const btn = qs("hyper-mute-btn");
    if (btn) {
      btn.textContent = hyperAudioMuted ? "MUTED" : "MUTE";
      btn.style.borderColor = hyperAudioMuted ? "var(--acc-warn)" : "#777";
      btn.style.color = hyperAudioMuted ? "var(--acc-warn)" : "#aaa";
    }
  }

  function hyperConsoleFocus() {
    if (currentRfb) currentRfb.focus();
  }

  function humanBytes(value) {
    let n = Number(value || 0);
    const units = ["B", "KB", "MB", "GB", "TB"];
    let unit = 0;
    while (n >= 1024 && unit < units.length - 1) {
      n /= 1024;
      unit++;
    }
    return unit === 0 ? `${Math.round(n)} ${units[unit]}` : `${n.toFixed(1)} ${units[unit]}`;
  }

  function forgeStatus(text, ok) {
    const el = qs("forge-status");
    if (!el) return;
    el.style.color = ok === false ? "var(--acc-crit)" : ok === true ? "#0f0" : "var(--acc-cyan)";
    el.style.borderColor = ok === false ? "var(--acc-crit)" : ok === true ? "#0f0" : "var(--acc-purple)";
    el.style.background = ok === false ? "rgba(255,0,70,.08)" : ok === true ? "rgba(0,255,114,.06)" : "rgba(170,0,255,.08)";
    el.textContent = readableDetail(text);
  }

  function presetById(id) {
    return osCatalog.find(item => item.id === id) || osCatalog[0] || null;
  }

  function vmSafeName(text) {
    return String(text || "nexus-vm").toLowerCase().replace(/[^a-z0-9_.-]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 54) || "nexus-vm";
  }

  function autoVmName(preset) {
    const stamp = Date.now().toString(36).slice(-5);
    return vmSafeName(`nexus-${preset?.id || "vm"}-${stamp}`);
  }

  function isoScoreForPreset(item, preset) {
    const text = `${item.name || ""} ${item.path || ""}`.toLowerCase();
    const id = String(preset?.id || "").toLowerCase();
    const name = String(preset?.name || "").toLowerCase();
    let score = 0;
    if (id && text.includes(id)) score += 8;
    for (const part of name.split(/[^a-z0-9]+/).filter(x => x.length >= 3)) {
      if (text.includes(part)) score += 3;
    }
    if (id === "win10pe-project2015" && /(win[_-]?10[_-]?project|project[_-]?2015|win10pese|portable[_-]?czysty)/.test(text)) score += 24;
    if (id === "win7pe-dreamos" && /(win[_-]?7[_-]?sp1[_-]?ent|dreamos|win7pese)/.test(text)) score += 24;
    if (id === "winxp" && /(grtmpoem|windows.?xp|\bxp\b)/.test(text)) score += 18;
    if (id === "win7" && /(^|[\/\\_-])win7\.iso$|pl[_-]?win7sp1x64|windows.?7/.test(text)) score += 18;
    if (id.startsWith("win") && /\bwin|windows/.test(text)) score += 4;
    if (id === "ubuntu" && text.includes("ubuntu")) score += 7;
    if (id === "debian" && text.includes("debian")) score += 7;
    if (id === "kali" && text.includes("kali")) score += 7;
    if (id === "arch" && text.includes("archlinux")) score += 9;
    if (id === "alpine" && text.includes("alpine")) score += 9;
    if (id === "freebsd" && text.includes("freebsd")) score += 7;
    if (id === "macos-uefi" && /(macos|mac.?os|osx|os.?x|darwin|sonoma|ventura|monterey|bigsur|catalina|mojave|high.?sierra|recovery|basesystem)/.test(text)) score += 20;
    if (String(item.kind || "").toLowerCase() === "qcow2") score -= 2;
    return score;
  }

  function pickIsoPath(preset) {
    if (!isoItems.length) return "";
    const cdromItems = isoItems.filter(item => item.cdrom_attachable || String(item.kind || "").toLowerCase() === "iso");
    if (!cdromItems.length) return "";
    const ranked = cdromItems.map(item => ({ item, score: isoScoreForPreset(item, preset) })).sort((a, b) => b.score - a.score);
    return (ranked[0]?.score > 0 ? ranked[0].item : cdromItems[0]).path || "";
  }

  function renderIsoOptions(selectedPath) {
    const select = qs("forge-iso-select");
    if (!select) return;
    const cdromItems = isoItems.filter(item => item.cdrom_attachable || String(item.kind || "").toLowerCase() === "iso");
    if (!cdromItems.length) {
      select.innerHTML = `<option value="">Brak ISO .iso - pobierz albo wrzuc obraz instalacyjny</option>`;
      return;
    }
    select.innerHTML = cdromItems.map(item => `<option value="${esc(item.path)}">${esc(item.name)} | ${esc(item.size_label || humanBytes(item.size))}</option>`).join("");
    if (selectedPath && cdromItems.some(item => item.path === selectedPath)) select.value = selectedPath;
  }

  function isOpenCoreItem(item) {
    const text = `${item?.name || ""} ${item?.path || ""}`.toLowerCase();
    return text.includes("opencore") && /\.(qcow2|raw|img)(\s|$|[?#])/i.test(text);
  }

  function openCoreItemsFrom(items) {
    return (items || []).filter(isOpenCoreItem);
  }

  function renderOpenCoreDatalist() {
    const list = qs("forge-opencore-list");
    if (!list) return;
    list.innerHTML = openCoreItemsFrom(diskItems)
      .map(item => `<option value="${esc(item.path)}">${esc(item.name)} | ${esc(item.size_label || humanBytes(item.size))}</option>`)
      .join("");
  }

  function renderDriverOptions(selectedPath) {
    const select = qs("forge-driver-select");
    if (!select) return;
    const options = [
      `<option value="">AUTO: VirtIO dla Windows / brak dla Linux</option>`,
      `<option value="none">BRAK STEROWNIKOW</option>`,
    ];
    driverItems.forEach(item => {
      const label = `${item.name} | ${item.size_label || humanBytes(item.size)}${item.attachable ? "" : " | ZIP"}`;
      options.push(`<option value="${esc(item.path)}">${esc(label)}</option>`);
    });
    select.innerHTML = options.join("");
    if (selectedPath && Array.from(select.options).some(opt => opt.value === selectedPath)) select.value = selectedPath;
  }

  function renderDriverList() {
    const list = qs("driver-list");
    if (!list) return;
    renderDriverOptions(qs("forge-driver-select")?.value || "");
    if (!driverItems.length) {
      list.innerHTML = `<div class="download-row">Brak sterownikow. Wrzuć virtio-win.iso albo paczke ZIP z nazwa driver/virtio/sterownik.</div>`;
      return;
    }
    list.innerHTML = driverItems.map(item => `
      <div class="iso-row">
        <div>
          <strong>${esc(item.name)}</strong>
          <small>${esc(item.kind || "driver")} | ${esc(item.size_label || humanBytes(item.size))} | ${item.attachable ? "CD-ROM ready" : "wymaga rozpakowania ISO"}</small>
          <small>${item.extracted ? `Rozpakowano: ${esc(item.extract_dir)} (${esc(item.extracted_count)} plikow)` : esc(item.path)}</small>
          ${renderDriverCategories(item)}
        </div>
        <div style="display:flex;gap:6px;flex-wrap:wrap;justify-content:flex-end;">
          <button class="nav-btn" style="margin:0;padding:6px 8px;border-color:var(--acc-cyan);color:var(--acc-cyan);" onclick="document.getElementById('forge-driver-select').value='${esc(item.path)}';forgeStatus('Wybrane sterowniki: ${esc(item.name).replaceAll("'", "\\'")}')">USE</button>
          ${item.kind === "zip" || item.kind === "iso" ? `<button class="nav-btn" style="margin:0;padding:6px 8px;border-color:var(--acc-warn);color:var(--acc-warn);" onclick="extractVmDriver('${esc(item.path)}')">ROZPAKUJ</button>` : ""}
        </div>
      </div>
    `).join("");
  }

  function renderDriverCategories(item) {
    const categories = item.categories || [];
    if (!item.extracted || !categories.length) {
      return `<div class="download-row" style="margin-top:8px;">Brak matrycy kategorii. Kliknij ROZPAKUJ, a potem zaznacz ptaszkiem konkretne sterowniki.</div>`;
    }
    return `
      <div class="driver-matrix">
        ${categories.map(cat => `
          <label class="driver-cat ${cat.recommended ? "recommended" : ""} ${cat.id === "unknown" ? "unknown" : ""}">
            <input class="driver-cat-check" type="checkbox" data-driver-path="${esc(item.path)}" value="${esc(cat.id)}" ${cat.recommended ? "checked" : ""}>
            <span>
              <strong>${esc(cat.label || cat.id)}</strong>
              <span>${esc(cat.count)} plikow | ${esc(cat.size_label || "")}</span>
              <span>${esc((cat.samples || []).slice(0,2).join(" / "))}</span>
            </span>
          </label>
        `).join("")}
      </div>
    `;
  }

  function collectDriverCategories() {
    const selectedPath = qs("forge-driver-select")?.value || "";
    if (!selectedPath || selectedPath === "none") return [];
    return Array.from(document.querySelectorAll(".driver-cat-check:checked"))
      .filter(input => input.dataset.driverPath === selectedPath)
      .map(input => input.value)
      .filter(Boolean);
  }

  async function loadDriverVault() {
    try {
      const data = await (await apiFetch("/api/vms/drivers/list")).json();
      driverItems = data.items || [];
      const tools = qs("driver-tools");
      if (tools) {
        const info = data.tools || {};
        tools.textContent = `extract: ${info.extractor || "BRAK"} | iso-build: ${info.iso_builder || "BRAK"} | virtio: ${info.virtio_win_iso ? "OK" : "BRAK"}`;
        tools.style.color = info.virtio_win_iso ? "#0f0" : "var(--acc-warn)";
      }
      renderDriverList();
    } catch (err) {
      const list = qs("driver-list");
      if (list) list.innerHTML = `<div class="download-row" style="color:var(--acc-crit);">Nie udalo sie pobrac Driver Vault.</div>`;
    }
  }

  async function extractVmDriver(path) {
    try {
      forgeStatus("Rozpakowuje sterowniki...", null);
      const response = await apiFetch("/api/vms/drivers/extract", { method: "POST", body: JSON.stringify({ path }) });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.detail || "Rozpakowanie nie powiodlo sie");
      forgeStatus(`Sterowniki rozpakowane: ${data.file_count || 0} plikow${data.driver_iso ? " + ISO gotowe" : ""}`, true);
      await loadDriverVault();
    } catch (err) {
      forgeStatus(err.message || "Rozpakowanie sterownikow nie powiodlo sie.", false);
    }
  }

  function fillForgeFromPreset(preset, forceName) {
    if (!preset) return;
    selectedOsId = preset.id;
    const osSelect = qs("forge-os-select");
    if (osSelect) osSelect.value = preset.id;
    const name = qs("forge-vm-name");
    const currentName = name?.value || "";
    if (name && (forceName || !currentName || currentName.startsWith("nexus-"))) name.value = autoVmName(preset);
    if (qs("forge-memory")) qs("forge-memory").value = preset.memory_mb || 1024;
    if (qs("forge-vcpus")) qs("forge-vcpus").value = preset.vcpus || 1;
    if (qs("forge-disk")) qs("forge-disk").value = preset.disk_gb || 16;
    renderIsoOptions(pickIsoPath(preset));
    forgeStatus(`${preset.name}: RAM ${preset.memory_mb} MB, vCPU ${preset.vcpus}, dysk ${preset.disk_gb} GB. ${preset.note || ""}`);
    renderForgeCatalog();
  }

  function selectForgePreset(id) {
    const preset = presetById(id);
    if (preset) fillForgeFromPreset(preset, true);
  }

  function renderForgeCatalog() {
    const grid = qs("forge-os-grid");
    if (!grid) return;
    const filter = String(qs("forge-search")?.value || "").toLowerCase().trim();
    const items = osCatalog.filter(item => {
      const blob = `${item.name} ${item.family} ${item.note} ${item.id}`.toLowerCase();
      return !filter || blob.includes(filter);
    });
    grid.innerHTML = items.length ? items.map(item => `
      <article class="forge-os-card ${item.id === selectedOsId ? "selected" : ""}" onclick="selectForgePreset('${esc(item.id)}')">
        <strong>${esc(item.name)}</strong>
        <small>${esc(item.family)} / ${esc(item.drivers || "native")}</small>
        <small>RAM ${esc(item.memory_mb)} MB | vCPU ${esc(item.vcpus)} | dysk ${esc(item.disk_gb)} GB</small>
        <small>${esc(item.note || "")}</small>
      </article>
    `).join("") : `<div class="download-row">Brak presetow dla filtra.</div>`;
  }

  function renderIsoList() {
    const list = qs("iso-list");
    if (!list) return;
    renderIsoOptions(qs("forge-iso-select")?.value || "");
    const cdromItems = isoItems.filter(item => item.cdrom_attachable || String(item.kind || "").toLowerCase() === "iso");
    if (!cdromItems.length) {
      list.innerHTML = `<div class="iso-row"><div><strong>PUSTY ISO VAULT</strong><small>Pobierz obraz .iso albo wgraj plik .iso do ISO Vault. Dyski .qcow2/.raw/.img sa pokazywane osobno w VM CONFIG.</small></div></div>`;
      return;
    }
    list.innerHTML = cdromItems.map(item => `
      <div class="iso-row">
        <div>
          <strong>${esc(item.name)}</strong>
          <small>${esc(item.kind || "iso")} | ${esc(item.size_label || humanBytes(item.size))} | ${esc(item.modified || "")}</small>
          <small>${esc(item.path)}</small>
        </div>
        <button class="nav-btn" style="margin:0;padding:6px 8px;border-color:var(--acc-cyan);color:var(--acc-cyan);" onclick="document.getElementById('forge-iso-select').value='${esc(item.path)}';forgeStatus('Wybrane ISO: ${esc(item.name).replaceAll("'", "\\'")}')">USE</button>
      </div>
    `).join("");
  }

  function renderDiskList() {
    const list = qs("disk-list");
    if (!list) return;
    renderOpenCoreDatalist();
    if (!diskItems.length) {
      list.innerHTML = `<div class="iso-row"><div><strong>DYSK VAULT PUSTY</strong><small>Tutaj pojawiaja sie .qcow2/.raw/.img. Podpinanie dyskow jest osobne od ISO/CD-ROM.</small></div></div>`;
      return;
    }
    list.innerHTML = `
      <div class="forge-title" style="margin-top:0;">DYSKI VM <span style="color:#888;font-size:10px;">.qcow2/.raw/.img - nie CD-ROM</span></div>
      ${diskItems.map(item => `
        <div class="iso-row">
          <div>
            <strong>${esc(item.name)}</strong>
            <small>${esc(item.kind || "disk")} | ${esc(item.size_label || humanBytes(item.size))} | ${esc(item.modified || "")}</small>
            <small>${esc(item.path)}</small>
          </div>
          <div style="display:flex;gap:6px;align-items:center;flex-wrap:wrap;justify-content:flex-end;">
            ${isOpenCoreItem(item) ? `<button class="nav-btn" style="margin:0;padding:6px 8px;border-color:var(--acc-warn);color:var(--acc-warn);" onclick="document.getElementById('forge-opencore').value='${esc(item.path)}';forgeStatus('Wybrane OpenCore: ${esc(item.name).replaceAll("'", "\\'")}')">USE OPENCORE</button>` : ""}
            <span class="proc-pill" style="border-color:var(--acc-cyan);color:var(--acc-cyan);">DYSK</span>
          </div>
        </div>
      `).join("")}
    `;
  }

  function renderDownloads() {
    const box = qs("iso-downloads");
    if (!box) return;
    const active = isoDownloads.filter(job => ["queued", "running"].includes(String(job.status || "")));
    if (window.NexusTransfers && typeof window.NexusTransfers.syncRemoteJobs === "function") {
      window.NexusTransfers.syncRemoteJobs(isoDownloads.map(job => ({
        id: `iso:${job.id}`,
        label: `ISO: ${job.filename || "obraz"}`,
        loaded: job.downloaded || 0,
        total: job.total || 0,
        status: job.status,
        detail: job.error || job.target || "",
      })));
    }
    box.innerHTML = active.length ? active.map(job => {
      const total = Number(job.total || 0);
      const done = Number(job.downloaded || 0);
      const pct = total ? Math.round((done / total) * 100) : 0;
      return `<div class="download-row"><b style="color:#fff;">${esc(job.filename)}</b><br>${esc(job.status)} | ${humanBytes(done)}${total ? " / " + humanBytes(total) + " (" + pct + "%)" : ""}</div>`;
    }).join("") : "";
  }

  function renderIsoSources() {
    const grid = qs("iso-source-grid");
    if (!grid) return;
    grid.innerHTML = isoSources.map(src => {
      const direct = src.mode === "direct" && src.url;
      const filename = direct ? String(src.url).split("/").pop() : "";
      return `
        <div class="source-card ${direct ? "direct" : "manual"}">
          <strong>${esc(src.name)}</strong>
          <small>${esc(src.family)} | ${direct ? "direct download" : "manual source"}</small>
          <div class="nx-mod-actions">
            ${direct ? `<button class="nav-btn" onclick="downloadIso('${esc(src.url)}','${esc(filename)}')">POBIERZ</button>` : ""}
            <button class="nav-btn" onclick="window.open('${esc(src.source_page || src.url)}','_blank','noopener')">ZRODLO</button>
          </div>
        </div>
      `;
    }).join("");
  }

  async function loadIsoVault() {
    try {
      const data = await (await apiFetch("/api/vms/iso/list")).json();
      isoItems = data.cdrom_items || (data.items || []).filter(item => item.cdrom_attachable || String(item.kind || "").toLowerCase() === "iso");
      diskItems = data.disk_items || (data.items || []).filter(item => item.disk_attachable || ["qcow2", "raw", "img"].includes(String(item.kind || "").toLowerCase()));
      isoDownloads = data.downloads || [];
      const roots = qs("iso-roots");
      if (roots) roots.textContent = (data.roots || []).join(" | ");
      renderDownloads();
      renderIsoList();
      renderDiskList();
      const hasActive = isoDownloads.some(job => ["queued", "running"].includes(String(job.status || "")));
      if (hasActive && !isoPollTimer) isoPollTimer = setInterval(loadIsoVault, 1800);
      if (!hasActive && isoPollTimer) {
        clearInterval(isoPollTimer);
        isoPollTimer = null;
      }
      const preset = presetById(selectedOsId);
      if (preset && !(qs("forge-iso-select")?.value)) renderIsoOptions(pickIsoPath(preset));
    } catch (err) {
      const list = qs("iso-list");
      if (list) list.innerHTML = `<div class="download-row" style="color:var(--acc-crit);">Nie udalo sie pobrac ISO Vault.</div>`;
    }
  }

  async function loadOsForge() {
    installPage();
    try {
      const [catalogData] = await Promise.all([
        (await apiFetch("/api/vms/os-catalog")).json(),
        loadIsoVault(),
        loadDriverVault(),
      ]);
      osCatalog = catalogData.catalog || [];
      isoSources = catalogData.sources || [];
      const tools = catalogData.tools || {};
      const toolsLabel = qs("forge-tools");
      if (toolsLabel) {
        toolsLabel.textContent = `${tools.backend || "none"} | virt-install: ${tools.virt_install ? "OK" : "BRAK"} | qemu-img: ${tools.qemu_img ? "OK" : "BRAK"}`;
        toolsLabel.style.color = tools.virt_install && tools.qemu_img ? "#0f0" : "var(--acc-warn)";
      }
      const select = qs("forge-os-select");
      if (select) {
        select.innerHTML = osCatalog.map(item => `<option value="${esc(item.id)}">${esc(item.family)} / ${esc(item.name)}</option>`).join("");
      }
      renderIsoSources();
      renderDriverList();
      const current = presetById(selectedOsId) || presetById("debian");
      if (current) fillForgeFromPreset(current, !qs("forge-vm-name")?.value);
    } catch (err) {
      forgeStatus("OS FORGE nie moze pobrac katalogu systemow.", false);
    }
  }

  async function downloadIso(url, filename) {
    const sourceUrl = url || qs("iso-url")?.value || "";
    const targetName = filename || qs("iso-filename")?.value || "";
    if (!sourceUrl) {
      forgeStatus("Wklej URL do obrazu ISO/IMG/QCOW2.", false);
      return;
    }
    try {
      forgeStatus("Dodaje pobieranie ISO do kolejki...", null);
      const response = await apiFetch("/api/vms/iso/download", {
        method: "POST",
        body: JSON.stringify({ url: sourceUrl, filename: targetName }),
      });
      const job = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(job.detail || "Nie udalo sie uruchomic pobierania ISO");
      if (qs("iso-url") && !url) qs("iso-url").value = "";
      if (qs("iso-filename") && !filename) qs("iso-filename").value = "";
      if (window.NexusTransfers && typeof window.NexusTransfers.trackRemoteJobs === "function") {
        window.NexusTransfers.trackRemoteJobs([{
          id: `iso:${job.id}`,
          label: `ISO: ${job.filename || targetName || "obraz"}`,
          loaded: job.downloaded || 0,
          total: job.total || 0,
          status: job.status || "queued",
          detail: job.target || sourceUrl,
        }], () => loadIsoVault());
      }
      forgeStatus(`ISO w kolejce: ${job.filename || targetName || "obraz"}`, true);
      await loadIsoVault();
    } catch (err) {
      forgeStatus(err.message || "Blad pobierania ISO.", false);
    }
  }

  async function turboUploadIsoVault() {
    const input = qs("iso-upload-file");
    const files = Array.from(input?.files || []);
    if (!files.length) return forgeStatus("Wybierz plik .iso, opencore.qcow2 albo dysk VM.", false);
    const chunkSize = 5 * 1024 * 1024;
    const concurrency = 6;
    try {
      for (const file of files) {
        if (!/\.(iso|qcow2|raw|img)$/i.test(file.name)) {
          throw new Error(`${file.name}: przyjmuje tylko .iso, .qcow2, .raw albo .img`);
        }
        forgeStatus(`Turbo upload start: ${file.name} / ${humanBytes(file.size)}`, null);
        const init = await apiJson("/api/vms/upload/init", {
          method: "POST",
          body: JSON.stringify({ filename: file.name, size: file.size, purpose: "iso", chunk_size: chunkSize, overwrite: false })
        });
        let nextPart = 0;
        let uploaded = 0;
        const partCount = Number(init.part_count || Math.ceil(file.size / chunkSize));
        const uploadPart = async partNumber => {
          const start = partNumber * Number(init.chunk_size || chunkSize);
          const end = Math.min(file.size, start + Number(init.chunk_size || chunkSize));
          const blob = file.slice(start, end);
          await apiJson(`/api/vms/upload/${encodeURIComponent(init.upload_id)}/parts/${partNumber}`, {
            method: "PUT",
            headers: { "Content-Type": "application/octet-stream" },
            body: blob
          });
          uploaded += blob.size;
          const pct = file.size ? Math.round((uploaded / file.size) * 100) : 100;
          forgeStatus(`Turbo upload ${file.name}: ${humanBytes(uploaded)} / ${humanBytes(file.size)} (${pct}%)`, null);
          if (window.NexusTransfers && typeof window.NexusTransfers.syncRemoteJobs === "function") {
            window.NexusTransfers.syncRemoteJobs([{
              id: `vmupload:${init.upload_id}`,
              label: `Turbo VM: ${file.name}`,
              loaded: uploaded,
              total: file.size,
              status: "running",
              detail: init.target || "",
            }]);
          }
        };
        const workers = Array.from({ length: Math.min(concurrency, partCount) }, async () => {
          while (nextPart < partCount) {
            const part = nextPart++;
            await uploadPart(part);
          }
        });
        await Promise.all(workers);
        forgeStatus(`Skladam plik na serwerze: ${file.name}`, null);
        const complete = await apiJson("/api/vms/upload/complete", {
          method: "POST",
          body: JSON.stringify({ upload_id: init.upload_id })
        });
        forgeStatus(`Gotowe: ${complete.path || file.name}`, true);
      }
      if (input) input.value = "";
      await loadIsoVault();
    } catch (err) {
      forgeStatus(err.message || "Turbo upload nie powiodl sie.", false);
    }
  }

  function isCupertinoPreset(preset) {
    const text = `${preset?.id || ""} ${preset?.name || ""} ${preset?.family || ""}`.toLowerCase();
    return /macos|apple|darwin/.test(text);
  }

  async function cupertinoCheckForge() {
    const vmName = qs("forge-vm-name")?.value || "";
    const bootloader = qs("forge-opencore")?.value || "opencore.qcow2";
    const ovmfCode = qs("forge-ovmf-code")?.value || "";
    const ovmfVars = qs("forge-ovmf-vars")?.value || "";
    try {
      forgeStatus("Cupertino Check: sprawdzam OpenCore, OVMF i VM...", null);
      const params = new URLSearchParams({
        vm_name: vmName,
        bootloader,
        ovmf_code_path: ovmfCode,
        ovmf_vars_path: ovmfVars,
      });
      const data = await apiJson(`/api/vms/cupertino/prerequisites?${params.toString()}`);
      const missing = data.missing?.length ? ` Braki: ${data.missing.join(", ")}` : "";
      forgeStatus(`${data.status || "status"}: ${data.ready ? "gotowe do startu" : "wymaga uzupelnienia"}.${missing}`, !!data.ready);
      openHyperModal("CUPERTINO CHECK", `<pre style="white-space:pre-wrap;color:#9cf;">${esc(JSON.stringify(data, null, 2))}</pre>`);
    } catch (err) {
      forgeStatus(err.message || "Cupertino Check nie powiodl sie.", false);
    }
  }

  async function createForgeVm() {
    const preset = presetById(qs("forge-os-select")?.value || selectedOsId);
    const isoPath = qs("forge-iso-select")?.value || "";
    const payload = {
      name: qs("forge-vm-name")?.value || autoVmName(preset),
      os_id: preset?.id || selectedOsId,
      iso_path: isoPath,
      driver_path: qs("forge-driver-select")?.value || "",
      driver_categories: collectDriverCategories(),
      memory_mb: Number(qs("forge-memory")?.value || preset?.memory_mb || 1024),
      vcpus: Number(qs("forge-vcpus")?.value || preset?.vcpus || 1),
      disk_gb: Number(qs("forge-disk")?.value || preset?.disk_gb || 16),
      start: true,
      network: "default",
    };
    if (!preset) return forgeStatus("Wybierz preset systemu.", false);
    if (!payload.iso_path) return forgeStatus("Wybierz ISO z ISO Vault albo najpierw je pobierz.", false);
    if (isCupertinoPreset(preset)) {
      const checked = !!qs("forge-byol")?.checked;
      const ok = checked || confirm("NEXUS dostarcza wylacznie infrastrukture BYOL. Potwierdzam, ze mam legalny obraz/licencje macOS oraz wlasny bootloader OpenCore. NEXUS nie dostarcza OSK/SMC ani chronionych komponentow Apple.");
      if (!ok) return forgeStatus("Cupertino Legal Shield: zaznacz BYOL, zeby kontynuowac.", false);
      if (qs("forge-byol")) qs("forge-byol").checked = true;
      payload.legal_byol_ack = true;
      payload.opencore_path = qs("forge-opencore")?.value || "opencore.qcow2";
      payload.ovmf_code_path = qs("forge-ovmf-code")?.value || "";
      payload.ovmf_vars_path = qs("forge-ovmf-vars")?.value || "";
    }
    try {
      forgeStatus(`Tworze VM ${payload.name}${payload.driver_categories.length ? " z wybranymi sterownikami: " + payload.driver_categories.join(", ") : ""}...`, null);
      const response = await apiFetch("/api/vms/create", { method: "POST", body: JSON.stringify(payload) });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.detail || "Tworzenie VM nie powiodlo sie");
      forgeStatus(`VM ${data.vm_id} utworzona. Otwieram konsole...`, true);
      notify("ok", "Tworzenie VM", `${data.vm_id}: backend potwierdzil utworzenie.`);
      if (typeof window.verifyVmActionEffect === "function") window.verifyVmActionEffect(data.vm_id, "start", 1200);
      await loadHyperDeck();
      setTimeout(() => openHyperConsole(data.vm_id, data.backend || "libvirt", data.name || data.vm_id), 1400);
    } catch (err) {
      forgeStatus(err.message || "Tworzenie VM nie powiodlo sie.", false);
      notify("error", "Tworzenie VM", err.message || "Tworzenie VM nie powiodlo sie.");
    }
  }

  function patchShow() {
    if (typeof window.show !== "function" || window.show.__hyperDeckPatched) return false;
    const original = window.show;
    function patchedShow(id, btn) {
      const result = original.apply(this, arguments);
      if (id === "hyper_deck") {
        setTimeout(loadHyperDeck, 80);
        setTimeout(loadOsForge, 140);
      }
      return result;
    }
    patchedShow.__hyperDeckPatched = true;
    window.show = patchedShow;
    return true;
  }

  function boot() {
    addStyles();
    installPage();
    addNavButton();
    patchShow();
    setTimeout(loadOsForge, 350);
    let tries = 0;
    const timer = setInterval(() => {
      tries++;
      installPage();
      const okNav = addNavButton();
      const okShow = patchShow();
      if ((okNav && okShow) || tries > 80) clearInterval(timer);
    }, 150);
    setTimeout(() => setHyperDeckTab(localStorage.getItem("nexus_hyperdeck_tab") || "vms"), 250);
  }

  window.loadHyperDeck = loadHyperDeck;
  window.loadOsForge = loadOsForge;
  window.loadIsoVault = loadIsoVault;
  window.loadDriverVault = loadDriverVault;
  window.setHyperDeckTab = setHyperDeckTab;
  window.renderForgeCatalog = renderForgeCatalog;
  window.renderHyperVmGrid = renderHyperVmGrid;
  window.selectForgePreset = selectForgePreset;
  window.downloadIso = downloadIso;
  window.turboUploadIsoVault = turboUploadIsoVault;
  window.cupertinoCheckForge = cupertinoCheckForge;
  window.extractVmDriver = extractVmDriver;
  window.createForgeVm = createForgeVm;
  window.forgeStatus = forgeStatus;
  window.hyperVmAction = hyperVmAction;
  window.hyperCupertinoStart = hyperCupertinoStart;
  window.openVmSnapshots = openVmSnapshots;
  window.openVmConfig = openVmConfig;
  window.openVmLogs = openVmLogs;
  window.openVmPorts = openVmPorts;
  window.openVmGuestAgent = openVmGuestAgent;
  window.createVmSnapshot = createVmSnapshot;
  window.revertVmSnapshot = revertVmSnapshot;
  window.deleteVmSnapshot = deleteVmSnapshot;
  window.saveVmConfig = saveVmConfig;
  window.attachVmIso = attachVmIso;
  window.openVmIsoPicker = openVmIsoPicker;
  window.openConsoleIsoPicker = openConsoleIsoPicker;
  window.attachConsoleIso = attachConsoleIso;
  window.startConsoleCupertino = startConsoleCupertino;
  window.copyConsoleOpenCoreToForge = copyConsoleOpenCoreToForge;
  window.ejectConsoleIso = ejectConsoleIso;
  window.repairConsoleMedia = repairConsoleMedia;
  window.attachVmDisk = attachVmDisk;
  window.openVmThinStatus = openVmThinStatus;
  window.applyVmThinPolicy = applyVmThinPolicy;
  window.openVmCompactPlan = openVmCompactPlan;
  window.executeVmCompact = executeVmCompact;
  window.setVmInternet = setVmInternet;
  window.repairVmMedia = repairVmMedia;
  window.createVmPort = createVmPort;
  window.deleteVmPort = deleteVmPort;
  window.deleteVmPrompt = deleteVmPrompt;
  window.checkVmAlerts = checkVmAlerts;
  window.putCommandInClipboardBox = putCommandInClipboardBox;
  window.closeHyperModal = closeHyperModal;
  window.openHyperConsole = openHyperConsole;
  window.openHyperConsoleFromDash = openHyperConsoleFromDash;
  window.closeHyperConsole = closeHyperConsole;
  window.sendHyperCtrlAltDel = sendHyperCtrlAltDel;
  window.sendHyperClipboard = sendHyperClipboard;
  window.typeHyperClipboardToVm = typeHyperClipboardToVm;
  window.readSystemClipboardToHyper = readSystemClipboardToHyper;
  window.fitHyperConsole = fitHyperConsole;
  window.setHyperCustomSize = setHyperCustomSize;
  window.clearHyperCustomSize = clearHyperCustomSize;
  window.centerHyperConsoleView = centerHyperConsoleView;
  window.toggleHyperFullscreen = toggleHyperFullscreen;
  window.restartHyperConsoleView = restartHyperConsoleView;
  window.toggleHyperPointer = toggleHyperPointer;
  window.toggleHyperCursorMode = toggleHyperCursorMode;
  window.repairHyperMouse = repairHyperMouse;
  window.resetHyperMouse = resetHyperMouse;
  window.toggleHyperAudioMute = toggleHyperAudioMute;
  window.toggleHyperKeyboard = toggleHyperKeyboard;
  window.sendHyperVirtualKey = sendHyperVirtualKey;
  window.hyperConsoleFocus = hyperConsoleFocus;

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
