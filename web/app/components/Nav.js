"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import CurrencySelector from "./CurrencySelector";
import ThemeToggle from "./ThemeToggle";

export default function Nav() {
    const pathname = usePathname();
    const [menuOpen, setMenuOpen] = useState(false);
    const isActive = (path) => pathname === path || pathname.startsWith(`${path}/`);

    return (
        <nav className="nav">
            <div className="container nav-inner">
                <Link href="/" className="nav-logo">CheapHouse <small>Japan</small></Link>
                <button className="nav-hamburger" onClick={() => setMenuOpen(!menuOpen)} aria-label="Toggle menu">
                    {menuOpen ? "×" : "≡"}
                </button>
                <ul className={`nav-links ${menuOpen ? "nav-open" : ""}`}>
                    <li><Link className={isActive("/properties") ? "active" : ""} href="/properties" onClick={() => setMenuOpen(false)}>Verified listings</Link></li>
                    <li><Link className={isActive("/verify") ? "active" : ""} href="/verify" onClick={() => setMenuOpen(false)}>Check a listing</Link></li>
                    <li><CurrencySelector /></li>
                    <li><ThemeToggle /></li>
                </ul>
            </div>
        </nav>
    );
}
