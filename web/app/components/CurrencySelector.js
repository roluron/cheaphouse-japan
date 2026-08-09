"use client";

import { useState, useSyncExternalStore } from "react";
import { SUPPORTED_CURRENCIES } from "../lib/currencies";

const STORAGE_KEY = "cheaphouse_currency";

function subscribe(listener) {
    window.addEventListener("currencyChange", listener);
    window.addEventListener("storage", listener);
    return () => {
        window.removeEventListener("currencyChange", listener);
        window.removeEventListener("storage", listener);
    };
}

function getSnapshot() {
    const stored = localStorage.getItem(STORAGE_KEY);
    return SUPPORTED_CURRENCIES.includes(stored) ? stored : "USD";
}

export default function CurrencySelector() {
    const currency = useSyncExternalStore(subscribe, getSnapshot, () => "USD");
    const [open, setOpen] = useState(false);

    const handleSelect = (code) => {
        localStorage.setItem(STORAGE_KEY, code);
        window.dispatchEvent(new CustomEvent("currencyChange", { detail: code }));
        setOpen(false);
    };

    return (
        <div style={{ position: "relative" }}>
            <button onClick={() => setOpen(!open)} style={{
                background: "var(--bg-secondary)", border: "1px solid var(--border-subtle)",
                borderRadius: "var(--radius-sm)", padding: "6px 10px", color: "var(--text-secondary)",
                fontSize: 12, fontWeight: 600, cursor: "pointer", fontFamily: "inherit",
            }}>
                {currency} <span style={{ fontSize: 9, opacity: 0.6 }}>▼</span>
            </button>
            {open && (
                <>
                    <div style={{ position: "fixed", inset: 0, zIndex: 98 }} onClick={() => setOpen(false)} />
                    <div style={{
                        position: "absolute", top: "calc(100% + 4px)", right: 0, background: "var(--bg-card)",
                        border: "1px solid var(--border-subtle)", borderRadius: "var(--radius-md)", padding: 4,
                        zIndex: 99, minWidth: 100, maxHeight: 280, overflowY: "auto",
                    }}>
                        {SUPPORTED_CURRENCIES.map((code) => (
                            <button key={code} onClick={() => handleSelect(code)} style={{
                                display: "block", width: "100%", textAlign: "left", padding: "6px 10px",
                                border: "none", borderRadius: 4, background: "transparent",
                                color: code === currency ? "var(--accent-gold)" : "var(--text-secondary)",
                                fontSize: 12, cursor: "pointer", fontFamily: "inherit",
                            }}>
                                {code}
                            </button>
                        ))}
                    </div>
                </>
            )}
        </div>
    );
}
