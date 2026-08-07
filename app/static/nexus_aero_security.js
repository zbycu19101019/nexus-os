(function () {
  "use strict";

  const dockItems = [
    { id: "dash", label: "Dashboard", module: "dash", icon: "dash" },
    { id: "hyperdeck", label: "Hyper-Deck", module: "hyperdeck", icon: "server" },
    { id: "iso", label: "ISO Vault", module: "hyperdeck", icon: "disc" },
    { id: "iam", label: "IAM", module: "admin", icon: "iam" },
    { id: "settings", label: "Ustawienia", module: "api", icon: "settings" }
  ];

  let otpPromise = null;
  let otpResolve = null;
  let otpReject = null;
  let activeDockId = "dash";
  let dockReady = false;

  function iconSvg(name) {
    const attrs = 'viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"';
    const paths = {
      dash: '<rect x="3" y="3" width="7" height="7" rx="2"/><rect x="14" y="3" width="7" height="7" rx="2"/><rect x="3" y="14" width="7" height="7" rx="2"/><rect x="14" y="14" width="7" height="7" rx="2"/>',
      server: '<rect x="4" y="4" width="16" height="6" rx="2"/><rect x="4" y="14" width="16" height="6" rx="2"/><path d="M8 7h.01M8 17h.01M12 7h4M12 17h4"/>',
      disc: '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="2.4"/><path d="M12 4v3M20 12h-3M12 20v-3M4 12h3"/>',
      iam: '<path d="M16 21v-2a4 4 0 0 0-8 0v2"/><circle cx="12" cy="8" r="4"/><path d="M19 8l1.5 1.5L22 8"/><path d="M20.5 9.5V13"/>',
      settings: '<path d="M4 7h10"/><path d="M18 7h2"/><circle cx="16" cy="7" r="2"/><path d="M4 17h2"/><path d="M10 17h10"/><circle cx="8" cy="17" r="2"/><path d="M4 12h5"/><path d="M13 12h7"/><circle cx="11" cy="12" r="2"/>'
    };
    return `<svg ${attrs}>${paths[name] || paths.dash}</svg>`;
  }

  function ensureOtpOverlay() {
    let overlay = document.querySelector(".aero-otp-overlay");
    if (overlay) return overlay;

    overlay = document.createElement("section");
    overlay.className = "aero-otp-overlay";
    overlay.setAttribute("aria-modal", "true");
    overlay.setAttribute("role", "dialog");
    overlay.innerHTML = `
      <div class="aero-otp-card">
        <div class="aero-otp-inner">
          <p class="aero-otp-kicker">Secure access layer</p>
          <h2 class="aero-otp-title">OTP VERIFICATION</h2>
          <p class="aero-otp-copy">Wpisz 4 cyfry kodu. Po ostatniej cyfrze NEXUS narysuje sciezke zaufania i odblokuje panel AERO.</p>
          <div class="aero-otp-inputs" aria-label="Kod OTP">
            <input class="aero-otp-input" inputmode="numeric" pattern="[0-9]*" maxlength="1" autocomplete="one-time-code" aria-label="Cyfra 1">
            <input class="aero-otp-input" inputmode="numeric" pattern="[0-9]*" maxlength="1" aria-label="Cyfra 2">
            <input class="aero-otp-input" inputmode="numeric" pattern="[0-9]*" maxlength="1" aria-label="Cyfra 3">
            <input class="aero-otp-input" inputmode="numeric" pattern="[0-9]*" maxlength="1" aria-label="Cyfra 4">
          </div>
          <div class="aero-otp-stage" aria-hidden="true">
            <svg class="aero-otp-constellation" viewBox="0 0 320 210">
              <path class="aero-otp-line is-soft" d="M160 24 L282 105 L160 186 L38 105 Z M160 24 L160 186 M38 105 L282 105" />
              <path class="aero-otp-line is-main" d="M160 24 L282 105 L160 186 L38 105 Z M160 24 L160 186 M38 105 L282 105" />
              <circle class="aero-otp-node" cx="160" cy="24" r="8" />
              <circle class="aero-otp-node" cx="282" cy="105" r="8" />
              <circle class="aero-otp-node" cx="160" cy="186" r="8" />
              <circle class="aero-otp-node" cx="38" cy="105" r="8" />
              <circle class="aero-otp-node" cx="160" cy="105" r="6" />
            </svg>
            <div class="aero-otp-success">
              <div>
                <div class="aero-otp-check">
                  <svg viewBox="0 0 24 24" width="36" height="36" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M20 6 9 17l-5-5" />
                  </svg>
                </div>
                <h3>Verified successfully</h3>
                <p>Sesja AERO zostala potwierdzona lokalnym OTP.</p>
                <button class="aero-otp-continue" type="button">Kontynuuj</button>
              </div>
            </div>
          </div>
        </div>
      </div>`;

    document.body.appendChild(overlay);
    wireOtpOverlay(overlay);
    return overlay;
  }

  function wireOtpOverlay(overlay) {
    const inputs = Array.from(overlay.querySelectorAll(".aero-otp-input"));
    const button = overlay.querySelector(".aero-otp-continue");

    function codeReady() {
      return inputs.map(input => input.value).join("").length === inputs.length;
    }

    function beginVerification() {
      if (overlay.classList.contains("is-verifying")) return;
      inputs.forEach(input => input.blur());
      overlay.classList.add("is-verifying");
      window.setTimeout(() => {
        overlay.classList.add("is-success");
        button.focus({ preventScroll: true });
      }, 1280);
    }

    inputs.forEach((input, index) => {
      input.addEventListener("input", event => {
        const value = String(event.target.value || "").replace(/\D/g, "").slice(-1);
        event.target.value = value;
        if (value && inputs[index + 1]) inputs[index + 1].focus();
        if (codeReady()) beginVerification();
      });

      input.addEventListener("keydown", event => {
        if (event.key === "Backspace" && !input.value && inputs[index - 1]) {
          inputs[index - 1].focus();
          inputs[index - 1].value = "";
          event.preventDefault();
        }
      });

      input.addEventListener("paste", event => {
        const text = (event.clipboardData || window.clipboardData).getData("text");
        const digits = String(text || "").replace(/\D/g, "").slice(0, inputs.length).split("");
        if (!digits.length) return;
        event.preventDefault();
        inputs.forEach((field, idx) => { field.value = digits[idx] || ""; });
        const next = inputs[Math.min(digits.length, inputs.length) - 1];
        if (next) next.focus();
        if (codeReady()) beginVerification();
      });
    });

    button.addEventListener("click", () => {
      overlay.classList.remove("is-open");
      window.setTimeout(() => {
        if (otpResolve) otpResolve(true);
        otpPromise = otpResolve = otpReject = null;
      }, 180);
    });
  }

  function requestOtp() {
    if (otpPromise) return otpPromise;
    const overlay = ensureOtpOverlay();
    const inputs = Array.from(overlay.querySelectorAll(".aero-otp-input"));
    overlay.classList.remove("is-verifying", "is-success");
    inputs.forEach(input => { input.value = ""; input.disabled = false; });
    otpPromise = new Promise((resolve, reject) => {
      otpResolve = resolve;
      otpReject = reject;
    });
    window.requestAnimationFrame(() => {
      overlay.classList.add("is-open");
      window.setTimeout(() => inputs[0]?.focus({ preventScroll: true }), 120);
    });
    return otpPromise;
  }

  function ensureGooDefs() {
    if (document.getElementById("aero-goo-svg-defs")) return;
    const defs = document.createElement("div");
    defs.className = "aero-goo-defs";
    defs.id = "aero-goo-svg-defs";
    defs.innerHTML = `
      <svg width="0" height="0" aria-hidden="true" focusable="false">
        <defs>
          <filter id="aero-goo-filter">
            <feGaussianBlur in="SourceGraphic" stdDeviation="8" result="blur" />
            <feColorMatrix in="blur" mode="matrix" values="
              1 0 0 0 0
              0 1 0 0 0
              0 0 1 0 0
              0 0 0 20 -9" result="goo" />
            <feComposite in="SourceGraphic" in2="goo" operator="atop" />
          </filter>
        </defs>
      </svg>`;
    document.body.appendChild(defs);
  }

  function ensureDock() {
    if (dockReady || document.querySelector(".aero-liquid-dock-shell")) return;
    ensureGooDefs();
    const shell = document.createElement("nav");
    shell.className = "aero-liquid-dock-shell";
    shell.setAttribute("aria-label", "NEXUS AERO liquid navigation");
    shell.innerHTML = `
      <div class="aero-liquid-dock">
        <div class="aero-liquid-base"></div>
        <div class="aero-liquid-bubble"></div>
        ${dockItems.map(item => `
          <button class="aero-liquid-item" type="button" data-dock-id="${item.id}" data-module="${item.module}" aria-label="${item.label}">
            ${iconSvg(item.icon)}
            <span class="aero-liquid-label">${item.label}</span>
          </button>`).join("")}
      </div>`;
    document.body.appendChild(shell);
    dockReady = true;

    shell.addEventListener("click", event => {
      const button = event.target.closest(".aero-liquid-item");
      if (!button) return;
      setDockActive(button.dataset.dockId);
      window.dispatchEvent(new CustomEvent("nexus:aero:set-module", {
        detail: { module: button.dataset.module, source: "liquid-dock", dockId: button.dataset.dockId }
      }));
    });

    window.addEventListener("resize", () => setDockActive(activeDockId, true), { passive: true });
    window.addEventListener("nexus:aero:module-changed", event => {
      const module = event.detail?.module;
      const match = dockItems.find(item => item.module === module && item.id !== "iso") || dockItems.find(item => item.module === module);
      if (match) setDockActive(match.id, true);
      updateDockVisibility();
    });

    updateDockVisibility();
    setDockActive(activeDockId, true);
  }

  function setDockActive(id, passive) {
    const shell = document.querySelector(".aero-liquid-dock-shell");
    if (!shell) return;
    const dock = shell.querySelector(".aero-liquid-dock");
    const bubble = shell.querySelector(".aero-liquid-bubble");
    const buttons = Array.from(shell.querySelectorAll(".aero-liquid-item"));
    const target = buttons.find(button => button.dataset.dockId === id) || buttons[0];
    if (!target || !bubble || !dock) return;
    activeDockId = target.dataset.dockId;
    buttons.forEach(button => button.classList.toggle("is-active", button === target));
    const dockRect = dock.getBoundingClientRect();
    const targetRect = target.getBoundingClientRect();
    const x = targetRect.left - dockRect.left;
    const y = targetRect.top - dockRect.top;
    bubble.style.width = `${targetRect.width}px`;
    bubble.style.height = `${targetRect.height}px`;
    bubble.style.transform = `translate3d(${x}px, ${y}px, 0)`;
    if (!passive && navigator.vibrate) navigator.vibrate(12);
  }

  function updateDockVisibility() {
    const shell = document.querySelector(".aero-liquid-dock-shell");
    if (!shell) return;
    const hasToken = !!localStorage.getItem("nexus_token");
    shell.classList.toggle("is-visible", hasToken);
  }

  function boot() {
    ensureDock();
    updateDockVisibility();
    window.setInterval(updateDockVisibility, 1200);
  }

  window.NexusAeroSecurity = {
    requestOtp,
    updateDockVisibility,
    setDockActive
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot, { once: true });
  } else {
    boot();
  }
})();
