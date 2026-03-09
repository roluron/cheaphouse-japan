import { redirect } from "next/navigation";
import { getSupabaseServer } from "../lib/supabase-server";
import { getCurrentUser } from "../lib/auth";

const ADMIN_EMAILS = ["roluron@gmail.com"];

export default async function AdminLayout({ children }) {
    const user = await getCurrentUser();
    if (!user || !ADMIN_EMAILS.includes(user.email)) {
        redirect("/");
    }

    return (
        <div style={{ display: "flex", minHeight: "100vh", background: "var(--bg-primary)" }}>
            {/* Sidebar */}
            <aside style={{
                width: 220, padding: "24px 16px", borderRight: "1px solid var(--border-subtle)",
                display: "flex", flexDirection: "column", gap: 4, flexShrink: 0,
            }}>
                <div style={{ fontSize: 16, fontWeight: 700, fontFamily: "var(--font-display)", marginBottom: 24, padding: "0 12px" }}>
                    <span className="text-gradient">Admin</span>
                </div>
                <a href="/admin" style={{ padding: "10px 12px", borderRadius: "var(--radius-md)", fontSize: 14, color: "var(--text-secondary)", textDecoration: "none" }}>Dashboard</a>
                <a href="/admin/review" style={{ padding: "10px 12px", borderRadius: "var(--radius-md)", fontSize: 14, color: "var(--text-secondary)", textDecoration: "none" }}>Review Queue</a>
                <a href="/admin/sources" style={{ padding: "10px 12px", borderRadius: "var(--radius-md)", fontSize: 14, color: "var(--text-secondary)", textDecoration: "none" }}>Sources</a>
                <div style={{ flex: 1 }} />
                <a href="/" style={{ padding: "10px 12px", fontSize: 13, color: "var(--text-muted)", textDecoration: "none" }}>← Back to site</a>
            </aside>

            {/* Main content */}
            <main style={{ flex: 1, padding: 32, overflowY: "auto" }}>
                {children}
            </main>
        </div>
    );
}
