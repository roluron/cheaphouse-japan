"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, useEffect } from "react";
import CurrencySelector from "./CurrencySelector";
import ThemeToggle from "./ThemeToggle";
import { getSupabaseBrowser } from "../lib/supabase-browser";

export default function Nav() {
    const pathname = usePathname();
    const [menuOpen, setMenuOpen] = useState(false);
    const [user, setUser] = useState(null);

    useEffect(() => {
        try {
            const supabase = getSupabaseBrowser();
            supabase.auth.getUser().then(({ data }) => setUser(data?.user || null));
            const { data: { subscription } } = supabase.auth.onAuthStateChange((_e, session) => {
                setUser(session?.user || null);
            });
            return () => subscription?.unsubscribe();
        } catch { /* supabase not configured */ }
    }, []);

    const handleLogout = async () => {
        const supabase = getSupabaseBrowser();
        await supabase.auth.signOut();
        setUser(null);
        window.location.href = "/";
    };

    const isActive = (path) => pathname === path || pathname.startsWith(path + "/");

    return (
        <nav className="nav">
            <div className="container nav-inner">
                <Link href="/" className="nav-logo">
                    CheapHouse
                </Link>

                <button
                    className="nav-hamburger"
                    onClick={() => setMenuOpen(!menuOpen)}
                    aria-label="Menu"
                    style={{
                        display: "none", background: "none", border: "none", color: "var(--text-primary)",
                        fontSize: 20, cursor: "pointer", padding: 8,
                    }}
                >
                    {menuOpen ? "\u00D7" : "\u2261"}
                </button>

                <ul className={`nav-links ${menuOpen ? "nav-open" : ""}`}>
                    <li>
                        <Link
                            href="/properties"
                            style={{ color: isActive("/properties") ? "var(--text-primary)" : undefined }}
                            onClick={() => setMenuOpen(false)}
                        >
                            Properties
                        </Link>
                    </li>
                    <li>
                        <Link
                            href="/quiz"
                            style={{ color: isActive("/quiz") ? "var(--text-primary)" : undefined }}
                            onClick={() => setMenuOpen(false)}
                        >
                            Quiz
                        </Link>
                    </li>
                    <li>
                        <Link
                            href="/pricing"
                            style={{ color: isActive("/pricing") ? "var(--text-primary)" : undefined }}
                            onClick={() => setMenuOpen(false)}
                        >
                            Pricing
                        </Link>
                    </li>
                    <li><CurrencySelector /></li>
                    <li><ThemeToggle /></li>
                    {user ? (
                        <>
                            <li>
                                <Link
                                    href="/account"
                                    style={{ color: isActive("/account") ? "var(--text-primary)" : undefined }}
                                    onClick={() => setMenuOpen(false)}
                                >
                                    Account
                                </Link>
                            </li>
                            <li>
                                <button
                                    onClick={handleLogout}
                                    style={{
                                        background: "none", border: "none", cursor: "pointer",
                                        font: "inherit", fontSize: 11, fontWeight: 500,
                                        color: "var(--text-muted)", textTransform: "uppercase",
                                        letterSpacing: "0.1em",
                                    }}
                                >
                                    Logout
                                </button>
                            </li>
                        </>
                    ) : (
                        <>
                            <li>
                                <Link href="/login" onClick={() => setMenuOpen(false)}>
                                    Login
                                </Link>
                            </li>
                            <li>
                                <Link
                                    href="/signup"
                                    onClick={() => setMenuOpen(false)}
                                    style={{
                                        background: "var(--accent-gold)", color: "#060608",
                                        padding: "8px 18px", borderRadius: "var(--radius-sm)",
                                        fontSize: 11, fontWeight: 600, letterSpacing: "0.08em",
                                        textTransform: "uppercase",
                                    }}
                                >
                                    Sign Up
                                </Link>
                            </li>
                        </>
                    )}
                </ul>
            </div>
        </nav>
    );
}
