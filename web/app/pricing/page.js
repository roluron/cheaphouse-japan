import Nav from "../components/Nav";
import Footer from "../components/Footer";
import Link from "next/link";

export const metadata = {
    title: "Pricing — CheapHouse",
    description: "Access unlimited property listings, hazard data, and personalized match scores.",
};

const TIERS = [
    {
        name: "Free",
        price: "$0",
        period: "forever",
        description: "Get started exploring Japanese properties",
        features: [
            "Browse up to 10 properties per day",
            "Basic filters (price, prefecture)",
            "Limited property details",
            "Basic hazard data",
        ],
        cta: "Start Free",
        ctaLink: "/signup",
        highlight: false,
    },
    {
        name: "Pro",
        price: "$10",
        period: "/month",
        description: "Full access to all data and features",
        features: [
            "Unlimited property access",
            "All filters (lifestyle, hazard, condition)",
            'Full "What to Know" reports',
            "Save & Compare properties",
            "Personalized match scores",
            "Priority support",
        ],
        cta: "Subscribe Now",
        ctaLink: "/api/stripe/checkout",
        highlight: true,
    },
];

const FAQ = [
    { q: "Can I cancel anytime?", a: "Yes, cancel your subscription anytime from your account page. You'll retain access until the end of your billing period." },
    { q: "What payment methods do you accept?", a: "We accept all major credit cards, Apple Pay, and Google Pay through Stripe." },
    { q: "Is there a free trial?", a: "The free tier gives you access to browse properties. Upgrade to Pro when you're ready for full data access." },
    { q: "What happens to my saved properties if I cancel?", a: "Your saved properties remain in your account. You can re-subscribe anytime to access them again." },
];

export default function PricingPage() {
    return (
        <>
            <Nav />
            <main style={{ paddingTop: 80, minHeight: "100vh" }}>
                <div className="container" style={{ paddingTop: 64, paddingBottom: 80, textAlign: "center" }}>
                    <h1 style={{ fontSize: "clamp(32px, 5vw, 44px)", fontWeight: 400, marginBottom: 12 }}>
                        Simple, Transparent Pricing
                    </h1>
                    <p style={{ color: "var(--text-secondary)", fontSize: 16, maxWidth: 480, margin: "0 auto 48px" }}>
                        Everything you need to find your dream home in Japan.
                    </p>

                    {/* Tier cards */}
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24, maxWidth: 740, margin: "0 auto 80px" }}>
                        {TIERS.map((tier) => (
                            <div
                                key={tier.name}
                                className="glass-card"
                                style={{
                                    padding: 36,
                                    textAlign: "left",
                                    border: tier.highlight ? "1px solid var(--accent-gold)" : undefined,
                                    position: "relative",
                                }}
                            >
                                {tier.highlight && (
                                    <div style={{
                                        position: "absolute", top: -12, left: "50%", transform: "translateX(-50%)",
                                        background: "var(--gradient-primary)", color: "#000", fontSize: 11,
                                        fontWeight: 700, padding: "4px 16px", borderRadius: 20,
                                    }}>
                                        MOST POPULAR
                                    </div>
                                )}
                                <h3 style={{ fontSize: 20, fontWeight: 700, marginBottom: 8 }}>{tier.name}</h3>
                                <div style={{ marginBottom: 8 }}>
                                    <span style={{ fontSize: 40, fontWeight: 800, fontFamily: "var(--font-display)" }}>{tier.price}</span>
                                    <span style={{ color: "var(--text-muted)", fontSize: 14 }}>{tier.period}</span>
                                </div>
                                <p style={{ color: "var(--text-secondary)", fontSize: 13, marginBottom: 24 }}>{tier.description}</p>

                                <ul style={{ listStyle: "none", marginBottom: 32 }}>
                                    {tier.features.map((f) => (
                                        <li key={f} style={{ fontSize: 13, color: "var(--text-secondary)", padding: "6px 0", display: "flex", alignItems: "flex-start", gap: 8 }}>
                                            <span style={{ color: "var(--accent-gold)", flexShrink: 0, fontSize: 12 }}>&bull;</span>
                                            {f}
                                        </li>
                                    ))}
                                </ul>

                                {tier.highlight ? (
                                    <form action="/api/stripe/checkout" method="POST" style={{ margin: 0 }}>
                                        <button type="submit" className="btn btn-primary" style={{ width: "100%", padding: "12px 0" }}>
                                            {tier.cta}
                                        </button>
                                    </form>
                                ) : (
                                    <Link href={tier.ctaLink} className="btn btn-secondary" style={{ width: "100%", padding: "12px 0", display: "block", textAlign: "center" }}>
                                        {tier.cta}
                                    </Link>
                                )}
                            </div>
                        ))}
                    </div>

                    {/* FAQ */}
                    <div style={{ maxWidth: 640, margin: "0 auto", textAlign: "left" }}>
                        <h2 style={{ fontSize: 28, fontWeight: 700, marginBottom: 32, textAlign: "center", fontFamily: "var(--font-display)" }}>
                            Frequently Asked Questions
                        </h2>
                        {FAQ.map((item) => (
                            <div key={item.q} className="glass-card" style={{ padding: 24, marginBottom: 12 }}>
                                <h4 style={{ fontSize: 15, fontWeight: 600, marginBottom: 8 }}>{item.q}</h4>
                                <p style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.6 }}>{item.a}</p>
                            </div>
                        ))}
                    </div>
                </div>
            </main>
            <Footer />
        </>
    );
}
