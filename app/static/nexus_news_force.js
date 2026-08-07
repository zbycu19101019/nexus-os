(function initNexusNewsDeck() {
    const newsPage = document.getElementById('news');
    if (!newsPage) {
        setTimeout(initNexusNewsDeck, 200);
        return;
    }

    if (newsPage.dataset.nexusDeckReady === '1') {
        return;
    }
    newsPage.dataset.nexusDeckReady = '1';

    const style = document.createElement('style');
    style.textContent = `
        .news-deck { display:flex; flex-direction:column; gap:14px; min-height:100%; }
        .news-hero { display:grid; grid-template-columns:minmax(0,1.4fr) 320px; gap:12px; align-items:stretch; }
        .news-panel { background:linear-gradient(180deg,#111,#070707); border:1px solid #27343a; border-radius:6px; box-shadow:0 0 22px rgba(0,255,255,0.08); }
        .news-hero-main { padding:18px; border-left:4px solid var(--acc-cyan); position:relative; overflow:hidden; }
        .news-hero-main:before { content:""; position:absolute; inset:0; background:linear-gradient(110deg,rgba(0,255,255,0.09),transparent 45%,rgba(176,0,255,0.08)); pointer-events:none; }
        .news-hero-main > * { position:relative; z-index:1; }
        .news-kicker { color:var(--acc-warn); font-size:11px; font-weight:bold; letter-spacing:1px; text-transform:uppercase; }
        .news-hero h2 { margin:7px 0 8px; color:#fff; font-size:clamp(24px,3vw,42px); line-height:1.05; letter-spacing:0; }
        .news-hero p { margin:0; color:#aeb8ba; font-size:13px; line-height:1.55; max-width:820px; }
        .news-clock { padding:16px; display:flex; flex-direction:column; justify-content:space-between; gap:12px; }
        .news-clock strong { color:#fff; font-size:34px; line-height:1; text-shadow:0 0 14px rgba(0,255,255,0.4); }
        .news-clock span { color:#899; font-size:11px; text-transform:uppercase; }
        .news-toolbar { display:grid; grid-template-columns:1fr 170px minmax(180px,0.75fr) auto; gap:8px; align-items:center; padding:10px; }
        .news-toolbar .cyber-input, .news-toolbar select { margin:0; min-height:40px; }
        .news-stats { display:grid; grid-template-columns:repeat(4,minmax(140px,1fr)); gap:10px; }
        .news-stat { padding:12px; border-top:3px solid var(--acc-cyan); }
        .news-stat.warn { border-top-color:var(--acc-warn); }
        .news-stat.purp { border-top-color:var(--acc-purple); }
        .news-stat.crit { border-top-color:var(--acc-crit); }
        .news-stat span { color:#888; font-size:10px; text-transform:uppercase; }
        .news-stat strong { display:block; margin-top:5px; color:#fff; font-size:22px; line-height:1.1; overflow-wrap:anywhere; }
        .news-section-title { display:flex; justify-content:space-between; align-items:center; gap:10px; color:#fff; font-weight:bold; font-size:13px; letter-spacing:1px; text-transform:uppercase; border-bottom:1px solid #263136; padding:4px 0 9px; }
        .news-section-title span { color:#888; font-size:11px; font-weight:normal; letter-spacing:0; text-transform:none; }
        .news-spotlight { display:grid; grid-template-columns:minmax(0,1.1fr) minmax(280px,0.9fr); gap:12px; padding:12px; }
        .news-spot-media { min-height:250px; background:#030303; border:1px solid #243136; display:grid; place-items:center; overflow:hidden; }
        .news-spot-media img, .news-card-media img { width:100%; height:100%; object-fit:cover; display:block; }
        .news-spot-media iframe, .news-card-media iframe, .news-video iframe { width:100%; aspect-ratio:16/9; border:0; background:#000; display:block; }
        .news-spot-body { padding:4px 2px; display:flex; flex-direction:column; gap:10px; min-width:0; }
        .news-tag { display:inline-flex; align-items:center; width:max-content; max-width:100%; padding:3px 7px; border:1px solid #344; background:#080808; color:var(--acc-cyan); font-size:10px; font-weight:bold; text-transform:uppercase; }
        .news-tag.alert { color:#ff6767; border-color:#733; }
        .news-tag.watch { color:var(--acc-warn); border-color:#765512; }
        .news-tag.video { color:var(--acc-purple); border-color:#62306c; }
        .news-spot-body h3 { margin:0; color:#fff; font-size:24px; line-height:1.2; letter-spacing:0; overflow-wrap:anywhere; }
        .news-meta { color:#899; font-size:11px; display:flex; gap:8px; flex-wrap:wrap; }
        .news-summary { color:#b7b7b7; font-size:13px; line-height:1.55; margin:0; }
        .news-actions { display:flex; gap:8px; flex-wrap:wrap; margin-top:auto; }
        .news-video-strip { display:grid; grid-template-columns:repeat(auto-fit,minmax(250px,1fr)); gap:10px; }
        .news-video { padding:10px; border-left:3px solid var(--acc-purple); }
        .news-video h4 { margin:8px 0 4px; color:#fff; font-size:13px; line-height:1.3; overflow-wrap:anywhere; }
        .news-video .news-meta { font-size:10px; }
        .news-masonry { display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:12px; padding-bottom:18px; }
        .news-card { padding:12px; border-left:4px solid #334; transition:transform .16s ease,border-color .16s ease,box-shadow .16s ease; }
        .news-card:hover { transform:translateY(-2px); border-color:var(--acc-cyan); box-shadow:0 0 18px rgba(0,255,255,0.12); }
        .news-card.alert { border-left-color:var(--acc-crit); background:linear-gradient(180deg,#160808,#080808); }
        .news-card.watch { border-left-color:var(--acc-warn); background:linear-gradient(180deg,#151007,#080808); }
        .news-card.video { border-left-color:var(--acc-purple); }
        .news-card h3 { margin:8px 0; color:#fff; font-size:15px; line-height:1.35; letter-spacing:0; overflow-wrap:anywhere; }
        .news-card-media { height:150px; border:1px solid #242424; background:#020202; overflow:hidden; margin:8px 0; }
        .news-card p { margin:0 0 10px; color:#aaa; font-size:12px; line-height:1.45; }
        .news-status { color:#8ff; padding:16px; text-align:center; border:1px dashed #255; background:#061012; }
        .news-empty { color:#ffaa00; padding:16px; text-align:center; border:1px dashed #5f4310; background:#130d04; }
        @media (max-width:1050px) {
            .news-hero, .news-spotlight, .news-toolbar { grid-template-columns:1fr; }
            .news-stats { grid-template-columns:repeat(2,minmax(130px,1fr)); }
        }
        @media (max-width:560px) {
            .news-stats, .news-masonry, .news-video-strip { grid-template-columns:1fr; }
            .news-hero h2 { font-size:26px; }
            .news-clock strong { font-size:28px; }
            .news-spot-body h3 { font-size:19px; }
        }
    `;
    document.head.appendChild(style);

    newsPage.innerHTML = `
        <div class="news-deck">
            <section class="news-hero">
                <div class="news-panel news-hero-main">
                    <div class="news-kicker">NEXUS LIVE INTEL</div>
                    <h2>Centrum wiadomosci i wideo</h2>
                    <p>Jeden panel dla depesz z Polski, swiata, cyberbezpieczenstwa, technologii i kanalu wideo. Dane ida z backendowego /api/news, wiec nie meczymy przegladarki zewnetrznym proxy RSS.</p>
                </div>
                <div class="news-panel news-clock">
                    <span>Czas operacyjny</span>
                    <strong id="news-clock">00:00:00</strong>
                    <span id="news-last-sync">Ostatni sync: --</span>
                </div>
            </section>

            <section class="news-panel news-toolbar">
                <select id="news-source" class="cyber-input">
                    <option value="ALL">WSZYSTKO / GLOBAL MIX</option>
                    <option value="POLSKA">POLSKA</option>
                    <option value="SWIAT">SWIAT</option>
                    <option value="CYBER">CYBERSEC</option>
                    <option value="TECH">TECH</option>
                    <option value="VIDEO">WIDEO</option>
                </select>
                <select id="news-mode" class="cyber-input">
                    <option value="MIX">ARTYKULY + WIDEO</option>
                    <option value="VIDEO">TYLKO WIDEO</option>
                </select>
                <input id="news-search" class="cyber-input" placeholder="Szukaj w tytulach...">
                <button class="nav-btn" id="news-refresh" style="margin:0;">SYNCHRONIZUJ</button>
            </section>

            <section class="news-stats">
                <div class="news-panel news-stat"><span>Wiadomosci</span><strong id="news-count">0</strong></div>
                <div class="news-panel news-stat purp"><span>Materialy wideo</span><strong id="news-video-count">0</strong></div>
                <div class="news-panel news-stat crit"><span>Alerty</span><strong id="news-alert-count">0</strong></div>
                <div class="news-panel news-stat warn"><span>Filtr</span><strong id="news-filter-label">ALL</strong></div>
            </section>

            <div class="news-section-title">Najwazniejsza depesza <span id="news-headline-meta">oczekuje</span></div>
            <section id="news-spotlight" class="news-panel news-spotlight"></section>

            <div class="news-section-title">Wideo feed <span id="news-video-meta">automatycznie wykryte materialy</span></div>
            <section id="news-video-strip" class="news-video-strip"></section>

            <div class="news-section-title">Strumien depesz <span id="news-feed-meta">sortowanie: najnowsze</span></div>
            <section id="news-container" class="news-masonry"></section>
        </div>
    `;

    const controls = {
        source: document.getElementById('news-source'),
        mode: document.getElementById('news-mode'),
        search: document.getElementById('news-search'),
        refresh: document.getElementById('news-refresh')
    };

    controls.source.addEventListener('change', fetchNews);
    controls.mode.addEventListener('change', fetchNews);
    controls.refresh.addEventListener('click', fetchNews);
    controls.search.addEventListener('input', debounce(renderCurrentNews, 180));

    let currentItems = [];
    let currentRawItems = [];

    function updateClock() {
        const clock = document.getElementById('news-clock');
        if (clock) {
            clock.textContent = new Date().toLocaleTimeString('pl-PL', { hour12: false });
        }
    }

    function severity(item) {
        const title = normalize(item.title || '');
        const red = ['PILNE','WAZNE','UWAGA','ALERT','BREAKING','ATAK','AWARIA','KRYZYS','WOJNA','TRAGEDIA','WYCIEK','SMIERC','ZABOJSTWO','RANNI','ZABICI'];
        const yellow = ['OSTRZEZENIE','ZMIANA','UTRUDNIENIA','WYPADEK','SLEDZTWO','PROTEST','POGODA','BURZA','INFLACJA','CENY','STRAJK','ZAGROZENIE'];
        if (red.some(word => title.includes(word))) return 'alert';
        if (yellow.some(word => title.includes(word))) return 'watch';
        if (item.type === 'video' || item.embed_url) return 'video';
        return 'info';
    }

    function normalize(text) {
        return String(text).toUpperCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
    }

    function tagFor(item) {
        const level = severity(item);
        if (level === 'alert') return { cls: 'alert', label: 'ALERT' };
        if (level === 'watch') return { cls: 'watch', label: 'WATCH' };
        if (level === 'video') return { cls: 'video', label: 'VIDEO' };
        return { cls: '', label: item.category || 'INFO' };
    }

    function mediaHtml(item, mode) {
        if (item.embed_url) {
            return `<iframe src="${esc(item.embed_url)}" title="${esc(item.title || 'video')}" loading="lazy" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>`;
        }
        if (item.image) {
            return `<img src="${esc(item.image)}" alt="">`;
        }
        if (mode === 'spot') {
            return `<div style="color:#455;text-align:center;padding:28px;">NO MEDIA SIGNAL</div>`;
        }
        return '';
    }

    function metaHtml(item) {
        const source = item.source || item.category || 'NEWS';
        const date = item.published || item.pubDate || '';
        return `<div class="news-meta"><span>${esc(source)}</span><span>${esc(item.category || '')}</span><span>${esc(date)}</span></div>`;
    }

    function renderSpotlight(items) {
        const box = document.getElementById('news-spotlight');
        const meta = document.getElementById('news-headline-meta');
        const item = items[0];
        if (!item) {
            box.innerHTML = '<div class="news-empty">Brak depesz dla tego filtra.</div>';
            meta.textContent = 'brak danych';
            return;
        }
        const tag = tagFor(item);
        meta.textContent = item.source || item.category || 'LIVE';
        box.innerHTML = `
            <div class="news-spot-media">${mediaHtml(item, 'spot')}</div>
            <div class="news-spot-body">
                <span class="news-tag ${tag.cls}">${esc(tag.label)}</span>
                <h3>${esc(item.title || 'Bez tytulu')}</h3>
                ${metaHtml(item)}
                <p class="news-summary">${esc(trimText(item.description || '', 420))}</p>
                <div class="news-actions">
                    <button class="nav-btn" onclick="window.open('${escAttr(item.link || '#')}','_blank')" style="margin:0;border-color:var(--acc-cyan);color:var(--acc-cyan);">OTWORZ ZRODLO</button>
                    ${item.embed_url ? `<button class="nav-btn" onclick="window.open('${escAttr(item.link || item.embed_url)}','_blank')" style="margin:0;border-color:var(--acc-purple);color:var(--acc-purple);">OTWORZ WIDEO</button>` : ''}
                </div>
            </div>
        `;
    }

    function renderVideoStrip(items) {
        const strip = document.getElementById('news-video-strip');
        const videos = items.filter(item => item.type === 'video' || item.embed_url).slice(0, 6);
        document.getElementById('news-video-meta').textContent = videos.length ? `${videos.length} materialow wideo` : 'brak wideo w tym filtrze';
        if (!videos.length) {
            strip.innerHTML = '<div class="news-empty">W tym filtrze nie ma aktualnie wideo.</div>';
            return;
        }
        strip.innerHTML = videos.map(item => `
            <article class="news-panel news-video">
                ${mediaHtml(item, 'video')}
                <h4>${esc(item.title || '')}</h4>
                ${metaHtml(item)}
            </article>
        `).join('');
    }

    function renderCards(items) {
        const container = document.getElementById('news-container');
        document.getElementById('news-feed-meta').textContent = `${items.length} pozycji`;
        if (!items.length) {
            container.innerHTML = '<div class="news-empty">Nic nie pasuje do wyszukiwania.</div>';
            return;
        }
        container.innerHTML = items.map(item => {
            const tag = tagFor(item);
            const media = mediaHtml(item, 'card');
            return `
                <article class="news-panel news-card ${tag.cls}">
                    <span class="news-tag ${tag.cls}">${esc(tag.label)}</span>
                    <h3>${esc(item.title || '')}</h3>
                    ${media ? `<div class="news-card-media">${media}</div>` : ''}
                    ${metaHtml(item)}
                    <p>${esc(trimText(item.description || '', 220))}</p>
                    <button class="nav-btn" onclick="window.open('${escAttr(item.link || '#')}','_blank')" style="margin:0;padding:7px 10px;font-size:11px;border-color:#355;color:#9ff;background:#050505;">CZYTAJ</button>
                </article>
            `;
        }).join('');
    }

    function renderCurrentNews() {
        const phrase = normalize(controls.search.value || '');
        currentItems = phrase
            ? currentRawItems.filter(item => normalize(`${item.title || ''} ${item.description || ''}`).includes(phrase))
            : currentRawItems.slice();

        const videos = currentItems.filter(item => item.type === 'video' || item.embed_url).length;
        const alerts = currentItems.filter(item => severity(item) === 'alert').length;
        document.getElementById('news-count').textContent = currentItems.length;
        document.getElementById('news-video-count').textContent = videos;
        document.getElementById('news-alert-count').textContent = alerts;
        document.getElementById('news-filter-label').textContent = `${controls.source.value} / ${controls.mode.value}`;
        renderSpotlight(currentItems);
        renderVideoStrip(currentItems);
        renderCards(currentItems);
    }

    async function fetchNews() {
        const container = document.getElementById('news-container');
        if (container) {
            container.innerHTML = '<div class="news-status">Synchronizuje rozszerzony strumien RSS i wideo z VPS...</div>';
        }
        try {
            const source = controls.source.value || 'ALL';
            const mode = controls.mode.value || 'MIX';
            const url = `/api/news?source=${encodeURIComponent(source)}&limit=100&video=${mode === 'VIDEO' ? 1 : 0}`;
            const response = await fetch(url, { cache: 'no-store' });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const items = await response.json();
            currentRawItems = Array.isArray(items) ? items : [];
            document.getElementById('news-last-sync').textContent = `Ostatni sync: ${new Date().toLocaleTimeString('pl-PL', { hour12:false })}`;
            renderCurrentNews();
        } catch (err) {
            currentRawItems = [];
            renderCurrentNews();
            const container = document.getElementById('news-container');
            if (container) {
                container.innerHTML = `<div class="news-empty">Blad pobierania feedu: ${esc(err.message || err)}</div>`;
            }
        }
    }

    function trimText(text, limit) {
        const clean = String(text).replace(/\s+/g, ' ').trim();
        if (clean.length <= limit) return clean;
        return clean.slice(0, limit - 3).trim() + '...';
    }

    function esc(value) {
        return String(value == null ? '' : value)
            .replaceAll('&', '&amp;')
            .replaceAll('<', '&lt;')
            .replaceAll('>', '&gt;')
            .replaceAll('"', '&quot;')
            .replaceAll("'", '&#039;');
    }

    function escAttr(value) {
        return esc(value).replaceAll('`', '&#096;');
    }

    function debounce(fn, delay) {
        let timer = null;
        return function debounced() {
            clearTimeout(timer);
            timer = setTimeout(fn, delay);
        };
    }

    window.fetchNews = fetchNews;
    window.nexusNewsRefresh = fetchNews;

    updateClock();
    setInterval(updateClock, 1000);
    fetchNews();
    setInterval(fetchNews, 300000);
})();
