document.addEventListener("DOMContentLoaded", () => {
    console.log("Nexus UI Builder Init...");
    // Jeśli tabsData istnieje w nexus_ui_builder, wymuszamy aktualizację
    if (typeof tabsData !== "undefined") {
        for (const [id, html] of Object.entries(tabsData)) {
            let tab = document.getElementById(id);
            if (tab) {
                tab.innerHTML = html;
                console.log("Zaktualizowano zakładkę: " + id);
            }
        }
    }
});
