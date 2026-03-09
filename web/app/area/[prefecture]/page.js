import Nav from "../../components/Nav";
import Footer from "../../components/Footer";
import Link from "next/link";
import { getSupabaseServer } from "../../lib/supabase-server";
import { notFound } from "next/navigation";

const PREFECTURE_LIST = [
    "Hokkaido", "Aomori", "Iwate", "Miyagi", "Akita", "Yamagata", "Fukushima", "Ibaraki", "Tochigi", "Gunma",
    "Saitama", "Chiba", "Tokyo", "Kanagawa", "Niigata", "Toyama", "Ishikawa", "Fukui", "Yamanashi", "Nagano",
    "Gifu", "Shizuoka", "Aichi", "Mie", "Shiga", "Kyoto", "Osaka", "Hyogo", "Nara", "Wakayama", "Tottori",
    "Shimane", "Okayama", "Hiroshima", "Yamaguchi", "Tokushima", "Kagawa", "Ehime", "Kochi", "Fukuoka",
    "Saga", "Nagasaki", "Kumamoto", "Oita", "Miyazaki", "Kagoshima", "Okinawa"
];

export async function generateMetadata({ params }) {
    const { prefecture } = await params;
    const name = decodeURIComponent(prefecture);
    return {
        title: `${name} Area Analysis — CheapHouse`,
        description: `Property market analysis for ${name}, Japan. Average prices, building sizes, hazard risks, and available listings.`,
    };
}

