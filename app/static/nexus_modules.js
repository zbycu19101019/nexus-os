(function () {
  const token = () => encodeURIComponent(localStorage.getItem("nexus_token") || "");
  const esc = (v) => String(v ?? "").replace(/[&<>"']/g, ch => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]));
  const qs = (id) => document.getElementById(id);
  const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));
  const deviceId = (() => {
    let id = localStorage.getItem("nexus_device_id");
    if (!id) {
      id = "dev-" + Math.random().toString(16).slice(2) + Date.now().toString(16);
      localStorage.setItem("nexus_device_id", id);
    }
    return id;
  })();

  let presenceTimer = null;
  let alertTimer = null;
  let knownAlerts = new Set();
  let p2pState = { room: "nexus", peer: deviceId.slice(-10), pc: null, channel: null, poll: null, seen: new Set(), chunks: [], meta: null };
  let nexusCanvasDraft = { name: "lab-topology", nodes: [], edges: [] };
  let nexusCanvasLinkFrom = null;

  function addModuleStyles() {
    if (qs("nexus-modules-style")) return;
    const style = document.createElement("style");
    style.id = "nexus-modules-style";
    style.textContent = `
      .nx-mod-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(210px,100%),1fr));gap:12px}
      .nx-mod-card{background:#090909;border:1px solid #252525;border-left:3px solid var(--acc-cyan);border-radius:6px;padding:12px;min-height:88px;box-sizing:border-box;min-width:0;overflow-wrap:anywhere}
      .nx-mod-card strong{display:block;color:#fff;margin-bottom:6px}
      .nx-mod-card small{color:#888;display:block;line-height:1.5}
      .nx-mod-actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}
      .nx-mod-actions .nav-btn{margin:0;padding:7px 9px;font-size:10px}
      .media-player{width:100%;min-width:0;background:#030303;border:1px solid #233;border-radius:6px;margin-bottom:14px;padding:12px;box-sizing:border-box}
      .audio-bars{display:flex;align-items:flex-end;gap:4px;height:42px;margin-top:10px}
      .audio-bars span{width:10px;background:var(--acc-cyan);box-shadow:0 0 8px var(--acc-cyan);animation:mxBar .7s infinite alternate}
      .audio-bars span:nth-child(2n){background:var(--acc-purple);animation-delay:.2s}.audio-bars span:nth-child(3n){background:var(--acc-warn);animation-delay:.35s}
      @keyframes mxBar{from{height:7px}to{height:40px}}
      .bbs-post{background:#080808;border:1px solid #222;border-left:4px solid var(--acc-purple);border-radius:6px;padding:14px;margin-bottom:12px}
      .bbs-avatar{width:34px;height:34px;border-radius:50%;background:#111;border:1px solid var(--acc-cyan);display:flex;align-items:center;justify-content:center;color:var(--acc-cyan);font-weight:bold;flex:0 0 auto}
      .bbs-img{max-width:100%;max-height:260px;border:1px solid #333;border-radius:4px;margin-top:10px;object-fit:contain;background:#000}
      .gallery-thumb{height:150px;width:100%;object-fit:cover;border-radius:4px;border:1px solid #222;background:#000;cursor:pointer}
      .lightbox{position:fixed;inset:0;background:rgba(0,0,0,.92);z-index:25000;display:none;align-items:center;justify-content:center;padding:22px;box-sizing:border-box}
      .lightbox.active{display:flex}.lightbox img{max-width:74vw;max-height:86vh;border:1px solid var(--acc-cyan);box-shadow:0 0 30px rgba(0,255,255,.25);filter:contrast(1.08)}
      .lightbox-info{width:250px;margin-left:18px;color:#aaa;font-size:12px}
      .kanban-board{display:grid;grid-template-columns:repeat(3,minmax(220px,1fr));gap:12px;align-items:start}
      .kanban-col{background:#070707;border:1px solid #233;border-top:3px solid var(--acc-cyan);border-radius:6px;padding:10px;min-height:320px;min-width:0}
      .kanban-card{background:#111;border:1px solid #333;border-left:3px solid var(--acc-warn);border-radius:5px;padding:10px;margin:8px 0;cursor:grab}
      .kanban-card strong{color:#fff}.kanban-card p{color:#aaa;font-size:11px;line-height:1.4;margin:6px 0 0}
      .drop-count{font-size:28px;color:var(--acc-cyan);font-weight:bold;text-shadow:0 0 12px rgba(0,255,255,.35)}
      .radar-wrap{display:grid;grid-template-columns:minmax(min(260px,100%),1fr) minmax(min(240px,100%),380px);gap:14px}
      .radar-screen{position:relative;min-height:340px;border:1px solid #164;background:radial-gradient(circle at center,rgba(0,255,255,.18),rgba(0,0,0,.04) 36%,#030505 70%);overflow:hidden;border-radius:6px}
      .radar-screen:before{content:"";position:absolute;inset:-30%;background:conic-gradient(from 0deg,rgba(0,255,255,.45),transparent 18%,transparent);animation:nxSweep 3.5s linear infinite}
      .radar-screen:after{content:"";position:absolute;inset:12%;border:1px solid rgba(0,255,255,.18);border-radius:50%;box-shadow:0 0 0 55px rgba(0,255,255,.05),0 0 0 110px rgba(0,255,255,.035)}
      @keyframes nxSweep{to{transform:rotate(360deg)}}
      .radar-dot{position:absolute;width:12px;height:12px;border-radius:50%;background:var(--acc-cyan);box-shadow:0 0 16px var(--acc-cyan);z-index:2}
      .radar-dot.idle{background:var(--acc-warn);box-shadow:0 0 16px var(--acc-warn)}
      .alert-row{background:#080808;border:1px solid #222;border-left:4px solid #555;border-radius:6px;padding:12px;margin-bottom:10px}
      .alert-row.critical{border-left-color:var(--acc-crit)}.alert-row.warn{border-left-color:var(--acc-warn)}.alert-row.info{border-left-color:var(--acc-cyan)}
      .p2p-log{height:170px;overflow:auto;background:#030303;border:1px solid #222;border-radius:6px;padding:10px;color:#aaa;font-size:11px;white-space:pre-wrap}
      .karma-bar{height:12px;background:#111;border:1px solid #333;border-radius:10px;overflow:hidden}.karma-bar span{display:block;height:100%;background:linear-gradient(90deg,var(--acc-cyan),var(--acc-warn));box-shadow:0 0 12px var(--acc-cyan)}
      .object-status-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:10px;margin-bottom:12px}
      .object-kv{background:#060606;border:1px solid #223;border-left:3px solid var(--acc-cyan);border-radius:5px;padding:10px}
      .object-kv b{display:block;color:#fff;margin-bottom:5px}.object-kv span{color:#888;font-size:11px;overflow-wrap:anywhere}
      .object-pill{display:inline-block;border:1px solid #244;background:#040809;color:var(--acc-cyan);border-radius:4px;padding:3px 6px;margin:2px;font-size:10px}
      .object-token-row{background:#080808;border:1px solid #222;border-left:3px solid var(--acc-purple);border-radius:5px;padding:10px;display:grid;gap:6px;min-width:0}
      .object-token-secret{width:100%;min-height:54px;background:#030303;border:1px solid var(--acc-warn);color:var(--acc-warn);font-family:monospace;font-size:11px;padding:8px;box-sizing:border-box}
      .coop-link-box{width:100%;min-height:52px;background:#030303;border:1px solid #244;color:var(--acc-cyan);font:11px monospace;padding:8px;box-sizing:border-box;resize:vertical}
      .sleep-state{border-left-color:var(--acc-purple)}
      .canvas-shell{display:grid;grid-template-columns:minmax(180px,260px) minmax(320px,1fr);gap:12px;align-items:stretch}
      .canvas-tools{background:#070707;border:1px solid #233;border-radius:6px;padding:10px}
      .canvas-board{position:relative;min-height:520px;border:1px solid #244;border-radius:6px;background:
        linear-gradient(rgba(0,255,255,.05) 1px,transparent 1px),
        linear-gradient(90deg,rgba(0,255,255,.05) 1px,transparent 1px),#020405;background-size:28px 28px;overflow:hidden}
      .canvas-wire{position:absolute;inset:0;width:100%;height:100%;pointer-events:none;z-index:1}
      .canvas-node{position:absolute;z-index:2;width:126px;min-height:58px;background:#090909;border:1px solid #2a5;border-left:4px solid var(--acc-cyan);border-radius:6px;padding:9px;box-sizing:border-box;cursor:grab;user-select:none;box-shadow:0 0 18px rgba(0,255,255,.12)}
      .canvas-node.router{border-left-color:var(--acc-warn)}.canvas-node.database{border-left-color:var(--acc-purple)}.canvas-node.windows{border-left-color:#66f}
      .canvas-node.selected{outline:2px solid var(--acc-warn);box-shadow:0 0 22px rgba(255,170,0,.28)}
      .canvas-node strong{display:block;color:#fff;font-size:11px}.canvas-node small{display:block;color:#888;font-size:10px;margin-top:5px}
      .commander-log{height:220px;overflow:auto;background:#030303;border:1px solid #222;border-radius:6px;padding:10px;color:#aaa;font-size:11px;white-space:pre-wrap}
      .archiver-list{height:310px;overflow:auto;background:#030303;border:1px solid #222;border-radius:6px;padding:8px}
      .archiver-row{display:grid;grid-template-columns:24px 1fr 90px;gap:8px;align-items:center;border-bottom:1px solid #111;padding:6px;color:#bbb;font-size:11px}
      .bastion-badge{display:inline-block;border:1px solid #333;color:var(--acc-cyan);padding:2px 6px;border-radius:4px;font-size:10px;margin-right:5px}
      .worker-editor{height:260px;background:#030303;border:1px solid #244;color:#ddd;font:12px Consolas,monospace;padding:10px;resize:vertical;width:100%;box-sizing:border-box}
      .vault-link{width:100%;min-height:70px;background:#030303;border:1px solid var(--acc-warn);color:var(--acc-warn);font:11px Consolas,monospace;padding:8px;box-sizing:border-box}
      #global-terminal{position:fixed;left:0;right:0;top:0;z-index:39000;background:rgba(2,5,6,.98);border-bottom:1px solid #244;box-shadow:0 18px 42px rgba(0,0,0,.75);transform:translateY(-105%);transition:transform .2s ease;padding:12px}
      #global-terminal.open{transform:translateY(0)}
      .global-terminal-row{display:grid;grid-template-columns:1fr auto;gap:8px}
      #global-terminal-log{max-height:170px;overflow:auto;background:#030303;border:1px solid #222;border-radius:6px;padding:8px;margin-top:8px;color:#aaa;font-size:11px;white-space:pre-wrap}
      .hyper-toolbar{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:12px}
      .hyper-idea{min-height:116px;position:relative;overflow:hidden}
      .hyper-idea:after{content:"";position:absolute;inset:auto 0 0 0;height:2px;background:linear-gradient(90deg,var(--acc-cyan),var(--acc-purple),var(--acc-warn));opacity:.7}
      .hyper-badge{display:inline-block;border:1px solid #333;border-radius:4px;padding:2px 6px;color:#999;font-size:10px;margin-bottom:8px}
      .hyper-ticker{position:fixed;top:0;left:0;right:0;z-index:26000;background:#020202;border-bottom:1px solid #244;color:var(--acc-cyan);font-size:11px;white-space:nowrap;overflow:hidden;padding:5px 0;box-shadow:0 0 18px rgba(0,255,255,.18)}
      .hyper-ticker span{display:inline-block;padding-left:100%;animation:hyperTicker 28s linear infinite}
      @keyframes hyperTicker{to{transform:translateX(-100%)}}
      #nx-hyper-bg{position:fixed;inset:0;z-index:0;pointer-events:none;opacity:.25}
      body.nx-hyper-bg #content,body.nx-hyper-bg .sidebar,body.nx-hyper-bg #nx-drawer{position:relative;z-index:1}
      body.nx-crt:after{content:"";position:fixed;inset:0;pointer-events:none;z-index:27000;background:repeating-linear-gradient(0deg,rgba(255,255,255,.045),rgba(255,255,255,.045) 1px,transparent 1px,transparent 4px);mix-blend-mode:overlay}
      .gallery-thumb:hover{filter:contrast(1.25) saturate(1.45) hue-rotate(12deg);transform:translateY(-1px);box-shadow:0 0 18px rgba(0,255,255,.25)}
      #nexus-floating-chat{position:fixed;left:14px;bottom:0;z-index:18000;width:min(360px,calc(100vw - 28px));font-family:monospace;transition:transform .28s ease}
      body.auth-locked #nexus-floating-chat{display:none}
      #nexus-floating-chat.collapsed{transform:translateY(calc(100% - 38px))}
      #nexus-floating-chat.collapsed .floating-chat-panel{visibility:hidden;pointer-events:none}
      .floating-chat-handle{width:132px;height:38px;background:rgba(5,10,15,.96);border:1px solid var(--acc-cyan);border-bottom:none;color:var(--acc-cyan);font-weight:bold;border-radius:8px 8px 0 0;cursor:pointer;box-shadow:0 0 14px rgba(0,255,255,.2)}
      .floating-chat-panel{background:rgba(5,8,10,.97);border:1px solid #244;border-left:3px solid var(--acc-cyan);border-radius:0 8px 0 0;padding:10px;box-shadow:0 -5px 22px rgba(0,0,0,.65)}
      .floating-chat-log{height:220px;overflow:auto;background:#030303;border:1px solid #222;border-radius:4px;padding:8px;margin-bottom:8px}
      .floating-chat-msg{border-left:2px solid var(--acc-cyan);padding:6px 7px;margin-bottom:6px;background:#080808;color:#ddd;font-size:11px}
      .floating-chat-msg small{color:#777;display:block;margin-bottom:3px}
      .floating-chat-row{display:grid;grid-template-columns:92px 1fr 68px;gap:6px}
      .floating-chat-row input{margin:0;padding:8px;font-size:11px}
      @media(max-width:768px){
        .kanban-board,.radar-wrap,.object-status-grid{grid-template-columns:1fr!important}
        .lightbox{flex-direction:column}.lightbox img{max-width:95vw}.lightbox-info{width:95vw;margin:12px 0 0}
        #object_storage .card,#cloud_drive .card,#usb_devices .card,#secure_drop .card,#p2p_drop .card,#neural_alerts .card,#media_deck .card,#visual_archive .card{grid-template-columns:1fr!important;overflow-x:hidden}
        .source-grid,.driver-matrix,.nx-mod-grid{grid-template-columns:1fr!important}
        .nx-mod-actions .nav-btn{flex:1 1 calc(50% - 8px);white-space:normal}
        .canvas-shell{grid-template-columns:1fr}.canvas-board{min-height:430px}
        .global-terminal-row{grid-template-columns:1fr}
      }
      @media(max-width:520px){#nexus-floating-chat{bottom:54px;width:calc(100vw - 28px)}#nexus-floating-chat.collapsed{transform:translateY(calc(100% - 34px))}.floating-chat-handle{height:34px;width:124px;font-size:10px}.floating-chat-row{grid-template-columns:1fr}.floating-chat-row input{font-size:10px;padding:7px}.floating-chat-row .nav-btn{font-size:9px;padding:7px 5px}}
    `;
    document.head.appendChild(style);
  }

  function page(id, html) {
    if (qs(id)) return;
    const div = document.createElement("div");
    div.id = id;
    div.className = "page";
    div.innerHTML = html;
    qs("content").appendChild(div);
  }

  const NAV_GROUPS = {
    media_deck: "data",
    visual_archive: "data",
    secure_drop: "data",
    object_storage: "data",
    cloud_drive: "data",
    usb_devices: "ops",
    nexus_shield: "ops",
    time_machine: "ops",
    cloud_init: "ops",
    api_webhooks: "ops",
    hardware_telemetry: "core",
    nexus_coop: "ops",
    hyper_sleep: "ops",
    nexus_canvas: "ops",
    nexus_forge: "ops",
    ai_commander: "intel",
    nexus_archiver: "data",
    nexus_bastion: "ops",
    nexus_workers: "ops",
    secure_vault: "data",
    global_terminal_page: "social",
    p2p_drop: "data",
    cyber_bbs: "social",
    kanban: "social",
    presence_radar: "core",
    neural_alerts: "core",
    morning_briefing: "core",
    sys_karma: "core",
    web3_gate: "intel",
    hyperspace_lab: "lab",
  };

  function addButton(id, label, cls = "nx-btn-cyan", group = NAV_GROUPS[id] || "lab") {
    if (window.nexusAddNavButton) {
      window.nexusAddNavButton({ id, label, cls, group });
      return;
    }
    const drawer = qs("nx-drawer-content");
    if (drawer && !drawer.querySelector(`[data-target="${id}"]`)) {
      const btn = document.createElement("button");
      btn.className = `nx-btn ${cls}`;
      btn.dataset.target = id;
      btn.textContent = label;
      btn.onclick = () => { show(id, btn); if (window.closeDrawer) closeDrawer(); };
      drawer.appendChild(btn);
    }
  }

  function installPages() {
    page("media_deck", `
      <h2 style="color:var(--acc-cyan);border-bottom:1px solid #044;padding-bottom:10px;">NEXUS MEDIA DECK</h2>
      <div class="media-player">
        <div id="media-title" style="color:#fff;font-weight:bold;margin-bottom:8px;">Wybierz plik z biblioteki</div>
        <video id="media-video" controls style="display:none;width:100%;max-height:420px;background:#000;"></video>
        <audio id="media-audio" controls style="display:none;width:100%;"></audio>
        <img id="media-image" style="display:none;max-width:100%;max-height:420px;background:#000;border:1px solid #222;">
        <div class="audio-bars"><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span></div>
      </div>
      <div class="card"><button class="nav-btn" onclick="loadMediaDeck()">ODSWIEZ BIBLIOTEKE</button><span style="color:#888;font-size:11px;margin-left:10px;">Folder: /root/nexus2/media</span></div>
      <div id="media-grid" class="nx-mod-grid"></div>
    `);
    page("cyber_bbs", `
      <h2 style="color:var(--acc-purple);border-bottom:1px solid #303;padding-bottom:10px;">CYBER BBS</h2>
      <div class="card" style="background:#08050a;border-color:#303;">
        <textarea id="bbs-text" class="cyber-input" placeholder="Nowy wpis na tablice..." style="height:90px;"></textarea>
        <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;"><input type="file" id="bbs-image" class="cyber-input" style="flex:1;margin:0;" accept="image/*"><button class="nav-btn" style="margin:0;border-color:var(--acc-purple);color:var(--acc-purple);" onclick="createBBSPost()">PUBLIKUJ</button></div>
      </div>
      <div id="bbs-feed"></div>
    `);
    page("visual_archive", `
      <h2 style="color:var(--acc-warn);border-bottom:1px solid #440;padding-bottom:10px;">VISUAL ARCHIVE</h2>
      <div class="card"><button class="nav-btn" onclick="loadGallery()">SKANUJ OBRAZY</button><span style="color:#888;font-size:11px;margin-left:10px;">Foldery: media + visual_archive</span></div>
      <div id="gallery-grid" class="nx-mod-grid"></div>
      <div id="gallery-lightbox" class="lightbox" onclick="closeGalleryLightbox(event)"><img id="gallery-full"><div class="lightbox-info" id="gallery-info"></div></div>
    `);
    page("kanban", `
      <h2 style="color:var(--acc-cyan);border-bottom:1px solid #044;padding-bottom:10px;">TABLICA OPERACYJNA</h2>
      <div class="card" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px;"><input id="kanban-title" class="cyber-input" style="margin:0;" placeholder="Tytul karty"><input id="kanban-body" class="cyber-input" style="margin:0;" placeholder="Opis"><select id="kanban-col" class="cyber-input" style="margin:0;"><option value="ideas">POMYSLY</option><option value="doing">W TRAKCIE</option><option value="done">ZROBIONE</option></select><button class="nav-btn" style="margin:0;" onclick="addKanbanCard()">DODAJ KARTE</button></div>
      <div id="kanban-board" class="kanban-board"></div>
    `);
    page("secure_drop", `
      <h2 style="color:var(--acc-crit);border-bottom:1px solid #400;padding-bottom:10px;">SECURE DROP</h2>
      <div class="card" style="display:grid;grid-template-columns:2fr 1fr auto;gap:10px;"><input id="drop-path" class="cyber-input" style="margin:0;" placeholder="/root/nexus2/media/plik.mp4"><input id="drop-title" class="cyber-input" style="margin:0;" placeholder="Nazwa linku"><button class="nav-btn" style="margin:0;border-color:var(--acc-crit);color:var(--acc-crit);" onclick="createDropShare()">GENERUJ LINK</button></div>
      <div id="drop-list" class="nx-mod-grid"></div>
    `);
    page("object_storage", `
      <h2 style="color:var(--acc-cyan);border-bottom:1px solid #044;padding-bottom:10px;">OBJECT STORAGE / MINIO S3</h2>
      <div class="card" style="display:grid;grid-template-columns:1fr 170px auto auto;gap:10px;align-items:center;">
        <input type="file" id="object-files" class="cyber-input" style="margin:0;" multiple>
        <select id="object-purpose" class="cyber-input" style="margin:0;">
          <option value="auto">AUTO ROUTE</option>
          <option value="iso">ISO / VM</option>
          <option value="driver">STEROWNIKI</option>
          <option value="audio">AUDIO</option>
          <option value="video">VIDEO</option>
          <option value="image">OBRAZY</option>
          <option value="backup">BACKUP</option>
          <option value="drop">DROP</option>
        </select>
        <button class="nav-btn" style="margin:0;border-color:var(--acc-cyan);color:var(--acc-cyan);" onclick="uploadObjectStorageSelected()">WRZUC DO S3</button>
        <button class="nav-btn" style="margin:0;" onclick="loadObjectStorage()">ODSWIEZ</button>
      </div>
      <div id="object-status" class="object-status-grid"></div>
      <h3 style="color:var(--acc-purple);border-bottom:1px solid #303;padding-bottom:8px;">TOKEN VAULT</h3>
      <div class="card" style="display:grid;grid-template-columns:1fr 150px 110px 130px auto;gap:10px;align-items:center;">
        <input id="object-token-name" class="cyber-input" style="margin:0;" placeholder="nazwa tokenu np. telefon-backup">
        <select id="object-token-purpose" class="cyber-input" style="margin:0;">
          <option value="auto">AUTO</option>
          <option value="iso">ISO</option>
          <option value="driver">STEROWNIKI</option>
          <option value="audio">AUDIO</option>
          <option value="video">VIDEO</option>
          <option value="image">OBRAZY</option>
          <option value="backup">BACKUP</option>
          <option value="drop">DROP</option>
        </select>
        <input id="object-token-days" type="number" min="1" max="3650" value="30" class="cyber-input" style="margin:0;" title="dni waznosci">
        <input id="object-token-max" type="number" min="0" max="102400" value="0" class="cyber-input" style="margin:0;" title="limit MB, 0 bez limitu">
        <button class="nav-btn" style="margin:0;border-color:var(--acc-purple);color:var(--acc-purple);" onclick="createObjectToken()">GENERUJ</button>
      </div>
      <div id="object-token-result"></div>
      <div id="object-token-list" class="nx-mod-grid" style="margin-bottom:14px;"></div>
      <h3 style="color:var(--acc-cyan);border-bottom:1px solid #044;padding-bottom:8px;">OBIEKTY</h3>
      <div id="object-grid" class="nx-mod-grid"></div>
    `);
    page("cloud_drive", `
      <h2 style="color:var(--acc-cyan);border-bottom:1px solid #044;padding-bottom:10px;">CLOUD DRIVE / GOOGLE 2TB</h2>
      <div class="card" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px;align-items:end;">
        <div>
          <label style="color:#777;font-size:10px;">REMOTE</label>
          <input id="cloud-remote" class="cyber-input" style="margin:4px 0 0;" value="gdrive">
        </div>
        <div>
          <label style="color:#777;font-size:10px;">ROOT FOLDER</label>
          <input id="cloud-root" class="cyber-input" style="margin:4px 0 0;" value="NEXUS_CORE">
        </div>
        <button class="nav-btn" style="margin:0;border-color:var(--acc-cyan);color:var(--acc-cyan);" onclick="loadCloudDrive()">STATUS</button>
        <button class="nav-btn" style="margin:0;border-color:var(--acc-purple);color:var(--acc-purple);" onclick="listCloudDrive()">LISTUJ DRIVE</button>
      </div>
      <div id="cloud-status" class="object-status-grid"></div>
      <div class="card" style="display:grid;grid-template-columns:minmax(260px,1fr) minmax(260px,1fr);gap:12px;">
        <div>
          <label style="color:#777;font-size:10px;">TOKEN JSON Z RCLONE AUTHORIZE</label>
          <textarea id="cloud-token" class="cyber-input" style="height:130px;margin:4px 0 8px;" placeholder='{"access_token":"...","refresh_token":"..."}'></textarea>
          <button class="nav-btn" style="margin:0;border-color:var(--acc-warn);color:var(--acc-warn);" onclick="saveCloudDriveToken()">ZAPISZ TOKEN GOOGLE</button>
        </div>
        <div>
          <label style="color:#777;font-size:10px;">KOMENDA TOKENU NA TWOIM PC</label>
          <textarea class="cyber-input" readonly style="height:130px;margin:4px 0 8px;">rclone authorize "drive"</textarea>
          <div id="cloud-config-result" style="color:#888;font-size:11px;"></div>
        </div>
      </div>
      <div class="card">
        <div style="display:flex;gap:8px;flex-wrap:wrap;">
          <button class="nav-btn" style="margin:0;border-color:var(--acc-cyan);color:var(--acc-cyan);" onclick="startCloudSync('backups','copy')">COPY BACKUPY</button>
          <button class="nav-btn" style="margin:0;border-color:var(--acc-warn);color:var(--acc-warn);" onclick="startCloudSync('server_backups','copy')">COPY SERVER BACKUP</button>
          <button class="nav-btn" style="margin:0;border-color:var(--acc-purple);color:var(--acc-purple);" onclick="startCloudSync('isos','copy')">COPY ISO</button>
          <button class="nav-btn" style="margin:0;border-color:#0f0;color:#0f0;" onclick="startCloudSync('media','copy')">COPY MEDIA</button>
          <button class="nav-btn" style="margin:0;border-color:#777;color:#aaa;" onclick="startCloudSync('vm_images','copy')">COPY VM IMAGES</button>
        </div>
      </div>
      <div class="card" style="display:grid;grid-template-columns:minmax(240px,1.4fr) minmax(180px,.8fr) 110px auto;gap:10px;align-items:end;">
        <div>
          <label style="color:#777;font-size:10px;">PLIK / FOLDER NA SERWERZE</label>
          <input id="cloud-push-path" class="cyber-input" style="margin:4px 0 0;" placeholder="/root/nexus2/media/plik.mp4">
        </div>
        <div>
          <label style="color:#777;font-size:10px;">FOLDER W GOOGLE DRIVE</label>
          <input id="cloud-push-dest" class="cyber-input" style="margin:4px 0 0;" value="server-files">
        </div>
        <select id="cloud-push-mode" class="cyber-input" style="margin:0;">
          <option value="copy">COPY</option>
          <option value="move">MOVE</option>
        </select>
        <button class="nav-btn" style="margin:0;border-color:#0f0;color:#0f0;" onclick="pushServerFileToDrive()">WYSLIJ DO DRIVE</button>
        <div id="cloud-push-result" style="grid-column:1/-1;color:#888;font-size:11px;">Wrzuca plik/folder bezposrednio z VPS do Google Drive przez rclone.</div>
      </div>
      <div id="cloud-sources" class="nx-mod-grid"></div>
      <h3 style="color:var(--acc-purple);border-bottom:1px solid #303;padding-bottom:8px;">ZADANIA RCLONE</h3>
      <div id="cloud-jobs" class="nx-mod-grid"></div>
      <h3 style="color:var(--acc-cyan);border-bottom:1px solid #044;padding-bottom:8px;">GOOGLE DRIVE LISTING</h3>
      <div id="cloud-list" class="nx-mod-grid"></div>
    `);
    page("nexus_shield", `
      <h2 style="color:var(--acc-warn);border-bottom:1px solid #440;padding-bottom:10px;">NEXUS SHIELD / FIREWALL</h2>
      <div class="card" style="display:grid;grid-template-columns:110px minmax(170px,1fr) 110px 120px minmax(160px,1fr) auto;gap:10px;align-items:end;">
        <select id="shield-action" class="cyber-input" style="margin:0;"><option value="block">BLOCK</option><option value="allow">ALLOW</option></select>
        <input id="shield-source" class="cyber-input" style="margin:0;" placeholder="IP/CIDR np. 1.2.3.4/32">
        <select id="shield-proto" class="cyber-input" style="margin:0;"><option value="all">ALL</option><option value="tcp">TCP</option><option value="udp">UDP</option><option value="icmp">ICMP</option></select>
        <input id="shield-port" type="number" min="0" max="65535" class="cyber-input" style="margin:0;" placeholder="port">
        <input id="shield-note" class="cyber-input" style="margin:0;" placeholder="opis reguly">
        <button class="nav-btn" style="margin:0;border-color:var(--acc-warn);color:var(--acc-warn);" onclick="addShieldRule()">DODAJ</button>
      </div>
      <div id="shield-status" class="object-status-grid"></div>
      <h3 style="color:var(--acc-cyan);border-bottom:1px solid #044;padding-bottom:8px;">PORT FORWARDING / DDOS WATCH</h3>
      <div id="shield-grid" class="nx-mod-grid"></div>
    `);
    page("time_machine", `
      <h2 style="color:var(--acc-purple);border-bottom:1px solid #303;padding-bottom:10px;">TIME MACHINE / SNAPSHOT POLICIES</h2>
      <div class="card" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:10px;align-items:end;">
        <input id="tm-vm" class="cyber-input" style="margin:0;" placeholder="vm id">
        <input id="tm-label" class="cyber-input" style="margin:0;" value="auto" placeholder="label">
        <input id="tm-hour" class="cyber-input" style="margin:0;" value="03:00" placeholder="HH:MM">
        <input id="tm-keep" type="number" min="1" max="30" class="cyber-input" style="margin:0;" value="3">
        <button class="nav-btn" style="margin:0;border-color:var(--acc-purple);color:var(--acc-purple);" onclick="saveTimeMachinePolicy()">ZAPISZ POLITYKE</button>
      </div>
      <div id="time-machine-list" class="nx-mod-grid"></div>
    `);
    page("cloud_init", `
      <h2 style="color:var(--acc-cyan);border-bottom:1px solid #044;padding-bottom:10px;">CLOUD-INIT / RECIPES</h2>
      <div class="card" style="display:grid;grid-template-columns:minmax(180px,.8fr) minmax(160px,.6fr) minmax(220px,1fr);gap:10px;">
        <input id="ci-name" class="cyber-input" style="margin:0;" placeholder="nazwa recipe">
        <select id="ci-kind" class="cyber-input" style="margin:0;"><option value="bash">BASH</option><option value="yaml">YAML</option></select>
        <input id="ci-ssh" class="cyber-input" style="margin:0;" placeholder="opcjonalny klucz SSH publiczny">
        <textarea id="ci-body" class="cyber-input" style="grid-column:1/-1;height:170px;margin:0;" placeholder="apt update && apt install -y docker.io nginx"></textarea>
        <button class="nav-btn" style="grid-column:1/-1;margin:0;border-color:var(--acc-cyan);color:var(--acc-cyan);" onclick="saveCloudInitRecipe()">ZAPISZ RECIPE</button>
      </div>
      <div class="card" style="display:grid;grid-template-columns:1fr 1fr auto;gap:10px;align-items:end;">
        <select id="ci-recipe-select" class="cyber-input" style="margin:0;"></select>
        <input id="ci-vm" class="cyber-input" style="margin:0;" placeholder="vm id z QEMU Guest Agent">
        <button class="nav-btn" style="margin:0;border-color:#0f0;color:#0f0;" onclick="applyCloudInitRecipe()">WSTRZYKNIJ DO VM</button>
      </div>
      <div id="cloud-init-list" class="nx-mod-grid"></div>
    `);
    page("api_webhooks", `
      <h2 style="color:var(--acc-warn);border-bottom:1px solid #440;padding-bottom:10px;">API & WEBHOOKS</h2>
      <div class="card" style="display:grid;grid-template-columns:minmax(170px,1fr) minmax(180px,1fr) minmax(140px,.7fr) 110px auto;gap:10px;align-items:end;">
        <input id="api-token-name" class="cyber-input" style="margin:0;" placeholder="nazwa tokenu">
        <input id="api-token-scopes" class="cyber-input" style="margin:0;" value="vm.action" placeholder="scopes po przecinku">
        <input id="api-token-vm" class="cyber-input" style="margin:0;" placeholder="opcjonalnie vm id">
        <input id="api-token-days" type="number" min="1" max="3650" value="30" class="cyber-input" style="margin:0;">
        <button class="nav-btn" style="margin:0;border-color:var(--acc-warn);color:var(--acc-warn);" onclick="createApiToken()">TOKEN</button>
      </div>
      <div id="api-token-result"></div>
      <div class="card" style="display:grid;grid-template-columns:minmax(160px,.7fr) minmax(260px,1.4fr) minmax(180px,.9fr) auto;gap:10px;align-items:end;">
        <input id="webhook-name" class="cyber-input" style="margin:0;" placeholder="nazwa webhooka">
        <input id="webhook-url" class="cyber-input" style="margin:0;" placeholder="https://discord/slack/telegram">
        <input id="webhook-events" class="cyber-input" style="margin:0;" value="vm.action,billing.empty,alert">
        <button class="nav-btn" style="margin:0;border-color:var(--acc-cyan);color:var(--acc-cyan);" onclick="createWebhook()">WEBHOOK</button>
      </div>
      <div id="api-webhooks-grid" class="nx-mod-grid"></div>
    `);
    page("hardware_telemetry", `
      <h2 style="color:var(--acc-cyan);border-bottom:1px solid #044;padding-bottom:10px;">HARDWARE TELEMETRY</h2>
      <div class="card"><button class="nav-btn" style="margin:0;border-color:var(--acc-cyan);color:var(--acc-cyan);" onclick="loadHardwareTelemetry()">SKANUJ HOST</button><span id="hardware-status" style="color:#888;font-size:11px;margin-left:10px;">SMART / sensors / NUMA</span></div>
      <div id="hardware-grid" class="nx-mod-grid"></div>
    `);
    page("nexus_coop", `
      <h2 style="color:var(--acc-cyan);border-bottom:1px solid #044;padding-bottom:10px;">NEXUS CO-OP / MULTIUSER noVNC</h2>
      <div class="card" style="display:grid;grid-template-columns:minmax(180px,1fr) 130px 120px auto;gap:10px;align-items:end;">
        <input id="coop-vm" class="cyber-input" style="margin:0;" placeholder="vm id np. nexus-win7">
        <select id="coop-role" class="cyber-input" style="margin:0;"><option value="control">CONTROL</option><option value="view">VIEW ONLY</option></select>
        <input id="coop-minutes" type="number" min="5" max="1440" value="60" class="cyber-input" style="margin:0;">
        <button class="nav-btn" style="margin:0;border-color:var(--acc-cyan);color:var(--acc-cyan);" onclick="createCoopSession()">LINK CO-OP</button>
      </div>
      <div id="coop-result"></div>
      <div id="coop-list" class="nx-mod-grid"></div>
    `);
    page("hyper_sleep", `
      <h2 style="color:var(--acc-purple);border-bottom:1px solid #303;padding-bottom:10px;">HYPER-SLEEP / RAM FREEZE</h2>
      <div class="card" style="display:grid;grid-template-columns:minmax(180px,1fr) minmax(160px,1fr) auto auto;gap:10px;align-items:end;">
        <input id="sleep-vm" class="cyber-input" style="margin:0;" placeholder="vm id do zamrozenia">
        <input id="sleep-label" class="cyber-input" style="margin:0;" value="manual" placeholder="label">
        <button class="nav-btn" style="margin:0;border-color:var(--acc-purple);color:var(--acc-purple);" onclick="freezeHyperSleep()">ZAMROZ</button>
        <button class="nav-btn" style="margin:0;" onclick="loadHyperSleep()">ODSWIEZ</button>
      </div>
      <div class="card" style="color:#888;font-size:11px;">Tryb dziala przez virsh save/restore. Plik stanu RAM jest zapisywany na serwerze i moze byc pozniej wyslany do Object Storage / Google Drive.</div>
      <div id="sleep-list" class="nx-mod-grid"></div>
    `);
    page("nexus_canvas", `
      <h2 style="color:var(--acc-warn);border-bottom:1px solid #440;padding-bottom:10px;">NEXUS CANVAS / TOPOLOGY BUILDER</h2>
      <div class="canvas-shell">
        <div class="canvas-tools">
          <input id="canvas-name" class="cyber-input" style="margin:0 0 10px;" value="lab-topology" placeholder="nazwa topologii">
          <div class="nx-mod-actions" style="margin-top:0;">
            <button class="nav-btn" onclick="addCanvasNode('router')">ROUTER</button>
            <button class="nav-btn" onclick="addCanvasNode('linux')">LINUX VM</button>
            <button class="nav-btn" onclick="addCanvasNode('windows')">WINDOWS VM</button>
            <button class="nav-btn" onclick="addCanvasNode('database')">DATABASE</button>
          </div>
          <div class="nx-mod-actions">
            <button class="nav-btn" style="border-color:var(--acc-cyan);color:var(--acc-cyan);" onclick="saveCanvasTopology()">ZAPISZ</button>
            <button class="nav-btn" style="border-color:var(--acc-warn);color:var(--acc-warn);" onclick="clearCanvasDraft()">WYCZYSC</button>
          </div>
          <div style="color:#888;font-size:11px;line-height:1.5;margin-top:10px;">Kliknij jeden wezel, potem drugi, aby zrobic kabel. Przeciagaj wezly po siatce.</div>
          <h3 style="color:var(--acc-cyan);border-bottom:1px solid #044;padding-bottom:7px;">ZAPISANE</h3>
          <div id="canvas-saved" class="nx-mod-grid"></div>
        </div>
        <div id="canvas-board" class="canvas-board"></div>
      </div>
    `);
    page("nexus_forge", `
      <h2 style="color:var(--acc-warn);border-bottom:1px solid #440;padding-bottom:10px;">NEXUS FORGE / TEMPLATE MARKET</h2>
      <div class="card" style="display:grid;grid-template-columns:minmax(150px,.8fr) minmax(180px,1fr) 110px minmax(220px,1.4fr) auto;gap:10px;align-items:end;">
        <input id="forge-vm" class="cyber-input" style="margin:0;" placeholder="vm id">
        <input id="forge-name" class="cyber-input" style="margin:0;" placeholder="nazwa template">
        <input id="forge-price" type="number" min="0" step="0.01" value="0" class="cyber-input" style="margin:0;">
        <input id="forge-desc" class="cyber-input" style="margin:0;" placeholder="opis">
        <button class="nav-btn" style="margin:0;border-color:var(--acc-warn);color:var(--acc-warn);" onclick="publishForgeTemplate()">PUBLIKUJ</button>
      </div>
      <div id="forge-grid" class="nx-mod-grid"></div>
    `);
    page("ai_commander", `
      <h2 style="color:var(--acc-purple);border-bottom:1px solid #303;padding-bottom:10px;">A.I. INFRASTRUCTURE COMMANDER</h2>
      <div class="card">
        <textarea id="commander-input" class="cyber-input" style="height:92px;margin:0 0 10px;" placeholder="np. Zabij Viste, podnies RAM w Siodemce do 8GB i zrob snapshot o nazwie przed aktualizacja"></textarea>
        <div style="display:flex;gap:10px;flex-wrap:wrap;align-items:center;">
          <label style="color:#aaa;font-size:11px;"><input id="commander-execute" type="checkbox"> wykonaj naprawde</label>
          <button class="nav-btn" style="margin:0;border-color:var(--acc-purple);color:var(--acc-purple);" onclick="runAiCommander()">URUCHOM</button>
          <button class="nav-btn" style="margin:0;" onclick="loadAiCommanderLog()">LOG</button>
        </div>
      </div>
      <div id="commander-result" class="nx-mod-card"><strong>GOTOWY</strong><small>Bez zaznaczenia wykonania pokazuje tylko plan akcji.</small></div>
      <div id="commander-log" class="commander-log"></div>
    `);
    page("nexus_archiver", `
      <h2 style="color:var(--acc-cyan);border-bottom:1px solid #044;padding-bottom:10px;">NEXUS ARCHIVER / CLOUD ZIP ISO ENGINE</h2>
      <div class="card" style="display:grid;grid-template-columns:minmax(260px,1fr) auto auto;gap:10px;align-items:end;">
        <input id="archiver-path" class="cyber-input" style="margin:0;" placeholder="/root/nexus2/drop/archive.zip">
        <button class="nav-btn" style="margin:0;border-color:var(--acc-cyan);color:var(--acc-cyan);" onclick="listArchive()">X-RAY</button>
        <button class="nav-btn" style="margin:0;" onclick="loadArchiver()">STATUS</button>
      </div>
      <div id="archiver-status" class="object-status-grid"></div>
      <div class="archiver-list" id="archiver-list"></div>
      <div class="card" style="display:grid;grid-template-columns:minmax(260px,1fr) 140px auto;gap:10px;align-items:end;">
        <textarea id="archiver-pack-paths" class="cyber-input" style="height:70px;margin:0;" placeholder="Jedna sciezka na linie do spakowania"></textarea>
        <input id="archiver-output" class="cyber-input" style="margin:0;" value="nexus-pack.zip">
        <button class="nav-btn" style="margin:0;border-color:var(--acc-warn);color:var(--acc-warn);" onclick="createArchiveZip()">ZIP</button>
        <button class="nav-btn" style="grid-column:1/-1;margin:0;border-color:var(--acc-purple);color:var(--acc-purple);" onclick="createArchiveIso()">KONWERTUJ DO ISO DLA VM</button>
      </div>
      <div id="archiver-jobs" class="nx-mod-grid"></div>
    `);
    page("nexus_bastion", `
      <h2 style="color:var(--acc-warn);border-bottom:1px solid #440;padding-bottom:10px;">NEXUS BASTION / UNIVERSAL GATEWAY</h2>
      <div class="card" style="display:grid;grid-template-columns:minmax(150px,.8fr) 120px minmax(180px,1fr) 100px minmax(120px,.7fr) auto;gap:10px;align-items:end;">
        <input id="bastion-name" class="cyber-input" style="margin:0;" placeholder="domowy PC">
        <select id="bastion-kind" class="cyber-input" style="margin:0;"><option value="rdp">RDP</option><option value="vnc">VNC</option><option value="ssh">SSH</option><option value="nexus-link">NEXUS LINK</option></select>
        <input id="bastion-host" class="cyber-input" style="margin:0;" placeholder="host / IP">
        <input id="bastion-port" type="number" min="1" max="65535" value="3389" class="cyber-input" style="margin:0;">
        <input id="bastion-user" class="cyber-input" style="margin:0;" placeholder="user">
        <button class="nav-btn" style="margin:0;border-color:var(--acc-warn);color:var(--acc-warn);" onclick="saveBastionTarget()">DODAJ</button>
      </div>
      <div id="bastion-status" class="object-status-grid"></div>
      <div id="bastion-list" class="nx-mod-grid"></div>
    `);
    page("nexus_workers", `
      <h2 style="color:var(--acc-purple);border-bottom:1px solid #303;padding-bottom:10px;">NEXUS WORKERS / SERVERLESS</h2>
      <div class="card" style="display:grid;grid-template-columns:minmax(180px,1fr) 140px 110px auto auto;gap:10px;align-items:end;">
        <input id="worker-name" class="cyber-input" style="margin:0;" value="quick-worker">
        <select id="worker-runtime" class="cyber-input" style="margin:0;"><option value="python">PYTHON</option><option value="javascript">JAVASCRIPT</option></select>
        <input id="worker-timeout" type="number" min="1" max="30" value="8" class="cyber-input" style="margin:0;">
        <button class="nav-btn" style="margin:0;border-color:var(--acc-purple);color:var(--acc-purple);" onclick="saveWorker()">ZAPISZ</button>
        <button class="nav-btn" style="margin:0;border-color:#0f0;color:#0f0;" onclick="runWorker()">RUN</button>
      </div>
      <textarea id="worker-code" class="worker-editor">print("NEXUS WORKER ONLINE")</textarea>
      <div id="worker-status" class="object-status-grid"></div>
      <div id="worker-result" class="commander-log"></div>
      <div id="worker-list" class="nx-mod-grid"></div>
    `);
    page("secure_vault", `
      <h2 style="color:var(--acc-crit);border-bottom:1px solid #400;padding-bottom:10px;">SECURE VAULT / MISSION IMPOSSIBLE FILES</h2>
      <div class="card" style="display:grid;grid-template-columns:minmax(260px,1fr) 110px 120px auto;gap:10px;align-items:end;">
        <input type="file" id="vault-file" class="cyber-input" style="margin:0;">
        <input id="vault-views" type="number" min="1" max="100" value="1" class="cyber-input" style="margin:0;">
        <input id="vault-ttl" type="number" min="1" max="43200" value="1440" class="cyber-input" style="margin:0;">
        <button class="nav-btn" style="margin:0;border-color:var(--acc-crit);color:var(--acc-crit);" onclick="encryptAndUploadVault()">SZYFRUJ + LINK</button>
      </div>
      <div class="card" style="display:grid;grid-template-columns:minmax(260px,1fr) 110px 120px auto;gap:10px;align-items:end;">
        <input id="vault-server-path" class="cyber-input" style="margin:0;" placeholder="/root/nexus2/secure_drop/file.bin">
        <input id="vault-server-views" type="number" min="1" max="100" value="1" class="cyber-input" style="margin:0;">
        <input id="vault-server-ttl" type="number" min="1" max="43200" value="1440" class="cyber-input" style="margin:0;">
        <button class="nav-btn" style="margin:0;border-color:var(--acc-warn);color:var(--acc-warn);" onclick="createVaultServerLink()">LINK SERWER</button>
      </div>
      <div id="vault-result"></div>
      <div id="vault-list" class="nx-mod-grid"></div>
    `);
    page("global_terminal_page", `
      <h2 style="color:var(--acc-cyan);border-bottom:1px solid #044;padding-bottom:10px;">GLOBAL TERMINAL / COMMAND CENTER</h2>
      <div class="card"><button class="nav-btn" style="margin:0;border-color:var(--acc-cyan);color:var(--acc-cyan);" onclick="toggleGlobalTerminal(true)">OTWORZ TYLDĄ ~</button><span style="color:#888;font-size:11px;margin-left:10px;">Komendy: /help /balance /pay /tokens add /vm list /ai</span></div>
      <div id="global-terminal-page-log" class="commander-log"></div>
    `);
    page("usb_devices", `
      <h2 style="color:var(--acc-purple);border-bottom:1px solid #303;padding-bottom:10px;">USB DEVICES / CLOUD USB</h2>
      <div class="card" style="display:grid;grid-template-columns:1fr 1fr auto;gap:10px;align-items:center;">
        <select id="cloud-usb-vm" class="cyber-input" style="margin:0;"></select>
        <input id="cloud-usb-label" class="cyber-input" style="margin:0;" value="NEXUS_USB" placeholder="etykieta nosnika">
        <button class="nav-btn" style="margin:0;border-color:var(--acc-purple);color:var(--acc-purple);" onclick="mountCloudUsb()">MOUNT CLOUD USB</button>
      </div>
      <div id="usb-status" class="object-status-grid"></div>
      <h3 style="color:var(--acc-cyan);border-bottom:1px solid #044;padding-bottom:8px;">OBIEKTY DO WIRTUALNEGO NOSNIKA</h3>
      <div id="cloud-usb-objects" class="nx-mod-grid"></div>
      <h3 style="color:var(--acc-warn);border-bottom:1px solid #440;padding-bottom:8px;">AKTYWNE MOUNTY</h3>
      <div id="cloud-usb-mounts" class="nx-mod-grid"></div>
      <h3 style="color:#aaa;border-bottom:1px solid #333;padding-bottom:8px;">HOST USB / FIZYCZNY SERWER</h3>
      <div id="host-usb-list" class="nx-mod-grid"></div>
    `);
    page("presence_radar", `
      <h2 style="color:var(--acc-cyan);border-bottom:1px solid #044;padding-bottom:10px;">REAL-TIME PRESENCE / GRID RADAR</h2>
      <div class="radar-wrap">
        <div class="radar-screen" id="presence-radar"></div>
        <div>
          <div class="nx-mod-card"><strong>ONLINE</strong><div class="drop-count" id="presence-count">0</div><small>aktywne sesje panelu</small><div class="nx-mod-actions"><button class="nav-btn" onclick="loadPresence()">ODSWIEZ</button></div></div>
          <div id="presence-list" style="margin-top:12px;"></div>
        </div>
      </div>
    `);
    page("neural_alerts", `
      <h2 style="color:var(--acc-warn);border-bottom:1px solid #440;padding-bottom:10px;">NEURAL LINK ALERTS</h2>
      <div class="card" style="display:grid;grid-template-columns:1fr 2fr 140px auto;gap:10px;"><input id="alert-title" class="cyber-input" style="margin:0;" placeholder="Tytul alertu"><input id="alert-body" class="cyber-input" style="margin:0;" placeholder="Opis"><select id="alert-level" class="cyber-input" style="margin:0;"><option value="info">INFO</option><option value="warn">WARN</option><option value="critical">CRITICAL</option></select><button class="nav-btn" style="margin:0;" onclick="createAlert()">WYSLIJ</button></div>
      <div class="card"><button class="nav-btn" onclick="enableNeuralAlerts()">WLACZ POWIADOMIENIA</button><span id="alert-permission" style="color:#888;font-size:11px;margin-left:10px;">Status: nieaktywny</span></div>
      <div id="alerts-list"></div>
    `);
    page("p2p_drop", `
      <h2 style="color:var(--acc-purple);border-bottom:1px solid #303;padding-bottom:10px;">P2P FILE DROP / DATA LINK</h2>
      <div class="card" style="display:grid;grid-template-columns:1fr 1fr auto auto;gap:10px;"><input id="p2p-room" class="cyber-input" style="margin:0;" value="nexus" placeholder="Pokoj"><input id="p2p-peer" class="cyber-input" style="margin:0;" placeholder="Peer ID"><button class="nav-btn" style="margin:0;" onclick="p2pListen()">NASLUCH</button><button class="nav-btn" style="margin:0;border-color:var(--acc-purple);color:var(--acc-purple);" onclick="p2pOffer()">POLACZ</button></div>
      <div class="card" style="display:flex;gap:10px;flex-wrap:wrap;align-items:center;"><input type="file" id="p2p-file" class="cyber-input" style="flex:1;margin:0;"><button class="nav-btn" style="margin:0;" onclick="p2pSendFile()">WYSLIJ PLIK</button><span id="p2p-status" style="color:#888;font-size:11px;">OFFLINE</span></div>
      <div class="p2p-log" id="p2p-log"></div>
      <div id="p2p-downloads" class="nx-mod-grid" style="margin-top:12px;"></div>
    `);
    page("morning_briefing", `
      <h2 style="color:var(--acc-cyan);border-bottom:1px solid #044;padding-bottom:10px;">MORNING BRIEFING</h2>
      <div class="card"><button class="nav-btn" onclick="generateBriefing()">GENERUJ TERAZ</button><span style="color:#888;font-size:11px;margin-left:10px;">Auto odswiezanie po 08:00, jeden briefing dziennie.</span></div>
      <div id="briefing-box"></div>
    `);
    page("sys_karma", `
      <h2 style="color:var(--acc-warn);border-bottom:1px solid #440;padding-bottom:10px;">SYS-KARMA / UPTIME STREAK</h2>
      <div id="karma-box" class="nx-mod-grid"></div>
    `);
    page("web3_gate", `
      <h2 style="color:var(--acc-purple);border-bottom:1px solid #303;padding-bottom:10px;">WEB3 AUTH-GATE</h2>
      <div class="card"><button class="nav-btn" style="border-color:var(--acc-purple);color:var(--acc-purple);" onclick="connectWeb3()">POLACZ METAMASK</button><span id="web3-status" style="color:#888;font-size:11px;margin-left:10px;">Niepolaczone</span></div>
      <div id="web3-box" class="nx-mod-card"><strong>STATUS</strong><small>Standardowe konto nadal zostaje brama awaryjna. Web3 podpisuje wyzwanie kryptograficzne konta.</small></div>
    `);
    page("hyperspace_lab", `
      <h2 style="color:var(--acc-cyan);border-bottom:1px solid #044;padding-bottom:10px;">HYPERSPACE LAB / 100 POMYSLOW</h2>
      <div class="card">
        <div class="hyper-toolbar">
          <button class="nav-btn" style="margin:0;" onclick="toggleMatrixRain()">MATRIX LIVE BG</button>
          <button class="nav-btn" style="margin:0;" onclick="toggleCryptoTicker()">CRYPTO TICKER</button>
          <button class="nav-btn" style="margin:0;" onclick="toggleSoundscape()">SOUNDSCAPE</button>
          <button class="nav-btn" style="margin:0;border-color:var(--acc-warn);color:var(--acc-warn);" onclick="triggerDataShred()">DATA SHREDDER</button>
          <button class="nav-btn" style="margin:0;border-color:var(--acc-purple);color:var(--acc-purple);" onclick="toggleCrtMode()">CRT GLITCH</button>
          <select id="hyper-filter" class="cyber-input" style="margin:0;max-width:260px;" onchange="renderHyperspaceIdeas()">
            <option value="ALL">WSZYSTKIE KATEGORIE</option>
          </select>
        </div>
        <div style="color:#888;font-size:11px;">Konami Code odblokowuje ukryty tryb DEV. Karty mozna wyslac do Kanbana jako backlog.</div>
      </div>
      <div id="hyper-summary" class="nx-mod-grid" style="margin-bottom:12px;"></div>
      <div id="hyper-grid" class="nx-mod-grid"></div>
    `);
  }

  const HYPERSPACE_IDEAS = [
    { cat: "MEDIA", items: ["Neon-Drive 3D","Cyber-Deck DJ Station","Glitch-Gallery","Holo-Viewer 3D","Data-Mosh Studio","Audio-Spectrogram","Cyber-Zine Reader","GIF-Bombing ASCII","Live-Wallpaper Engine","Retro-Emulator WebNES","Podcaster Node","CCTV-Grid","Code-Cinema","WebTorrent Player","Holograficzny Oscyloskop","ASCII-Webcam","Synthwave-Radio Visualizer","Steganografia Vault-X","System-Soundscape","Visual Data Node"] },
    { cat: "SPOLECZNOSC", items: ["Co-Op Terminal","Ping-Pong Chat","Live-Cursor Radar","Reputation Ledger","WebRTC Voice-Comms","Shared-Canvas Pixel Art","Hacker-News-Holo","Emoji-Glitch Reakcje","Squad-Status","Live-Code Share","Bounty-Board","Secret-Handshake P2P","Pulse-Syndicate","Cyber-Jukebox","Ankiety Operacyjne","Ephemeral Messages","BBS-Archive","Zero-Knowledge Uprawnienia","Targowisko Modulow P2P","Anonimowy Whistleblower"] },
    { cat: "GRYWALIZACJA", items: ["Uptime-Tamagotchi","Terminal-RPG Skill Trees","Daily-Hacking Quest","Achievement-Unlocker","Lootboxy Systemowe","Web3 Login-Gate NFT","Crypto-Ticker-Tape","NFT-Avatar Sync","Typing-Racer Bash","Sys-Karma Ekonomia","Hacknet-Style Login","Pomodoro-Boss-Fight","Osiagniecia NFT","Habit-Tracker 3D","Wirtualny Ogrod Danych","Cyber-Pets","Konami-Code Unlock","System-Bingo","Odznaki wertykalne","Drag-and-Drop Kanban"] },
    { cat: "AI", items: ["Generative UI","Ghost-Typing","Face-Morph-Login","Dall-E Backgrounds","Voice-Synthesizer TTS","News-Debunker","Log-Haiku","AI-Avatar Live-2D","Cyber-Therapist","Wizualizator Nastroju AI","Auto-Meme Generator","Mind-Map Auto-Builder","Stylizer One-Click Theme AI","Holo-Companion","AI-DJ Tempo-Control","Intelligent-Autocomplete-Terminal","Sentyment-Radar","Dynamic-Translations","AI-Code-Explainer","Syntetyczne Glosy Multichannel"] },
    { cat: "OPERACYJNE UI", items: ["Matrix-Cascades","Threat Globe Hacker-Map","Visual Network Node-Graph","Data-Shredder","Hex-View-Lens","Fingerprint-Spoofer Slider","Wirtualny Stol Operacyjny","Radar Podatnosci","Secure Type Randomizer","Stealth-Mode Boss-Key","Trace-Route Visualizer","Terminal-Glitch","Biometric-Scan-Screen","Silosy Danych Tanks","Log-Visualizer 3D","Wizualny Cron-Wheel","Visual Leak","Zamek Obrotowy Safe Cracker","Cyber-Dragons Upload","God-Mode Switch"] },
  ];

  async function loadMediaDeck() {
    const grid = qs("media-grid");
    grid.innerHTML = '<div class="nx-mod-card"><strong>SKANOWANIE...</strong></div>';
    const data = await (await apiFetch("/api/media/list")).json();
    if (!data.items.length) { grid.innerHTML = '<div class="nx-mod-card"><strong>PUSTO</strong><small>Wrzuc MP3/MP4/WAV do /root/nexus2/media.</small></div>'; return; }
    grid.innerHTML = data.items.map(i => `<div class="nx-mod-card"><strong>${i.kind.toUpperCase()} ${esc(i.name)}</strong><small>${esc(i.size_label)} | ${esc(i.modified)}</small><div class="nx-mod-actions"><button class="nav-btn" onclick="playMedia('${encodeURIComponent(i.path)}','${i.kind}','${esc(i.name)}')">PLAY</button></div></div>`).join("");
  }

  window.playMedia = function (path, kind, name) {
    const url = `/api/media/stream?path=${path}&token=${token()}`;
    qs("media-title").textContent = name;
    const video = qs("media-video"), audio = qs("media-audio"), image = qs("media-image");
    video.pause(); audio.pause(); video.style.display = "none"; audio.style.display = "none"; image.style.display = "none";
    if (kind === "video") { video.src = url; video.style.display = "block"; video.play().catch(() => {}); }
    else if (kind === "image") { image.src = url; image.style.display = "block"; }
    else { audio.src = url; audio.style.display = "block"; audio.play().catch(() => {}); }
  };

  async function loadBBS() {
    const feed = qs("bbs-feed");
    feed.innerHTML = '<div class="bbs-post">LADOWANIE TABLICY...</div>';
    const posts = await (await apiFetch("/api/bbs/posts")).json();
    if (!posts.length) { feed.innerHTML = '<div class="bbs-post">Brak wpisow. Wrzuc pierwszy sygnal.</div>'; return; }
    feed.innerHTML = posts.map(p => {
      const image = p.image ? `<img class="bbs-img" src="/api/bbs/image/${encodeURIComponent(p.image)}?token=${token()}">` : "";
      const comments = (p.comments || []).map(c => `<div style="border-top:1px solid #222;padding-top:7px;margin-top:7px;"><b style="color:var(--acc-cyan);">${esc(c.author)}</b> <span style="color:#777;font-size:10px;">${esc(c.created_at)}</span><div>${esc(c.text)}</div></div>`).join("");
      return `<div class="bbs-post"><div style="display:flex;gap:10px;"><div class="bbs-avatar">${esc((p.author || "?")[0]).toUpperCase()}</div><div style="flex:1;"><div><b style="color:#fff;">${esc(p.author)}</b> <span style="color:var(--acc-warn);font-size:10px;">${esc(p.role)}</span> <span style="color:#777;font-size:10px;">${esc(p.created_at)}</span></div><div style="white-space:pre-wrap;margin-top:8px;">${esc(p.text)}</div>${image}<div class="nx-mod-actions"><button class="nav-btn" onclick="repBBS('${p.id}')">REP ${p.reputation || 0}</button><button class="nav-btn" onclick="commentBBS('${p.id}')">KOMENTARZ</button></div>${comments}</div></div></div>`;
    }).join("");
  }

  window.createBBSPost = async function () {
    const text = qs("bbs-text").value.trim();
    if (!text) return;
    const form = new FormData();
    form.append("text", text);
    const f = qs("bbs-image").files[0];
    if (f) form.append("file", f);
    await apiFetch("/api/bbs/posts", { method: "POST", body: form });
    qs("bbs-text").value = ""; qs("bbs-image").value = "";
    loadBBS();
  };
  window.commentBBS = async function (id) {
    const text = prompt("Komentarz:");
    if (!text) return;
    await apiFetch("/api/bbs/comment", { method: "POST", body: JSON.stringify({ post_id: id, text }) });
    loadBBS();
  };
  window.repBBS = async function (id) {
    await apiFetch("/api/bbs/rep", { method: "POST", body: JSON.stringify({ post_id: id }) });
    loadBBS();
  };

  async function loadGallery() {
    const grid = qs("gallery-grid");
    grid.innerHTML = '<div class="nx-mod-card"><strong>SKANOWANIE...</strong></div>';
    const data = await (await apiFetch("/api/gallery/list")).json();
    if (!data.items.length) { grid.innerHTML = '<div class="nx-mod-card"><strong>BRAK OBRAZOW</strong><small>Wrzuc PNG/JPG/WEBP do media albo visual_archive.</small></div>'; return; }
    grid.innerHTML = data.items.map(i => {
      const src = `/api/gallery/image?source=${encodeURIComponent(i.source)}&path=${encodeURIComponent(i.path)}&token=${token()}`;
      return `<div class="nx-mod-card"><img class="gallery-thumb" src="${src}" onclick="openGalleryLightbox('${src}','${esc(i.name)}','${esc(i.size_label)}','${esc(i.modified)}')"><strong>${esc(i.name)}</strong><small>${esc(i.size_label)} | ${esc(i.modified)}</small></div>`;
    }).join("");
  }
  window.openGalleryLightbox = function (src, name, size, mod) {
    qs("gallery-full").src = src;
    qs("gallery-info").innerHTML = `<h3 style="color:var(--acc-cyan);">${name}</h3><p>Waga: ${size}</p><p>Data: ${mod}</p><p>Tryb: GLITCH LIGHTBOX</p>`;
    qs("gallery-lightbox").classList.add("active");
  };
  window.closeGalleryLightbox = function (event) {
    if (event.target.id === "gallery-lightbox") qs("gallery-lightbox").classList.remove("active");
  };

  async function loadKanban() {
    const board = await (await apiFetch("/api/kanban")).json();
    qs("kanban-board").innerHTML = (board.columns || []).map(col => `<div class="kanban-col" data-col="${esc(col.id)}" ondragover="event.preventDefault()" ondrop="dropKanban(event,'${esc(col.id)}')"><h3 style="color:var(--acc-cyan);margin-top:0;">${esc(col.title)}</h3>${(col.cards || []).map(card => `<div class="kanban-card" draggable="true" data-card="${esc(card.id)}" ondragstart="dragKanban(event)"><strong>${esc(card.title)}</strong><p>${esc(card.body || "")}</p><small style="color:#666;">${esc(card.created_at || "")}</small></div>`).join("")}</div>`).join("");
  }
  window.addKanbanCard = async function () {
    const title = qs("kanban-title").value.trim();
    if (!title) return;
    await apiFetch("/api/kanban/card", { method: "POST", body: JSON.stringify({ column_id: qs("kanban-col").value, title, body: qs("kanban-body").value }) });
    qs("kanban-title").value = ""; qs("kanban-body").value = "";
    loadKanban();
  };
  window.dragKanban = function (event) { event.dataTransfer.setData("card", event.target.dataset.card); };
  window.dropKanban = async function (event, colId) {
    const cardId = event.dataTransfer.getData("card");
    const board = await (await apiFetch("/api/kanban")).json();
    let moved = null;
    for (const col of board.columns) col.cards = (col.cards || []).filter(c => { if (c.id === cardId) { moved = c; return false; } return true; });
    const dest = board.columns.find(c => c.id === colId);
    if (moved && dest) dest.cards.push(moved);
    await apiFetch("/api/kanban/state", { method: "POST", body: JSON.stringify({ columns: board.columns }) });
    loadKanban();
  };

  async function loadDrop() {
    const list = qs("drop-list");
    list.innerHTML = '<div class="nx-mod-card"><strong>LADOWANIE...</strong></div>';
    try {
      const [shares, inboxData] = await Promise.all([
        (await apiFetch("/api/drop/list")).json(),
        (await apiFetch("/api/drop/inbox")).json().catch(() => ({ items: [] })),
      ]);
      const inbox = inboxData.items || [];
      if (!shares.length && !inbox.length) { list.innerHTML = '<div class="nx-mod-card"><strong>BRAK PLIKOW</strong><small>Przeciagnij plik na strone albo wybierz plik i wygeneruj pierwszy link.</small></div>'; return; }
      const shareHtml = shares.length ? shares.map(s => `<div class="nx-mod-card"><strong>${esc(s.title)}</strong><small>${esc(s.name)} | ${esc(s.size_label)}</small><div class="drop-count">${s.downloads || 0}</div><small>pobran</small><div class="nx-mod-actions"><button class="nav-btn" onclick="navigator.clipboard.writeText(location.origin + '${esc(s.url)}')">KOPIUJ LINK</button><button class="nav-btn" onclick="window.open('${esc(s.url)}','_blank')">OTWORZ</button></div></div>`).join("") : "";
      const inboxHtml = inbox.length ? `<div class="nx-mod-card" style="grid-column:1/-1;min-height:0;border-left-color:var(--acc-warn);"><strong>DROP INBOX</strong><small>Pliki wrzucone przez globalny smart-drop. Nie sa publiczne, dopoki nie klikniesz UDOSTEPNIJ.</small></div>` + inbox.map(f => `<div class="nx-mod-card"><strong>${esc(f.name)}</strong><small>${esc(f.size_label)} | ${esc(f.modified)}</small><small>${esc(f.full_path)}</small><div class="nx-mod-actions"><button class="nav-btn" onclick="document.getElementById('drop-path').value='${esc(f.full_path)}';document.getElementById('drop-title').value='${esc(f.name)}';createDropShare()">UDOSTEPNIJ</button></div></div>`).join("") : "";
      list.innerHTML = shareHtml + inboxHtml;
    } catch (e) {
      list.innerHTML = '<div class="nx-mod-card"><strong>ADMIN ONLY</strong><small>Secure Drop jest tylko dla admina.</small></div>';
    }
  }
  window.createDropShare = async function () {
    const path = qs("drop-path").value.trim();
    if (!path) return;
    await apiFetch("/api/drop/share", { method: "POST", body: JSON.stringify({ path, title: qs("drop-title").value }) });
    qs("drop-path").value = ""; qs("drop-title").value = "";
    loadDrop();
  };

  function refreshObjectImportTarget(kind) {
    if (kind === "iso" || kind === "driver") {
      if (typeof window.loadIsoVault === "function") window.loadIsoVault();
      if (typeof window.loadDriverVault === "function") window.loadDriverVault();
      if (typeof window.loadHyperDeck === "function") window.loadHyperDeck();
    }
    if ((kind === "audio" || kind === "video") && typeof window.loadMediaDeck === "function") loadMediaDeck();
    if (kind === "image" && typeof window.loadGallery === "function") loadGallery();
    if (kind === "drop" && typeof window.loadDrop === "function") loadDrop();
  }

  async function loadObjectStorage() {
    const statusBox = qs("object-status");
    const grid = qs("object-grid");
    if (!statusBox || !grid) return;
    statusBox.innerHTML = '<div class="object-kv"><b>STATUS</b><span>Ladowanie Object Storage...</span></div>';
    grid.innerHTML = '<div class="nx-mod-card"><strong>SKANOWANIE S3...</strong></div>';
    loadObjectTokens();
    try {
      const data = await (await apiFetch("/api/storage/status")).json();
      const buckets = (data.buckets || []).map(b => `<span class="object-pill">${esc(b)}</span>`).join("") || '<span class="object-pill">brak bucketow</span>';
      statusBox.innerHTML = `
        <div class="object-kv"><b>MINIO</b><span>${data.enabled ? "AKTYWNE" : "BRAK KONFIGURACJI"} / ${esc(data.service || "unknown")}</span></div>
        <div class="object-kv"><b>PUBLIC BASE</b><span>${esc(data.public_base || "-")}</span></div>
        <div class="object-kv"><b>BUCKETS</b><span>${buckets}</span></div>
        <div class="object-kv"><b>TRYB</b><span>FastAPI podpisuje URL, plik idzie bezposrednio do MinIO.</span></div>
      `;
      const objects = data.objects || [];
      if (!objects.length) {
        grid.innerHTML = '<div class="nx-mod-card"><strong>BRAK OBIEKTOW</strong><small>Przeciagnij duzy plik na strone albo uzyj WRZUC DO S3.</small></div>';
        return;
      }
      grid.innerHTML = objects.map(item => `
        <div class="nx-mod-card">
          <strong>${esc((item.kind || "data").toUpperCase())} ${esc(item.filename || item.key)}</strong>
          <small>${esc(item.size_label || "")} | ${esc(item.bucket || "")}</small>
          <small>${esc(item.key || "")}</small>
          <small>${item.imported_path ? "Import: " + esc(item.imported_path) : "Jeszcze nie zaimportowany do katalogu modulu"}</small>
          <div class="nx-mod-actions">
            <button class="nav-btn" onclick="importObjectStorage('${esc(item.id)}')">IMPORT</button>
          </div>
        </div>
      `).join("");
    } catch (e) {
      statusBox.innerHTML = '<div class="object-kv"><b>ERROR</b><span>Nie udalo sie odczytac Object Storage.</span></div>';
      grid.innerHTML = '<div class="nx-mod-card"><strong>OFFLINE</strong><small>MinIO albo backend nie odpowiada.</small></div>';
    }
  }

  async function loadObjectTokens() {
    const list = qs("object-token-list");
    if (!list) return;
    list.innerHTML = '<div class="nx-mod-card"><strong>LADOWANIE TOKENOW...</strong></div>';
    try {
      const data = await (await apiFetch("/api/storage/tokens")).json();
      const tokens = data.tokens || [];
      if (!tokens.length) {
        list.innerHTML = '<div class="nx-mod-card"><strong>BRAK TOKENOW</strong><small>Wygeneruj token dla uploadu z telefonu, automatu albo zewnetrznego narzedzia.</small></div>';
        return;
      }
      list.innerHTML = tokens.map(t => `
        <div class="object-token-row">
          <strong style="color:${t.active ? "var(--acc-purple)" : "#777"};">${esc(t.name || "token")}</strong>
          <small>${esc(t.preview || "")} | ${esc(t.purpose || "auto")} | owner: ${esc(t.owner || "")}</small>
          <small>wazny do: ${esc(t.expires_at || "-")} | uzyc: ${Number(t.uses || 0)} | ${esc(t.bytes_uploaded_label || "0 B")}</small>
          <small>${t.revoked_at ? "odwolany: " + esc(t.revoked_at) : "status: aktywny"}</small>
          <div class="nx-mod-actions">
            ${t.active ? `<button class="nav-btn" style="border-color:var(--acc-crit);color:var(--acc-crit);" onclick="revokeObjectToken('${esc(t.id)}')">ODWOLAJ</button>` : ""}
          </div>
        </div>
      `).join("");
    } catch (e) {
      list.innerHTML = '<div class="nx-mod-card"><strong>ADMIN ONLY</strong><small>Token Vault wymaga konta admina.</small></div>';
    }
  }

  window.uploadObjectStorageSelected = async function () {
    const input = qs("object-files");
    const files = Array.from(input?.files || []);
    const purpose = qs("object-purpose")?.value || "auto";
    if (!files.length) return;
    if (!window.NexusTransfers || typeof window.NexusTransfers.uploadObjectStorage !== "function") {
      alert("TRANSFER CORE nie zaladowal modulu S3.");
      return;
    }
    for (const file of files) {
      await window.NexusTransfers.uploadObjectStorage(file, { purpose, label: `S3 OBJECT: ${file.name}` });
    }
    input.value = "";
    loadObjectStorage();
  };

  window.createObjectToken = async function () {
    const name = (qs("object-token-name")?.value || "").trim();
    if (!name) return;
    const body = {
      name,
      purpose: qs("object-token-purpose")?.value || "auto",
      expires_days: Number(qs("object-token-days")?.value || 30),
      max_size_mb: Number(qs("object-token-max")?.value || 0),
    };
    const res = await apiFetch("/api/storage/tokens", { method: "POST", body: JSON.stringify(body) });
    if (!res.ok) return;
    const data = await res.json();
    const box = qs("object-token-result");
    if (box) {
      box.innerHTML = `
        <div class="card" style="border-color:var(--acc-warn);">
          <b style="color:var(--acc-warn);">TOKEN WIDOCZNY TYLKO TERAZ</b>
          <textarea class="object-token-secret" readonly>${esc(data.token || "")}</textarea>
          <div class="nx-mod-actions">
            <button class="nav-btn" onclick="navigator.clipboard.writeText(document.querySelector('.object-token-secret')?.value || '')">KOPIUJ TOKEN</button>
          </div>
        </div>
      `;
    }
    qs("object-token-name").value = "";
    loadObjectTokens();
  };

  window.revokeObjectToken = async function (tokenId) {
    await apiFetch("/api/storage/tokens/revoke", { method: "POST", body: JSON.stringify({ token_id: tokenId }) });
    loadObjectTokens();
  };

  window.importObjectStorage = async function (objectId) {
    const res = await apiFetch("/api/storage/import", { method: "POST", body: JSON.stringify({ object_id: objectId }) });
    if (!res.ok) return;
    const data = await res.json();
    refreshObjectImportTarget(data.object?.kind || "");
    loadObjectStorage();
  };

  async function loadCloudDrive() {
    const statusBox = qs("cloud-status");
    const sourcesBox = qs("cloud-sources");
    const jobsBox = qs("cloud-jobs");
    if (!statusBox || !sourcesBox || !jobsBox) return;
    statusBox.innerHTML = '<div class="object-kv"><b>CLOUD DRIVE</b><span>Skanowanie rclone...</span></div>';
    try {
      const data = await (await apiFetch("/api/cloud-drive/status")).json();
      const about = data.about || {};
      const used = about.used ? `${Math.round((about.used / 1024 / 1024 / 1024) * 10) / 10} GB` : "--";
      const total = about.total ? `${Math.round((about.total / 1024 / 1024 / 1024) * 10) / 10} GB` : "--";
      const free = about.free ? `${Math.round((about.free / 1024 / 1024 / 1024) * 10) / 10} GB` : "--";
      statusBox.innerHTML = `
        <div class="object-kv"><b>RCLONE</b><span>${data.installed ? "OK / " + esc(data.binary) : "BRAK NA VPS"}</span></div>
        <div class="object-kv"><b>REMOTE</b><span>${data.configured ? "gdrive: GOTOWY" : "gdrive: NIE SKONFIGUROWANY"} | ${esc((data.remotes || []).join(", ") || "-")}</span></div>
        <div class="object-kv"><b>GOOGLE DRIVE</b><span>used ${esc(used)} / total ${esc(total)} / free ${esc(free)}</span></div>
        <div class="object-kv"><b>CONFIG</b><span>${esc(data.config_path || "")}</span></div>
      `;
      sourcesBox.innerHTML = (data.sources || []).map(src => `
        <div class="nx-mod-card">
          <strong>${esc(src.id)}</strong>
          <small>${esc(src.path)}<br>${esc(src.size)} / ${src.exists ? "OK" : "BRAK"}</small>
        </div>
      `).join("");
      renderCloudJobs(data.jobs || []);
    } catch (e) {
      statusBox.innerHTML = '<div class="object-kv"><b>ERROR</b><span>Cloud Drive API nie odpowiada.</span></div>';
    }
  }

  function renderCloudJobs(jobs) {
    const jobsBox = qs("cloud-jobs");
    if (!jobsBox) return;
    jobsBox.innerHTML = jobs.length ? jobs.map(job => {
      const color = job.status === "done" ? "#0f0" : job.status === "error" ? "var(--acc-crit)" : "var(--acc-warn)";
      return `
        <div class="nx-mod-card">
          <strong>${esc(job.source || job.id)} -> ${esc(job.remote || "gdrive")}</strong>
          <small style="color:${color};font-weight:bold;">${esc(job.status || "queued")}</small>
          <small>${esc(job.dest || job.root_folder || "")}</small>
          <small>${esc(job.error || job.output || "").slice(0, 260)}</small>
        </div>
      `;
    }).join("") : '<div class="nx-mod-card"><strong>BRAK ZADAN</strong><small>Nie uruchomiono jeszcze synchronizacji.</small></div>';
  }

  async function refreshCloudJobs() {
    try {
      const data = await (await apiFetch("/api/cloud-drive/jobs", { silent: true })).json();
      renderCloudJobs(data.jobs || []);
      if ((data.jobs || []).some(job => ["queued", "running"].includes(job.status))) setTimeout(refreshCloudJobs, 5000);
    } catch (e) {}
  }

  window.saveCloudDriveToken = async function () {
    const tokenJson = (qs("cloud-token")?.value || "").trim();
    const remote = qs("cloud-remote")?.value || "gdrive";
    const root_folder = qs("cloud-root")?.value || "NEXUS_CORE";
    const result = qs("cloud-config-result");
    if (!tokenJson) return alert("Wklej token JSON z rclone authorize.");
    const res = await apiFetch("/api/cloud-drive/config", { method: "POST", body: JSON.stringify({ remote, root_folder, token_json: tokenJson }) });
    const data = await res.json().catch(() => ({}));
    if (result) result.textContent = res.ok ? `Zapisano remote ${data.remote || remote}` : (data.detail || "Blad zapisu tokenu");
    if (res.ok) qs("cloud-token").value = "";
    loadCloudDrive();
  };

  window.startCloudSync = async function (source, mode) {
    const remote = qs("cloud-remote")?.value || "gdrive";
    const root_folder = qs("cloud-root")?.value || "NEXUS_CORE";
    const res = await apiFetch("/api/cloud-drive/sync", { method: "POST", body: JSON.stringify({ source, remote, root_folder, mode: mode || "copy" }) });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) return alert(data.detail || "Nie udalo sie uruchomic sync.");
    renderCloudJobs([data]);
    refreshCloudJobs();
  };

  window.pushServerFileToDrive = async function () {
    const path = (qs("cloud-push-path")?.value || "").trim();
    const dest_folder = (qs("cloud-push-dest")?.value || "server-files").trim();
    const mode = qs("cloud-push-mode")?.value || "copy";
    const remote = qs("cloud-remote")?.value || "gdrive";
    const root_folder = qs("cloud-root")?.value || "NEXUS_CORE";
    const result = qs("cloud-push-result");
    if (!path) return alert("Wpisz sciezke pliku albo folderu na VPS.");
    if (result) result.textContent = "Kolejkuje transfer do Google Drive...";
    const res = await apiFetch("/api/cloud-drive/push", {
      method: "POST",
      body: JSON.stringify({ path, dest_folder, mode, remote, root_folder })
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      if (result) result.textContent = data.detail || "Nie udalo sie uruchomic transferu.";
      return alert(data.detail || "Nie udalo sie uruchomic transferu.");
    }
    if (result) result.textContent = `Start: ${data.source_path || path} -> ${data.root_folder}/${data.dest_folder}`;
    renderCloudJobs([data]);
    refreshCloudJobs();
  };

  window.listCloudDrive = async function () {
    const listBox = qs("cloud-list");
    if (!listBox) return;
    listBox.innerHTML = '<div class="nx-mod-card"><strong>LISTING...</strong></div>';
    const remote = encodeURIComponent(qs("cloud-remote")?.value || "gdrive");
    const root = encodeURIComponent(qs("cloud-root")?.value || "NEXUS_CORE");
    try {
      const data = await (await apiFetch(`/api/cloud-drive/list?remote=${remote}&root_folder=${root}`)).json();
      const items = data.items || [];
      listBox.innerHTML = items.length ? items.map(item => `
        <div class="nx-mod-card">
          <strong>${esc(item.Name || item.Path || "item")}</strong>
          <small>${item.IsDir ? "DIR" : esc(item.size_label || "")}<br>${esc(item.ModTime || "")}</small>
        </div>
      `).join("") : '<div class="nx-mod-card"><strong>PUSTO</strong><small>Folder NEXUS_CORE nie ma jeszcze plikow.</small></div>';
    } catch (e) {
      listBox.innerHTML = '<div class="nx-mod-card"><strong>BLAD LISTINGU</strong><small>Remote nie jest gotowy albo token wymaga poprawki.</small></div>';
    }
  };

  async function loadNexusShield() {
    const status = qs("shield-status");
    const grid = qs("shield-grid");
    if (!status || !grid) return;
    const data = await (await apiFetch("/api/shield/status")).json();
    status.innerHTML = `
      <div class="object-kv"><b>FIREWALL</b><span>iptables: ${data.iptables ? "OK" : "BRAK"} / reguly: ${(data.rules || []).length}</span></div>
      <div class="object-kv"><b>PORT FORWARD</b><span>${(data.port_forwards || []).length} aktywnych definicji</span></div>
      <div class="object-kv"><b>RUCH</b><span>${(data.interfaces || []).map(i => `${esc(i.name)} RX ${esc(i.rx)} TX ${esc(i.tx)}`).join(" | ") || "-"}</span></div>
    `;
    const rules = (data.rules || []).map(r => `<div class="nx-mod-card"><strong>${esc((r.action || "").toUpperCase())} ${esc(r.source)}</strong><small>${esc(r.proto || "all")} / port ${r.port || "*"} / ${esc(r.note || "")}</small><small>${esc(r.system?.output || r.created_at || "")}</small><div class="nx-mod-actions"><button class="nav-btn" onclick="deleteShieldRule('${esc(r.id)}')">USUN</button></div></div>`);
    const forwards = (data.port_forwards || []).map(p => `<div class="nx-mod-card"><strong>PF ${esc(p.host_port)} -> ${esc(p.vm_id)}:${esc(p.vm_port)}</strong><small>${esc(p.guest_ip || "")} / ${esc(p.proto || "tcp")}</small></div>`);
    grid.innerHTML = [...rules, ...forwards].join("") || '<div class="nx-mod-card"><strong>BRAK REGUL</strong><small>Dodaj pierwsza regule firewall albo port forward w VM.</small></div>';
  }

  window.addShieldRule = async function () {
    const payload = {
      action: qs("shield-action")?.value || "block",
      source: qs("shield-source")?.value || "",
      proto: qs("shield-proto")?.value || "all",
      port: Number(qs("shield-port")?.value || 0),
      note: qs("shield-note")?.value || "",
      apply: true
    };
    const res = await apiFetch("/api/shield/firewall/rules", { method: "POST", body: JSON.stringify(payload) });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) return alert(data.detail || "Nie udalo sie dodac reguly.");
    qs("shield-source").value = "";
    qs("shield-note").value = "";
    loadNexusShield();
  };

  window.deleteShieldRule = async function (id) {
    await apiFetch("/api/shield/firewall/delete", { method: "POST", body: JSON.stringify({ id, remove_system: true }) });
    loadNexusShield();
  };

  async function loadTimeMachine() {
    const box = qs("time-machine-list");
    if (!box) return;
    const data = await (await apiFetch("/api/time-machine/policies")).json();
    const rows = data.items || [];
    box.innerHTML = rows.length ? rows.map(p => `<div class="nx-mod-card"><strong>${esc(p.vm_id)} / ${esc(p.label)}</strong><small>${esc(p.hour)} / keep ${esc(p.max_keep)} / ${p.enabled ? "ON" : "OFF"}</small><small>last: ${esc(p.last_snapshot || "-")}</small><div class="nx-mod-actions"><button class="nav-btn" onclick="runTimeMachine('${esc(p.id)}')">SNAPSHOT</button><button class="nav-btn" onclick="deleteTimeMachine('${esc(p.id)}')">USUN</button></div></div>`).join("") : '<div class="nx-mod-card"><strong>BRAK POLITYK</strong><small>Dodaj harmonogram snapshotow.</small></div>';
  }

  window.saveTimeMachinePolicy = async function () {
    const payload = { vm_id: qs("tm-vm")?.value || "", label: qs("tm-label")?.value || "auto", hour: qs("tm-hour")?.value || "03:00", max_keep: Number(qs("tm-keep")?.value || 3), enabled: true };
    const res = await apiFetch("/api/time-machine/policies", { method: "POST", body: JSON.stringify(payload) });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) return alert(data.detail || "Nie zapisano polityki.");
    loadTimeMachine();
  };
  window.runTimeMachine = async id => { const r = await apiFetch("/api/time-machine/run", { method: "POST", body: JSON.stringify({ id }) }); const d = await r.json().catch(() => ({})); if (!r.ok) alert(d.detail || "Snapshot failed"); loadTimeMachine(); };
  window.deleteTimeMachine = async id => { await apiFetch("/api/time-machine/delete", { method: "POST", body: JSON.stringify({ id }) }); loadTimeMachine(); };

  async function loadCloudInit() {
    const list = qs("cloud-init-list");
    const sel = qs("ci-recipe-select");
    if (!list || !sel) return;
    const data = await (await apiFetch("/api/cloud-init/recipes")).json();
    const rows = data.items || [];
    sel.innerHTML = rows.map(r => `<option value="${esc(r.id)}">${esc(r.name)} / ${esc(r.kind)}</option>`).join("") || '<option value="">Brak recipe</option>';
    list.innerHTML = rows.length ? rows.map(r => `<div class="nx-mod-card"><strong>${esc(r.name)}</strong><small>${esc(r.kind)} / ${esc(r.created_at || "")}</small><small>${esc((r.body || "").slice(0, 160))}</small><div class="nx-mod-actions"><button class="nav-btn" onclick="deleteCloudInitRecipe('${esc(r.id)}')">USUN</button></div></div>`).join("") : '<div class="nx-mod-card"><strong>BRAK RECIPES</strong><small>Dodaj bash/yaml albo klucz SSH.</small></div>';
  }
  window.saveCloudInitRecipe = async function () { const payload = { name: qs("ci-name")?.value || "", kind: qs("ci-kind")?.value || "bash", body: qs("ci-body")?.value || "", ssh_key: qs("ci-ssh")?.value || "" }; const r = await apiFetch("/api/cloud-init/recipes", { method: "POST", body: JSON.stringify(payload) }); const d = await r.json().catch(() => ({})); if (!r.ok) return alert(d.detail || "Nie zapisano recipe."); qs("ci-body").value = ""; loadCloudInit(); };
  window.deleteCloudInitRecipe = async id => { await apiFetch("/api/cloud-init/delete", { method: "POST", body: JSON.stringify({ id }) }); loadCloudInit(); };
  window.applyCloudInitRecipe = async function () { const recipe_id = qs("ci-recipe-select")?.value || ""; const vm_id = qs("ci-vm")?.value || ""; const r = await apiFetch("/api/cloud-init/apply", { method: "POST", body: JSON.stringify({ recipe_id, vm_id }) }); const d = await r.json().catch(() => ({})); alert(r.ok ? "Recipe wyslane do QEMU Guest Agent." : (d.detail || "Nie udalo sie wstrzyknac recipe.")); };

  async function loadApiWebhooks() {
    const grid = qs("api-webhooks-grid");
    if (!grid) return;
    const [tokens, hooks] = await Promise.all([(await apiFetch("/api/integrations/tokens")).json(), (await apiFetch("/api/integrations/webhooks")).json()]);
    const t = (tokens.items || []).map(x => `<div class="nx-mod-card"><strong>API ${esc(x.name)}</strong><small>${esc(x.preview || "")} / ${esc((x.scopes || []).join(","))}</small><small>vm: ${esc(x.vm_id || "*")} / exp: ${esc(x.expires_at || "")}</small><div class="nx-mod-actions"><button class="nav-btn" onclick="revokeApiToken('${esc(x.id)}')">REVOKE</button></div></div>`);
    const h = (hooks.items || []).map(x => `<div class="nx-mod-card"><strong>WEBHOOK ${esc(x.name)}</strong><small>${esc(x.url)}</small><small>${esc((x.events || []).join(","))}</small><div class="nx-mod-actions"><button class="nav-btn" onclick="testWebhook('${esc(x.id)}')">TEST</button><button class="nav-btn" onclick="deleteWebhook('${esc(x.id)}')">USUN</button></div></div>`);
    grid.innerHTML = [...t, ...h].join("") || '<div class="nx-mod-card"><strong>BRAK INTEGRACJI</strong><small>Wygeneruj token albo webhook.</small></div>';
  }
  window.createApiToken = async function () { const scopes = (qs("api-token-scopes")?.value || "vm.action").split(",").map(s => s.trim()).filter(Boolean); const payload = { name: qs("api-token-name")?.value || "api-token", scopes, vm_id: qs("api-token-vm")?.value || "", days: Number(qs("api-token-days")?.value || 30) }; const r = await apiFetch("/api/integrations/tokens", { method: "POST", body: JSON.stringify(payload) }); const d = await r.json().catch(() => ({})); if (!r.ok) return alert(d.detail || "Nie utworzono tokenu."); qs("api-token-result").innerHTML = `<textarea class="object-token-secret" readonly>${esc(d.token || "")}</textarea>`; loadApiWebhooks(); };
  window.revokeApiToken = async id => { await apiFetch("/api/integrations/tokens/revoke", { method: "POST", body: JSON.stringify({ id }) }); loadApiWebhooks(); };
  window.createWebhook = async function () { const events = (qs("webhook-events")?.value || "alert").split(",").map(s => s.trim()).filter(Boolean); const payload = { name: qs("webhook-name")?.value || "webhook", url: qs("webhook-url")?.value || "", events, enabled: true }; const r = await apiFetch("/api/integrations/webhooks", { method: "POST", body: JSON.stringify(payload) }); const d = await r.json().catch(() => ({})); if (!r.ok) return alert(d.detail || "Nie zapisano webhooka."); loadApiWebhooks(); };
  window.deleteWebhook = async id => { await apiFetch("/api/integrations/webhooks/delete", { method: "POST", body: JSON.stringify({ id }) }); loadApiWebhooks(); };
  window.testWebhook = async id => { const r = await apiFetch("/api/integrations/webhooks/test", { method: "POST", body: JSON.stringify({ id }) }); const d = await r.json().catch(() => ({})); alert(r.ok ? "Webhook test wyslany." : (d.detail || "Webhook test failed.")); };

  window.loadHardwareTelemetry = async function () {
    const grid = qs("hardware-grid");
    const status = qs("hardware-status");
    if (!grid) return;
    if (status) status.textContent = "Skanuje hardware...";
    const data = await (await apiFetch("/api/hardware/telemetry")).json();
    if (status) status.textContent = `Ostatni skan: ${data.checked_at || ""}`;
    const smart = (data.smart_devices || []).map((d, i) => `<div class="nx-mod-card"><strong>SMART ${i + 1}</strong><small>${esc(d.data?.device?.name || d.raw || d.error || "device")}</small><small>health: ${esc(d.data?.smart_status?.passed === true ? "PASSED" : d.data?.smart_status?.passed === false ? "FAILED" : "n/a")}</small></div>`);
    const sensors = `<div class="nx-mod-card"><strong>SENSORS</strong><small>${esc(data.sensors?.ok ? "OK" : data.sensors?.error || "brak")}</small><small>${esc(JSON.stringify(data.sensors?.data || {}).slice(0, 260))}</small></div>`;
    const cpu = `<div class="nx-mod-card"><strong>CPU / LSCPU</strong><small>${esc(JSON.stringify(data.lscpu?.data || data.lscpu?.raw || data.lscpu?.error || {}).slice(0, 320))}</small></div>`;
    const numa = `<div class="nx-mod-card"><strong>NUMA</strong><small>${esc(data.numa?.raw || data.numa?.error || "")}</small></div>`;
    grid.innerHTML = [...smart, sensors, cpu, numa].join("");
  };

  async function loadCoopSessions() {
    const box = qs("coop-list");
    if (!box) return;
    box.innerHTML = '<div class="nx-mod-card"><strong>LADOWANIE CO-OP...</strong></div>';
    const data = await (await apiFetch("/api/coop/sessions")).json();
    const rows = data.items || [];
    box.innerHTML = rows.length ? rows.map(row => {
      const link = `${location.origin}/static/coop.html?ticket=${encodeURIComponent(row.ticket || "")}`;
      return `<div class="nx-mod-card" style="border-left-color:${row.expired || row.enabled === false ? "var(--acc-warn)" : "var(--acc-cyan)"}">
        <strong>${esc(row.vm_id)} / ${esc((row.role || "view").toUpperCase())}</strong>
        <small>${row.enabled === false ? "REVOKED" : row.expired ? "EXPIRED" : "ACTIVE"} / exp: ${esc(row.expires_at || "")}</small>
        <textarea class="coop-link-box" readonly>${esc(link)}</textarea>
        <div class="nx-mod-actions"><a class="nav-btn" href="${esc(link)}" target="_blank" rel="noopener">OTWORZ</a><button class="nav-btn" onclick="revokeCoopSession('${esc(row.id)}')">REVOKE</button></div>
      </div>`;
    }).join("") : '<div class="nx-mod-card"><strong>BRAK SESJI</strong><small>Wygeneruj pierwszy link multiplayer do VM.</small></div>';
  }

  window.createCoopSession = async function () {
    const payload = {
      vm_id: qs("coop-vm")?.value || "",
      role: qs("coop-role")?.value || "control",
      minutes: Number(qs("coop-minutes")?.value || 60)
    };
    const r = await apiFetch("/api/coop/sessions", { method: "POST", body: JSON.stringify(payload) });
    const d = await r.json().catch(() => ({}));
    if (!r.ok) return alert(d.detail || "Nie utworzono sesji CO-OP.");
    qs("coop-result").innerHTML = `<div class="nx-mod-card"><strong>LINK GOTOWY</strong><textarea class="coop-link-box" readonly>${esc(d.link || "")}</textarea><div class="nx-mod-actions"><a class="nav-btn" href="${esc(d.link || "#")}" target="_blank" rel="noopener">OTWORZ</a></div></div>`;
    loadCoopSessions();
  };

  window.revokeCoopSession = async function (id) {
    await apiFetch("/api/coop/sessions/revoke", { method: "POST", body: JSON.stringify({ id }) });
    loadCoopSessions();
  };

  async function loadHyperSleep() {
    const box = qs("sleep-list");
    if (!box) return;
    box.innerHTML = '<div class="nx-mod-card"><strong>SKANUJE STANY...</strong></div>';
    const data = await (await apiFetch("/api/hyper-sleep/states")).json();
    const rows = data.items || [];
    box.innerHTML = rows.length ? rows.map(row => `<div class="nx-mod-card sleep-state">
      <strong>${esc(row.vm_id)} / ${esc(row.label || "state")}</strong>
      <small>${esc(row.status || "")} / ${esc(row.size || "")} / ${row.exists ? "plik OK" : "plik zniknal"}</small>
      <small>${esc(row.path || "")}</small>
      <div class="nx-mod-actions"><button class="nav-btn" onclick="wakeHyperSleep('${esc(row.id)}')">WYBUDZ</button><button class="nav-btn" onclick="deleteHyperSleep('${esc(row.id)}')">USUN</button></div>
    </div>`).join("") : '<div class="nx-mod-card"><strong>BRAK STANOW</strong><small>Zamroz VM, aby zapisac RAM na dysk.</small></div>';
  }

  window.loadHyperSleep = loadHyperSleep;
  window.freezeHyperSleep = async function () {
    const payload = { vm_id: qs("sleep-vm")?.value || "", label: qs("sleep-label")?.value || "manual" };
    const r = await apiFetch("/api/hyper-sleep/freeze", { method: "POST", body: JSON.stringify(payload) });
    const d = await r.json().catch(() => ({}));
    if (!r.ok) return alert(d.detail || "Nie zamrozono VM.");
    loadHyperSleep();
  };
  window.wakeHyperSleep = async function (id) {
    const r = await apiFetch("/api/hyper-sleep/wake", { method: "POST", body: JSON.stringify({ id }) });
    const d = await r.json().catch(() => ({}));
    if (!r.ok) alert(d.detail || "Nie wybudzono VM.");
    loadHyperSleep();
  };
  window.deleteHyperSleep = async function (id) {
    if (!confirm("Usunac plik stanu Hyper-Sleep?")) return;
    await apiFetch("/api/hyper-sleep/delete", { method: "POST", body: JSON.stringify({ id }) });
    loadHyperSleep();
  };

  function canvasNodeTitle(type) {
    return ({ router: "Router", linux: "Linux VM", windows: "Windows VM", database: "Database" }[type] || "Node");
  }

  function renderCanvasDraft() {
    const board = qs("canvas-board");
    if (!board) return;
    const nodes = nexusCanvasDraft.nodes || [];
    const byId = new Map(nodes.map(n => [n.id, n]));
    const wires = (nexusCanvasDraft.edges || []).map(edge => {
      const a = byId.get(edge.from), b = byId.get(edge.to);
      if (!a || !b) return "";
      return `<line x1="${a.x + 9}%" y1="${a.y + 6}%" x2="${b.x + 9}%" y2="${b.y + 6}%" stroke="rgba(0,255,255,.75)" stroke-width="2" stroke-dasharray="7 5" />`;
    }).join("");
    board.innerHTML = `<svg class="canvas-wire" viewBox="0 0 100 100" preserveAspectRatio="none">${wires}</svg>` + nodes.map(node => `
      <div class="canvas-node ${esc(node.type)} ${nexusCanvasLinkFrom === node.id ? "selected" : ""}" style="left:${node.x}%;top:${node.y}%;" onpointerdown="startCanvasDrag(event,'${esc(node.id)}')">
        <strong>${esc(node.label || canvasNodeTitle(node.type))}</strong>
        <small>${esc(node.type)} / ${esc(node.id)}</small>
        <div class="nx-mod-actions" style="margin-top:7px;"><button class="nav-btn" style="padding:4px 6px;font-size:9px;" onclick="event.stopPropagation();connectCanvasNode('${esc(node.id)}')">KABEL</button><button class="nav-btn" style="padding:4px 6px;font-size:9px;" onclick="event.stopPropagation();deleteCanvasNode('${esc(node.id)}')">X</button></div>
      </div>`).join("");
  }

  window.addCanvasNode = function (type) {
    const idx = nexusCanvasDraft.nodes.length + 1;
    nexusCanvasDraft.nodes.push({ id: `${type}-${Date.now().toString(36)}-${idx}`, type, label: `${canvasNodeTitle(type)} ${idx}`, x: 8 + ((idx * 13) % 66), y: 10 + ((idx * 17) % 66) });
    renderCanvasDraft();
  };

  window.startCanvasDrag = function (event, id) {
    if (event.target.tagName === "BUTTON") return;
    event.preventDefault();
    const board = qs("canvas-board");
    const node = nexusCanvasDraft.nodes.find(n => n.id === id);
    if (!board || !node) return;
    const move = ev => {
      const rect = board.getBoundingClientRect();
      node.x = Math.max(1, Math.min(86, ((ev.clientX - rect.left - 56) / rect.width) * 100));
      node.y = Math.max(1, Math.min(86, ((ev.clientY - rect.top - 28) / rect.height) * 100));
      renderCanvasDraft();
    };
    const up = () => { document.removeEventListener("pointermove", move); document.removeEventListener("pointerup", up); };
    document.addEventListener("pointermove", move);
    document.addEventListener("pointerup", up);
  };

  window.connectCanvasNode = function (id) {
    if (!nexusCanvasLinkFrom) {
      nexusCanvasLinkFrom = id;
      renderCanvasDraft();
      return;
    }
    if (nexusCanvasLinkFrom !== id) {
      const exists = nexusCanvasDraft.edges.some(e => (e.from === nexusCanvasLinkFrom && e.to === id) || (e.from === id && e.to === nexusCanvasLinkFrom));
      if (!exists) nexusCanvasDraft.edges.push({ from: nexusCanvasLinkFrom, to: id });
    }
    nexusCanvasLinkFrom = null;
    renderCanvasDraft();
  };

  window.deleteCanvasNode = function (id) {
    nexusCanvasDraft.nodes = nexusCanvasDraft.nodes.filter(n => n.id !== id);
    nexusCanvasDraft.edges = nexusCanvasDraft.edges.filter(e => e.from !== id && e.to !== id);
    if (nexusCanvasLinkFrom === id) nexusCanvasLinkFrom = null;
    renderCanvasDraft();
  };

  window.clearCanvasDraft = function () {
    nexusCanvasDraft = { name: qs("canvas-name")?.value || "lab-topology", nodes: [], edges: [] };
    nexusCanvasLinkFrom = null;
    renderCanvasDraft();
  };

  async function loadCanvasTopologies() {
    const box = qs("canvas-saved");
    if (!box) return;
    const data = await (await apiFetch("/api/canvas/topologies")).json();
    const rows = data.items || [];
    box.innerHTML = rows.length ? rows.map(row => `<div class="nx-mod-card">
      <strong>${esc(row.name)}</strong>
      <small>${(row.nodes || []).length} wezlow / ${(row.edges || []).length} kabli</small>
      <div class="nx-mod-actions"><button class="nav-btn" onclick="loadCanvasDraft('${esc(row.id)}')">WCZYTAJ</button><button class="nav-btn" onclick="deployCanvasTopology('${esc(row.id)}')">WDROZ PLAN</button></div>
    </div>`).join("") : '<div class="nx-mod-card"><strong>BRAK TOPOLOGII</strong><small>Zbuduj i zapisz pierwszy diagram.</small></div>';
    window.__canvasSavedRows = rows;
  }

  window.loadCanvasDraft = function (id) {
    const row = (window.__canvasSavedRows || []).find(x => x.id === id);
    if (!row) return;
    nexusCanvasDraft = { name: row.name, nodes: row.nodes || [], edges: row.edges || [] };
    if (qs("canvas-name")) qs("canvas-name").value = row.name || "lab-topology";
    renderCanvasDraft();
  };

  window.saveCanvasTopology = async function () {
    const payload = { name: qs("canvas-name")?.value || nexusCanvasDraft.name || "lab-topology", nodes: nexusCanvasDraft.nodes, edges: nexusCanvasDraft.edges };
    const r = await apiFetch("/api/canvas/topologies", { method: "POST", body: JSON.stringify(payload) });
    const d = await r.json().catch(() => ({}));
    if (!r.ok) return alert(d.detail || "Nie zapisano topologii.");
    loadCanvasTopologies();
  };

  window.deployCanvasTopology = async function (id) {
    const r = await apiFetch("/api/canvas/deploy", { method: "POST", body: JSON.stringify({ id }) });
    const d = await r.json().catch(() => ({}));
    alert(r.ok ? JSON.stringify(d.plan || {}, null, 2) : (d.detail || "Nie przygotowano planu wdrozenia."));
    loadCanvasTopologies();
  };

  async function loadCanvas() {
    renderCanvasDraft();
    loadCanvasTopologies();
  }

  async function loadForge() {
    const grid = qs("forge-grid");
    if (!grid) return;
    grid.innerHTML = '<div class="nx-mod-card"><strong>LADOWANIE FORGE...</strong></div>';
    const data = await (await apiFetch("/api/forge/templates")).json();
    const rows = data.items || [];
    grid.innerHTML = rows.length ? rows.map(item => `<div class="nx-mod-card">
      <strong>${esc(item.name)}</strong>
      <small>${esc(item.vm_id)} / seller: ${esc(item.seller || "")} / price: ${esc(item.price || 0)} tokenow</small>
      <small>${esc(item.description || "")}</small>
      <input class="cyber-input" id="forge-buy-${esc(item.id)}" style="margin:8px 0 0;" placeholder="nazwa nowej VM">
      <div class="nx-mod-actions"><button class="nav-btn" onclick="buyForgeTemplate('${esc(item.id)}')">KUP / KLONUJ</button></div>
    </div>`).join("") : '<div class="nx-mod-card"><strong>BRAK TEMPLATE</strong><small>Opublikuj gotowa VM jako wzorzec.</small></div>';
  }

  window.publishForgeTemplate = async function () {
    const payload = { vm_id: qs("forge-vm")?.value || "", name: qs("forge-name")?.value || "", price: Number(qs("forge-price")?.value || 0), description: qs("forge-desc")?.value || "" };
    const r = await apiFetch("/api/forge/publish", { method: "POST", body: JSON.stringify(payload) });
    const d = await r.json().catch(() => ({}));
    if (!r.ok) return alert(d.detail || "Nie opublikowano template.");
    loadForge();
  };

  window.buyForgeTemplate = async function (id) {
    const name = qs(`forge-buy-${id}`)?.value || `forge-${Date.now().toString(36)}`;
    const r = await apiFetch("/api/forge/buy", { method: "POST", body: JSON.stringify({ id, name }) });
    const d = await r.json().catch(() => ({}));
    alert(r.ok ? `Klon gotowy: ${d.vm_id}` : (d.detail || "Nie sklonowano template."));
    loadForge();
  };

  async function loadAiCommanderLog() {
    const box = qs("commander-log");
    if (!box) return;
    const data = await (await apiFetch("/api/ai-commander/log")).json();
    box.textContent = (data.items || []).map(row => `[${row.created_at}] ${row.created_by}: ${row.command}\nTARGET: ${row.target || "-"}\nACTIONS: ${(row.actions || []).map(a => a.kind + ":" + (a.action || a.snapshot || a.memory_mb || "")).join(", ") || "-"}\nRESULTS: ${(row.results || []).map(r => `${r.kind}:${r.code}`).join(", ") || "-"}\n`).join("\n") || "Brak historii.";
  }

  window.loadAiCommanderLog = loadAiCommanderLog;
  window.runAiCommander = async function () {
    const payload = { command: qs("commander-input")?.value || "", execute: !!qs("commander-execute")?.checked };
    const r = await apiFetch("/api/ai-commander/run", { method: "POST", body: JSON.stringify(payload) });
    const d = await r.json().catch(() => ({}));
    qs("commander-result").innerHTML = `<strong>${esc(d.status || "AI")}</strong><small>target: ${esc(d.target || "-")} / ${esc(d.message || "")}</small><pre style="white-space:pre-wrap;color:#aaa;font-size:11px;">${esc(JSON.stringify(d.actions || d.results || [], null, 2))}</pre>`;
    loadAiCommanderLog();
  };

  async function loadArchiver() {
    const status = qs("archiver-status");
    const jobs = qs("archiver-jobs");
    if (!status || !jobs) return;
    const data = await (await apiFetch("/api/archiver/status")).json();
    const tools = data.tools || {};
    status.innerHTML = `
      <div class="object-kv"><b>ZIP/TAR</b><span>${tools.zipfile && tools.tarfile ? "OK" : "BRAK"}</span></div>
      <div class="object-kv"><b>7Z</b><span>${tools.py7zr ? "OK" : "brak py7zr"}</span></div>
      <div class="object-kv"><b>ISO</b><span>${tools.genisoimage ? "genisoimage/mkisofs OK" : "brak generatora ISO"}</span></div>
    `;
    jobs.innerHTML = (data.jobs || []).map(j => `<div class="nx-mod-card"><strong>${esc(j.kind)} / ${esc(j.target || j.member || "")}</strong><small>${esc(j.created_at || "")} / ${esc(j.size || "")}</small><small>${esc(j.archive || "")}</small></div>`).join("") || '<div class="nx-mod-card"><strong>BRAK JOBOW</strong><small>Operacje archiwum pojawia sie tutaj.</small></div>';
  }

  window.listArchive = async function () {
    const path = qs("archiver-path")?.value || "";
    const box = qs("archiver-list");
    box.innerHTML = '<div class="archiver-row"><span></span><b>SKAN...</b><span></span></div>';
    const r = await apiFetch("/api/archiver/list", { method: "POST", body: JSON.stringify({ path }) });
    const d = await r.json().catch(() => ({}));
    if (!r.ok) { box.innerHTML = `<div class="archiver-row"><span></span><b>ERROR</b><span>${esc(d.detail || "")}</span></div>`; return; }
    box.dataset.archivePath = path;
    box.innerHTML = (d.items || []).map(item => `<label class="archiver-row">
      <input type="radio" name="archive-member" value="${esc(item.name)}" ${item.is_dir ? "disabled" : ""}>
      <span>${item.is_dir ? "[DIR]" : "[FILE]"} ${esc(item.name)}</span>
      <span>${esc(item.size_label || "")}</span>
    </label>`).join("") || '<div class="archiver-row"><span></span><b>PUSTO</b><span></span></div>';
    box.insertAdjacentHTML("afterend", '<div class="nx-mod-actions" id="archiver-extract-actions"><button class="nav-btn" onclick="extractArchiveMember()">WYPACKUJ DO DROP</button><button class="nav-btn" onclick="extractArchiveMember(\'iso\')">WYPACKUJ DO ISO</button></div>');
  };

  window.extractArchiveMember = async function (dest) {
    const member = document.querySelector('input[name="archive-member"]:checked')?.value;
    const path = qs("archiver-list")?.dataset.archivePath || qs("archiver-path")?.value || "";
    if (!member) return alert("Zaznacz plik w archiwum.");
    const r = await apiFetch("/api/archiver/extract", { method: "POST", body: JSON.stringify({ path, member, dest: dest || "drop" }) });
    const d = await r.json().catch(() => ({}));
    if (!r.ok) return alert(d.detail || "Nie wypakowano.");
    loadArchiver();
  };

  function packPathsFromBox() {
    return (qs("archiver-pack-paths")?.value || "").split(/\r?\n/).map(x => x.trim()).filter(Boolean);
  }
  window.createArchiveZip = async function () {
    const r = await apiFetch("/api/archiver/zip", { method: "POST", body: JSON.stringify({ paths: packPathsFromBox(), output_name: qs("archiver-output")?.value || "nexus-pack.zip" }) });
    const d = await r.json().catch(() => ({}));
    if (!r.ok) return alert(d.detail || "ZIP failed");
    loadArchiver();
  };
  window.createArchiveIso = async function () {
    const output = (qs("archiver-output")?.value || "nexus-pack.iso").replace(/\.zip$/i, ".iso");
    const r = await apiFetch("/api/archiver/iso", { method: "POST", body: JSON.stringify({ paths: packPathsFromBox(), output_name: output }) });
    const d = await r.json().catch(() => ({}));
    if (!r.ok) return alert(d.detail || "ISO failed");
    loadArchiver();
  };

  async function loadBastion() {
    const status = qs("bastion-status");
    const list = qs("bastion-list");
    if (!status || !list) return;
    const [st, rows] = await Promise.all([(await apiFetch("/api/bastion/status")).json(), (await apiFetch("/api/bastion/targets")).json()]);
    status.innerHTML = `
      <div class="object-kv"><b>GUACD</b><span>${st.tools?.guacd ? "OK" : "brak Apache Guacamole"}</span></div>
      <div class="object-kv"><b>SSH</b><span>${st.tools?.ssh ? "OK" : "brak ssh"}</span></div>
      <div class="object-kv"><b>CELE</b><span>${esc(st.targets || 0)} zapisanych bram</span></div>
    `;
    list.innerHTML = (rows.items || []).map(t => `<div class="nx-mod-card">
      <strong><span class="bastion-badge">${esc((t.kind || "").toUpperCase())}</span>${esc(t.name)}</strong>
      <small>${esc(t.username || "")}@${esc(t.host)}:${esc(t.port)}<br>${esc(t.note || "")}</small>
      <div class="nx-mod-actions"><button class="nav-btn" onclick="launchBastion('${esc(t.id)}')">LAUNCH</button><button class="nav-btn" onclick="deleteBastion('${esc(t.id)}')">USUN</button></div>
    </div>`).join("") || '<div class="nx-mod-card"><strong>BRAK CELÓW</strong><small>Dodaj RDP/VNC/SSH albo NEXUS Link.</small></div>';
  }

  window.saveBastionTarget = async function () {
    const payload = { name: qs("bastion-name")?.value || "", kind: qs("bastion-kind")?.value || "rdp", host: qs("bastion-host")?.value || "", port: Number(qs("bastion-port")?.value || 3389), username: qs("bastion-user")?.value || "", note: "" };
    const r = await apiFetch("/api/bastion/targets", { method: "POST", body: JSON.stringify(payload) });
    const d = await r.json().catch(() => ({}));
    if (!r.ok) return alert(d.detail || "Nie zapisano Bastion target.");
    loadBastion();
  };
  window.launchBastion = async id => { const r = await apiFetch("/api/bastion/launch", { method: "POST", body: JSON.stringify({ id }) }); const d = await r.json().catch(() => ({})); alert(d.message || d.status || "Bastion"); };
  window.deleteBastion = async id => { await apiFetch("/api/bastion/delete", { method: "POST", body: JSON.stringify({ id }) }); loadBastion(); };

  async function loadWorkers() {
    const status = qs("worker-status");
    const list = qs("worker-list");
    if (!status || !list) return;
    const [st, rows] = await Promise.all([(await apiFetch("/api/workers/status")).json(), (await apiFetch("/api/workers")).json()]);
    status.innerHTML = `
      <div class="object-kv"><b>PYTHON</b><span>${st.tools?.python3 ? "OK" : "BRAK"}</span></div>
      <div class="object-kv"><b>NODE</b><span>${st.tools?.node ? "OK" : "BRAK"}</span></div>
      <div class="object-kv"><b>DOCKER/FIRECRACKER</b><span>${st.tools?.docker ? "Docker OK" : "Docker brak"} / ${st.tools?.firecracker ? "Firecracker OK" : "Firecracker brak"}</span></div>
    `;
    list.innerHTML = (rows.items || []).map(w => `<div class="nx-mod-card"><strong>${esc(w.name)}</strong><small>${esc(w.runtime)} / ${esc(w.created_at || "")}</small><div class="nx-mod-actions"><button class="nav-btn" onclick="loadWorkerIntoEditor('${esc(w.id)}')">WCZYTAJ</button><button class="nav-btn" onclick="runWorker('${esc(w.id)}')">RUN</button></div></div>`).join("") || '<div class="nx-mod-card"><strong>BRAK WORKERÓW</strong><small>Zapisz pierwszy skrypt.</small></div>';
    window.__workersRows = rows.items || [];
  }

  window.loadWorkerIntoEditor = function (id) {
    const row = (window.__workersRows || []).find(w => w.id === id);
    if (!row) return;
    qs("worker-name").value = row.name || "worker";
    qs("worker-runtime").value = row.runtime || "python";
    qs("worker-code").value = row.code || "";
  };
  window.saveWorker = async function () {
    const payload = { name: qs("worker-name")?.value || "worker", runtime: qs("worker-runtime")?.value || "python", code: qs("worker-code")?.value || "" };
    const r = await apiFetch("/api/workers", { method: "POST", body: JSON.stringify(payload) });
    const d = await r.json().catch(() => ({}));
    if (!r.ok) return alert(d.detail || "Nie zapisano workera.");
    loadWorkers();
  };
  window.runWorker = async function (id) {
    const payload = id ? { id, timeout: Number(qs("worker-timeout")?.value || 8) } : { runtime: qs("worker-runtime")?.value || "python", code: qs("worker-code")?.value || "", timeout: Number(qs("worker-timeout")?.value || 8) };
    const r = await apiFetch("/api/workers/run", { method: "POST", body: JSON.stringify(payload) });
    const d = await r.json().catch(() => ({}));
    if (!r.ok) return alert(d.detail || "Worker failed");
    qs("worker-result").textContent = `CODE ${d.result?.code}\nSTDOUT:\n${d.result?.stdout || ""}\nSTDERR:\n${d.result?.stderr || ""}`;
    loadWorkers();
  };

  function b64FromBytes(bytes) {
    let bin = "";
    bytes.forEach(b => bin += String.fromCharCode(b));
    return btoa(bin).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
  }

  async function loadVault() {
    const box = qs("vault-list");
    if (!box) return;
    const data = await (await apiFetch("/api/vault/links")).json();
    box.innerHTML = (data.items || []).map(v => `<div class="nx-mod-card" style="border-left-color:${v.status === "active" && !v.expired ? "var(--acc-crit)" : "var(--acc-warn)"}">
      <strong>${esc(v.title || v.filename)}</strong>
      <small>${esc(v.status || "")} / views ${esc(v.views || 0)}:${esc(v.max_views || 1)} / exp ${esc(v.expires_at || "")}</small>
      <small>${v.encrypted ? "client-side AES-GCM" : "server file link"} / ${esc(v.size || "")}</small>
      <div class="nx-mod-actions"><button class="nav-btn" onclick="deleteVaultLink('${esc(v.id)}')">USUN</button></div>
    </div>`).join("") || '<div class="nx-mod-card"><strong>BRAK VAULT LINKÓW</strong><small>Utworz pierwszy jednorazowy link.</small></div>';
  }

  window.encryptAndUploadVault = async function () {
    const file = qs("vault-file")?.files?.[0];
    if (!file) return alert("Wybierz plik.");
    if (!crypto.subtle) return alert("Ta przegladarka nie wspiera Web Crypto.");
    const key = await crypto.subtle.generateKey({ name: "AES-GCM", length: 256 }, true, ["encrypt", "decrypt"]);
    const rawKey = new Uint8Array(await crypto.subtle.exportKey("raw", key));
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const cipher = new Uint8Array(await crypto.subtle.encrypt({ name: "AES-GCM", iv }, key, await file.arrayBuffer()));
    const blob = new Blob([iv, cipher], { type: "application/octet-stream" });
    const form = new FormData();
    form.append("file", new File([blob], file.name + ".nexusvault"));
    form.append("title", file.name);
    form.append("max_views", qs("vault-views")?.value || "1");
    form.append("ttl_minutes", qs("vault-ttl")?.value || "1440");
    form.append("encrypted", "1");
    const r = await apiFetch("/api/vault/upload", { method: "POST", body: form });
    const d = await r.json().catch(() => ({}));
    if (!r.ok) return alert(d.detail || "Vault upload failed");
    const link = `${d.public_url}#${b64FromBytes(rawKey)}`;
    qs("vault-result").innerHTML = `<div class="nx-mod-card"><strong>VAULT LINK GOTOWY</strong><textarea class="vault-link" readonly>${esc(link)}</textarea><small>Fragment po # nie trafia do serwera. Bez niego plik jest bezuzyteczny.</small></div>`;
    loadVault();
  };

  window.createVaultServerLink = async function () {
    const payload = { path: qs("vault-server-path")?.value || "", max_views: Number(qs("vault-server-views")?.value || 1), ttl_minutes: Number(qs("vault-server-ttl")?.value || 1440), destroy_after_read: true };
    const r = await apiFetch("/api/vault/link", { method: "POST", body: JSON.stringify(payload) });
    const d = await r.json().catch(() => ({}));
    if (!r.ok) return alert(d.detail || "Nie utworzono linku.");
    qs("vault-result").innerHTML = `<div class="nx-mod-card"><strong>SERVER VAULT LINK</strong><textarea class="vault-link" readonly>${esc(d.public_url || "")}</textarea></div>`;
    loadVault();
  };
  window.deleteVaultLink = async id => { await apiFetch("/api/vault/delete", { method: "POST", body: JSON.stringify({ id }) }); loadVault(); };

  async function loadGlobalTerminalLog() {
    const data = await (await apiFetch("/api/global-terminal/log")).json();
    const text = (data.items || []).map(row => `[${row.created_at}] ${row.user}> ${row.command}\n${row.response?.message || ""}`).join("\n\n") || "Brak historii.";
    if (qs("global-terminal-page-log")) qs("global-terminal-page-log").textContent = text;
    if (qs("global-terminal-log")) qs("global-terminal-log").textContent = text;
  }

  function installGlobalTerminal() {
    if (qs("global-terminal")) return;
    const box = document.createElement("div");
    box.id = "global-terminal";
    box.innerHTML = `<div class="global-terminal-row"><input id="global-terminal-input" class="cyber-input" style="margin:0;" placeholder="/help albo wiadomosc na czat"><button class="nav-btn" style="margin:0;border-color:var(--acc-cyan);color:var(--acc-cyan);" onclick="sendGlobalTerminal()">SEND</button></div><div id="global-terminal-log"></div>`;
    document.body.appendChild(box);
    document.addEventListener("keydown", event => {
      if (event.key === "~" || event.key === "`") {
        if (["INPUT","TEXTAREA"].includes(document.activeElement?.tagName)) return;
        event.preventDefault();
        toggleGlobalTerminal();
      }
    });
  }

  window.toggleGlobalTerminal = function (force) {
    const box = qs("global-terminal");
    if (!box) return;
    box.classList.toggle("open", force === true ? true : force === false ? false : !box.classList.contains("open"));
    if (box.classList.contains("open")) { qs("global-terminal-input")?.focus(); loadGlobalTerminalLog(); }
  };

  window.sendGlobalTerminal = async function () {
    const input = qs("global-terminal-input");
    const command = input?.value || "";
    if (!command.trim()) return;
    const r = await apiFetch("/api/global-terminal/command", { method: "POST", body: JSON.stringify({ command }) });
    const d = await r.json().catch(() => ({}));
    if (!r.ok) alert(d.detail || "Global terminal error");
    if (input) input.value = "";
    loadGlobalTerminalLog();
  };

  async function loadUsbDevices() {
    const statusBox = qs("usb-status");
    const objectsBox = qs("cloud-usb-objects");
    const mountsBox = qs("cloud-usb-mounts");
    const hostBox = qs("host-usb-list");
    const vmSelect = qs("cloud-usb-vm");
    if (!statusBox || !objectsBox || !mountsBox || !hostBox || !vmSelect) return;
    statusBox.innerHTML = '<div class="object-kv"><b>USB</b><span>Ladowanie...</span></div>';
    objectsBox.innerHTML = '<div class="nx-mod-card"><strong>SKANOWANIE OBJECT STORAGE...</strong></div>';
    mountsBox.innerHTML = '<div class="nx-mod-card"><strong>SKANOWANIE MOUNTOW...</strong></div>';
    hostBox.innerHTML = '<div class="nx-mod-card"><strong>LSUSB...</strong></div>';
    try {
      const [status, vms, objects, host] = await Promise.all([
        (await apiFetch("/api/usb/status")).json(),
        (await apiFetch("/api/vms/list", { silent: true })).json(),
        (await apiFetch("/api/usb/cloud/objects")).json(),
        (await apiFetch("/api/usb/host/list")).json().catch(() => ({ items: [], message: "admin only albo brak lsusb" })),
      ]);
      const tools = status.tools || {};
      statusBox.innerHTML = `
        <div class="object-kv"><b>CLOUD USB</b><span>${tools.iso_builder ? "ISO builder: " + esc(tools.iso_builder) : "Brak buildera ISO"}</span></div>
        <div class="object-kv"><b>HOST USB</b><span>lsusb: ${tools.lsusb ? "OK" : "BRAK"}</span></div>
        <div class="object-kv"><b>TRYB</b><span>MinIO -> ISO -> virsh attach-disk jako nośnik readonly.</span></div>
      `;
      const runningAware = vms.items || [];
      vmSelect.innerHTML = runningAware.map(vm => `<option value="${esc(vm.id)}">${esc(vm.name || vm.id)} / ${esc(vm.status || "")}</option>`).join("") || '<option value="">Brak VM</option>';
      const objectRows = objects.objects || [];
      objectsBox.innerHTML = objectRows.length ? objectRows.map(item => `
        <label class="nx-mod-card" style="cursor:pointer;">
          <input type="checkbox" class="cloud-usb-object" value="${esc(item.id)}" style="margin-right:7px;">
          <strong>${esc(item.filename || item.key)}</strong>
          <small>${esc(item.kind || "data")} | ${esc(item.size_label || "")}</small>
          <small>${esc(item.bucket || "")}</small>
        </label>
      `).join("") : '<div class="nx-mod-card"><strong>BRAK OBIEKTOW</strong><small>Najpierw wrzuc pliki do OBJECTS / MinIO.</small></div>';
      const mounts = status.mounts || [];
      mountsBox.innerHTML = mounts.length ? mounts.map(m => `
        <div class="nx-mod-card">
          <strong>${esc(m.label || "CLOUD_USB")} -> ${esc(m.vm_id || "")}</strong>
          <small>${esc(m.status || "")} / target: ${esc(m.target || "")}</small>
          <small>${(m.files || []).map(esc).join(", ")}</small>
          <div class="nx-mod-actions">${m.status === "attached" ? `<button class="nav-btn" style="border-color:var(--acc-warn);color:var(--acc-warn);" onclick="detachCloudUsb('${esc(m.id)}')">EJECT</button>` : ""}</div>
        </div>
      `).join("") : '<div class="nx-mod-card"><strong>BRAK MOUNTOW</strong><small>Nic nie jest podpiete do VM.</small></div>';
      const hostItems = host.items || [];
      hostBox.innerHTML = hostItems.length ? hostItems.map(u => `<div class="nx-mod-card"><strong>${esc(u.vendor_id)}:${esc(u.product_id)}</strong><small>${esc(u.name || u.raw)}</small></div>`).join("") : `<div class="nx-mod-card"><strong>BRAK HOST USB</strong><small>${esc(host.message || "Brak fizycznych urzadzen USB na VPS.")}</small></div>`;
    } catch (e) {
      statusBox.innerHTML = '<div class="object-kv"><b>ERROR</b><span>USB API nie odpowiada.</span></div>';
    }
  }

  window.mountCloudUsb = async function () {
    const vm_id = qs("cloud-usb-vm")?.value || "";
    const object_ids = Array.from(document.querySelectorAll(".cloud-usb-object:checked")).map(input => input.value);
    const label = qs("cloud-usb-label")?.value || "NEXUS_USB";
    if (!vm_id) return alert("Wybierz VM.");
    if (!object_ids.length) return alert("Zaznacz pliki z Object Storage.");
    await apiFetch("/api/usb/cloud/mount", { method: "POST", body: JSON.stringify({ vm_id, object_ids, label }) });
    loadUsbDevices();
  };

  window.detachCloudUsb = async function (mountId) {
    await apiFetch("/api/usb/cloud/detach", { method: "POST", body: JSON.stringify({ mount_id: mountId }) });
    loadUsbDevices();
  };

  async function sendPresenceHeartbeat() {
    try {
      const label = `${navigator.platform || "WEB"} / ${navigator.userAgent.split(" ").slice(-2).join(" ")}`;
      await apiFetch("/api/presence/heartbeat", { method: "POST", body: JSON.stringify({ device_id: deviceId, label }) });
    } catch (e) {}
  }
  function startPresenceHeartbeat() {
    if (presenceTimer) return;
    sendPresenceHeartbeat();
    presenceTimer = setInterval(sendPresenceHeartbeat, 30000);
  }
  async function loadPresence() {
    startPresenceHeartbeat();
    const data = await (await apiFetch("/api/presence")).json();
    qs("presence-count").textContent = String(data.active_count || data.count || 0);
    qs("presence-list").innerHTML = (data.sessions || []).map(s => `<div class="nx-mod-card" style="min-height:0;border-left-color:${s.active ? "var(--acc-cyan)" : "var(--acc-warn)"}"><strong>${esc(s.username)} / ${esc(s.role)}</strong><small>${esc(s.label)}<br>ostatnio: ${s.age_seconds}s temu<br>ID: ${esc(s.device_id)}</small></div>`).join("");
    const radar = qs("presence-radar");
    radar.querySelectorAll(".radar-dot").forEach(dot => dot.remove());
    (data.sessions || []).forEach((s, i) => {
      const dot = document.createElement("span");
      dot.className = "radar-dot" + (s.active ? "" : " idle");
      dot.style.left = `${18 + ((i * 29) % 68)}%`;
      dot.style.top = `${20 + ((i * 43) % 62)}%`;
      dot.title = `${s.username} ${s.label}`;
      radar.appendChild(dot);
    });
  }

  async function loadAlerts() {
    const alerts = await (await apiFetch("/api/alerts")).json();
    qs("alerts-list").innerHTML = alerts.length ? alerts.map(a => `<div class="alert-row ${esc(a.level)}"><strong style="color:#fff;">${esc(a.title)}</strong><small style="display:block;color:#777;">${esc(a.created_at)} / ${esc(a.created_by)} / ${esc(a.level)}</small><div style="color:#bbb;margin-top:6px;">${esc(a.body)}</div></div>`).join("") : '<div class="alert-row info">Brak alertow.</div>';
  }
  window.createAlert = async function () {
    const title = qs("alert-title").value.trim();
    if (!title) return;
    await apiFetch("/api/alerts", { method: "POST", body: JSON.stringify({ title, body: qs("alert-body").value, level: qs("alert-level").value }) });
    qs("alert-title").value = ""; qs("alert-body").value = "";
    loadAlerts();
  };
  async function pollAlertsForNotifications() {
    try {
      const alerts = await (await apiFetch("/api/alerts")).json();
      alerts.slice(0, 8).forEach(a => {
        if (!knownAlerts.has(a.id)) {
          knownAlerts.add(a.id);
          if (Notification.permission === "granted" && (a.level === "critical" || a.level === "warn")) {
            navigator.serviceWorker.getRegistration().then(reg => {
              if (reg) reg.showNotification(a.title || "NEXUS ALERT", { body: a.body || a.level, tag: a.id, data: "/#alerts" });
              else new Notification(a.title || "NEXUS ALERT", { body: a.body || a.level });
            });
          }
        }
      });
    } catch (e) {}
  }
  window.enableNeuralAlerts = async function () {
    if (!("Notification" in window)) { qs("alert-permission").textContent = "Status: brak wsparcia w przegladarce"; return; }
    const permission = await Notification.requestPermission();
    if ("serviceWorker" in navigator) await navigator.serviceWorker.register("/sw.js");
    await apiFetch("/api/push/subscribe", { method: "POST", body: JSON.stringify({ subscription: { endpoint: "local-notification:" + deviceId } }) });
    qs("alert-permission").textContent = "Status: " + permission;
    if (!alertTimer) alertTimer = setInterval(pollAlertsForNotifications, 15000);
    pollAlertsForNotifications();
  };

  function p2pLog(msg) {
    const log = qs("p2p-log");
    if (!log) return;
    log.textContent += `[${new Date().toLocaleTimeString()}] ${msg}\n`;
    log.scrollTop = log.scrollHeight;
  }
  async function sendP2PSignal(payload) {
    await apiFetch("/api/p2p/signal", { method: "POST", body: JSON.stringify({ room: p2pState.room, peer: p2pState.peer, payload }) });
  }
  function setupP2PChannel(channel) {
    p2pState.channel = channel;
    channel.binaryType = "arraybuffer";
    channel.onopen = () => { qs("p2p-status").textContent = "DATA LINK ONLINE"; p2pLog("kanal danych otwarty"); };
    channel.onclose = () => { qs("p2p-status").textContent = "DATA LINK CLOSED"; p2pLog("kanal danych zamkniety"); };
    channel.onmessage = event => {
      if (typeof event.data === "string") {
        const msg = JSON.parse(event.data);
        if (msg.type === "file-meta") {
          p2pState.meta = msg;
          p2pState.chunks = [];
          p2pState.rxBytes = 0;
          p2pState.rxTransferId = "p2p-in-" + Date.now();
          if (window.NexusTransfers) window.NexusTransfers.start({ id: p2pState.rxTransferId, label: `P2P IN: ${msg.name}`, type: "p2p", total: msg.size || 0, status: "running", detail: "WebRTC" });
          p2pLog(`odbieram ${msg.name} (${msg.size} B)`);
        }
        if (msg.type === "file-done") {
          const blob = new Blob(p2pState.chunks, { type: p2pState.meta?.mime || "application/octet-stream" });
          const url = URL.createObjectURL(blob);
          qs("p2p-downloads").innerHTML = `<div class="nx-mod-card"><strong>${esc(p2pState.meta?.name || "plik.bin")}</strong><small>${blob.size} B odebrane P2P</small><div class="nx-mod-actions"><a class="nav-btn" download="${esc(p2pState.meta?.name || "plik.bin")}" href="${url}">POBIERZ</a></div></div>` + qs("p2p-downloads").innerHTML;
          if (window.NexusTransfers && p2pState.rxTransferId) window.NexusTransfers.finish(p2pState.rxTransferId, "odebrano");
          p2pLog("plik odebrany");
        }
      } else {
        p2pState.chunks.push(event.data);
        p2pState.rxBytes = (p2pState.rxBytes || 0) + (event.data.byteLength || event.data.size || 0);
        if (window.NexusTransfers && p2pState.rxTransferId) window.NexusTransfers.update(p2pState.rxTransferId, { loaded: p2pState.rxBytes, total: p2pState.meta?.size || 0, status: "running", detail: "WebRTC" });
      }
    };
  }
  function createPeerConnection(initiator) {
    if (p2pState.pc) p2pState.pc.close();
    p2pState.pc = new RTCPeerConnection({ iceServers: [{ urls: "stun:stun.l.google.com:19302" }] });
    p2pState.pc.onicecandidate = event => { if (event.candidate) sendP2PSignal({ type: "candidate", candidate: event.candidate.toJSON() }).catch(() => {}); };
    p2pState.pc.onconnectionstatechange = () => { qs("p2p-status").textContent = p2pState.pc.connectionState.toUpperCase(); };
    p2pState.pc.ondatachannel = event => setupP2PChannel(event.channel);
    if (initiator) setupP2PChannel(p2pState.pc.createDataChannel("nexus-file"));
  }
  async function handleP2PSignal(signal) {
    if (p2pState.seen.has(signal.id)) return;
    p2pState.seen.add(signal.id);
    const payload = signal.payload || {};
    if (payload.type === "offer") {
      if (!p2pState.pc) createPeerConnection(false);
      await p2pState.pc.setRemoteDescription(new RTCSessionDescription(payload.offer));
      const answer = await p2pState.pc.createAnswer();
      await p2pState.pc.setLocalDescription(answer);
      await sendP2PSignal({ type: "answer", answer: answer.toJSON ? answer.toJSON() : answer });
      p2pLog("odebrano oferte, wyslano odpowiedz");
    } else if (payload.type === "answer" && p2pState.pc && !p2pState.pc.currentRemoteDescription) {
      await p2pState.pc.setRemoteDescription(new RTCSessionDescription(payload.answer));
      p2pLog("polaczenie zestawione");
    } else if (payload.type === "candidate" && p2pState.pc) {
      try { await p2pState.pc.addIceCandidate(new RTCIceCandidate(payload.candidate)); } catch (e) {}
    }
  }
  async function p2pPoll() {
    try {
      const data = await (await apiFetch(`/api/p2p/signals?room=${encodeURIComponent(p2pState.room)}&peer=${encodeURIComponent(p2pState.peer)}`)).json();
      for (const signal of data.signals || []) await handleP2PSignal(signal);
    } catch (e) {}
  }
  window.p2pListen = async function () {
    p2pState.room = qs("p2p-room").value.trim() || "nexus";
    p2pState.peer = qs("p2p-peer").value.trim() || deviceId.slice(-10);
    qs("p2p-peer").value = p2pState.peer;
    if (p2pState.poll) clearInterval(p2pState.poll);
    p2pState.poll = setInterval(p2pPoll, 1500);
    p2pLog(`nasluch w pokoju ${p2pState.room} jako ${p2pState.peer}`);
    await p2pPoll();
  };
  window.p2pOffer = async function () {
    await window.p2pListen();
    createPeerConnection(true);
    const offer = await p2pState.pc.createOffer();
    await p2pState.pc.setLocalDescription(offer);
    await sendP2PSignal({ type: "offer", offer: offer.toJSON ? offer.toJSON() : offer });
    p2pLog("wyslano oferte WebRTC");
  };
  window.p2pSendFile = async function () {
    const file = qs("p2p-file").files[0];
    if (!file || !p2pState.channel || p2pState.channel.readyState !== "open") { p2pLog("brak pliku albo kanal nie jest online"); return; }
    p2pState.channel.send(JSON.stringify({ type: "file-meta", name: file.name, size: file.size, mime: file.type }));
    const buffer = await file.arrayBuffer();
    const size = 16 * 1024;
    const transferId = "p2p-out-" + Date.now();
    if (window.NexusTransfers) window.NexusTransfers.start({ id: transferId, label: `P2P OUT: ${file.name}`, type: "p2p", loaded: 0, total: file.size, status: "running", detail: "WebRTC" });
    for (let offset = 0; offset < buffer.byteLength; offset += size) {
      while (p2pState.channel.bufferedAmount > 4 * 1024 * 1024) await sleep(80);
      const chunk = buffer.slice(offset, offset + size);
      p2pState.channel.send(chunk);
      if (window.NexusTransfers) window.NexusTransfers.update(transferId, { loaded: Math.min(offset + chunk.byteLength, buffer.byteLength), total: buffer.byteLength, status: "running", detail: "WebRTC" });
    }
    p2pState.channel.send(JSON.stringify({ type: "file-done" }));
    if (window.NexusTransfers) window.NexusTransfers.finish(transferId, "wyslano P2P");
    p2pLog(`wyslano ${file.name}`);
  };

  async function loadBriefing() {
    const box = qs("briefing-box");
    box.innerHTML = '<div class="nx-mod-card"><strong>GENEROWANIE...</strong></div>';
    const data = await (await apiFetch("/api/briefing")).json();
    box.innerHTML = `<div class="nx-mod-card"><strong>${esc(data.title || "MORNING BRIEFING")}</strong><small>${esc(data.generated_at || "")}</small>${(data.summary || []).map(x => `<p style="color:#ddd;">${esc(x)}</p>`).join("")}</div><h3 style="color:var(--acc-cyan);">SYGNALY</h3><div class="p2p-log">${esc((data.signals || []).join("\n") || "Brak krytycznych wpisow.")}</div>`;
  }
  window.generateBriefing = async function () {
    await apiFetch("/api/briefing/generate", { method: "POST" });
    loadBriefing();
  };

  async function loadKarma() {
    const k = await (await apiFetch("/api/karma")).json();
    const progress = Math.min(100, Math.round((k.exp / k.next_level_exp) * 100));
    qs("karma-box").innerHTML = `
      <div class="nx-mod-card"><strong>LEVEL ${k.level}</strong><div class="karma-bar"><span style="width:${progress}%"></span></div><small>${k.exp} / ${k.next_level_exp} EXP</small></div>
      <div class="nx-mod-card"><strong>LOGIN STREAK</strong><div class="drop-count">${k.login_streak}</div><small>dni z rzedu</small></div>
      <div class="nx-mod-card"><strong>UPTIME STREAK</strong><div class="drop-count">${k.uptime_days}</div><small>dni bez restartu systemu</small></div>
    `;
  }

  async function loadWeb3() {
    const box = qs("web3-box");
    try {
      const data = await (await apiFetch("/api/web3/status")).json();
      box.innerHTML = `<strong>${data.linked ? "WEB3 ZWERYFIKOWANE" : "WEB3 NIEPOLACZONE"}</strong><small>${esc(data.address || "Brak adresu portfela.")}</small>`;
      qs("web3-status").textContent = data.linked ? "Polaczone" : "Niepolaczone";
    } catch (e) {}
  }
  window.connectWeb3 = async function () {
    const status = qs("web3-status");
    if (!window.ethereum) { status.textContent = "Brak MetaMask / portfela"; return; }
    try {
      const accounts = await window.ethereum.request({ method: "eth_requestAccounts" });
      const address = accounts[0];
      const nonce = await (await apiFetch("/api/web3/nonce", { method: "POST", body: JSON.stringify({ address }) })).json();
      const signature = await window.ethereum.request({ method: "personal_sign", params: [nonce.challenge, address] });
      const response = await apiFetch("/api/web3/verify", { method: "POST", body: JSON.stringify({ address, signature }) });
      if (!response.ok) throw new Error(await response.text());
      status.textContent = "Podpis zweryfikowany";
      loadWeb3();
    } catch (e) {
      status.textContent = "Web3 wymaga eth_account na serwerze albo poprawnego podpisu";
    }
  };

  let floatingChatTimer = null;
  function installFloatingChat() {
    if (qs("nexus-floating-chat")) return;
    const box = document.createElement("div");
    box.id = "nexus-floating-chat";
    box.className = "collapsed";
    box.innerHTML = `
      <button class="floating-chat-handle" onclick="toggleFloatingChat()">CHAT / COMMS</button>
      <div class="floating-chat-panel">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
          <b style="color:var(--acc-cyan);font-size:12px;">SZYBKI CZAT</b>
          <button class="nav-btn" style="margin:0;padding:4px 8px;font-size:10px;" onclick="loadFloatingChat()">SYNC</button>
        </div>
        <div id="floating-chat-log" class="floating-chat-log"></div>
        <div class="floating-chat-row">
          <input id="floating-chat-nick" class="cyber-input" placeholder="nick">
          <input id="floating-chat-text" class="cyber-input" placeholder="wiadomosc..." onkeydown="if(event.key==='Enter') sendFloatingChat()">
          <button class="nav-btn" style="margin:0;padding:6px;font-size:10px;" onclick="sendFloatingChat()">WYSLIJ</button>
        </div>
      </div>
    `;
    document.body.appendChild(box);
    const nick = qs("floating-chat-nick");
    if (nick) nick.value = localStorage.getItem("nexus_user") || "GHOST";
  }
  async function loadFloatingChat() {
    const log = qs("floating-chat-log");
    if (!log) return;
    try {
      const msgs = await (await apiFetch("/api/community/messages")).json();
      log.innerHTML = (msgs || []).slice(-20).map(m => `<div class="floating-chat-msg"><small>[${esc(m.time || "")}] ${esc(m.author || "?")}</small>${esc(m.text || "")}</div>`).join("") || '<div style="color:#777;font-size:11px;">Brak wiadomosci.</div>';
      log.scrollTop = log.scrollHeight;
    } catch (e) {
      log.innerHTML = '<div style="color:var(--acc-crit);font-size:11px;">Zaloguj sie, zeby odczytac czat.</div>';
    }
  }
  window.toggleFloatingChat = function () {
    const box = qs("nexus-floating-chat");
    if (!box) return;
    box.classList.toggle("collapsed");
    if (!box.classList.contains("collapsed")) {
      loadFloatingChat();
      if (!floatingChatTimer) floatingChatTimer = setInterval(() => {
        if (!box.classList.contains("collapsed")) loadFloatingChat();
      }, 5000);
      setTimeout(() => qs("floating-chat-text")?.focus(), 80);
    }
  };
  window.loadFloatingChat = loadFloatingChat;
  window.sendFloatingChat = async function () {
    const nick = (qs("floating-chat-nick")?.value || localStorage.getItem("nexus_user") || "GHOST").trim().slice(0, 20);
    const input = qs("floating-chat-text");
    const text = (input?.value || "").trim();
    if (!text) return;
    await apiFetch("/api/community/message", { method: "POST", body: JSON.stringify({ author: nick, text }) });
    input.value = "";
    loadFloatingChat();
    if (window.loadMsgs && qs("community")?.classList.contains("active")) window.loadMsgs();
  };

  function flatHyperspaceIdeas() {
    return HYPERSPACE_IDEAS.flatMap(group => group.items.map((name, index) => ({ cat: group.cat, name, index: index + 1 })));
  }
  window.renderHyperspaceIdeas = function () {
    const filter = qs("hyper-filter")?.value || "ALL";
    const select = qs("hyper-filter");
    if (select && select.options.length <= 1) {
      HYPERSPACE_IDEAS.forEach(group => select.insertAdjacentHTML("beforeend", `<option value="${esc(group.cat)}">${esc(group.cat)}</option>`));
    }
    const ideas = flatHyperspaceIdeas().filter(idea => filter === "ALL" || idea.cat === filter);
    const summary = qs("hyper-summary");
    if (summary) {
      summary.innerHTML = HYPERSPACE_IDEAS.map(group => `<div class="nx-mod-card" style="min-height:0;"><strong>${esc(group.cat)}</strong><div class="drop-count">${group.items.length}</div><small>pomyslow</small></div>`).join("");
    }
    const grid = qs("hyper-grid");
    if (!grid) return;
    grid.innerHTML = ideas.map(idea => `<div class="nx-mod-card hyper-idea"><span class="hyper-badge">${esc(idea.cat)} #${idea.index}</span><strong>${esc(idea.name)}</strong><small>Status: backlog / gotowe do przerzucenia na tablice operacyjna</small><div class="nx-mod-actions"><button class="nav-btn" onclick="sendIdeaToKanban('${esc(idea.name)}','${esc(idea.cat)}')">DO KANBANA</button></div></div>`).join("");
  };
  window.sendIdeaToKanban = async function (name, cat) {
    try {
      await apiFetch("/api/kanban/card", { method: "POST", body: JSON.stringify({ column_id: "ideas", title: name, body: `HYPERSPACE / ${cat}` }) });
      alert("Dodane do Kanbana: " + name);
    } catch (e) {
      alert("Kanban moze edytowac tylko admin.");
    }
  };

  let matrixCanvas = null, matrixCtx = null, matrixTimer = null, matrixTuneTimer = null, matrixCols = [], matrixIntensity = 0.18;
  function drawMatrixRain() {
    if (!matrixCanvas || !matrixCtx) return;
    matrixCtx.fillStyle = `rgba(0,0,0,${matrixIntensity})`;
    matrixCtx.fillRect(0, 0, matrixCanvas.width, matrixCanvas.height);
    matrixCtx.fillStyle = "#00ffff";
    matrixCtx.font = "13px monospace";
    matrixCols.forEach((y, i) => {
      const text = Math.random() > 0.5 ? "1" : "0";
      matrixCtx.fillText(text, i * 14, y);
      matrixCols[i] = y > matrixCanvas.height + Math.random() * 900 ? 0 : y + 14;
    });
  }
  async function tuneMatrixIntensity() {
    try {
      const stats = await (await apiFetch("/api/system/stats")).json();
      matrixIntensity = Math.max(0.08, Math.min(0.28, 0.22 - Number(stats.cpu || 0) / 700));
    } catch (e) {}
  }
  window.toggleMatrixRain = function () {
    if (matrixTimer) {
      clearInterval(matrixTimer);
      if (matrixTuneTimer) clearInterval(matrixTuneTimer);
      matrixTimer = null;
      matrixTuneTimer = null;
      matrixCanvas?.remove();
      matrixCanvas = null;
      document.body.classList.remove("nx-hyper-bg");
      return;
    }
    matrixCanvas = document.createElement("canvas");
    matrixCanvas.id = "nx-hyper-bg";
    document.body.prepend(matrixCanvas);
    matrixCtx = matrixCanvas.getContext("2d");
    const resize = () => {
      matrixCanvas.width = window.innerWidth;
      matrixCanvas.height = window.innerHeight;
      matrixCols = Array(Math.ceil(matrixCanvas.width / 14)).fill(0).map(() => Math.random() * matrixCanvas.height);
    };
    resize();
    window.addEventListener("resize", resize);
    document.body.classList.add("nx-hyper-bg");
    tuneMatrixIntensity();
    matrixTimer = setInterval(drawMatrixRain, 50);
    matrixTuneTimer = setInterval(tuneMatrixIntensity, 6000);
  };

  let cryptoTickerTimer = null;
  window.toggleCryptoTicker = async function () {
    let ticker = qs("nx-crypto-ticker");
    if (ticker) {
      ticker.remove();
      if (cryptoTickerTimer) clearInterval(cryptoTickerTimer);
      cryptoTickerTimer = null;
      return;
    }
    ticker = document.createElement("div");
    ticker.id = "nx-crypto-ticker";
    ticker.className = "hyper-ticker";
    ticker.innerHTML = "<span>LADOWANIE RYNKU...</span>";
    document.body.appendChild(ticker);
    async function loadPrices() {
      try {
        const r = await fetch("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana,polygon-ecosystem-token&vs_currencies=usd,pln&include_24hr_change=true");
        const data = await r.json();
        const line = Object.entries(data).map(([key, val]) => `${key.toUpperCase()} $${Number(val.usd || 0).toLocaleString()} / ${Number(val.pln || 0).toLocaleString()} PLN / 24h ${Number(val.usd_24h_change || 0).toFixed(2)}%`).join("     ");
        ticker.innerHTML = `<span>${esc(line || "BRAK DANYCH RYNKU")}</span>`;
      } catch (e) {
        ticker.innerHTML = "<span>BRAK DANYCH RYNKU / RETRY ZA 30S</span>";
      }
    }
    loadPrices();
    cryptoTickerTimer = setInterval(loadPrices, 30000);
  };

  let soundscapeOn = false, audioCtx = null;
  function playNexusClick() {
    if (!soundscapeOn) return;
    audioCtx = audioCtx || new (window.AudioContext || window.webkitAudioContext)();
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.frequency.value = 120 + Math.random() * 180;
    gain.gain.value = 0.025;
    osc.connect(gain).connect(audioCtx.destination);
    osc.start();
    gain.gain.exponentialRampToValueAtTime(0.0001, audioCtx.currentTime + 0.12);
    osc.stop(audioCtx.currentTime + 0.13);
  }
  window.toggleSoundscape = function () {
    soundscapeOn = !soundscapeOn;
    playNexusClick();
    alert("System-Soundscape: " + (soundscapeOn ? "ON" : "OFF"));
  };
  window.toggleCrtMode = function () {
    document.body.classList.toggle("nx-crt");
  };
  window.triggerDataShred = function () {
    for (let i = 0; i < 38; i++) {
      const shard = document.createElement("div");
      shard.textContent = Math.random() > 0.5 ? "PURGE" : "0x" + Math.random().toString(16).slice(2, 6);
      shard.style.cssText = `position:fixed;z-index:28000;left:${Math.random() * 100}vw;top:-30px;color:${i % 3 ? "#0ff" : "#f33"};font:11px monospace;pointer-events:none;transform:rotate(${Math.random() * 70 - 35}deg);transition:transform 1.4s linear,opacity 1.4s`;
      document.body.appendChild(shard);
      requestAnimationFrame(() => {
        shard.style.transform += ` translateY(${110 + Math.random() * 40}vh)`;
        shard.style.opacity = "0";
      });
      setTimeout(() => shard.remove(), 1500);
    }
  };

  const konami = ["ArrowUp","ArrowUp","ArrowDown","ArrowDown","ArrowLeft","ArrowRight","ArrowLeft","ArrowRight","b","a"];
  let konamiBuffer = [];
  document.addEventListener("keydown", event => {
    konamiBuffer.push(event.key);
    konamiBuffer = konamiBuffer.slice(-konami.length);
    if (konamiBuffer.join("|").toLowerCase() === konami.join("|").toLowerCase()) {
      document.body.classList.add("nx-crt");
      alert("HYPERSPACE DEV UNLOCKED");
      triggerDataShred();
    }
  });

  function loadModule(id) {
    if (id === "media_deck") loadMediaDeck();
    if (id === "cyber_bbs") loadBBS();
    if (id === "visual_archive") loadGallery();
    if (id === "kanban") loadKanban();
    if (id === "secure_drop") loadDrop();
    if (id === "object_storage") loadObjectStorage();
    if (id === "cloud_drive") loadCloudDrive();
    if (id === "usb_devices") loadUsbDevices();
    if (id === "nexus_shield") loadNexusShield();
    if (id === "time_machine") loadTimeMachine();
    if (id === "cloud_init") loadCloudInit();
    if (id === "api_webhooks") loadApiWebhooks();
    if (id === "hardware_telemetry") loadHardwareTelemetry();
    if (id === "nexus_coop") loadCoopSessions();
    if (id === "hyper_sleep") loadHyperSleep();
    if (id === "nexus_canvas") loadCanvas();
    if (id === "nexus_forge") loadForge();
    if (id === "ai_commander") loadAiCommanderLog();
    if (id === "nexus_archiver") loadArchiver();
    if (id === "nexus_bastion") loadBastion();
    if (id === "nexus_workers") loadWorkers();
    if (id === "secure_vault") loadVault();
    if (id === "global_terminal_page") loadGlobalTerminalLog();
    if (id === "presence_radar") loadPresence();
    if (id === "neural_alerts") loadAlerts();
    if (id === "p2p_drop") { qs("p2p-peer").value = qs("p2p-peer").value || deviceId.slice(-10); }
    if (id === "morning_briefing") loadBriefing();
    if (id === "sys_karma") loadKarma();
    if (id === "web3_gate") loadWeb3();
    if (id === "hyperspace_lab") renderHyperspaceIdeas();
  }

  document.addEventListener("DOMContentLoaded", () => {
    addModuleStyles();
    installPages();
    installFloatingChat();
    installGlobalTerminal();
    addButton("media_deck", "MEDIA");
    addButton("cyber_bbs", "BBS", "nx-btn-purp");
    addButton("visual_archive", "GALERIA", "nx-btn-warn");
    addButton("kanban", "KANBAN");
    addButton("secure_drop", "DROP", "nx-btn-crit");
    addButton("object_storage", "OBJECTS", "nx-btn-cyan");
    addButton("cloud_drive", "GDRIVE", "nx-btn-cyan", "data");
    addButton("usb_devices", "USB", "nx-btn-purp", "ops");
    addButton("nexus_shield", "SHIELD", "nx-btn-warn", "ops");
    addButton("time_machine", "TIME", "nx-btn-purp", "ops");
    addButton("cloud_init", "INIT", "nx-btn-cyan", "ops");
    addButton("api_webhooks", "API/HOOK", "nx-btn-warn", "ops");
    addButton("hardware_telemetry", "HW", "nx-btn-cyan", "core");
    addButton("nexus_coop", "CO-OP", "nx-btn-cyan", "ops");
    addButton("hyper_sleep", "SLEEP", "nx-btn-purp", "ops");
    addButton("nexus_canvas", "CANVAS", "nx-btn-warn", "ops");
    addButton("nexus_forge", "FORGE", "nx-btn-warn", "ops");
    addButton("ai_commander", "AICMD", "nx-btn-purp", "intel");
    addButton("nexus_archiver", "ARCHIVER", "nx-btn-cyan", "data");
    addButton("nexus_bastion", "BASTION", "nx-btn-warn", "ops");
    addButton("nexus_workers", "WORKERS", "nx-btn-purp", "ops");
    addButton("secure_vault", "VAULT", "nx-btn-crit", "data");
    addButton("global_terminal_page", "GTERM", "nx-btn-cyan", "social");
    addButton("presence_radar", "PRESENCE");
    addButton("neural_alerts", "ALERTS", "nx-btn-warn");
    addButton("p2p_drop", "P2P", "nx-btn-purp");
    addButton("morning_briefing", "BRIEF");
    addButton("sys_karma", "KARMA", "nx-btn-warn");
    addButton("web3_gate", "WEB3", "nx-btn-purp");
    addButton("hyperspace_lab", "HYPER", "nx-btn-cyan");
    const originalShow = window.show;
    window.show = function (id, btn) {
      originalShow(id, btn);
      playNexusClick();
      loadModule(id);
    };
    document.addEventListener("nexus:authenticated", startPresenceHeartbeat);
    if (localStorage.getItem("nexus_token")) startPresenceHeartbeat();
  });

  window.loadMediaDeck = loadMediaDeck;
  window.loadGallery = loadGallery;
  window.loadDrop = loadDrop;
  window.loadObjectStorage = loadObjectStorage;
  window.loadCloudDrive = loadCloudDrive;
  window.loadUsbDevices = loadUsbDevices;
  window.loadPresence = loadPresence;
  window.loadAlerts = loadAlerts;
})();
