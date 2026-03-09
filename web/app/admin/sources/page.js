"use client";

import { useState, useEffect } from "react";
import { getSupabaseBrowser } from "../../lib/supabase-browser";

export default function SourcesPage() {
    const [sources, setSources] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetch = async () => {
            const supabase = getSupabaseBrowser();
            const { data } = await supabase
                .from("sources")
                .select("*, scrape_runs(id, status, listings_found, started_at, finished_at)")
                .order("name");
            setSources(data || []);
            setLoading(false);
        };
        fetch();
    }, []);

    const toggleActive = async (id, currentActive) => {
        const supabase = getSupabaseBrowser();
        await supabase.from("sources").update({ is_active: !currentActive }).eq("id", id);
        setSources(prev => prev.map(s => s.id === id ? { ...s, is_active: !currentActive } : s));
    };

    return (
        <div>
            <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 24 }}>Sources</h1>

            {loading ? (
                <div style={{ padding: 40, textAlign: "center", color: "var(--text-muted)" }}>Loading...</div>
            ) : (
                <div style={{ display: "grid", gap: 16 }}>
                    {sources.map(s => {
                        const runs = (s.scrape_runs || []).sort((a, b) => new Date(b.started_at) - new Date(a.started_at));
                        const lastRun = runs[0];
                        return (
                            <div key={s.id} className="glass-card" style={{ padding: 20 }}>
                                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
                                    <div>
                                        <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 4 }}>{s.name}</h3>
                                        <div style={{ fontSize: 12, color: "var(--text-muted)" }}>{s.base_url}</div>
                                    </div>
                                    <button
                                        onClick={() => toggleActive(s.id, s.is_active)}
                                        style={{
                                            background: s.is_active ? "rgba(34,197,94,0.15)" : "rgba(239,68,68,0.15)",
                                            color: s.is_active ? "var(--accent-green)" : "var(--accent-rose)",
                                            border: "none", borderRadius: 4, padding: "6px 12px", cursor: "pointer", fontSize: 12,
                                        }}
                                    >
                                        {s.is_active ? "Active" : "Inactive"}
                                    </button>
                                </div>
                                {lastRun ? (
                                    <div style={{ fontSize: 12, color: "var(--text-secondary)", display: "flex", gap: 16 }}>
                                        <span>Last run: {new Date(lastRun.started_at).toLocaleDateString()}</span>
                                        <span>Status: <span className={`badge ${lastRun.status === "completed" ? "badge-green" : "badge-rose"}`}>{lastRun.status}</span></span>
                                        <span>Found: {lastRun.listings_found || 0}</span>
                                    </div>
                                ) : (
                                    <div style={{ fontSize: 12, color: "var(--text-muted)" }}>No runs yet</div>
                                )}
                                {runs.length > 1 && (
                                    <details style={{ marginTop: 8 }}>
                                        <summary style={{ fontSize: 12, color: "var(--text-muted)", cursor: "pointer" }}>
                                            History ({runs.length} runs)
                                        </summary>
                                        <div style={{ marginTop: 8, fontSize: 11 }}>
                                            {runs.slice(0, 5).map(r => (
                                                <div key={r.id} style={{ padding: "4px 0", color: "var(--text-muted)" }}>
                                                    {new Date(r.started_at).toLocaleDateString()} — {r.status} — {r.listings_found || 0} found
                                                </div>
                                            ))}
                                        </div>
                                    </details>
                                )}
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}
