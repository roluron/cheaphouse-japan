"use client";

import { useState } from "react";
import Link from "next/link";
import { COUNTRIES } from "../lib/countries";
import { getSupabaseBrowser } from "../lib/supabase-browser";

export default function CountrySelector() {
    const [modalCountry, setModalCountry] = useState(null);
    const [email, setEmail] = useState("");
    const [submitted, setSubmitted] = useState(false);
    const [error, setError] = useState(null);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!email || !modalCountry) return;
        try {
            const supabase = getSupabaseBrowser();
            const { error: err } = await supabase
                .from("waitlist")
                .insert({ email, country_code: modalCountry.code });
            if (err && err.code === "23505") {
                setSubmitted(true); // already exists
            } else if (err) {
                setError("Something went wrong. Please try again.");
            } else {
                setSubmitted(true);
            }
        } catch {
            setError("Something went wrong. Please try again.");
        }
    };

    return (
        <>
            <div style={{
                display: "flex", gap: 8, overflowX: "auto", padding: "12px 0",
                scrollbarWidth: "none", WebkitOverflowScrolling: "touch",
            }}>
                {COUNTRIES.map((c) => (
                    c.status === "active" ? (
                        <Link
                            key={c.code}
                            href="/properties"
                            style={{
                                display: "flex", alignItems: "center", gap: 6, padding: "8px 16px",
                                borderRadius: 24, border: "1.5px solid var(--accent-blue)",
                                background: "rgba(56,189,248,0.08)", textDecoration: "none",
                                color: "var(--text-primary)", fontSize: 13, fontWeight: 500,
                                whiteSpace: "nowrap", flexShrink: 0, transition: "all 0.2s",
                                boxShadow: "0 0 12px rgba(56,189,248,0.15)",
                            }}
                        >
                            <span style={{ fontSize: 18 }}>{c.flag}</span> {c.name}
                        </Link>
                    ) : (
                        <button
                            key={c.code}
                            onClick={() => { setModalCountry(c); setSubmitted(false); setEmail(""); setError(null); }}
                            style={{
                                display: "flex", alignItems: "center", gap: 6, padding: "8px 16px",
                                borderRadius: 24, border: "1.5px dashed var(--border-subtle)",
                                background: "transparent", color: "var(--text-primary)",
                                fontSize: 13, fontWeight: 400, whiteSpace: "nowrap", flexShrink: 0,
                                cursor: "pointer", opacity: 0.5, transition: "opacity 0.2s",
                                fontFamily: "inherit",
                            }}
                            onMouseEnter={e => e.currentTarget.style.opacity = "0.8"}
                            onMouseLeave={e => e.currentTarget.style.opacity = "0.5"}
                        >
                            <span style={{ fontSize: 18 }}>{c.flag}</span> {c.name}
                            <span style={{ fontSize: 10, color: "var(--text-muted)", marginLeft: 2 }}>Soon</span>
                        </button>
                    )
                ))}
            </div>

            {/* Modal */}
            {modalCountry && (
                <div
                    style={{
                        position: "fixed", inset: 0, background: "rgba(0,0,0,0.7)", zIndex: 1000,
                        display: "flex", alignItems: "center", justifyContent: "center", padding: 24,
                    }}
                    onClick={() => setModalCountry(null)}
                >
                    <div
                        className="glass-card"
                        style={{ maxWidth: 420, width: "100%", padding: 36, textAlign: "center" }}
                        onClick={e => e.stopPropagation()}
                    >
                        <div style={{ fontSize: 56, marginBottom: 12 }}>{modalCountry.flag}</div>
                        <h2 style={{ fontSize: 24, fontWeight: 700, marginBottom: 8, fontFamily: "var(--font-display)" }}>
                            {modalCountry.name}
                        </h2>
                        <p style={{ color: "var(--text-secondary)", fontSize: 14, marginBottom: 24, lineHeight: 1.6 }}>
                            {modalCountry.tagline}
                        </p>

                        {submitted ? (
                            <div style={{ padding: 20 }}>
                                <div style={{ fontSize: 32, marginBottom: 12 }}>🎉</div>
                                <p style={{ fontSize: 15, fontWeight: 600, marginBottom: 4 }}>
                                    You&apos;re on the list for {modalCountry.name}!
                                </p>
                                <p style={{ fontSize: 13, color: "var(--text-muted)" }}>
                                    We&apos;ll email you when we launch.
                                </p>
                            </div>
                        ) : (
                            <>
                                <p style={{ fontSize: 14, color: "var(--text-secondary)", marginBottom: 20 }}>
                                    We&apos;re expanding to {modalCountry.name}. Be the first to know when we launch.
                                </p>
                                <form onSubmit={handleSubmit} style={{ display: "flex", gap: 8, marginBottom: 12 }}>
                                    <input
                                        type="email"
                                        value={email}
                                        onChange={e => setEmail(e.target.value)}
                                        placeholder="your@email.com"
                                        required
                                        style={{
                                            flex: 1, padding: "10px 14px", borderRadius: "var(--radius-md)",
                                            border: "1px solid var(--border-subtle)", background: "var(--bg-secondary)",
                                            color: "var(--text-primary)", fontSize: 14, outline: "none",
                                        }}
                                    />
                                    <button type="submit" className="btn btn-primary" style={{ padding: "10px 20px", whiteSpace: "nowrap" }}>
                                        Notify Me
                                    </button>
                                </form>
                                {error && <p style={{ fontSize: 12, color: "var(--accent-rose)" }}>{error}</p>}
                                <p style={{ fontSize: 11, color: "var(--text-muted)" }}>No spam. One email when we launch.</p>
                            </>
                        )}

                        <button
                            onClick={() => setModalCountry(null)}
                            style={{
                                marginTop: 16, background: "none", border: "none",
                                color: "var(--text-muted)", fontSize: 13, cursor: "pointer", fontFamily: "inherit",
                            }}
                        >
                            Close
                        </button>
                    </div>
                </div>
            )}
        </>
    );
}
