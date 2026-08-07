(function nexusCoreAudioBoot() {
    "use strict";

    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (!AudioContextClass) return;

    const state = {
        ctx: null,
        master: null,
        ambient: null,
        enabled: localStorage.getItem("nexus_audio") !== "off",
        unlocked: false,
        ambientNodes: [],
        lastDrawer: 0,
        lastClick: 0
    };

    function ensure() {
        if (!state.ctx) {
            state.ctx = new AudioContextClass();
            state.master = state.ctx.createGain();
            state.master.gain.value = 0.18;
            state.master.connect(state.ctx.destination);
        }
        if (state.ctx.state === "suspended") {
            state.ctx.resume().catch(() => {});
        }
        state.unlocked = true;
        return state.ctx;
    }

    function now() {
        return state.ctx ? state.ctx.currentTime : 0;
    }

    function connectGain(value, destination) {
        const ctx = ensure();
        const gain = ctx.createGain();
        gain.gain.value = value;
        gain.connect(destination || state.master);
        return gain;
    }

    function tone(freq, dur, type, gainValue, delay, destination) {
        if (!state.enabled) return;
        const ctx = ensure();
        const t = ctx.currentTime + (delay || 0);
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = type || "sine";
        osc.frequency.setValueAtTime(freq, t);
        gain.gain.setValueAtTime(0.0001, t);
        gain.gain.exponentialRampToValueAtTime(Math.max(gainValue || 0.04, 0.0002), t + 0.01);
        gain.gain.exponentialRampToValueAtTime(0.0001, t + dur);
        osc.connect(gain);
        gain.connect(destination || state.master);
        osc.start(t);
        osc.stop(t + dur + 0.03);
    }

    function sweep(from, to, dur, type, gainValue, delay, destination) {
        if (!state.enabled) return;
        const ctx = ensure();
        const t = ctx.currentTime + (delay || 0);
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = type || "sine";
        osc.frequency.setValueAtTime(from, t);
        osc.frequency.exponentialRampToValueAtTime(Math.max(to, 1), t + dur);
        gain.gain.setValueAtTime(0.0001, t);
        gain.gain.exponentialRampToValueAtTime(gainValue || 0.05, t + 0.02);
        gain.gain.exponentialRampToValueAtTime(0.0001, t + dur);
        osc.connect(gain);
        gain.connect(destination || state.master);
        osc.start(t);
        osc.stop(t + dur + 0.04);
    }

    function noiseBurst(dur, gainValue, filterFreq, type, delay, destination) {
        if (!state.enabled) return;
        const ctx = ensure();
        const t = ctx.currentTime + (delay || 0);
        const buffer = ctx.createBuffer(1, Math.max(1, Math.floor(ctx.sampleRate * dur)), ctx.sampleRate);
        const data = buffer.getChannelData(0);
        for (let i = 0; i < data.length; i++) {
            data[i] = (Math.random() * 2 - 1) * (1 - i / data.length);
        }
        const source = ctx.createBufferSource();
        const filter = ctx.createBiquadFilter();
        const gain = ctx.createGain();
        source.buffer = buffer;
        filter.type = type || "bandpass";
        filter.frequency.value = filterFreq || 1400;
        filter.Q.value = 5;
        gain.gain.setValueAtTime(gainValue || 0.035, t);
        gain.gain.exponentialRampToValueAtTime(0.0001, t + dur);
        source.connect(filter);
        filter.connect(gain);
        gain.connect(destination || state.master);
        source.start(t);
        source.stop(t + dur + 0.02);
    }

    function startAmbient() {
        if (!state.enabled || document.body.classList.contains("auth-locked") || state.ambient) return;
        const ctx = ensure();
        state.ambient = ctx.createGain();
        state.ambient.gain.setValueAtTime(0.0001, ctx.currentTime);
        state.ambient.gain.linearRampToValueAtTime(0.055, ctx.currentTime + 1.4);
        state.ambient.connect(state.master);

        const low = ctx.createOscillator();
        const lowGain = ctx.createGain();
        low.type = "sine";
        low.frequency.value = 49;
        lowGain.gain.value = 0.18;
        low.connect(lowGain);
        lowGain.connect(state.ambient);

        const fan = ctx.createOscillator();
        const fanGain = ctx.createGain();
        fan.type = "triangle";
        fan.frequency.value = 93;
        fanGain.gain.value = 0.045;
        fan.connect(fanGain);
        fanGain.connect(state.ambient);

        const noise = ctx.createBufferSource();
        const buffer = ctx.createBuffer(1, ctx.sampleRate * 2, ctx.sampleRate);
        const data = buffer.getChannelData(0);
        for (let i = 0; i < data.length; i++) data[i] = Math.random() * 2 - 1;
        noise.buffer = buffer;
        noise.loop = true;
        const filter = ctx.createBiquadFilter();
        const noiseGain = ctx.createGain();
        filter.type = "lowpass";
        filter.frequency.value = 180;
        noiseGain.gain.value = 0.065;
        noise.connect(filter);
        filter.connect(noiseGain);
        noiseGain.connect(state.ambient);

        low.start();
        fan.start();
        noise.start();
        state.ambientNodes = [low, fan, noise];
    }

    function stopAmbient() {
        if (!state.ambient || !state.ctx) return;
        const ctx = state.ctx;
        state.ambient.gain.cancelScheduledValues(ctx.currentTime);
        state.ambient.gain.linearRampToValueAtTime(0.0001, ctx.currentTime + 0.35);
        setTimeout(() => {
            state.ambientNodes.forEach(node => {
                try { node.stop(); } catch (_) {}
            });
            try { state.ambient.disconnect(); } catch (_) {}
            state.ambient = null;
            state.ambientNodes = [];
        }, 420);
    }

    function uiClick() {
        const t = Date.now();
        if (t - state.lastClick < 45) return;
        state.lastClick = t;
        tone(760, 0.045, "sine", 0.035);
        tone(1180, 0.035, "triangle", 0.018, 0.018);
        noiseBurst(0.025, 0.012, 2600, "highpass");
    }

    function drawerLock() {
        const t = Date.now();
        if (t - state.lastDrawer < 500) return;
        state.lastDrawer = t;
        noiseBurst(0.18, 0.045, 420, "bandpass");
        sweep(82, 135, 0.28, "sawtooth", 0.045, 0.03);
        tone(260, 0.08, "square", 0.026, 0.2);
    }

    function chime() {
        tone(640, 0.14, "sine", 0.045);
        tone(920, 0.2, "sine", 0.036, 0.12);
    }

    function warn() {
        tone(330, 0.1, "triangle", 0.052);
        tone(250, 0.13, "triangle", 0.043, 0.09);
    }

    function terminalKey() {
        noiseBurst(0.018, 0.024, 1800, "bandpass");
        tone(520 + Math.random() * 90, 0.018, "square", 0.012);
    }

    function dataBurst() {
        noiseBurst(0.09, 0.036, 2300, "bandpass");
        [720, 860, 1040, 1280].forEach((f, i) => tone(f, 0.035, "triangle", 0.025, i * 0.025));
    }

    function createToggle() {
        if (document.getElementById("nexus-audio-toggle")) return;
        const style = document.createElement("style");
        style.textContent = `
            #nexus-audio-toggle {
                position:fixed; right:18px; bottom:78px; z-index:4600;
                min-width:94px; padding:9px 10px; border-radius:6px;
                border:1px solid var(--acc-cyan); background:rgba(5,5,5,.94);
                color:var(--acc-cyan); font:bold 10px monospace; cursor:pointer;
                box-shadow:0 0 16px rgba(0,255,255,.16);
            }
            #nexus-audio-toggle.off { border-color:#555; color:#888; box-shadow:none; }
            body.auth-locked #nexus-audio-toggle { display:none; }
            @media(max-width:520px) {
                #nexus-audio-toggle {
                    left:145px; right:auto; bottom:86px;
                    min-width:86px; padding:8px 8px; font-size:9px;
                }
            }
        `;
        document.head.appendChild(style);
        const btn = document.createElement("button");
        btn.id = "nexus-audio-toggle";
        btn.type = "button";
        btn.title = "Wlacz lub wylacz warstwe audio";
        btn.addEventListener("click", event => {
            event.stopPropagation();
            state.enabled = !state.enabled;
            localStorage.setItem("nexus_audio", state.enabled ? "on" : "off");
            if (state.enabled) {
                ensure();
                startAmbient();
                chime();
            } else {
                stopAmbient();
            }
            updateToggle();
        });
        document.body.appendChild(btn);
        updateToggle();
    }

    function updateToggle() {
        const btn = document.getElementById("nexus-audio-toggle");
        if (!btn) return;
        btn.textContent = state.enabled ? "AUDIO ON" : "AUDIO OFF";
        btn.classList.toggle("off", !state.enabled);
    }

    function patchFunction(name, wrapper) {
        let tries = 0;
        const timer = setInterval(() => {
            tries++;
            const fn = window[name];
            if (typeof fn === "function" && !fn.__nexusAudioPatched) {
                const patched = wrapper(fn);
                patched.__nexusAudioPatched = true;
                window[name] = patched;
                clearInterval(timer);
            }
            if (tries > 80) clearInterval(timer);
        }, 100);
    }

    function initEvents() {
        document.addEventListener("pointerdown", event => {
            ensure();
            if (state.enabled && !document.body.classList.contains("auth-locked")) startAmbient();
            const target = event.target.closest("button,.nav-btn,.nx-btn,select,.page-edit-lock");
            if (target && target.id !== "nexus-audio-toggle") uiClick();
        }, true);

        document.addEventListener("keydown", event => {
            if (event.target && event.target.id === "term-input") {
                if (event.key === "Enter") dataBurst();
                else if (event.key.length === 1 || event.key === "Backspace") terminalKey();
            }
        }, true);

        document.addEventListener("nexus:authenticated", () => {
            ensure();
            startAmbient();
            chime();
            createToggle();
        });

        const nativeAlert = window.alert;
        window.alert = function patchedAlert(message) {
            const text = String(message || "").toLowerCase();
            if (/(błąd|blad|error|utrata|brak|nieudana|denied|fail)/.test(text)) warn();
            else chime();
            return nativeAlert.apply(window, arguments);
        };

        patchFunction("show", original => function patchedShow() {
            uiClick();
            return original.apply(this, arguments);
        });

        patchFunction("executeCmd", original => async function patchedExecuteCmd() {
            dataBurst();
            try {
                const result = await original.apply(this, arguments);
                chime();
                return result;
            } catch (err) {
                warn();
                throw err;
            }
        });

        ["createBackup", "saveFile", "uploadSelectedFile", "createUser", "changeUserPassword"].forEach(name => {
            patchFunction(name, original => async function patchedAction() {
                try {
                    const result = await original.apply(this, arguments);
                    chime();
                    return result;
                } catch (err) {
                    warn();
                    throw err;
                }
            });
        });

        const drawerWatch = setInterval(() => {
            const drawer = document.getElementById("nx-bottom-drawer");
            if (!drawer || drawer.dataset.audioBound === "1") return;
            drawer.dataset.audioBound = "1";
            drawer.addEventListener("transitionstart", event => {
                if (event.propertyName === "bottom" && drawer.style.bottom === "0px") drawerLock();
            });
            drawer.addEventListener("click", event => {
                if (event.target && String(event.target.textContent || "").includes("SYSTEM NAV")) drawerLock();
            });
            clearInterval(drawerWatch);
        }, 250);
    }

    function init() {
        createToggle();
        initEvents();
        if (!document.body.classList.contains("auth-locked")) startAmbient();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }

    window.NexusAudio = {
        click: uiClick,
        chime,
        warn,
        drawer: drawerLock,
        terminalKey,
        dataBurst,
        start: startAmbient,
        stop: stopAmbient
    };
})();
