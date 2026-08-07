document.addEventListener("DOMContentLoaded", () => {
    // Szukamy zakładki NEWS z chirurgiczną precyzją
    let newsPage = document.getElementById('news');
    if (!newsPage) {
        newsPage = Array.from(document.querySelectorAll('div')).find(el => el.id && el.id.toLowerCase().includes('news'));
    }
    
    if (!newsPage) return;

    // Styl dla animacji pojawiania się wiadomości
    const style = document.createElement('style');
    style.innerHTML = `
        @keyframes slideIn { 
            from { opacity: 0; transform: translateY(-10px); } 
            to { opacity: 1; transform: translateY(0); } 
        }
        .nx-scrollbar::-webkit-scrollbar { width: 6px; }
        .nx-scrollbar::-webkit-scrollbar-thumb { background: #00f3ff; border-radius: 3px; }
    `;
    document.head.appendChild(style);

    // Główny układ zakładki
    newsPage.innerHTML = `
        <div style="max-width: 900px; margin: 0 auto; display: flex; flex-direction: column; gap: 20px;">
            
            <!-- MODUŁ ZEGARA -->
            <div style="background: rgba(5, 10, 20, 0.9); border: 2px solid #00f3ff; border-radius: 8px; padding: 20px; text-align: center; box-shadow: 0 0 20px rgba(0, 243, 255, 0.15);">
                <div style="color: #fcee0a; font-size: 16px; font-weight: bold; letter-spacing: 3px; margin-bottom: 15px; border-bottom: 1px dashed #00f3ff; padding-bottom: 8px; font-family: monospace;">
                    ⏱️ GLOBAL TIME SYNC
                </div>
                <div id="cyber-clock" style="font-size: 54px; color: #fff; font-family: 'Courier New', monospace; font-weight: bold; text-shadow: 0 0 15px #00f3ff; margin: 15px 0; letter-spacing: 5px;">
                    00:00:00
                </div>
                <div style="display: flex; justify-content: center; gap: 15px; align-items: center; font-family: monospace;">
                    <span style="color: #aaa; font-size: 14px;">[ STREFA ]</span>
                    <select id="tz-select" style="background: #000; color: #00f3ff; border: 1px solid #00f3ff; padding: 8px 15px; font-family: inherit; font-size: 14px; border-radius: 4px; outline: none; cursor: pointer;">
                        <option value="Europe/Warsaw">Warszawa (CET/CEST)</option>
                        <option value="UTC">Universal Time (UTC)</option>
                        <option value="America/New_York">New York (EST/EDT)</option>
                        <option value="Asia/Tokyo">Tokyo (JST)</option>
                        <option value="Europe/London">London (GMT/BST)</option>
                    </select>
                </div>
            </div>

            <!-- MODUŁ WIADOMOŚCI -->
            <div style="background: rgba(5, 10, 20, 0.9); border: 2px solid #00f3ff; border-radius: 8px; padding: 20px; box-shadow: 0 0 20px rgba(0, 243, 255, 0.15); display: flex; flex-direction: column;">
                <div style="color: #fcee0a; font-size: 16px; font-weight: bold; letter-spacing: 3px; margin-bottom: 15px; border-bottom: 1px dashed #00f3ff; padding-bottom: 8px; font-family: monospace; display: flex; justify-content: space-between;">
                    <span>⚡ DEKODER DANYCH OPERACYJNYCH</span>
                    <span style="color: #0f0; font-size: 12px; animation: eqAnim 1s infinite alternate;">● REC</span>
                </div>
                <div id="cyber-feed" class="nx-scrollbar" style="display: flex; flex-direction: column; gap: 12px; overflow-y: auto; height: 350px; padding-right: 10px;">
                    <!-- Tutaj będą wpadać wiadomości -->
                </div>
            </div>
            
        </div>
    `;

    // 1. LOGIKA ZEGARA
    function updateClock() {
        const tz = document.getElementById("tz-select").value;
        const now = new Date();
        const timeString = now.toLocaleTimeString('pl-PL', { timeZone: tz, hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
        document.getElementById("cyber-clock").innerText = timeString;
    }
    setInterval(updateClock, 1000);
    updateClock();

    // 2. BAZA DEPESZY (nasze poprzednie, potężne wiadomości)
    const db = [
        { t: "CRITICAL", c: "#ff003c", m: "Potężny cyberatak na serwery Węzła Alfa. Trwa izolacja klastra sieciowego." },
        { t: "INFO", c: "#00f3ff", m: "Połączenie zaszyfrowane nawiązane (RSA-4096). Parametry w normie." },
        { t: "LIVE", c: "#0f0", m: "Skanowanie częstotliwości... Odnaleziono ukrytą stację nadawczą." },
        { t: "WARN", c: "#fcee0a", m: "Wykryto niezidentyfikowany ruch kierowany na Twój węzeł proxy." },
        { t: "INTEL", c: "#b026ff", m: "Analiza zagrożeń zakończona. Wykryto nową lukę zero-day w sieciach DNS." },
        { t: "INFO", c: "#00f3ff", m: "Aktualizacja firmware wdrożona pomyślnie. Wszystkie moduły zsynchronizowane." },
        { t: "CRITICAL", c: "#ff003c", m: "Atak DDoS na główne przekaźniki. Przekierowywanie ruchu na węzły zapasowe." }
    ];

    const feed = document.getElementById("cyber-feed");

    // Funkcja dodająca nową wiadomość
    function addMessage() {
        if (!feed) return;
        const msg = db[Math.floor(Math.random() * db.length)];
        const time = new Date().toLocaleTimeString('pl-PL', {hour12: false});
        
        const div = document.createElement("div");
        div.style.cssText = `background: rgba(0,0,0,0.6); border-left: 4px solid ${msg.c}; padding: 15px; border-radius: 0 4px 4px 0; animation: slideIn 0.4s ease-out; box-shadow: inset 0 0 10px rgba(0,0,0,0.5);`;
        div.innerHTML = `
            <div style="display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 8px; font-family: monospace;">
                <span style="color:${msg.c}; font-weight:bold; letter-spacing: 1px;">[${msg.t}]</span>
                <span style="color:#889;">${time}</span>
            </div>
            <div style="font-size: 15px; color: #eee; line-height: 1.5; font-family: monospace;">${msg.m}</div>
        `;
        
        feed.prepend(div);
        
        // Zostawiamy tylko 8 ostatnich wiadomości, żeby nie przeciążać pamięci przeglądarki
        if (feed.children.length > 8) {
            feed.lastChild.remove();
        }
    }

    // Dodajemy kilka początkowych depesz od razu
    for(let i=0; i<4; i++) { addMessage(); }
    
    // Uruchamiamy pętlę co 4.5 sekundy
    setInterval(addMessage, 4500);
});
