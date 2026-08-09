"use client";

import { useSyncExternalStore } from "react";

function subscribe(listener) {
    window.addEventListener("themeChange", listener);
    window.addEventListener("storage", listener);
    return () => {
        window.removeEventListener("themeChange", listener);
        window.removeEventListener("storage", listener);
    };
}

function getSnapshot() {
    return localStorage.getItem("ch-theme") || "dark";
}

export default function ThemeToggle() {
    const theme = useSyncExternalStore(subscribe, getSnapshot, () => "dark");
    const isDark = theme === "dark";

    const toggle = () => {
        const next = isDark ? "light" : "dark";
        localStorage.setItem("ch-theme", next);
        document.documentElement.setAttribute("data-theme", next);
        window.dispatchEvent(new Event("themeChange"));
    };

    return (
        <button onClick={toggle} aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"} className="theme-toggle">
            <div className="theme-toggle-track">
                <svg className={`theme-icon theme-icon-sun ${isDark ? "theme-icon-hidden" : "theme-icon-visible"}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
                    <circle cx="12" cy="12" r="5" />
                    <path d="M12 1v2m0 18v2M4.2 4.2l1.4 1.4m12.8 12.8 1.4 1.4M1 12h2m18 0h2M4.2 19.8l1.4-1.4M18.4 5.6l1.4-1.4" />
                </svg>
                <svg className={`theme-icon theme-icon-moon ${isDark ? "theme-icon-visible" : "theme-icon-hidden"}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
                </svg>
            </div>
        </button>
    );
}
