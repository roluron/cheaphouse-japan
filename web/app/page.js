import Link from "next/link";
import Nav from "./components/Nav";
import Footer from "./components/Footer";
import PropertyCard from "./components/PropertyCard";
import { getSupabaseServer } from "./lib/supabase-server";
import { getVerifiedCutoff } from "./lib/availability";

export const revalidate = 900;

async function getFeaturedProperties() {
  try {
    const supabase = await getSupabaseServer();
    const { data, error } = await supabase
      .from("properties")
      .select("*")
      .eq("is_published", true)
      .eq("admin_status", "approved")
      .eq("country", "japan")
      .eq("listing_status", "active")
      .gte("last_checked_at", getVerifiedCutoff())
      .order("last_checked_at", { ascending: false })
      .limit(3);

    if (error) return { properties: [], dataState: "unavailable" };
    return { properties: data || [], dataState: "ready" };
  } catch {
    return { properties: [], dataState: "unavailable" };
  }
}

export default async function Home() {
  const { properties, dataState } = await getFeaturedProperties();

  return (
    <>
      <Nav />
      <main>
        <section className="hero-verified">
          <div className="container hero-verified-inner">
            <div className="eyebrow">Japan property, checked before you commit</div>
            <h1>
              Cheap listings are easy to find.
              <br />
              <span>Truth is harder.</span>
            </h1>
            <p className="hero-copy">
              Paste a Japanese property link. Within 48 hours, know whether it is still available,
              what is proven, what is risky, and what must be checked on site.
            </p>
            <div className="hero-actions">
              <Link href="/verify" className="btn btn-primary btn-lg">Check a listing</Link>
              <Link href="/properties" className="btn btn-secondary btn-lg">Browse verified listings</Link>
            </div>
            <div className="trust-rule">No dead listing presented as active. No invented certainty.</div>
          </div>
        </section>

        <section className="section" id="method">
          <div className="container">
            <div className="section-heading">
              <div className="eyebrow">The decision dossier</div>
              <h2>One answer before ten more tabs.</h2>
            </div>
            <div className="method-grid">
              {[
                ["01", "Availability", "We recheck the original source. Sold, removed, stale, and unreachable are separate states."],
                ["02", "Evidence", "Every claim is labelled proven, inferred, unknown, or requiring local inspection."],
                ["03", "Real cost", "Purchase price is separated from taxes, fees, renovation exposure, and unknowns."],
                ["04", "Decision", "You get the attractive points, unclear points, risks, and a concrete verification list."],
              ].map(([number, title, copy]) => (
                <article className="method-card" key={number}>
                  <span>{number}</span>
                  <h3>{title}</h3>
                  <p>{copy}</p>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="section verified-section">
          <div className="container">
            <div className="section-heading section-heading-row">
              <div>
                <div className="eyebrow">Checked within 72 hours</div>
                <h2>Recently verified</h2>
              </div>
              <Link href="/properties">View all &rarr;</Link>
            </div>

            {properties.length > 0 ? (
              <div className="property-grid">
                {properties.map((property) => <PropertyCard key={property.id} property={property} />)}
              </div>
            ) : (
              <div className="intentional-empty">
                <h3>{dataState === "unavailable" ? "Live listing data is temporarily unavailable" : "No listing currently passes the 72-hour rule"}</h3>
                <p>We would rather show nothing than quietly substitute sample or expired listings.</p>
                <Link href="/verify" className="btn btn-primary">Check a listing directly</Link>
              </div>
            )}
          </div>
        </section>

        <section className="verification-offer">
          <div className="container verification-offer-inner">
            <div>
              <div className="eyebrow">Founding beta</div>
              <h2>A 48-hour verification, not another subscription.</h2>
              <p>$149 per property. You only pay after we confirm the listing can be checked.</p>
            </div>
            <Link href="/verify" className="btn btn-primary btn-lg">Request verification</Link>
          </div>
        </section>
      </main>
      <Footer />
    </>
  );
}
