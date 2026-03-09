import { getSupabaseServer } from "../lib/supabase-server";

export default async function AdminDashboard() {
    const supabase = await getSupabaseServer();

    const [propRes, userRes, runsRes] = await Promise.all([
        supabase.from("properties").select("admin_status, is_published", { count: "exact" }),
        supabase.from("user_profiles").select("subscription_status", { count: "exact" }),
        supabase.from("scrape_runs").select("*").order("started_at", { ascending: false }).limit(10),
    ]);

    const props = propRes.data || [];
    const users = userRes.data || [];
    const runs = runsRes.data || [];

    const stats = {
        total: props.length,
        pending: props.filter(p => p.admin_status === "pending_review").length,
        approved: props.filter(p => p.admin_status === "approved").length,
        published: props.filter(p => p.is_published).length,
        totalUsers: users.length,
        activeSubscribers: users.filter(u => u.subscription_status === "active").length,
    };

    return (
        <div>
            <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 32 }}>Dashboard</h1>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16, marginBottom: 40 }}>
                {[
                    { label: "Total Properties", value: stats.total },
                    { label: "Pending Review", value: stats.pending },
                    { label: "Approved", value: stats.approved },
                    { label: "Published", value: stats.published },
                    { label: "Total Users", value: stats.totalUsers },
                    { label: "Active Subscribers", value: stats.activeSubscribers },
                ].map(s => (
                    <div key={s.label} className="glass-card" style={{ padding: 20 }}>
                        <div style={{ fontSize: 28, fontWeight: 600, fontFamily: "var(--font-display)" }}>{s.value}</div>
                        <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 4, letterSpacing: "0.05em", textTransform: "uppercase" }}>{s.label}</div>
                    </div>
                ))}
            </div>

            <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 16 }}>Recent Scrape Runs</h2>
            <div className="glass-card" style={{ padding: 0, overflow: "hidden" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                    <thead>
                        <tr style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                            <th style={{ padding: "10px 16px", textAlign: "left", color: "var(--text-muted)" }}>Source</th>
                            <th style={{ padding: "10px 16px", textAlign: "left", color: "var(--text-muted)" }}>Status</th>
                            <th style={{ padding: "10px 16px", textAlign: "left", color: "var(--text-muted)" }}>Count</th>
                            <th style={{ padding: "10px 16px", textAlign: "left", color: "var(--text-muted)" }}>Started</th>
                        </tr>
                    </thead>
                    <tbody>
                        {runs.map(r => (
                            <tr key={r.id} style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                                <td style={{ padding: "10px 16px" }}>{r.source_id || "—"}</td>
                                <td style={{ padding: "10px 16px" }}>
                                    <span className={`badge ${r.status === "completed" ? "badge-green" : r.status === "failed" ? "badge-rose" : "badge-amber"}`}>
                                        {r.status}
                                    </span>
                                </td>
                                <td style={{ padding: "10px 16px" }}>{r.listings_found || 0}</td>
                                <td style={{ padding: "10px 16px", color: "var(--text-muted)" }}>
                                    {r.started_at ? new Date(r.started_at).toLocaleString() : "—"}
                                </td>
                            </tr>
                        ))}
                        {runs.length === 0 && (
                            <tr><td colSpan={4} style={{ padding: 20, textAlign: "center", color: "var(--text-muted)" }}>No scrape runs yet</td></tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
