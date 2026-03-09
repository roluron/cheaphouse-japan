"use client";

import { useState, useEffect } from "react";
import { getSupabaseBrowser } from "../../lib/supabase-browser";

export default function ReviewPage() {
    const [properties, setProperties] = useState([]);
    const [expanded, setExpanded] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => { fetchQueue(); }, []);

    const fetchQueue = async () => {
        setLoading(true);
        const supabase = getSupabaseBrowser();
        const { data } = await supabase
            .from("properties")
            .select("*")
            .eq("admin_status", "pending_review")
            .order("quality_score", { ascending: false })
            .limit(50);
        setProperties(data || []);
        setLoading(false);
    };

    const handleAction = async (id, action) => {
        const supabase = getSupabaseBrowser();
        const updates = action === "approve"
            ? { admin_status: "approved", is_published: true }
            : { admin_status: "rejected", is_published: false };
        await supabase.from("properties").update(updates).eq("id", id);
        setProperties(prev => prev.filter(p => p.id !== id));
    };

    const handleBulkApprove = async () => {
        const supabase = getSupabaseBrowser();
        const toApprove = properties.filter(p => (p.quality_score || 0) > 0.7);
        for (const p of toApprove) {
            await supabase.from("properties").update({ admin_status: "approved", is_published: true }).eq("id", p.id);
        }
        fetchQueue();
    };

    return (
        <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
                <h1 style={{ fontSize: 24, fontWeight: 700 }}>Review Queue ({properties.length})</h1>
                <button onClick={handleBulkApprove} className="btn btn-primary" style={{ padding: "8px 16px", fontSize: 13 }}>
                    Approve All QS &gt; 70%
                </button>
            </div>

            {loading ? (
                <div style={{ padding: 40, textAlign: "center", color: "var(--text-muted)" }}>Loading...</div>
            ) : properties.length === 0 ? (
                <div className="glass-card" style={{ padding: 40, textAlign: "center", color: "var(--text-muted)" }}>
                    No properties pending review
                </div>
            ) : (
                <div className="glass-card" style={{ padding: 0, overflow: "hidden" }}>
                    <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                        <thead>
                            <tr style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                                <th style={{ padding: "10px 12px", textAlign: "left", color: "var(--text-muted)" }}>Image</th>
                                <th style={{ padding: "10px 12px", textAlign: "left", color: "var(--text-muted)" }}>Title</th>
                                <th style={{ padding: "10px 12px", textAlign: "left", color: "var(--text-muted)" }}>Prefecture</th>
                                <th style={{ padding: "10px 12px", textAlign: "left", color: "var(--text-muted)" }}>Price</th>
                                <th style={{ padding: "10px 12px", textAlign: "left", color: "var(--text-muted)" }}>QS</th>
                                <th style={{ padding: "10px 12px", textAlign: "left", color: "var(--text-muted)" }}>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {properties.map(p => (
                                <tr key={p.id} style={{ borderBottom: "1px solid var(--border-subtle)", cursor: "pointer" }} onClick={() => setExpanded(expanded === p.id ? null : p.id)}>
                                    <td style={{ padding: "8px 12px" }}>
                                        {p.thumbnail_url ? (
                                            <img src={p.thumbnail_url} alt="" style={{ width: 48, height: 36, objectFit: "cover", borderRadius: 4 }} />
                                        ) : <div style={{ width: 48, height: 36, background: "var(--bg-secondary)", borderRadius: 4 }} />}
                                    </td>
                                    <td style={{ padding: "8px 12px", maxWidth: 200, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                                        {p.title_en || p.original_title || "Untitled"}
                                    </td>
                                    <td style={{ padding: "8px 12px", color: "var(--text-secondary)" }}>{p.prefecture || "—"}</td>
                                    <td style={{ padding: "8px 12px" }}>{p.price_jpy ? `¥${p.price_jpy.toLocaleString()}` : "—"}</td>
                                    <td style={{ padding: "8px 12px" }}>
                                        <span style={{ color: (p.quality_score || 0) > 0.7 ? "var(--accent-green)" : "var(--text-muted)" }}>
                                            {Math.round((p.quality_score || 0) * 100)}%
                                        </span>
                                    </td>
                                    <td style={{ padding: "8px 12px" }} onClick={e => e.stopPropagation()}>
                                        <div style={{ display: "flex", gap: 6 }}>
                                            <button onClick={() => handleAction(p.id, "approve")} style={{ background: "rgba(34,197,94,0.15)", color: "var(--accent-green)", border: "none", borderRadius: 4, padding: "4px 10px", cursor: "pointer", fontSize: 12 }}>
                                                ✓ Approve
                                            </button>
                                            <button onClick={() => handleAction(p.id, "reject")} style={{ background: "rgba(239,68,68,0.15)", color: "var(--accent-rose)", border: "none", borderRadius: 4, padding: "4px 10px", cursor: "pointer", fontSize: 12 }}>
                                                ✕ Reject
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
}
