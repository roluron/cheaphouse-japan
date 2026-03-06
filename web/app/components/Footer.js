import Link from "next/link";

export default function Footer() {
    return (
        <footer className="footer">
            <div className="container">
                <div className="footer-grid">
                    <div>
                        <h4>
                            <span className="text-gradient">Cheap</span>House Japan
                        </h4>
                        <p style={{ marginBottom: 16, lineHeight: 1.7 }}>
                            The decision platform for international buyers.
                            Discover, compare, and decide on affordable homes in Japan
                            with hazard intelligence and honest insights.
                        </p>
                        <p style={{ fontSize: 12, color: "var(--text-muted)" }}>
                            © {new Date().getFullYear()} CheapHouse Japan
                        </p>
                    </div>

                    <div>
                        <h4>Platform</h4>
                        <Link href="/properties">Browse Properties</Link>
                        <Link href="/#how-it-works">How It Works</Link>
                        <Link href="/#pricing">Pricing</Link>
                        <a href="#">FAQ</a>
                    </div>

                    <div>
                        <h4>Resources</h4>
                        <a href="#">Buying Guide</a>
                        <a href="#">Hazard Maps</a>
                        <a href="#">Renovation FAQ</a>
                        <a href="#">Visa & Legal</a>
                    </div>

                    <div>
                        <h4>Company</h4>
                        <a href="#">About</a>
                        <a href="#">Contact</a>
                        <a href="#">Privacy Policy</a>
                        <a href="#">Terms of Service</a>
                    </div>
                </div>
            </div>
        </footer>
    );
}