export default async function AreaPage({ params }) {
    const { prefecture } = await params;
    const name = decodeURIComponent(prefecture);

    const supabase = await getSupabaseServer();
    const { data: properties } = await supabase
        .from("properties")
        .select("price_jpy, building_sqm, land_sqm, year_built, hazard_scores, lifestyle_tags, city, latitude, longitude")
        .eq("is_published", true)
        .eq("admin_status", "approved")
        .eq("listing_status", "active")
        .eq("prefecture", name);

    if (!properties || properties.length === 0) {
        return (
            <>
                <Nav />
                <main style={{ paddingTop: 80, minHeight: "100vh" }}>
                    <div className="container" style={{ paddingTop: 40, paddingBottom: 80, textAlign: "center" }}>
                        <h1 style={{ fontSize: 28, marginBottom: 12 }}>No data for {name}</h1>
                        <p style={{ color: "var(--text-secondary)", marginBottom: 24 }}>We don't have listings in this prefecture yet.</p>
                        <Link href="/properties" className="btn btn-primary" style={{ padding: "10px 24px" }}>Browse All Properties</Link>
                    </div>
                </main>
                <Footer />
            </>
        );
    }

    const count = properties.length;
    const prices = properties.map(p => p.price_jpy).filter(Boolean);
    const avgPrice = prices.length ? Math.round(prices.reduce((a, b) => a + b, 0) / prices.length) : 0;
    const minPrice = prices.length ? Math.min(...prices) : 0;
    const maxPrice = prices.length ? Math.max(...prices) : 0;
    const buildings = properties.map(p => p.building_sqm).filter(Boolean);
    const avgBuilding = buildings.length ? Math.round(buildings.reduce((a, b) => a + b, 0) / buildings.length) : 0;
    const lands = properties.map(p => p.land_sqm).filter(Boolean);
    const avgLand = lands.length ? Math.round(lands.reduce((a, b) => a + b, 0) / lands.length) : 0;
    const years = properties.map(p => p.year_built).filter(Boolean);
    const avgYear = years.length ? Math.round(years.reduce((a, b) => a + b, 0) / years.length) : null;

    // Hazard summary
    const hazardCounts = { low: 0, moderate: 0, high: 0 };
    properties.forEach(p => {
        if (p.hazard_scores) {
            Object.values(p.hazard_scores).forEach(h => {
                if (h?.level && hazardCounts[h.level] !== undefined) hazardCounts[h.level]++;
            });
        }
    });

    // Top lifestyle tags
    const tagCount = {};
    properties.forEach(p => {
        if (Array.isArray(p.lifestyle_tags)) {
            p.lifestyle_tags.forEach(t => {
                const tag = t.tag || t;
                tagCount[tag] = (tagCount[tag] || 0) + 1;
            });
        }
    });
    const topTags = Object.entries(tagCount).sort((a, b) => b[1] - a[1]).slice(0, 6);

    // Cities
    const cityCounts = {};
    properties.forEach(p => {
        if (p.city) cityCounts[p.city] = (cityCounts[p.city] || 0) + 1;
    });
    const topCities = Object.entries(cityCounts).sort((a, b) => b[1] - a[1]).slice(0, 8);

    // Map center
    const lats = properties.map(p => p.latitude).filter(Boolean);
    const lngs = properties.map(p => p.longitude).filter(Boolean);
    const hasMap = lats.length > 0 && lngs.length > 0;
    const centerLat = hasMap ? lats.reduce((a, b) => a + b, 0) / lats.length : 0;
    const centerLng = hasMap ? lngs.reduce((a, b) => a + b, 0) / lngs.length : 0;

    return (
        <>
            <Nav />
            <main style={{ paddingTop: 80, minHeight: "100vh" }}>
                <div className="container" style={{ paddingTop: 40, paddingBottom: 80 }}>
                    <div style={{ marginBottom: 32 }}>
                        <Link href="/properties" style={{ fontSize: 13, color: "var(--accent-blue)" }}>← All Properties</Link>
                        <h1 style={{ fontSize: 32, fontWeight: 800, fontFamily: "var(--font-display)", marginTop: 8 }}>
                            {name} Area Analysis
                        </h1>
                        <p style={{ color: "var(--text-secondary)", fontSize: 15 }}>{count} properties available</p>
                    </div>

                    {/* Stats grid */}
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))", gap: 16, marginBottom: 32 }}>
                        {[
                            { label: "Average Price", value: avgPrice ? `¥${avgPrice.toLocaleString()}` : "N/A" },
                            { label: "Price Range", value: `¥${minPrice.toLocaleString()} – ¥${maxPrice.toLocaleString()}` },
                            { label: "Avg Building Size", value: avgBuilding ? `${avgBuilding} m²` : "N/A" },
                            { label: "Avg Land Size", value: avgLand ? `${avgLand} m²` : "N/A" },
                            { label: "Avg Year Built", value: avgYear || "N/A" },
                            { label: "Total Listings", value: count },
                        ].map(s => (
                            <div key={s.label} className="glass-card" style={{ padding: 20 }}>
                                <div style={{ fontSize: 18, fontWeight: 600 }}>{s.value}</div>
                                <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 4, letterSpacing: "0.05em", textTransform: "uppercase" }}>{s.label}</div>
                            </div>
                        ))}
                    </div>

                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24, marginBottom: 32 }}>
                        {/* Hazard */}
                        <div className="glass-card" style={{ padding: 20 }}>
                            <h3 style={{ fontSize: 11, fontWeight: 500, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--text-muted)", marginBottom: 12, fontFamily: "var(--font-sans)" }}>Hazard Summary</h3>
                            {Object.entries(hazardCounts).map(([level, ct]) => (
                                <div key={level} style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", fontSize: 13 }}>
                                    <span style={{ textTransform: "capitalize" }}>{level} risk</span>
                                    <span style={{ fontWeight: 600, color: level === "high" ? "var(--accent-rose)" : level === "moderate" ? "var(--accent-amber)" : "var(--accent-green)" }}>
                                        {ct} indicators
                                    </span>
                                </div>
                            ))}
                        </div>

                        {/* Tags */}
                        <div className="glass-card" style={{ padding: 20 }}>
                            <h3 style={{ fontSize: 11, fontWeight: 500, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--text-muted)", marginBottom: 12, fontFamily: "var(--font-sans)" }}>Common Tags</h3>
                            <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                                {topTags.map(([tag, ct]) => (
                                    <span key={tag} className="badge badge-blue" style={{ fontSize: 11 }}>
                                        {tag} ({ct})
                                    </span>
                                ))}
                                {topTags.length === 0 && <span style={{ fontSize: 13, color: "var(--text-muted)" }}>No tags yet</span>}
                            </div>
                        </div>
                    </div>

                    {/* Map */}
                    {hasMap && (
                        <div style={{ marginBottom: 32 }}>
                            <h3 style={{ fontSize: 11, fontWeight: 500, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--text-muted)", marginBottom: 12, fontFamily: "var(--font-sans)" }}>Property Locations</h3>
                            <div style={{ borderRadius: "var(--radius-lg)", overflow: "hidden" }}>
                                <iframe
                                    src={`https://www.openstreetmap.org/export/embed.html?bbox=${centerLng - 0.5},${centerLat - 0.3},${centerLng + 0.5},${centerLat + 0.3}&layer=mapnik`}
                                    width="100%" height="350" style={{ border: 0, display: "block" }} loading="lazy"
                                />
                            </div>
                        </div>
                    )}

                    {/* Cities */}
                    {topCities.length > 0 && (
                        <div className="glass-card" style={{ padding: 20, marginBottom: 32 }}>
                            <h3 style={{ fontSize: 11, fontWeight: 500, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--text-muted)", marginBottom: 12, fontFamily: "var(--font-sans)" }}>Cities with Most Listings</h3>
                            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(150px, 1fr))", gap: 8 }}>
                                {topCities.map(([city, ct]) => (
                                    <div key={city} style={{ fontSize: 13 }}>
                                        <span style={{ fontWeight: 600 }}>{city}</span>
                                        <span style={{ color: "var(--text-muted)", marginLeft: 4 }}>({ct})</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    <Link href={`/properties?prefecture=${encodeURIComponent(name)}`} className="btn btn-primary" style={{ padding: "12px 24px" }}>
                        Browse {name} Properties →
                    </Link>
                </div>
            </main>
            <Footer />
        </>
    );
}
