"use client";

import { useState, useEffect } from "react";
import { SUPPORTED_CURRENCIES } from "../lib/currencies";

const STORAGE_KEY = "cheaphouse_currency";

export default function CurrencySelector() {
    const [currency, setCurrency] = useState("USD");
    const [open, setOpen] = useState(false);

    useEffect(() => {
        try {
            const stored = localStorage.getItem(STORAGE_KEY);
            if (stored && SUPPORTED_CURRENCIES.includes(stored)) setCurrency(stored);
        } catch { }
    }, []);

    const handleSelect = (code) => {
        setCurrency(code);
        setOpen(false);
        try { localStorage.setItem(STORAGE_KEY, code); } catch { }
        // Dispatch event for other components to react
        window.dispatchEvent(new CustomEvent("currencyChange", { detail: code }));
    };

    return (
        <div style={{ position: "relative" }}>
            <button
                onClick={() => setOpen(!open)}
                style={{
                    background: "var(--bg-secondary)", border: "1px solid var(--border-subtle)",
                    borderRadius: "var(--radius-sm)", padding: "6px 10px",
                    color: "var(--text-secondary)", fontSize: 12, fontWeight: 600,
                    cursor: "pointer", fontFamily: "inherit",
                    display: "flex", alignItems: "center", gap: 4,
                }}
            >
                {currency} <span style={{ fontSize: 9, opacity: 0.6 }}>▼</span>
            </button>

            {open && (
                <>
                    <div style={{ position: "fixed", inset: 0, zIndex: 98 }} onClick={() => setOpen(false)} />
                    <div style={{
                        position: "absolute", top: "calc(100% + 4px)", right: 0,
                        background: "var(--bg-card)", border: "1px solid var(--border-subtle)",
                        borderRadius: "var(--radius-md)", padding: 4, zIndex: 99,
                        minWidth: 100, maxHeight: 280, overflowY: "auto",
                        boxShadow: "var(--shadow-elevated)",
                    }}>
                        {SUPPORTED_CURRENCIES.map(code => (
                            <button
                                key={code}
                                onClick={() => handleSelect(code)}
                                style={{
                                    display: "block", width: "100%", textAlign: "left",
                                    padding: "6px 10px", border: "none", borderRadius: 4,
                                    background: code === currency ? "var(--bg-accent)" : "transparent",
                                    color: code === currency ? "var(--accent-blue)" : "var(--text-secondary)",
                                    fontSize: 12, fontWeight: code === currency ? 600 : 400,
                                    cursor: "pointer", fontFamily: "inherit",
                                }}
                            >
                                {code}
                            </button>
                        ))}
                    </div>
                </>
            )}
        </div>
    );
}
