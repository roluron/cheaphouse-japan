import Nav from "../../components/Nav";
import Footer from "../../components/Footer";
import PropertyFilters from "../../properties/PropertyFilters";
import { getSupabaseServer } from "../../lib/supabase-server";
import { MOCK_PROPERTIES } from "../../lib/data";
import { notFound } from "next/navigation";

export const revalidate = 3600;

const COUNTRY_CONFIG = {
    jp: { name: "Japan", country: "japan", flag: "🇯🇵", currency: "¥", priceField: "price_jpy" },
    fr: { name: "France", country: "france", flag: "🇫🇷", currency: "€", priceField: "price_jpy" },
    it: { name: "Italy", country: "italy", flag: "🇮🇹", currency: "€", priceField: "price_jpy" },
    pt: { name: "Portugal", country: "portugal", flag: "🇵🇹", currency: "€", priceField: "price_jpy" },
    se: { name: "Sweden", country: "sweden", flag: "🇸🇪", currency: "kr", priceField: "price_jpy" },
    us: { name: "USA", country: "usa", flag: "🇺🇸", currency: "$", priceField: "price_jpy" },
    nz: { name: "New Zealand", country: "new-zealand", flag: "🇳🇿", currency: "NZ$", priceField: "price_jpy" },
};

export async function generateStaticParams() {
    return Object.keys(COUNTRY_CONFIG).map((country) => ({ country }));
}

export async function generateMetadata({ params }) {
    const p = await params;
    const config = COUNTRY_CONFIG[p.country];
    if (!config) return { title: "Not Found" };
    return {
        title: `${config.flag} Properties in ${config.name} — CheapHouse`,
        description: `Discover affordable homes in ${config.name}. Browse real listings with photos, prices, and honest assessments.`,
        openGraph: { title: `Properties in ${config.name} — CheapHouse` },
    };
}

async function getCountryProperties(countrySlug, searchParams) {
    const config = COUNTRY_CONFIG[countrySlug];
    if (!config) return null;

    try {
        const supabase = await getSupabaseServer();
        let query = supabase
            .from("properties")
            .select("*", { count: "exact" })
            .eq("is_published", true)
            .eq("admin_status", "approved")
            .eq("listing_status", "active")
            .eq("country", config.country);

        const params = await searchParams;

        // Prefecture/region filter
        if (params?.prefecture && params.prefecture !== "All") {
            query = query.eq("prefecture", params.prefecture);
        }
        if (params?.region && params.region !== "All") {
            query = query.eq("region", params.region);
        }

        // Price filter
        if (params?.price && params.price !== "all") {
            const [min, max] = params.price.split("-").map(Number);
            if (min >= 0) query = query.gte("price_jpy", min);
            if (max) query = query.lte("price_jpy", max);
        }

        // Sort
        switch (params?.sort) {
            case "price-asc":
                query = query.order("price_jpy", { ascending: true, nullsFirst: false });
                break;
            case "price-desc":
                query = query.order("price_jpy", { ascending: false });
                break;
            case "size-desc":
                query = query.order("building_sqm", { ascending: false });
                break;
            case "newest":
                query = query.order("created_at", { ascending: false });
                break;
            default:
                query = query.order("quality_score", { ascending: false });
        }

        query = query.limit(50);

        const { data, error, count } = await query;

        if (error || !data) {
            return { properties: [], count: 0, config };
        }
        return { properties: data, count: count || data.length, config };
    } catch {
        return { properties: [], count: 0, config };
    }
}

export default async function CountryPropertiesPage({ params, searchParams }) {
    const p = await params;
    const config = COUNTRY_CONFIG[p.country];
    if (!config) notFound();

    const result = await getCountryProperties(p.country, searchParams);
    if (!result) notFound();

    const { properties, count } = result;

    return (
        <>
            <Nav />
            <main style={{ paddingTop: 80, minHeight: "100vh" }}>
                <div className="container" style={{ paddingTop: 32 }}>
                    <div style={{ marginBottom: 8 }}>
                        <h1 style={{ fontSize: "clamp(24px, 3vw, 32px)", marginBottom: 8, fontWeight: 400 }}>
                            {config.flag} Properties in {config.name}
                        </h1>
                        <p style={{ color: "var(--text-secondary)", marginBottom: 24 }}>
                            {count} {count === 1 ? "property" : "properties"} found
                            {count === 0 && (
                                <span style={{ fontSize: 12, color: "var(--text-muted)", marginLeft: 8 }}>
                                    — scrapers being configured, check back soon
                                </span>
                            )}
                        </p>
                    </div>

                    {count > 0 ? (
                        <PropertyFilters properties={properties} />
                    ) : (
                        <div style={{
                            textAlign: "center",
                            padding: "80px 0",
                            background: "var(--bg-secondary)",
                            borderRadius: 12,
                            border: "1px solid var(--border-color)",
                        }}>
                            <div style={{ fontSize: 48, marginBottom: 16 }}>{config.flag}</div>
                            <h2 style={{ fontSize: 20, marginBottom: 8 }}>
                                No properties in {config.name} yet
                            </h2>
                            <p style={{ color: "var(--text-secondary)", fontSize: 14, maxWidth: 400, margin: "0 auto" }}>
                                Our scrapers for {config.name} are being set up.
                                Properties will appear here once they&apos;re live.
                            </p>
                        </div>
                    )}
                </div>
            </main>
            <Footer />
        </>
    );
}
