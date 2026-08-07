(function nexusTransferPanelBoot() {
  "use strict";

  const qs = (id) => document.getElementById(id);
  const esc = (value) => String(value ?? "").replace(/[&<>"']/g, ch => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]));
  const token = () => localStorage.getItem("nexus_token") || "";
  const OBJECT_SMART_THRESHOLD = 16 * 1024 * 1024;

  const state = {
    items: new Map(),
    collapsed: localStorage.getItem("nexus_transfer_collapsed") === "1",
    dismissed: localStorage.getItem("nexus_transfer_dismissed") === "1",
    installed: false,
    dragDepth: 0,
  };

  function bytes(value) {
    let n = Number(value || 0);
    const units = ["B", "KB", "MB", "GB", "TB"];
    let idx = 0;
    while (n >= 1024 && idx < units.length - 1) {
      n /= 1024;
      idx++;
    }
    return idx === 0 ? `${Math.round(n)} ${units[idx]}` : `${n.toFixed(1)} ${units[idx]}`;
  }

  function addStyles() {
    if (qs("nexus-transfer-style")) return;
    const style = document.createElement("style");
    style.id = "nexus-transfer-style";
    style.textContent = `
      #nexus-transfer-panel{position:fixed;right:14px;bottom:14px;z-index:28500;width:min(390px,calc(100vw - 28px));font-family:monospace;background:rgba(5,8,10,.97);border:1px solid #244;border-left:3px solid var(--acc-cyan,#00ffff);border-radius:8px;box-shadow:0 0 26px rgba(0,255,255,.18),0 14px 34px rgba(0,0,0,.65);overflow:hidden;display:none}
      #nexus-transfer-panel.visible{display:block}
      body.auth-locked #nexus-transfer-panel{display:none!important}
      #nexus-transfer-panel.collapsed .nx-transfer-body{display:none}
      .nx-transfer-head{height:38px;display:flex;align-items:center;justify-content:space-between;gap:10px;padding:0 10px;background:#050505;border-bottom:1px solid #1d3438;color:var(--acc-cyan,#00ffff);cursor:pointer}
      .nx-transfer-head strong{font-size:12px;letter-spacing:0;text-transform:uppercase}
      .nx-transfer-head span{color:#888;font-size:10px}
      .nx-transfer-controls{display:flex;gap:6px;align-items:center}
      .nx-transfer-toggle,.nx-transfer-close{border:1px solid #244;background:#060606;color:var(--acc-cyan,#00ffff);width:26px;height:24px;border-radius:4px;cursor:pointer}
      .nx-transfer-close{color:var(--acc-crit,#ff3355);border-color:#522}
      .nx-transfer-body{max-height:310px;overflow:auto;padding:9px;display:grid;gap:8px}
      .nx-transfer-empty{color:#777;font-size:11px;padding:8px;background:#050505;border:1px solid #1c1c1c;border-radius:5px}
      .nx-transfer-row{background:#070707;border:1px solid #222;border-left:3px solid #555;border-radius:5px;padding:8px;display:grid;gap:6px}
      .nx-transfer-row.running,.nx-transfer-row.queued{border-left-color:var(--acc-cyan,#00ffff)}
      .nx-transfer-row.paused{border-left-color:var(--acc-warn,#ffaa00)}.nx-transfer-row.cancelled{border-left-color:#666}
      .nx-transfer-row.done{border-left-color:#00ff72}.nx-transfer-row.error{border-left-color:var(--acc-crit,#ff3355)}
      .nx-transfer-top{display:flex;justify-content:space-between;gap:8px;align-items:flex-start}
      .nx-transfer-label{color:#fff;font-size:12px;font-weight:bold;overflow-wrap:anywhere}
      .nx-transfer-status{color:#999;font-size:10px;text-transform:uppercase;white-space:nowrap}
      .nx-transfer-bar{height:7px;background:#111;border:1px solid #242424;border-radius:999px;overflow:hidden}
      .nx-transfer-fill{height:100%;width:0;background:linear-gradient(90deg,var(--acc-cyan,#00ffff),var(--acc-purple,#b000ff));box-shadow:0 0 10px rgba(0,255,255,.45);transition:width .18s ease}
      .nx-transfer-meta{display:flex;justify-content:space-between;gap:8px;color:#777;font-size:10px;overflow-wrap:anywhere}
      .nx-transfer-actions{display:flex;gap:5px;flex-wrap:wrap;justify-content:flex-end}
      .nx-transfer-action{border:1px solid #333;background:#050505;color:#aaa;border-radius:4px;padding:5px 7px;font-family:monospace;font-size:9px;cursor:pointer}
      .nx-transfer-action.pause{border-color:var(--acc-warn,#ffaa00);color:var(--acc-warn,#ffaa00)}
      .nx-transfer-action.resume{border-color:#00ff72;color:#00ff72}
      .nx-transfer-action.cancel{border-color:var(--acc-crit,#ff3355);color:var(--acc-crit,#ff3355)}
      #nexus-drop-shield{position:fixed;inset:0;z-index:28450;display:none;align-items:center;justify-content:center;background:rgba(0,0,0,.72);backdrop-filter:blur(3px);pointer-events:none}
      #nexus-drop-shield.active{display:flex;pointer-events:auto}
      .nx-drop-core{width:min(620px,calc(100vw - 36px));border:1px solid var(--acc-cyan,#00ffff);border-left:4px solid var(--acc-warn,#ffaa00);border-radius:8px;background:linear-gradient(180deg,rgba(5,12,14,.98),rgba(3,5,6,.98));box-shadow:0 0 34px rgba(0,255,255,.22);padding:24px;text-align:center}
      .nx-drop-core strong{display:block;color:#fff;font-size:20px;margin-bottom:8px}
      .nx-drop-core span{display:block;color:#9cc;font-size:12px;line-height:1.55}
      .nx-drop-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px;margin-top:16px}
      .nx-drop-grid b{display:block;border:1px solid #26343a;background:#060606;color:var(--acc-cyan,#00ffff);border-radius:5px;padding:8px;font-size:10px}
      @media(max-width:760px){#nexus-transfer-panel{right:8px;bottom:8px;width:calc(100vw - 16px)}}
      @media(max-width:760px){.nx-drop-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.nx-drop-core{padding:16px}}
    `;
    document.head.appendChild(style);
  }

  function installPanel() {
    if (state.installed && qs("nexus-transfer-panel")) return;
    addStyles();
    let panel = qs("nexus-transfer-panel");
    if (!panel) {
      panel = document.createElement("aside");
      panel.id = "nexus-transfer-panel";
      panel.innerHTML = `
        <div class="nx-transfer-head" id="nexus-transfer-head">
          <div><strong>TRANSFER CORE</strong> <span id="nx-transfer-count">0 aktywne</span></div>
          <div class="nx-transfer-controls">
            <button class="nx-transfer-toggle" id="nx-transfer-toggle" title="Zwin/rozwin">-</button>
            <button class="nx-transfer-close" id="nx-transfer-close" title="Zamknij okno">x</button>
          </div>
        </div>
        <div class="nx-transfer-body" id="nx-transfer-list"></div>
      `;
      document.body.appendChild(panel);
      qs("nexus-transfer-head").addEventListener("click", (event) => {
        event.preventDefault();
        setCollapsed(!state.collapsed);
      });
      qs("nx-transfer-close").addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        dismissPanel();
      });
    }
    if (!qs("nexus-drop-shield")) {
      const shield = document.createElement("div");
      shield.id = "nexus-drop-shield";
      shield.innerHTML = `
        <div class="nx-drop-core">
          <strong>PUŚĆ PLIKI DO NEXUS SMART VAULT</strong>
          <span>System sam rozpozna typ i zapisze pliki w odpowiednim module.</span>
          <div class="nx-drop-grid">
            <b>ISO / QCOW2 -> VM</b>
            <b>MP4 / MP3 -> MEDIA</b>
            <b>PNG / JPG -> GALERIA</b>
            <b>INNE -> DROP</b>
          </div>
        </div>
      `;
      document.body.appendChild(shield);
    }
    state.installed = true;
    setCollapsed(state.collapsed);
    render();
  }

  function setCollapsed(value) {
    state.collapsed = !!value;
    localStorage.setItem("nexus_transfer_collapsed", state.collapsed ? "1" : "0");
    const panel = qs("nexus-transfer-panel");
    const toggle = qs("nx-transfer-toggle");
    if (panel) panel.classList.toggle("collapsed", state.collapsed);
    if (toggle) toggle.textContent = state.collapsed ? "+" : "-";
  }

  function visible() {
    installPanel();
    state.dismissed = false;
    localStorage.setItem("nexus_transfer_dismissed", "0");
    const panel = qs("nexus-transfer-panel");
    if (panel) panel.classList.add("visible");
  }

  function dismissPanel() {
    state.dismissed = true;
    localStorage.setItem("nexus_transfer_dismissed", "1");
    const panel = qs("nexus-transfer-panel");
    if (panel) panel.classList.remove("visible");
  }

  function render() {
    installPanel();
    const list = qs("nx-transfer-list");
    const count = qs("nx-transfer-count");
    const panel = qs("nexus-transfer-panel");
    const rows = Array.from(state.items.values()).sort((a, b) => b.updated - a.updated).slice(0, 12);
    const active = rows.filter(item => ["queued", "running"].includes(item.status)).length;
    if (count) count.textContent = `${active} aktywne / ${rows.length} widoczne`;
    if (!rows.length) {
      if (list) list.innerHTML = `<div class="nx-transfer-empty">Brak aktywnych transferow.</div>`;
      if (panel) panel.classList.remove("visible");
      return;
    }
    if (panel && !state.dismissed) panel.classList.add("visible");
    if (!list) return;
    list.innerHTML = rows.map(item => {
      const total = Number(item.total || 0);
      const loaded = Number(item.loaded || 0);
      const pct = total ? Math.max(0, Math.min(100, Math.round((loaded / total) * 100))) : (item.status === "done" ? 100 : 8);
      const meta = total ? `${bytes(loaded)} / ${bytes(total)} (${pct}%)` : (loaded ? bytes(loaded) : "rozmiar nieznany");
      const actionHtml = renderTransferActions(item);
      return `
        <div class="nx-transfer-row ${esc(item.status)}">
          <div class="nx-transfer-top">
            <div class="nx-transfer-label">${esc(item.label)}</div>
            <div class="nx-transfer-status">${esc(item.status)}</div>
          </div>
          <div class="nx-transfer-bar"><div class="nx-transfer-fill" style="width:${pct}%"></div></div>
          <div class="nx-transfer-meta"><span>${esc(meta)}</span><span>${esc(item.detail || item.type || "")}</span></div>
          ${actionHtml}
        </div>
      `;
    }).join("");
  }

  function renderTransferActions(item) {
    const id = esc(item.id || "");
    const status = String(item.status || "");
    const actions = [];
    if (["queued", "running"].includes(status) && item.canPause !== false && item.type !== "remote") {
      actions.push(`<button class="nx-transfer-action pause" onclick="event.stopPropagation();NexusTransfers.pause('${id}')">PAUZA</button>`);
    }
    if (status === "paused") {
      actions.push(`<button class="nx-transfer-action resume" onclick="event.stopPropagation();NexusTransfers.resume('${id}')">WZNOW</button>`);
    }
    if (["queued", "running", "paused"].includes(status)) {
      actions.push(`<button class="nx-transfer-action cancel" onclick="event.stopPropagation();NexusTransfers.cancel('${id}')">ANULUJ</button>`);
    }
    return actions.length ? `<div class="nx-transfer-actions">${actions.join("")}</div>` : "";
  }

  function ensureItem(input) {
    const id = input.id || `tx-${Date.now()}-${Math.random().toString(16).slice(2)}`;
    const existing = state.items.get(id) || {};
    const item = {
      id,
      label: input.label || existing.label || "Transfer",
      type: input.type || existing.type || "transfer",
      loaded: Number(input.loaded ?? existing.loaded ?? 0),
      total: Number(input.total ?? existing.total ?? 0),
      status: input.status || existing.status || "running",
      detail: input.detail ?? existing.detail ?? "",
      xhr: input.xhr ?? existing.xhr ?? null,
      restart: input.restart ?? existing.restart ?? null,
      cancelRemote: input.cancelRemote ?? existing.cancelRemote ?? null,
      canPause: input.canPause ?? existing.canPause ?? true,
      pauseRequested: input.pauseRequested ?? existing.pauseRequested ?? false,
      cancelRequested: input.cancelRequested ?? existing.cancelRequested ?? false,
      updated: Date.now(),
    };
    state.items.set(id, item);
    visible();
    render();
    return item;
  }

  function update(id, patch) {
    const current = state.items.get(id);
    if (!current) return ensureItem({ id, ...patch });
    Object.assign(current, patch, { updated: Date.now() });
    state.items.set(id, current);
    visible();
    render();
    return current;
  }

  function finish(id, detail) {
    const item = update(id, { status: "done", detail: detail || "gotowe" });
    if (item && item.total && !item.loaded) item.loaded = item.total;
    render();
    setTimeout(() => {
      const current = state.items.get(id);
      if (current && current.status === "done") {
        state.items.delete(id);
        render();
      }
    }, 90000);
  }

  function fail(id, detail) {
    update(id, { status: "error", detail: detail || "blad" });
    setTimeout(() => {
      const current = state.items.get(id);
      if (current && current.status === "error") {
        state.items.delete(id);
        render();
      }
    }, 120000);
  }

  function controlledError(message) {
    const err = new Error(message || "Transfer zatrzymany");
    err.nxControlled = true;
    return err;
  }

  function pause(id) {
    const item = state.items.get(id);
    if (!item || !["queued", "running"].includes(item.status)) return;
    item.pauseRequested = true;
    item.cancelRequested = false;
    if (item.xhr && item.type !== "remote") {
      try { item.xhr.abort(); } catch (_) {}
    }
    update(id, { status: "paused", detail: "pauza - wznowienie wystartuje od poczatku", pauseRequested: true, xhr: null });
  }

  function resume(id) {
    const item = state.items.get(id);
    if (!item || item.status !== "paused") return;
    update(id, { status: "queued", loaded: 0, detail: "wznawianie od poczatku", pauseRequested: false, cancelRequested: false });
    if (typeof item.restart === "function") {
      setTimeout(() => item.restart().catch(err => { if (!err.nxControlled) fail(id, err.message); }), 80);
    }
  }

  async function cancel(id) {
    const item = state.items.get(id);
    if (!item || ["done", "error", "cancelled"].includes(item.status)) return;
    item.cancelRequested = true;
    item.pauseRequested = false;
    if (typeof item.cancelRemote === "function") {
      try { await item.cancelRemote(); } catch (_) {}
    }
    if (item.xhr) {
      try { item.xhr.abort(); } catch (_) {}
    }
    update(id, { status: "cancelled", detail: "anulowano", xhr: null, cancelRequested: true });
    setTimeout(() => {
      const current = state.items.get(id);
      if (current && current.status === "cancelled") {
        state.items.delete(id);
        render();
      }
    }, 45000);
  }

  function xhrErrorText(xhr, fallback) {
    try {
      const data = JSON.parse(xhr.responseText || "{}");
      if (typeof data.detail === "string") return data.detail;
      if (data.detail && typeof data.detail === "object") {
        const errors = Array.isArray(data.detail.errors) ? data.detail.errors.map(item => `${item.name || "plik"}: ${item.error || "blad"}`).join(" | ") : "";
        return [data.detail.message, errors].filter(Boolean).join(" | ") || fallback;
      }
      return data.error || fallback;
    } catch (_) {
      return xhr.responseText || fallback;
    }
  }

  function authHeaders(xhr) {
    const auth = token();
    if (auth) xhr.setRequestHeader("X-Auth-Token", auth);
  }

  async function apiRequest(url, options = {}) {
    const fetcher = typeof window.apiFetch === "function" ? window.apiFetch : (typeof apiFetch === "function" ? apiFetch : null);
    if (fetcher) return fetcher(url, options);
    const headers = { ...(options.headers || {}), "X-Auth-Token": token() };
    if (options.body && typeof options.body === "string" && !headers["Content-Type"]) headers["Content-Type"] = "application/json";
    return fetch(url, { ...options, headers });
  }

  async function responseMessage(res, fallback) {
    try {
      const clone = res.clone();
      const data = await clone.json();
      if (typeof data.detail === "string") return data.detail;
      if (data.detail && typeof data.detail === "object") return data.detail.message || JSON.stringify(data.detail);
      return data.error || fallback;
    } catch (_) {
      try {
        const text = await res.text();
        return text || fallback;
      } catch (__) {
        return fallback;
      }
    }
  }

  async function objectStorageReady() {
    try {
      const res = await apiRequest("/api/storage/status", { silent: true });
      if (!res.ok) return false;
      const data = await res.json();
      return !!data.enabled && data.service === "active";
    } catch (_) {
      return false;
    }
  }

  function uploadForm(url, form, options = {}) {
    const file = options.file || Array.from(form.values()).find(v => v instanceof File);
    const id = options.id || `upload-${Date.now()}-${Math.random().toString(16).slice(2)}`;
    const restart = () => uploadForm(url, form, { ...options, id });
    ensureItem({ id, label: options.label || `UPLOAD: ${file?.name || url}`, type: "upload", total: options.total || file?.size || 0, status: "queued", detail: options.detail || "", restart, canPause: true, pauseRequested: false, cancelRequested: false });
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      update(id, { xhr, restart, canPause: true, status: "queued", pauseRequested: false, cancelRequested: false });
      xhr.open(options.method || "POST", url, true);
      authHeaders(xhr);
      xhr.upload.onprogress = (event) => {
        update(id, { status: "running", loaded: event.loaded, total: event.lengthComputable ? event.total : (options.total || file?.size || 0), detail: options.detail || "wysylanie", xhr, restart });
      };
      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          update(id, { xhr: null, pauseRequested: false, cancelRequested: false });
          finish(id, "wyslano");
          let data = xhr.responseText;
          try { data = JSON.parse(xhr.responseText || "{}"); } catch (_) {}
          resolve({ data, xhr });
        } else {
          const message = xhrErrorText(xhr, "Upload nieudany");
          update(id, { xhr: null });
          if (!(state.items.get(id)?.cancelRequested || state.items.get(id)?.pauseRequested)) fail(id, message);
          if (xhr.status === 401 && typeof window.forceLoginGate === "function") window.forceLoginGate();
          reject(new Error(message));
        }
      };
      xhr.onerror = () => {
        const current = state.items.get(id);
        if (current?.pauseRequested || current?.cancelRequested || current?.status === "paused" || current?.status === "cancelled") {
          update(id, { xhr: null });
          reject(controlledError("Transfer zatrzymany"));
          return;
        }
        fail(id, "blad sieci");
        reject(new Error("Blad sieci podczas uploadu"));
      };
      xhr.onabort = () => {
        const current = state.items.get(id);
        if (current?.pauseRequested || current?.status === "paused") {
          update(id, { status: "paused", xhr: null, detail: "pauza - wznowienie wystartuje od poczatku" });
          reject(controlledError("Upload zatrzymany"));
          return;
        }
        if (current?.cancelRequested || current?.status === "cancelled") {
          update(id, { status: "cancelled", xhr: null, detail: "anulowano" });
          reject(controlledError("Upload anulowany"));
          return;
        }
        fail(id, "przerwano");
        reject(new Error("Upload przerwany"));
      };
      xhr.send(form);
    });
  }

  function uploadObjectStorage(file, options = {}) {
    const id = options.id || `object-${Date.now()}-${Math.random().toString(16).slice(2)}`;
    const restart = () => uploadObjectStorage(file, { ...options, id });
    const label = options.label || `S3 OBJECT: ${file?.name || "plik"}`;
    ensureItem({ id, label, type: "upload", total: file?.size || 0, status: "queued", detail: "presign S3", restart, canPause: true, pauseRequested: false, cancelRequested: false });
    return new Promise(async (resolve, reject) => {
      if (!file) {
        fail(id, "brak pliku");
        reject(new Error("Brak pliku"));
        return;
      }
      let presign;
      try {
        const res = await apiRequest("/api/storage/presign", {
          method: "POST",
          body: JSON.stringify({
            filename: file.name,
            size: file.size || 0,
            content_type: file.type || "application/octet-stream",
            purpose: options.purpose || "auto",
          }),
          silent: true,
        });
        if (!res.ok) throw new Error(await responseMessage(res, "Object Storage nie przygotowal linku"));
        presign = await res.json();
      } catch (err) {
        fail(id, err.message || "presign nieudany");
        reject(err);
        return;
      }

      const xhr = new XMLHttpRequest();
      update(id, { xhr, restart, canPause: true, status: "queued", detail: "PUT -> MinIO", pauseRequested: false, cancelRequested: false });
      xhr.open(presign.method || "PUT", presign.url, true);
      Object.entries(presign.headers || {}).forEach(([key, value]) => {
        if (value) xhr.setRequestHeader(key, value);
      });
      xhr.upload.onprogress = (event) => {
        update(id, { status: "running", loaded: event.loaded, total: event.lengthComputable ? event.total : (file.size || 0), detail: "bezposrednio do MinIO", xhr, restart });
      };
      xhr.onload = async () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            update(id, { xhr: null, loaded: file.size || 0, total: file.size || 0, status: "running", detail: "weryfikacja HEAD" });
            const completeRes = await apiRequest("/api/storage/complete", {
              method: "POST",
              body: JSON.stringify({
                bucket: presign.bucket,
                key: presign.key,
                filename: presign.filename || file.name,
                size: file.size || 0,
                content_type: file.type || "application/octet-stream",
                purpose: options.purpose || "auto",
                etag: (xhr.getResponseHeader("ETag") || "").replace(/"/g, ""),
              }),
              silent: !!options.silentComplete,
            });
            if (!completeRes.ok) throw new Error(await responseMessage(completeRes, "MinIO nie potwierdzil obiektu"));
            const completeData = await completeRes.json();
            let importData = null;
            if (options.autoImport && completeData.object?.id) {
              update(id, { status: "running", detail: "import do modulu" });
              const importRes = await apiRequest("/api/storage/import", {
                method: "POST",
                body: JSON.stringify({ object_id: completeData.object.id }),
                silent: !!options.silentComplete,
              });
              if (!importRes.ok) throw new Error(await responseMessage(importRes, "Import obiektu nieudany"));
              importData = await importRes.json();
            }
            update(id, { pauseRequested: false, cancelRequested: false });
            finish(id, importData ? "wyslano i zaimportowano" : "wyslano do S3");
            resolve({ data: { ...completeData, import: importData }, xhr });
          } catch (err) {
            fail(id, err.message || "kontrola S3 nieudana");
            reject(err);
          }
        } else {
          const message = xhr.responseText || `MinIO odrzucil upload (${xhr.status})`;
          update(id, { xhr: null });
          if (!(state.items.get(id)?.cancelRequested || state.items.get(id)?.pauseRequested)) fail(id, message);
          reject(new Error(message));
        }
      };
      xhr.onerror = () => {
        const current = state.items.get(id);
        if (current?.pauseRequested || current?.cancelRequested || current?.status === "paused" || current?.status === "cancelled") {
          update(id, { xhr: null });
          reject(controlledError("Transfer zatrzymany"));
          return;
        }
        fail(id, "blad sieci MinIO");
        reject(new Error("Blad sieci podczas uploadu do MinIO"));
      };
      xhr.onabort = () => {
        const current = state.items.get(id);
        if (current?.pauseRequested || current?.status === "paused") {
          update(id, { status: "paused", xhr: null, detail: "pauza - wznowienie wystartuje od poczatku" });
          reject(controlledError("Upload S3 zatrzymany"));
          return;
        }
        if (current?.cancelRequested || current?.status === "cancelled") {
          update(id, { status: "cancelled", xhr: null, detail: "anulowano" });
          reject(controlledError("Upload S3 anulowany"));
          return;
        }
        fail(id, "przerwano");
        reject(new Error("Upload S3 przerwany"));
      };
      xhr.send(file);
    });
  }

  function downloadBlob(url, options = {}) {
    const id = options.id || `download-${Date.now()}-${Math.random().toString(16).slice(2)}`;
    const restart = () => downloadBlob(url, { ...options, id });
    ensureItem({ id, label: options.label || `DOWNLOAD: ${url}`, type: "download", status: "queued", restart, canPause: true, pauseRequested: false, cancelRequested: false });
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      update(id, { xhr, restart, canPause: true, status: "queued", pauseRequested: false, cancelRequested: false });
      xhr.open(options.method || "GET", url, true);
      authHeaders(xhr);
      xhr.responseType = "blob";
      xhr.onprogress = (event) => {
        update(id, { status: "running", loaded: event.loaded, total: event.lengthComputable ? event.total : 0, detail: "pobieranie", xhr, restart });
      };
      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          const total = Number(xhr.getResponseHeader("Content-Length") || xhr.response?.size || 0);
          update(id, { loaded: total || xhr.response?.size || 0, total: total || xhr.response?.size || 0, xhr: null, pauseRequested: false, cancelRequested: false });
          finish(id, "pobrano");
          resolve({ blob: xhr.response, xhr, filename: filenameFromHeaders(xhr) });
        } else {
          const message = `Download nieudany (${xhr.status})`;
          update(id, { xhr: null });
          if (!(state.items.get(id)?.cancelRequested || state.items.get(id)?.pauseRequested)) fail(id, message);
          if (xhr.status === 401 && typeof window.forceLoginGate === "function") window.forceLoginGate();
          reject(new Error(message));
        }
      };
      xhr.onerror = () => {
        const current = state.items.get(id);
        if (current?.pauseRequested || current?.cancelRequested || current?.status === "paused" || current?.status === "cancelled") {
          update(id, { xhr: null });
          reject(controlledError("Transfer zatrzymany"));
          return;
        }
        fail(id, "blad sieci");
        reject(new Error("Blad sieci podczas pobierania"));
      };
      xhr.onabort = () => {
        const current = state.items.get(id);
        if (current?.pauseRequested || current?.status === "paused") {
          update(id, { status: "paused", xhr: null, detail: "pauza - wznowienie wystartuje od poczatku" });
          reject(controlledError("Download zatrzymany"));
          return;
        }
        if (current?.cancelRequested || current?.status === "cancelled") {
          update(id, { status: "cancelled", xhr: null, detail: "anulowano" });
          reject(controlledError("Download anulowany"));
          return;
        }
        fail(id, "przerwano");
        reject(new Error("Download przerwany"));
      };
      xhr.send();
    });
  }

  function filenameFromHeaders(xhr) {
    const header = xhr.getResponseHeader("Content-Disposition") || "";
    const utf = header.match(/filename\*=UTF-8''([^;]+)/i);
    if (utf) return decodeURIComponent(utf[1]);
    const plain = header.match(/filename="?([^";]+)"?/i);
    return plain ? plain[1] : "";
  }

  function saveBlob(blob, filename) {
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename || "nexus-download";
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 2500);
  }

  function isFileDrag(event) {
    const transfer = event.dataTransfer;
    if (!transfer) return false;
    if (transfer.files && transfer.files.length > 0) return true;
    const types = Array.from(transfer.types || []).map(type => String(type).toLowerCase());
    return types.includes("files") || types.includes("application/x-moz-file") || types.some(type => type.includes("file"));
  }

  function stopNativeFileDrop(event) {
    if (!isFileDrag(event)) return false;
    event.preventDefault();
    return true;
  }

  function setDropActive(active) {
    const shield = qs("nexus-drop-shield");
    if (shield) shield.classList.toggle("active", !!active);
    document.body.classList.toggle("nx-smart-drag", !!active);
  }

  function activePageId() {
    return document.querySelector(".page.active")?.id || "";
  }

  function refreshSmartDestinations(items) {
    const kinds = new Set((items || []).map(item => item.kind));
    if (kinds.has("iso")) {
      if (typeof window.loadIsoVault === "function") window.loadIsoVault();
      if (typeof window.loadOsForge === "function") window.loadOsForge();
    }
    if (kinds.has("driver") && typeof window.loadDriverVault === "function") {
      window.loadDriverVault();
    }
    if ((kinds.has("audio") || kinds.has("video")) && typeof window.loadMediaDeck === "function") {
      window.loadMediaDeck();
    }
    if (kinds.has("image") && typeof window.loadGallery === "function") {
      window.loadGallery();
    }
    if (kinds.has("drop") && typeof window.loadDrop === "function") {
      window.loadDrop();
    }
    if (activePageId() === "files" && typeof window.loadFiles === "function") {
      window.loadFiles(qs("current-path")?.value || "");
    }
  }

  async function smartUploadFiles(fileList) {
    const files = Array.from(fileList || []).filter(Boolean);
    if (!files.length) return;
    if (!token()) {
      alert("Najpierw zaloguj sie do panelu.");
      return;
    }
    const shouldUseObjects = files.some(file => Number(file.size || 0) >= OBJECT_SMART_THRESHOLD);
    if (shouldUseObjects && await objectStorageReady()) {
      try {
        const routed = [];
        for (const file of files) {
          const result = await uploadObjectStorage(file, {
            purpose: "auto",
            label: `SMART S3: ${file.name}`,
            autoImport: true,
            silentComplete: true,
          });
          const object = result.data?.import?.object || result.data?.object || {};
          routed.push({
            kind: object.kind || "data",
            name: object.filename || file.name,
            destination: result.data?.import?.path || object.imported_path || object.bucket || "Object Storage",
            verified: !!(result.data?.import?.path || object.imported_path),
          });
        }
        refreshSmartDestinations(routed);
        const summary = routed.map(item => `${item.name} -> ${item.destination} [S3 OK]`).join(" | ");
        ensureItem({ id: `smart-s3-summary-${Date.now()}`, label: "SMART VAULT S3 VERIFIED", status: "done", detail: summary || "sprawdzone" });
        return;
      } catch (err) {
        if (err.nxControlled) return;
        alert(err.message || "Smart upload S3 nieudany.");
        return;
      }
    }
    const form = new FormData();
    let total = 0;
    files.forEach(file => {
      form.append("files", file, file.name);
      total += Number(file.size || 0);
    });
    const label = files.length === 1 ? `SMART DROP: ${files[0].name}` : `SMART DROP: ${files.length} plikow`;
    try {
      const result = await uploadForm("/api/upload/smart", form, {
        id: `smart-${Date.now()}-${Math.random().toString(16).slice(2)}`,
        label,
        total,
        detail: "smart vault",
      });
      const data = result.data || {};
      const items = data.items || [];
      const failed = items.filter(item => item.verified !== true);
      if (failed.length) throw new Error("Kontrola miejsca docelowego nie przeszla: " + failed.map(item => item.name).join(", "));
      refreshSmartDestinations(items);
      const summary = items.map(item => `${item.name} -> ${item.destination} [OK]`).join(" | ");
      ensureItem({ id: `smart-summary-${Date.now()}`, label: "SMART VAULT VERIFIED", status: "done", detail: summary || "sprawdzone" });
    } catch (err) {
      if (err.nxControlled) return;
      alert(err.message || "Smart upload nieudany.");
    }
  }

  function installSmartDropZone() {
    if (document.documentElement.dataset.nexusSmartDrop === "1") return;
    document.documentElement.dataset.nexusSmartDrop = "1";
    const targets = [window, document, document.documentElement, document.body, qs("nexus-drop-shield")].filter(Boolean);
    targets.forEach(target => {
      ["dragenter", "dragover", "drop"].forEach(name => {
        target.addEventListener(name, stopNativeFileDrop, true);
        target.addEventListener(name, stopNativeFileDrop, false);
      });
      target.addEventListener("dragleave", event => {
        if (!isFileDrag(event)) return;
        event.preventDefault();
      }, true);
    });
    document.addEventListener("dragenter", event => {
      if (!stopNativeFileDrop(event)) return;
      state.dragDepth += 1;
      setDropActive(true);
    }, true);
    document.addEventListener("dragover", event => {
      if (!stopNativeFileDrop(event)) return;
      if (event.dataTransfer) event.dataTransfer.dropEffect = "copy";
      setDropActive(true);
    }, true);
    document.addEventListener("dragleave", event => {
      if (!isFileDrag(event)) return;
      event.preventDefault();
      state.dragDepth = Math.max(0, state.dragDepth - 1);
      if (state.dragDepth === 0) setDropActive(false);
    }, true);
    document.addEventListener("drop", event => {
      if (!stopNativeFileDrop(event)) return;
      state.dragDepth = 0;
      setDropActive(false);
      smartUploadFiles(event.dataTransfer.files);
    }, true);
  }

  function syncRemoteJobs(jobs) {
    (jobs || []).forEach(job => {
      const id = job.id || `remote-${job.label}`;
      const status = String(job.status || "running");
      const isIso = String(id).startsWith("iso:");
      const remoteId = isIso ? String(id).slice(4) : "";
      const normalizedStatus = status === "cancel_requested" ? "cancelled" : status;
      ensureItem({
        id,
        label: job.label || "REMOTE TRANSFER",
        type: "remote",
        loaded: job.loaded || 0,
        total: job.total || 0,
        status: ["done", "error", "queued", "running", "paused", "cancelled"].includes(normalizedStatus) ? normalizedStatus : "running",
        detail: job.detail || "",
        canPause: false,
        cancelRemote: isIso ? async () => {
          await apiFetch("/api/vms/iso/cancel", { method: "POST", body: JSON.stringify({ id: remoteId }) });
          if (typeof window.loadIsoVault === "function") window.loadIsoVault();
        } : null,
      });
      if (normalizedStatus === "done") finish(id, job.detail || "gotowe");
      if (normalizedStatus === "error") fail(id, job.detail || "blad");
    });
  }

  function trackRemoteJobs(jobs, onTick) {
    syncRemoteJobs(jobs);
    if (typeof onTick === "function") setTimeout(onTick, 1200);
  }

  function patchFileTransfers() {
    if (typeof window.downloadFile === "function" && !window.downloadFile.__nxTransfer) {
      const patchedDownload = async function (path) {
        try {
          const name = String(path || "").split(/[\\/]/).pop() || "nexus-download";
          const result = await downloadBlob("/api/files/download?path=" + encodeURIComponent(path), { label: `DOWNLOAD: ${name}` });
          saveBlob(result.blob, result.filename || name);
        } catch (err) {
          if (err.nxControlled) return;
          alert("Nie udalo sie pobrac pliku.");
        }
      };
      patchedDownload.__nxTransfer = true;
      window.downloadFile = patchedDownload;
    }

    if (typeof window.uploadSelectedFile === "function" && !window.uploadSelectedFile.__nxTransfer) {
      const patchedUpload = async function () {
        const input = qs("file-upload-input");
        const status = qs("upload-status");
        const file = input && input.files ? input.files[0] : null;
        const path = qs("current-path")?.value || "";
        if (!file) {
          if (status) status.textContent = "Wybierz plik do wyslania.";
          return;
        }
        const form = new FormData();
        form.append("path", path);
        form.append("file", file);
        if (status) {
          status.style.color = "var(--acc-cyan)";
          status.textContent = "Wysylanie: " + file.name;
        }
        try {
          const result = await uploadForm("/api/files/upload", form, { label: `UPLOAD: ${file.name}`, file, total: file.size });
          const data = result.data || {};
          if (status) {
            status.style.color = "#0f0";
            status.textContent = "Wyslano: " + (data.name || file.name);
          }
          input.value = "";
          if (typeof window.loadFiles === "function") window.loadFiles(path);
        } catch (err) {
          if (err.nxControlled) {
            if (status) {
              status.style.color = "var(--acc-warn)";
              status.textContent = "Transfer zatrzymany.";
            }
            return;
          }
          if (status) {
            status.style.color = "var(--acc-crit)";
            status.textContent = "Upload nieudany.";
          }
        }
      };
      patchedUpload.__nxTransfer = true;
      window.uploadSelectedFile = patchedUpload;
    }
  }

  function patchBbsUpload() {
    if (typeof window.createBBSPost === "function" && !window.createBBSPost.__nxTransfer) {
      const original = window.createBBSPost;
      const patched = async function () {
        const text = qs("bbs-text")?.value.trim();
        const file = qs("bbs-image")?.files?.[0];
        if (!file) return original.apply(this, arguments);
        if (!text) return;
        const form = new FormData();
        form.append("text", text);
        form.append("file", file);
        try {
          await uploadForm("/api/bbs/posts", form, { label: `BBS IMAGE: ${file.name}`, file, total: file.size });
          qs("bbs-text").value = "";
          qs("bbs-image").value = "";
          if (typeof window.show === "function") window.show("cyber_bbs");
        } catch (err) {
          if (err.nxControlled) return;
          alert("Nie udalo sie wyslac posta BBS.");
        }
      };
      patched.__nxTransfer = true;
      window.createBBSPost = patched;
    }
  }

  function boot() {
    installPanel();
    installSmartDropZone();
    patchFileTransfers();
    patchBbsUpload();
    let tries = 0;
    const timer = setInterval(() => {
      tries++;
      patchFileTransfers();
      patchBbsUpload();
      if (tries > 80) clearInterval(timer);
    }, 250);
  }

  window.NexusTransfers = {
    start: ensureItem,
    update,
    finish,
    fail,
    uploadForm,
    uploadObjectStorage,
    downloadBlob,
    saveBlob,
    pause,
    resume,
    cancel,
    syncRemoteJobs,
    trackRemoteJobs,
    smartUploadFiles,
    show: visible,
    close: dismissPanel,
    bytes,
  };

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
