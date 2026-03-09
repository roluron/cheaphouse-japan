"use client";

import { useState } from "react";
import Link from "next/link";
import { getSupabaseBrowser } from "../lib/supabase-browser";

export default function LoginPage() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(false);

    const handleLogin = async (e) => {
        e.preventDefault();
        setError(null);
        setLoading(true);
        try {
            const supabase = getSupabaseBrowser();
            const { error } = await supabase.auth.signInWithPassword({ email, password });
            if (error) throw error;
            window.location.href = "/properties";
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleGoogleLogin = async () => {
        const supabase = getSupabaseBrowser();
        await supabase.auth.signInWithOAuth({
            provider: "google",
            options: { redirectTo: `${window.location.origin}/auth/callback` },
        });
    };

    return (
        <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", padding: 24, background: "var(--bg-primary)" }}>
            <div className="glass-card" style={{ width: "100%", maxWidth: 420, padding: 40 }}>
                <div style={{ textAlign: "center", marginBottom: 32 }}>
                    <Link href="/" style={{ textDecoration: "none" }}>
                        <h1 style={{ fontSize: 24, fontFamily: "var(--font-display)" }}>
                            <span className="text-gradient">Cheap</span>House
                        </h1>
                    </Link>
                    <p style={{ color: "var(--text-muted)", fontSize: 14, marginTop: 8 }}>Sign in to your account</p>
                </div>

                {error && (
                    <div style={{ background: "rgba(239,68,68,0.1)", border: "1px solid var(--accent-rose)", borderRadius: "var(--radius-md)", padding: "12px 16px", marginBottom: 20, fontSize: 13, color: "var(--accent-rose)" }}>
                        {error}
                    </div>
                )}

                <form onSubmit={handleLogin}>
                    <div style={{ marginBottom: 16 }}>
                        <label style={{ display: "block", fontSize: 13, color: "var(--text-secondary)", marginBottom: 6 }}>Email</label>
                        <input
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            required
                            placeholder="you@example.com"
                            style={{
                                width: "100%", padding: "10px 14px", borderRadius: "var(--radius-md)",
                                border: "1px solid var(--border-subtle)", background: "var(--bg-secondary)",
                                color: "var(--text-primary)", fontSize: 14, outline: "none",
                            }}
                        />
                    </div>
                    <div style={{ marginBottom: 24 }}>
                        <label style={{ display: "block", fontSize: 13, color: "var(--text-secondary)", marginBottom: 6 }}>Password</label>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                            placeholder="••••••••"
                            style={{
                                width: "100%", padding: "10px 14px", borderRadius: "var(--radius-md)",
                                border: "1px solid var(--border-subtle)", background: "var(--bg-secondary)",
                                color: "var(--text-primary)", fontSize: 14, outline: "none",
                            }}
                        />
                    </div>
                    <button
                        type="submit"
                        disabled={loading}
                        className="btn btn-primary"
                        style={{ width: "100%", padding: "12px 0", fontSize: 15, marginBottom: 12, opacity: loading ? 0.7 : 1 }}
                    >
                        {loading ? "Signing in..." : "Sign In"}
                    </button>
                </form>

                <div style={{ position: "relative", textAlign: "center", margin: "20px 0" }}>
                    <div style={{ position: "absolute", top: "50%", left: 0, right: 0, height: 1, background: "var(--border-subtle)" }} />
                    <span style={{ position: "relative", background: "var(--bg-tertiary)", padding: "0 12px", fontSize: 12, color: "var(--text-muted)" }}>or</span>
                </div>

                <button
                    onClick={handleGoogleLogin}
                    className="btn btn-secondary"
                    style={{ width: "100%", padding: "12px 0", fontSize: 14, display: "flex", alignItems: "center", justifyContent: "center", gap: 8 }}
                >
                    <svg width="18" height="18" viewBox="0 0 24 24"><path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4" /><path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" /><path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" /><path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" /></svg>
                    Sign in with Google
                </button>

                <p style={{ textAlign: "center", fontSize: 13, color: "var(--text-muted)", marginTop: 24 }}>
                    Don&apos;t have an account?{" "}
                    <Link href="/signup" style={{ color: "var(--accent-blue)" }}>Sign up</Link>
                </p>
            </div>
        </div>
    );
}
