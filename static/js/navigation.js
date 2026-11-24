document.addEventListener("DOMContentLoaded", () => {
    const toggle = document.querySelector(".taigo-menu-toggle");
    const menu = document.querySelector(".taigo-dropdown");

    if (!toggle || !menu) return;

    function setMenuOpen(open) {
        menu.classList.toggle("open", open);
        menu.inert = !open;

        toggle.setAttribute("aria-expanded", String(open));
        toggle.setAttribute(
            "aria-label",
            open ? "Закрыть меню" : "Открыть меню"
        );

        toggle.innerHTML = open
            ? '<i data-lucide="x"></i>'
            : '<i data-lucide="menu"></i>';

        if (window.lucide) {
            lucide.createIcons();
        }
    }

    toggle.addEventListener("click", event => {
        event.stopPropagation();
        setMenuOpen(!menu.classList.contains("open"));
    });

    document.addEventListener("click", event => {
        if (
            !menu.contains(event.target) &&
            !toggle.contains(event.target)
        ) {
            setMenuOpen(false);
        }
    });

    document.addEventListener("keydown", event => {
        if (event.key === "Escape") {
            setMenuOpen(false);
            toggle.focus();
        }
    });

    setMenuOpen(false);
});