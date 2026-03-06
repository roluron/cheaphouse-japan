"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export default function Nav() {
    const pathname = usePathname();

    return (
        <nav className="nav">
            <div className="container nav-inner">
                <Link href="/" className="nav-logo">
                    <span className="text-gradient">Cheap</span>House Japan
                </Link>
                <ul className="nav-links">
                    <li>
                        <Link
                            href="/properties"
                            style={{
                                color: pathname.startsWith("/properties") ? "var(--accent-blue)" : undefined,
                            }}
                        >
                            Browse Properties
                        </Link>
                    </li>
                    <li>
                        <Link href="/#how-it-works">How It Works</Link>
                    </li>
                    <li>
                        <Link href="/#pricing">Pricing</Link>
                    </li>
                    <li>
                        <Link href="/properties" className="btn btn-primary btn-sm">
                            Start Free →
                        </Link>
                    </li>
                </ul>
            </div>
        </nav>
    );
}
