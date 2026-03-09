import Link from "next/link";
import Nav from "./components/Nav";
import Footer from "./components/Footer";
import PropertyCard from "./components/PropertyCard";
import { getSupabaseServer } from "./lib/supabase-server";
import { MOCK_PROPERTIES } from "./lib/data";

export const revalidate = 3600;

async function getFeaturedProperties() {
  try {
    const supabase = await getSupabaseServer();
    const { data, error } = await supabase
      .from("properties")
      .select("*")
      .eq("is_published", true)
      .eq("admin_status", "approved")
      .eq("listing_status", "active")
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
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          paddingTop: 100,
          paddingBottom: 80,
          background: "var(--bg-primary)",
        }}
      >
        <div className="container" style={{ textAlign: "center", maxWidth: 800 }}>
          <h1
            style={{
              fontFamily: "var(--font-serif)",
              fontSize: "clamp(40px, 7vw, 76px)",
              fontWeight: 400,
              lineHeight: 1.1,
              letterSpacing: "-0.03em",
              marginBottom: 24,
            }}
          >
            Find your dream home.
            <br />
            <span style={{ color: "var(--accent-gold)" }}>Anywhere.</span>
          </h1>

          <p
            style={{
              fontSize: 18,
              color: "var(--text-secondary)",
              maxWidth: 480,
              margin: "0 auto 48px",
              lineHeight: 1.6,
            }}
          >
            Honest data on affordable homes worldwide. Starting with Japan.
          </p>

          <div style={{ display: "flex", gap: 20, justifyContent: "center", alignItems: "center" }}>
            <Link href="/properties" className="btn btn-primary btn-lg">
              Explore Japan
            </Link>
            <Link
              href="#how-it-works"
              style={{
                fontSize: 14,
                color: "var(--text-secondary)",
                display: "inline-flex",
                alignItems: "center",
                gap: 6,
                transition: "color 0.2s",
              }}
            >
              How it works
              <span style={{ fontSize: 18 }}>&rarr;</span>
            </Link>
          </div>

          <div
            style={{
              marginTop: 80,
              fontSize: 11,
              fontWeight: 500,
              letterSpacing: "0.1em",
              textTransform: "uppercase",
              color: "var(--text-muted)",
            }}
          >
            340 Properties &middot; 29 Prefectures &middot; 3 Risk Layers
          </div>
        </div>
      </section>

      {/* ── HOW IT WORKS ── */}
      <section id="how-it-works" className="section" style={{ borderTop: "1px solid var(--border-subtle)" }}>
        <div className="container" style={{ maxWidth: 800 }}>
          <div
            style={{
              fontSize: 11,
              fontWeight: 500,
              letterSpacing: "0.1em",
              textTransform: "uppercase",
              color: "var(--text-muted)",
              marginBottom: 64,
            }}
          >
            How It Works
          </div>

          {/* Step 1 */}
          <div style={{ paddingBottom: 64, borderBottom: "1px solid var(--border-subtle)" }}>
            <div
              style={{
                fontFamily: "var(--font-serif)",
                fontSize: 64,
                fontWeight: 400,
                color: "rgba(255,255,255,0.04)",
                lineHeight: 1,
                marginBottom: -12,
              }}
            >
              01
            </div>
            <h2 style={{ fontSize: "clamp(28px, 4vw, 40px)", marginBottom: 16, fontWeight: 400 }}>
              Every listing, one place
            </h2>
            <p style={{ color: "var(--text-secondary)", fontSize: 16, maxWidth: 480 }}>
              We aggregate affordable properties from across Japan — akiya banks, auction houses,
              and listing platforms — into a single, searchable collection.
            </p>
          </div>

          {/* Step 2 */}
          <div style={{ paddingTop: 64, paddingBottom: 64, borderBottom: "1px solid var(--border-subtle)" }}>
            <div
              style={{
                fontFamily: "var(--font-serif)",
                fontSize: 64,
                fontWeight: 400,
                color: "rgba(255,255,255,0.04)",
                lineHeight: 1,
                marginBottom: -12,
              }}
            >
              02
            </div>
            <h2 style={{ fontSize: "clamp(28px, 4vw, 40px)", marginBottom: 16, fontWeight: 400 }}>
              Risk data on every property
            </h2>
            <p style={{ color: "var(--text-secondary)", fontSize: 16, maxWidth: 480 }}>
              Every listing includes flood, landslide, and tsunami hazard assessments —
              so you know what you&apos;re buying before you visit.
            </p>
          </div>

          {/* Step 3 */}
          <div style={{ paddingTop: 64 }}>
            <div
              style={{
                fontFamily: "var(--font-serif)",
                fontSize: 64,
                fontWeight: 400,
                color: "rgba(255,255,255,0.04)",
                lineHeight: 1,
                marginBottom: -12,
              }}
            >
              03
            </div>
            <h2 style={{ fontSize: "clamp(28px, 4vw, 40px)", marginBottom: 16, fontWeight: 400 }}>
              Know what to keep, what to avoid
            </h2>
            <p style={{ color: "var(--text-secondary)", fontSize: 16, maxWidth: 480 }}>
              Our analysis highlights the positives and the red flags of each property —
              honest assessments, not sales pitches.
            </p>
          </div>
        </div>
      </section>

      {/* ── SELECTED PROPERTIES ── */}
      <section className="section">
        <div className="container">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 48 }}>
            <h2 style={{ fontSize: "clamp(28px, 4vw, 40px)", fontWeight: 400 }}>
              Selected Properties
            </h2>
            <Link
              href="/properties"
              style={{
                fontSize: 14,
                color: "var(--text-secondary)",
                display: "inline-flex",
                alignItems: "center",
                gap: 6,
              }}
            >
              View all <span style={{ fontSize: 18 }}>&rarr;</span>
            </Link>
          </div>
          <div className="property-grid">
            {featuredProperties.map((p) => (
              <PropertyCard key={p.id || p.slug} property={p} />
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ── */}
      <section style={{ padding: "120px 0", textAlign: "center" }}>
        <div className="container">
          <h2 style={{ fontSize: "clamp(28px, 4vw, 44px)", fontWeight: 400, marginBottom: 16 }}>
            Start exploring
          </h2>
          <p style={{ color: "var(--text-secondary)", marginBottom: 40, fontSize: 16 }}>
            From $10/month. Cancel anytime.
          </p>
          <Link href="/properties" className="btn btn-primary btn-lg">
            Browse Properties
          </Link>
        </div>
      </section>

      <Footer />
    </>
  );
}
