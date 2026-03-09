import Link from "next/link";

export default function NotFound() {
    return (
        <div style={{
            minHeight: "100vh", display: "flex", flexDirection: "column",
            alignItems: "center", justifyContent: "center", background: "var(--bg-primary)", padding: 24,
        }}>
            <div style={{ fontSize: 80, marginBottom: 16, opacity: 0.6 }}>🏚️</div>
            <h1 style={{ fontSize: 48, fontWeight: 800, fontFamily: "var(--font-display)", marginBottom: 8 }}>404</h1>
            <p style={{ color: "var(--text-secondary)", fontSize: 16, marginBottom: 32, textAlign: "center" }}>
                This property seems to have vanished — even by Japanese standards.
            </p>
            <div style={{ display: "flex", gap: 12 }}>
                <Link href="/" className="btn btn-secondary" style={{ padding: "10px 24px" }}>
                    Go Home
                </Link>
                <Link href="/properties" className="btn btn-primary" style={{ padding: "10px 24px" }}>
                    Browse Properties
                </Link>
            </div>
        </div>
    );
}
