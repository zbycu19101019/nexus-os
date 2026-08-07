document.addEventListener("DOMContentLoaded", () => {
    const style = document.createElement('style');
    style.innerHTML = `
        .cy-panel { background: rgba(5,10,15,0.9); border: 1px solid #00f3ff; border-radius: 4px; padding: 20px; font-family: monospace; color: #00f3ff; box-shadow: inset 0 0 15px rgba(0,243,255,0.1); margin-top: 15px; }
        .cy-header { color: #fcee0a; font-weight: bold; border-bottom: 1px dashed #fcee0a; padding-bottom: 10px; margin-bottom: 15px; letter-spacing: 2px; display:flex; justify-content:space-between; }
        .cy-list { list-style: none; padding: 0; margin: 0; }
        .cy-list li { padding: 8px; border-bottom: 1px solid rgba(0,243,255,0.2); display: flex; justify-content: space-between; }
        .cy-list li:hover { background: rgba(0,243,255,0.1); }
        .cy-btn { background: #00f3ff; color: #000; border: none; padding: 5px 10px; cursor: pointer; font-weight: bold; transition: 0.2s; }
        .cy-btn:hover { filter: brightness(1.3); box-shadow: 0 0 10px currentColor; }
        .blink { animation: blinker 1s linear infinite; }
        .cy-input { background: rgba(0,0,0,0.8); border: 1px solid #ff003c; color: #fff; padding: 8px; font-family: monospace; width: 100%; box-sizing: border-box; outline: none; margin-top:5px; }
        @keyframes blinker { 50% { opacity: 0; } }
    `;
    document.head.appendChild(style);

    const layouts = {
        'dashboard': `<div class="cy-panel"><div class="cy-header"><span>📊 SYSTEM DASHBOARD</span> <span class="blink">● ONLINE</span></div><div style="text-align:center; padding:20px; font-size:16px;">[ CPU: <span style="color:#0f0;">34%</span> ] | [ RAM: <span style="color:#fcee0a;">2.4 GB</span> ]<br><br><span style="color:#ff003c; font-weight:bold; letter-spacing:2px;">FIREWALL: DEFLECTING</span></div></div>`,
        'ai': `<div class="cy-panel" style="border-color:#b026ff; box-shadow: inset 0 0 15px rgba(176,38,255,0.2);"><div class="cy-header" style="color:#b026ff; border-color:#b026ff;"><span>🧠 NEURAL NETWORK CORE</span> <span>SYNCED</span></div><div style="text-align:center; padding:20px; font-size:50px; color:#b026ff; animation: eqAnim 2s infinite alternate;">🜚</div></div>`,
        'files': `<div class="cy-panel"><div class="cy-header"><span>📁 ENCRYPTED FILE SYSTEM</span> <span>[ROOT]</span></div><ul class="cy-list"><li><span>🗀 /bin/sys_override</span> <span>24 MB</span></li><li><span style="color:#ff003c;">🗀 /root/black_ice (LOCKED)</span> <span style="color:#ff003c;">???</span></li></ul></div>`,
        'terminal': `<div class="cy-panel" style="background:#000; border-color:#0f0;"><div class="cy-header" style="color:#0f0; border-color:#0f0;"><span>>_ ROOT TERMINAL</span></div><div style="color:#0f0; font-family:'Courier New', monospace; font-size:14px;">root@nexus:~# <span class="blink">_</span></div></div>`,
        'processes': `<div class="cy-panel"><div class="cy-header"><span>🎰 ACTIVE PROCESSES</span></div><ul class="cy-list"><li style="color:#0f0;">[1024] nx_daemon.exe</li><li style="color:#ff003c;">[6660] UNKNOWN_PAYLOAD</li></ul></div>`,
        'games': `<div class="cy-panel" style="text-align:center;"><div class="cy-header"><span>🎮 NEURAL CALIBRATION</span></div><button class="cy-btn" style="background:#0f0; padding:15px; margin-top:20px; font-size:16px;">START TEST (100ms)</button></div>`,
        'community': `<div class="cy-panel"><div class="cy-header"><span>💬 SECURE COMMS</span></div><div style="height:100px; border:1px solid #333; padding:10px; background:#000; color:#00f3ff;">Kanał nasłuchowy otwarty...</div></div>`,
        'marketplace': `<div class="cy-panel" style="border-color:#fcee0a;"><div class="cy-header" style="color:#fcee0a; border-color:#fcee0a;"><span>🧩 DARKNET MARKET</span></div><div style="text-align:center; padding:15px; border:1px dashed #fcee0a;">ICEBREAKER v2 <br> <button class="cy-btn" style="background:#fcee0a; margin-top:10px;">0.5 BTC</button></div></div>`,
        'logs': `<div class="cy-panel"><div class="cy-header"><span>📜 SYSTEM EVENT LOGS</span></div><div style="font-size:12px; color:#888; background:#000; padding:10px; border:1px solid #333;">[SYS] Boot sequence initiated...<br>[NET] IP Spoofing active.</div></div>`,
        'admin': `
            <div class="cy-panel" style="border-color:#ff003c; background: rgba(15,0,0,0.9);">
                <div class="cy-header" style="color:#ff003c; border-color:#ff003c;"><span>⚙️ ROOT OVERRIDE // ADMIN</span> <span class="blink">RESTRICTED</span></div>
                <div style="margin-bottom: 20px;">
                    <div style="color:#ff003c; font-size:12px; margin-bottom:10px;">[ SERVER CORE CONTROLS ]</div>
                    <div style="display:flex; gap:10px;">
                        <button class="cy-btn" style="background:#ff003c; color:#fff; flex:1;" onclick="console.log('Action triggered')">RESTART</button>
                        <button class="cy-btn" style="background:transparent; border:1px solid #fcee0a; color:#fcee0a; flex:1;" onclick="console.log('Action triggered')">FLUSH CACHE</button>
                    </div>
                </div>
                <div style="margin-bottom: 20px;">
                    <div style="color:#ff003c; font-size:12px; margin-bottom:10px;">[ SYSTEM PARAMETERS ]</div>
                    <input type="text" placeholder="Wprowadź: np. --force-ssl" class="cy-input" style="color:#00f3ff;">
                    <button class="cy-btn" style="background:transparent; border:1px solid #0f0; color:#0f0; width:100%; margin-top:10px;">APPLY PARAMETERS</button>
                </div>
                <div>
                    <div style="color:#ff003c; font-size:12px; margin-bottom:10px;">[ SNAPSHOT & BACKUP MANAGER ]</div>
                    <button class="cy-btn" style="background:#b026ff; color:#fff; width:100%; padding:12px; letter-spacing:1px;" onclick="console.log('Action triggered')">CREATE NEW SYSTEM BACKUP</button>
                </div>
            </div>`
    };

    // Wstrzykujemy lub tworzymy zawartość dla każdej z zakładek
    for (const [id, html] of Object.entries(layouts)) {
        if(id === 'news' || id === 'weather' || id === 'pogoda') continue; // Tych nie ruszamy
        
        let tab = document.getElementById(id);
        if (tab) {
            tab.innerHTML = html; // Nadpisz jeśli istnieje i jest pusta
        } else {
            // Skrypt sam utworzy zakładkę, jeśli brakuje jej w pliku HTML!
            let newTab = document.createElement('div');
            newTab.id = id;
            newTab.className = "page";
            newTab.style.display = "none";
            newTab.innerHTML = html;
            document.body.appendChild(newTab);
        }
    }
});
