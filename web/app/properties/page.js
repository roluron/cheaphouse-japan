import Nav from "../components/Nav";
import Footer from "../components/Footer";
import PropertyFilters from "./PropertyFilters";
import { getSupabaseServer } from "../lib/supabase-server";
import { MOCK_PROPERTIES } from "../lib/data";

export const revalidate = 3600;

export async function generateMetadata({ searchParams }) {
    const params = await searchParams;
    const prefecture = params?.prefecture && params.prefecture !== "All Prefectures" ? params.prefecture : null;
    const title = prefecture
        ? `Properties in ${prefecture} — CheapHouse`
        : "Browse Properties in Japan — CheapHouse";
    return {
        title,
        description: `Discover affordable homes ${prefecture ? `in ${prefecture}` : "across Japan"} with hazard data, lifestyle tags, and honest assessments.`,
        openGraph: { title },
    };
}

async function getProperties(searchParams) {
    try {
        const supabase = await getSupabaseServer();
        let query = supabase
            .from("properties")
            .select("*", { count: "exact" })
            .eq("is_published", true)
            .eq("admin_status", "approved")
            .eq("listing_status", "active");

        const params = await searchParams;

        // Prefecture filter
        if (params?.prefecture && params.prefecture !== "All Prefectures") {
            query = query.eq("prefecture", params.prefecture);
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

        if (error || !data || data.length === 0) {
            return { properties: MOCK_PROPERTIES, count: MOCK_PROPERTIES.length, isMock: true };
        }
        return { properties: data, count: count || data.length, isMock: false };
    } catch {
        return { properties: MOCK_PROPERTIES, count: MOCK_PROPERTIES.length, isMock: true };
    }
}

export default async function PropertiesPage({ searchParams }) {
    const { properties, count, isMock } = await getProperties(searchParams);

    return (
        <>
            <Nav />
            <main style={{ paddingTop: 80, minHeight: "100vh" }}>
                <div className="container" style={{ paddingTop: 32 }}>
                    <div style={{ marginBottom: 8 }}>
                        <h1 style={{ fontSize: "clamp(24px, 3vw, 32px)", marginBottom: 8, fontWeight: 400 }}>Properties in Japan</h1>
                        <p style={{ color: "var(--text-secondary)", marginBottom: 24 }}>
                            {count} {count === 1 ? "property" : "properties"} found
                            {isMock && (
                                <span style={{ fontSize: 12, color: "var(--text-muted)", marginLeft: 8 }}>
                                    (sample data)
                                </span>
                            )}
                        </p>
                    </div>

                    <PropertyFilters properties={properties} />

                    {properties.length === 0 && (
                        <div style={{ textAlign: "center", padding: "80px 0" }}>
                            <div style={{ fontSize: 14, color: "var(--text-muted)", marginBottom: 16 }}>—</div>
                            <h2 style={{ fontSize: 20, marginBottom: 8 }}>No properties match your filters</h2>
                            <p style={{ color: "var(--text-secondary)", fontSize: 14 }}>
                                Try broadening your search or removing some filters.
                            </p>
                        </div>
                    )}
                </div>
            </main>
            <Footer />
        </>
    );
}
