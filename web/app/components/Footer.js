import Link from "next/link";

export default function Footer() {
    return (
        <footer className="footer">
            <div className="container">
                <div className="footer-grid">
                    <div>
                        <div style={{ fontFamily: "var(--font-serif)", fontSize: 18, color: "var(--text-primary)", marginBottom: 16, letterSpacing: "-0.02em" }}>
                            CheapHouse
                        </div>
                        <p style={{ lineHeight: 1.7, marginBottom: 16, maxWidth: 280 }}>
                            The decision platform for international home buyers. Honest data, real insights.
                        </p>
                        <p style={{ fontSize: 12, color: "var(--text-muted)" }}>
                            &copy; {new Date().getFullYear()} CheapHouse
                        </p>
                    </div>

                    <div>
                        <h4>Platform</h4>
                        <Link href="/properties">Properties</Link>
                        <Link href="/quiz">Quiz</Link>
                        <Link href="/pricing">Pricing</Link>
                    </div>

                    <div>
                        <h4>Account</h4>
                        <Link href="/login">Login</Link>
                        <Link href="/signup">Sign Up</Link>
                        <Link href="/saved">Saved</Link>
                    </div>

                    <div>
                        <h4>Countries</h4>
                        <Link href="/properties">Japan</Link>
                        <span style={{ color: "var(--text-muted)" }}>France — Soon</span>
                        <span style={{ color: "var(--text-muted)", display: "block", marginBottom: 10 }}>Italy — Soon</span>
                        <span style={{ color: "var(--text-muted)", display: "block", marginBottom: 10 }}>Portugal — Soon</span>
                    </div>
                </div>
            </div>
        </footer>
    );
}
