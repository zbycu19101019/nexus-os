document.addEventListener("DOMContentLoaded", () => {
    if (document.getElementById("nx-bottom-drawer")) return;

    const oldBtns = document.querySelectorAll("#sidebar > .nav-btn");
    oldBtns.forEach(btn => {
        btn.dataset.nxLegacyNav = "1";
        btn.style.display = "none";
    });
    if (oldBtns.length && oldBtns[0].parentElement) {
        oldBtns[0].parentElement.style.display = "none";
    }

    const navGroups = [
        { id: "core", label: "CORE", sub: "status" },
        { id: "ops", label: "OPS", sub: "vps" },
        { id: "data", label: "DATA", sub: "files" },
        { id: "intel", label: "INTEL", sub: "osint" },
        { id: "social", label: "COMMS", sub: "work" },
        { id: "lab", label: "LAB", sub: "fun" },
    ];

    const baseTabs = [
        { id: "dashboard", label: "DASH", cls: "nx-btn-cyan", group: "core" },
        { id: "readme", label: "README", cls: "nx-btn-cyan", group: "core" },
        { id: "hardware_telemetry", label: "HW", cls: "nx-btn-cyan", group: "core" },
        { id: "presence_radar", label: "PRESENCE", cls: "nx-btn-cyan", group: "core" },
        { id: "neural_alerts", label: "ALERTS", cls: "nx-btn-warn", group: "core" },
        { id: "morning_briefing", label: "BRIEF", cls: "nx-btn-cyan", group: "core" },
        { id: "sys_karma", label: "KARMA", cls: "nx-btn-warn", group: "core" },

        { id: "terminal", label: ">_ TERM", cls: "nx-btn-cyan", group: "ops" },
        { id: "processes", label: "PROC", cls: "nx-btn-cyan", group: "ops" },
        { id: "vms", label: "VM", cls: "nx-btn-cyan", group: "ops" },
        { id: "logs", label: "LOGI", cls: "nx-btn-cyan", group: "ops" },
        { id: "marketplace", label: "MARKET", cls: "nx-btn-warn", group: "ops" },
        { id: "admin", label: "ADMIN/IAM", cls: "nx-btn-crit", group: "ops" },
        { id: "usb_devices", label: "USB", cls: "nx-btn-purp", group: "ops" },
        { id: "nexus_shield", label: "SHIELD", cls: "nx-btn-warn", group: "ops" },

        { id: "files", label: "PLIKI", cls: "nx-btn-cyan", group: "data" },
        { id: "media_deck", label: "MEDIA", cls: "nx-btn-cyan", group: "data" },
        { id: "visual_archive", label: "GALERIA", cls: "nx-btn-warn", group: "data" },
        { id: "secure_drop", label: "DROP", cls: "nx-btn-crit", group: "data" },
        { id: "object_storage", label: "OBJECTS", cls: "nx-btn-cyan", group: "data" },
        { id: "cloud_drive", label: "GDRIVE", cls: "nx-btn-cyan", group: "data" },
        { id: "nexus_archiver", label: "ARCHIVER", cls: "nx-btn-cyan", group: "data" },
        { id: "secure_vault", label: "VAULT", cls: "nx-btn-crit", group: "data" },

        { id: "ai", label: "AI", cls: "nx-btn-purp", group: "intel" },
        { id: "news", label: "NEWS", cls: "nx-btn-cyan", group: "intel" },
        { id: "weather", label: "POGODA", cls: "nx-btn-cyan", group: "intel" },
        { id: "ai_commander", label: "AICMD", cls: "nx-btn-purp", group: "intel" },
        { id: "web3_gate", label: "WEB3", cls: "nx-btn-purp", group: "intel" },

        { id: "community", label: "CZAT", cls: "nx-btn-cyan", group: "social" },
        { id: "cyber_bbs", label: "BBS", cls: "nx-btn-purp", group: "social" },
        { id: "kanban", label: "KANBAN", cls: "nx-btn-cyan", group: "social" },
        { id: "global_terminal_page", label: "GTERM", cls: "nx-btn-cyan", group: "social" },

        { id: "radio", label: "RADIO", cls: "nx-btn-cyan", group: "lab" },
        { id: "games", label: "GRY", cls: "nx-btn-cyan", group: "lab" },
        { id: "hyperspace_lab", label: "HYPER", cls: "nx-btn-cyan", group: "lab" },
    ];

    const style = document.createElement("style");
    style.id = "nx-modern-nav-style";
    style.textContent = `
        body.nx-modern-nav-ready{padding-bottom:92px}
        body.auth-locked #nx-bottom-drawer{display:none}
        #nx-bottom-drawer{position:fixed;left:50%;bottom:14px;z-index:19000;width:min(1040px,calc(100vw - 18px));transform:translateX(-50%);font-family:"Courier New",monospace;pointer-events:none}
        #nx-bottom-drawer *{box-sizing:border-box}
        .nx-goo-svg{position:absolute;width:0;height:0;overflow:hidden}
        .nx-modern-flyout{position:absolute;left:50%;bottom:82px;width:min(940px,100%);max-height:min(58vh,430px);overflow:auto;transform:translate(-50%,18px) scale(.985);opacity:0;visibility:hidden;pointer-events:auto;background:linear-gradient(180deg,rgba(13,18,24,.94),rgba(3,6,10,.97));border:1px solid rgba(0,243,255,.34);border-top:1px solid rgba(255,255,255,.18);border-radius:22px;padding:14px;box-shadow:0 22px 70px rgba(0,0,0,.62),0 0 42px rgba(0,243,255,.14);backdrop-filter:blur(20px);transition:opacity .22s ease,transform .22s cubic-bezier(.2,.9,.2,1),visibility .22s}
        #nx-bottom-drawer.open .nx-modern-flyout{opacity:1;visibility:visible;transform:translate(-50%,0) scale(1)}
        .nx-modern-flyout::-webkit-scrollbar{width:7px;height:7px}.nx-modern-flyout::-webkit-scrollbar-thumb{background:linear-gradient(#00f3ff,#b026ff);border-radius:999px}
        .nx-flyout-head{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:12px;color:#eaffff}
        .nx-flyout-title{display:grid;gap:2px}.nx-flyout-title b{font-size:13px;letter-spacing:2px}.nx-flyout-title span{font-size:10px;color:#7b8e96;letter-spacing:2px;text-transform:uppercase}
        .nx-flyout-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(118px,1fr));gap:8px}
        .nx-modern-dock{pointer-events:auto;position:relative;display:flex;align-items:center;gap:8px;min-height:66px;padding:10px;background:linear-gradient(180deg,rgba(18,23,28,.95),rgba(2,5,9,.98));border:1px solid rgba(0,243,255,.38);border-top:1px solid rgba(255,255,255,.2);border-radius:24px;box-shadow:0 14px 48px rgba(0,0,0,.58),0 0 34px rgba(0,243,255,.18);backdrop-filter:blur(22px)}
        .nx-dock-groups{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:8px;flex:1;filter:url(#nx-core-goo)}
        .nx-dock-group,.nx-nav-arrow,.nx-close-flyout,#nx-bottom-drawer .nx-btn{border:0;appearance:none;font-family:inherit;text-transform:uppercase;cursor:pointer;user-select:none}
        .nx-dock-group{position:relative;min-width:0;min-height:46px;border-radius:18px;padding:9px 10px;color:#bffcff;background:rgba(255,255,255,.055);outline:1px solid rgba(0,243,255,.14);box-shadow:inset 0 1px 0 rgba(255,255,255,.12);transition:transform .18s cubic-bezier(.2,.9,.2,1),background .18s,outline-color .18s,box-shadow .18s}
        .nx-dock-group:before{content:"";position:absolute;inset:8px;border-radius:999px;background:radial-gradient(circle at 50% 0,#8ffcff,rgba(0,243,255,.22) 45%,transparent 72%);opacity:0;transform:scale(.76);transition:opacity .2s,transform .2s;z-index:-1}
        .nx-dock-group:hover,.nx-dock-group.active{transform:translateY(-3px);background:rgba(0,243,255,.13);outline-color:rgba(0,243,255,.55);box-shadow:0 10px 30px rgba(0,243,255,.16),inset 0 1px 0 rgba(255,255,255,.2)}
        .nx-dock-group.active:before{opacity:1;transform:scale(1.15)}
        .nx-dock-group b{display:block;font-size:12px;letter-spacing:1px;color:#fff}.nx-dock-group small{display:block;margin-top:2px;font-size:9px;letter-spacing:2px;color:#7fefff}
        .nx-nav-arrow{width:44px;min-width:44px;height:44px;border-radius:16px;background:rgba(255,255,255,.07);color:#00f3ff;outline:1px solid rgba(0,243,255,.24);font-size:18px;font-weight:bold;transition:transform .18s,background .18s,color .18s,box-shadow .18s}
        .nx-nav-arrow:hover{transform:translateY(-2px);background:#00f3ff;color:#001014;box-shadow:0 0 24px rgba(0,243,255,.45)}
        #nx-bottom-drawer .nx-btn{display:flex;align-items:center;justify-content:center;min-height:42px;padding:10px 12px;border-radius:14px;background:rgba(255,255,255,.045);color:#eaffff;outline:1px solid rgba(255,255,255,.11);box-shadow:inset 0 1px 0 rgba(255,255,255,.1);font-size:11px;font-weight:bold;letter-spacing:.8px;transition:transform .16s cubic-bezier(.2,.9,.2,1),background .16s,box-shadow .16s,outline-color .16s,color .16s}
        #nx-bottom-drawer .nx-btn:hover,#nx-bottom-drawer .nx-btn.active-tab{transform:translateY(-2px);animation:btnTextPulse 1.2s ease-in-out infinite;background:rgba(0,243,255,.12);outline-color:#00f3ff;box-shadow:0 0 22px rgba(0,243,255,.22),inset 0 1px 0 rgba(255,255,255,.16);color:#fff}
        #nx-bottom-drawer .nx-btn-cyan{outline-color:rgba(0,243,255,.32);color:#9ffcff}
        #nx-bottom-drawer .nx-btn-purp{outline-color:rgba(176,38,255,.35);color:#e1adff}
        #nx-bottom-drawer .nx-btn-warn{outline-color:rgba(252,238,10,.36);color:#fff38f}
        #nx-bottom-drawer .nx-btn-crit{outline-color:rgba(255,0,60,.36);color:#ff9eb3}
        .nx-close-flyout{min-width:40px;height:40px;border-radius:14px;background:rgba(255,255,255,.07);color:#d9faff;outline:1px solid rgba(255,255,255,.15);font-size:18px;transition:.16s}
        .nx-close-flyout:hover{background:#ff003c;color:#fff;outline-color:#ff003c;box-shadow:0 0 22px rgba(255,0,60,.35)}
        .nx-dock-pulse{position:absolute;right:16px;top:-5px;width:10px;height:10px;border-radius:50%;background:#00ff88;box-shadow:0 0 20px #00ff88;animation:nxDockPulse 1.4s ease-in-out infinite}
        @keyframes nxDockPulse{50%{transform:scale(1.7);opacity:.45}}
        body.nx-modern-nav-ready #nexus-floating-chat{bottom:92px}
        @media(max-width:900px){#nx-bottom-drawer{bottom:10px;width:calc(100vw - 12px)}.nx-modern-dock{border-radius:20px;padding:8px}.nx-dock-groups{display:flex;overflow-x:auto;gap:7px;scrollbar-width:none}.nx-dock-groups::-webkit-scrollbar{display:none}.nx-dock-group{min-width:96px}.nx-modern-flyout{bottom:76px;border-radius:18px;max-height:56vh}.nx-flyout-grid{grid-template-columns:repeat(auto-fit,minmax(104px,1fr))}}
        @media(max-width:560px){body.nx-modern-nav-ready{padding-bottom:84px}.nx-modern-dock{gap:6px;min-height:58px}.nx-nav-arrow{width:36px;min-width:36px;height:38px;border-radius:13px}.nx-dock-group{min-width:82px;min-height:40px;padding:7px 8px}.nx-dock-group b{font-size:10px}.nx-dock-group small{display:none}.nx-modern-flyout{bottom:68px;padding:10px}.nx-flyout-head{margin-bottom:9px}.nx-flyout-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:7px}#nx-bottom-drawer .nx-btn{min-height:38px;padding:8px 7px;font-size:10px;letter-spacing:.2px}body.nx-modern-nav-ready #nexus-floating-chat{bottom:82px}}
    `;
    document.head.appendChild(style);
    document.body.classList.add("nx-modern-nav-ready");

    const drawer = document.createElement("div");
    drawer.id = "nx-bottom-drawer";
    drawer.innerHTML = `
        <svg class="nx-goo-svg" aria-hidden="true" focusable="false">
            <filter id="nx-core-goo">
                <feGaussianBlur in="SourceGraphic" stdDeviation="5" result="blur"></feGaussianBlur>
                <feColorMatrix in="blur" mode="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 20 -9" result="goo"></feColorMatrix>
                <feBlend in="SourceGraphic" in2="goo"></feBlend>
            </filter>
        </svg>
        <div class="nx-modern-flyout" id="nx-modern-flyout">
            <div class="nx-flyout-head">
                <div class="nx-flyout-title"><b id="nx-flyout-title">NEXUS NAV</b><span id="nx-flyout-sub">Wybierz grupe z dolnego docka</span></div>
                <button type="button" class="nx-close-flyout" id="nx-close-flyout" title="Zamknij">x</button>
            </div>
            <div class="nx-flyout-grid" id="nx-flyout-grid"></div>
        </div>
        <div class="nx-modern-dock">
            <button type="button" class="nx-nav-arrow" id="nx-tab-prev" title="Poprzednia zakladka">&lt;</button>
            <div class="nx-dock-groups" id="nx-dock-groups"></div>
            <button type="button" class="nx-nav-arrow" id="nx-tab-next" title="Nastepna zakladka">&gt;</button>
            <span class="nx-dock-pulse" aria-hidden="true"></span>
        </div>
    `;
    document.body.appendChild(drawer);

    const items = new Map();
    let activeGroup = "core";
    let isOpen = false;

    function groupMeta(groupId) {
        return navGroups.find(group => group.id === groupId) || navGroups[navGroups.length - 1];
    }

    function classTone(cls) {
        if (cls && cls.includes("purp")) return "nx-btn-purp";
        if (cls && cls.includes("warn")) return "nx-btn-warn";
        if (cls && cls.includes("crit")) return "nx-btn-crit";
        return "nx-btn-cyan";
    }

    function renderGroups() {
        const groupHost = document.getElementById("nx-dock-groups");
        groupHost.innerHTML = navGroups.map(group => `
            <button type="button" class="nx-dock-group${group.id === activeGroup ? " active" : ""}" data-group="${group.id}">
                <b>${group.label}</b><small>${group.sub}</small>
            </button>
        `).join("");
        groupHost.querySelectorAll(".nx-dock-group").forEach(btn => {
            btn.addEventListener("click", () => {
                activeGroup = btn.dataset.group;
                isOpen = true;
                renderGroups();
                renderFlyout();
            });
        });
    }

    function renderFlyout() {
        const meta = groupMeta(activeGroup);
        const flyout = document.getElementById("nx-modern-flyout");
        const title = document.getElementById("nx-flyout-title");
        const sub = document.getElementById("nx-flyout-sub");
        const grid = document.getElementById("nx-flyout-grid");
        const groupItems = Array.from(items.values()).filter(item => item.group === activeGroup);
        title.textContent = `${meta.label} / ${meta.sub}`;
        sub.textContent = groupItems.length ? "Szybki dostep do zakladek NEXUS CORE" : "Moduly tej grupy zaladuja sie za moment";
        grid.innerHTML = groupItems.map(item => `
            <button type="button" class="nx-btn ${item.cls}" data-target="${item.id}">${item.label}</button>
        `).join("");
        grid.querySelectorAll("button[data-target]").forEach(btn => {
            btn.addEventListener("click", () => navigateTo(btn.dataset.target, btn));
        });
        drawer.classList.toggle("open", isOpen);
        flyout.setAttribute("aria-hidden", isOpen ? "false" : "true");
        refreshActive();
    }

    function refreshActive() {
        const activePage = document.querySelector(".page.active");
        const activeId = activePage ? activePage.id : "dashboard";
        drawer.querySelectorAll("[data-target]").forEach(btn => {
            btn.classList.toggle("active-tab", btn.dataset.target === activeId);
        });
        const activeItem = items.get(activeId);
        if (activeItem && activeItem.group !== activeGroup && !isOpen) {
            activeGroup = activeItem.group;
            renderGroups();
        }
    }

    function navigateTo(id, btn) {
        if (!document.getElementById(id)) {
            if (window.notifyNexus) window.notifyNexus("warn", "NEXUS NAV", `Modul ${id} nie jest jeszcze gotowy.`);
            return;
        }
        if (typeof window.show === "function") {
            window.show(id, btn || null);
        }
        const item = items.get(id);
        if (item) activeGroup = item.group;
        isOpen = false;
        renderGroups();
        renderFlyout();
        refreshActive();
    }

    function getSwitchableItems() {
        return Array.from(items.values()).filter(item => document.getElementById(item.id));
    }

    function switchTab(direction) {
        const switchable = getSwitchableItems();
        if (!switchable.length) return;
        const activePage = document.querySelector(".page.active");
        const activeId = activePage ? activePage.id : switchable[0].id;
        let index = switchable.findIndex(item => item.id === activeId);
        if (index < 0) index = 0;
        const next = switchable[(index + direction + switchable.length) % switchable.length];
        navigateTo(next.id, null);
    }

    function addNavButton({ id, label, cls = "nx-btn-cyan", group = "lab" }) {
        if (!id || items.has(id)) return;
        const safeGroup = navGroups.some(entry => entry.id === group) ? group : "lab";
        items.set(id, { id, label: label || id, cls: classTone(cls), group: safeGroup });
        window.nexusTabGroups[id] = safeGroup;
        renderGroups();
        if (safeGroup === activeGroup) renderFlyout();
    }

    window.nexusTabGroups = {};
    window.nexusAddNavButton = addNavButton;
    window.nexusSwitchTab = switchTab;
    window.closeDrawer = function () {
        isOpen = false;
        renderFlyout();
    };

    baseTabs.forEach(addNavButton);
    renderGroups();
    renderFlyout();

    document.getElementById("nx-tab-prev").addEventListener("click", () => switchTab(-1));
    document.getElementById("nx-tab-next").addEventListener("click", () => switchTab(1));
    document.getElementById("nx-close-flyout").addEventListener("click", window.closeDrawer);
    document.addEventListener("keydown", event => {
        if (event.key === "Escape" && isOpen) window.closeDrawer();
    });

    const observer = new MutationObserver(refreshActive);
    observer.observe(document.getElementById("content") || document.body, { attributes: true, subtree: true, attributeFilter: ["class"] });
});
