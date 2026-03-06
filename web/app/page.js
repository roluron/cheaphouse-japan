import Link from "next/link";
import Nav from "./components/Nav";
import Footer from "./components/Footer";
import PropertyCard from "./components/PropertyCard";
import { getSupabaseServer } from "./lib/supabase-server";
import { MOCK_PROPERTIES } from "./lib/data";

async function getFeaturedProperties() {
  try {
    const supabase = await getSupabaseServer();
    const { data, error } = await supabase
      .from("properties")
      .select("*")
      .eq("is_published", true)
      .eq("admin_status", "approved")
      .order("quality_score", { ascending: false })
      .limit(3);

    if (error || !data || data.length === 0) {
      return MOCK_PROPERTIES.slice(0, 3);
    }
    return data;
  } catch {
    return MOCK_PROPERTIES.slice(0, 3);
  }
}

export default async function Home() {
  const featuredProperties = await getFeaturedProperties();

  return (
    <>
      <Nav />

      {/* ── HERO ── */}
      <section
        style={{
          background: "var(--gradient-hero)",
          paddingTop: 140,
          paddingBottom: 100,
          position: "relative",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            position: "absolute",
            top: "20%",
            left: "50%",
            transform: "translateX(-50%)",
            width: 600,
            height: 600,
            background: "radial-gradient(circle, rgba(56,189,248,0.08) 0%, transparent 70%)",
            pointerEvents: "none",
          }}
        />

        <div className="container" style={{ position: "relative", textAlign: "center" }}>
          <div className="animate-in" style={{ marginBottom: 16 }}>
            <span className="badge badge-blue" style={{ fontSize: 13 }}>
              🏡 Now tracking 100+ properties across Japan
            </span>
          </div>

          <h1
            className="animate-in animate-delay-1"
            style={{ fontSize: "clamp(36px, 5vw, 64px)", marginBottom: 20, maxWidth: 800, margin: "0 auto 20px" }}
          >
            Find your dream home in{" "}
            <span className="text-gradient">Japan</span>
          </h1>

          <p
            className="animate-in animate-delay-2"
            style={{
              fontSize: "clamp(16px, 2vw, 20px)",
              color: "var(--text-secondary)",
              maxWidth: 600,
              margin: "0 auto 40px",
              lineHeight: 1.7,
            }}
          >
            The decision platform for international buyers.
            We aggregate listings, add hazard intelligence, and give you
            honest insights — so you can buy with confidence.
          </p>

          <div
            className="animate-in animate-delay-3"
            style={{ display: "flex", gap: 16, justifyContent: "center", flexWrap: "wrap" }}
          >
            <Link href="/properties" className="btn btn-primary btn-lg">
              Browse Properties →
            </Link>
            <Link href="#how-it-works" className="btn btn-secondary btn-lg">
              How It Works
            </Link>
          </div>

          <div
            className="animate-in animate-delay-4"
            style={{
              display: "flex",
              gap: 40,
              justifyContent: "center",
              marginTop: 60,
              color: "var(--text-muted)",
              fontSize: 14,
              flexWrap: "wrap",
            }}
          >
            <span>🗾 47 prefectures covered</span>
            <span>🌊 Hazard data on every listing</span>
            <span>🔍 Honest "What to Know" reports</span>
            <span>🤖 AI-powered insights</span>
          </div>
        </div>
      </section>

      {/* ── HOW IT WORKS ── */}
      <section id="how-it-works" className="section">
        <div className="container">
          <h2 style={{ textAlign: "center", fontSize: 36, marginBottom: 12 }}>
            Not another listing site
          </h2>
          <p style={{ textAlign: "center", color: "var(--text-secondary)", marginBottom: 48, maxWidth: 600, margin: "0 auto 48px" }}>
            We go beyond aggregation. Every property gets hazard analysis,
            lifestyle matching, and an honest assessment — because buying
            a house in Japan shouldn't require guesswork.
          </p>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 24 }}>
            {[
              { icon: "🔎", title: "Aggregated Listings", desc: "We pull from multiple sources and normalize the data so you can compare apples to apples." },
              { icon: "🌊", title: "Hazard Intelligence", desc: "Every listing includes flood, landslide, and tsunami risk data from official Japanese sources." },
              { icon: "🏷️", title: "Lifestyle Matching", desc: "Properties are tagged as pet-friendly, artist retreat, remote work ready, and more — with reasons." },
              { icon: "⚖️", title: "Honest Assessments", desc: "Our 'What to Know' section tells you what's attractive, what's unclear, and what's risky." },
              { icon: "📊", title: "Quality Scoring", desc: "Every listing gets a completeness score so you know which ones have reliable data." },
              { icon: "🔄", title: "Always Fresh", desc: "Listings are refreshed regularly. We track availability and mark stale or delisted properties." },
            ].map((item, i) => (
              <div key={i} className="glass-card" style={{ padding: 28 }}>
                <div style={{ fontSize: 32, marginBottom: 16 }}>{item.icon}</div>
                <h3 style={{ fontSize: 18, marginBottom: 8 }}>{item.title}</h3>
                <p style={{ color: "var(--text-secondary)", fontSize: 14, lineHeight: 1.7 }}>{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── FEATURED PROPERTIES ── */}
      <section className="section" style={{ background: "var(--bg-secondary)", paddingTop: 64, paddingBottom: 64 }}>
        <div className="container">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 32 }}>
            <h2 style={{ fontSize: 28 }}>Featured Properties</h2>
            <Link href="/properties" className="btn btn-secondary">View All →</Link>
          </div>
          <div className="property-grid">
            {featuredProperties.map((p) => (
              <PropertyCard key={p.id} property={p} />
            ))}
          </div>
        </div>
      </section>

      {/* ── PRICING ── */}
      <section id="pricing" className="section">
        <div className="container" style={{ textAlign: "center" }}>
          <h2 style={{ fontSize: 36, marginBottom: 12 }}>Simple Pricing</h2>
          <p style={{ color: "var(--text-secondary)", marginBottom: 48, maxWidth: 500, margin: "0 auto 48px" }}>
            Start free. Upgrade when you're serious.
          </p>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: 24, maxWidth: 900, margin: "0 auto" }}>
            <div className="glass-card" style={{ padding: 36 }}>
              <h3 style={{ fontSize: 20, marginBottom: 8 }}>Explorer</h3>
              <div style={{ fontSize: 42, fontWeight: 800, marginBottom: 4, fontFamily: "var(--font-display)" }}>Free</div>
              <p style={{ color: "var(--text-muted)", fontSize: 14, marginBottom: 24 }}>Browse and discover</p>
              <ul style={{ listStyle: "none", textAlign: "left", fontSize: 14, color: "var(--text-secondary)" }}>
                {["Browse all listings", "Basic property details", "Hazard risk levels", "Filter by prefecture"].map((f, i) => (
                  <li key={i} style={{ padding: "8px 0", borderBottom: "1px solid var(--border-subtle)" }}>✓ {f}</li>
                ))}
              </ul>
              <Link href="/properties" className="btn btn-secondary" style={{ width: "100%", marginTop: 24 }}>Start Browsing</Link>
            </div>

            <div className="glass-card" style={{ padding: 36, border: "1px solid var(--accent-blue)", boxShadow: "var(--shadow-glow)", position: "relative" }}>
              <span className="badge badge-blue" style={{ position: "absolute", top: -12, left: "50%", transform: "translateX(-50%)" }}>Most Popular</span>
              <h3 style={{ fontSize: 20, marginBottom: 8 }}>Decision Maker</h3>
              <div style={{ fontSize: 42, fontWeight: 800, marginBottom: 4, fontFamily: "var(--font-display)" }}>
                <span className="text-gradient">$10</span>
                <span style={{ fontSize: 16, color: "var(--text-muted)", fontWeight: 400 }}>/mo</span>
              </div>
              <p style={{ color: "var(--text-muted)", fontSize: 14, marginBottom: 24 }}>Everything you need to decide</p>
              <ul style={{ listStyle: "none", textAlign: "left", fontSize: 14, color: "var(--text-secondary)" }}>
                {["Everything in Explorer", "Full \"What to Know\" reports", "Lifestyle matching profiles", "Quality scores & data completeness", "Saved properties & shortlists", "Email alerts for new matches", "Detailed hazard reports"].map((f, i) => (
                  <li key={i} style={{ padding: "8px 0", borderBottom: "1px solid var(--border-subtle)" }}>✓ {f}</li>
                ))}
              </ul>
              <button className="btn btn-primary" style={{ width: "100%", marginTop: 24 }}>Get Started →</button>
            </div>
          </div>
        </div>
      </section>

      {/* ── CTA ── */}
      <section style={{ padding: "80px 0", background: "linear-gradient(135deg, rgba(56,189,248,0.05), rgba(45,212,191,0.05))" }}>
        <div className="container" style={{ textAlign: "center" }}>
          <h2 style={{ fontSize: 32, marginBottom: 16 }}>Ready to find your place in Japan?</h2>
          <p style={{ color: "var(--text-secondary)", marginBottom: 32, maxWidth: 500, margin: "0 auto 32px" }}>
            We aggregate the listings. We check the risks. You make the decision.
          </p>
          <Link href="/properties" className="btn btn-primary btn-lg">Browse Properties →</Link>
        </div>
      </section>

      <Footer />
    </>
  );
}
