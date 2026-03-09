"use client";

import Link from "next/link";

export default function PropertiesError({ error, reset }) {
    return (
        <div style={{ paddingTop: 80, minHeight: "100vh" }}>
            <div className="container" style={{ paddingTop: 80, textAlign: "center" }}>
                <div style={{ fontSize: 14, color: "var(--text-muted)", marginBottom: 16 }}>—</div>
                <h2 style={{ fontSize: 24, marginBottom: 8 }}>Something went wrong</h2>
                <p style={{ color: "var(--text-secondary)", fontSize: 14, marginBottom: 24 }}>
                    {error?.message || "We couldn't load the properties. Please try again."}
                </p>
                <div style={{ display: "flex", gap: 12, justifyContent: "center" }}>
                    <button onClick={reset} className="btn btn-primary" style={{ padding: "10px 24px" }}>
                        Try Again
                    </button>
                    <Link href="/" className="btn btn-secondary" style={{ padding: "10px 24px" }}>
                        Go Home
                    </Link>
                </div>
            </div>
        </div>
    );
}
