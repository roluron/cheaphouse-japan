import Nav from "../components/Nav";
import Footer from "../components/Footer";
import PropertyFilters from "./PropertyFilters";
import { getSupabaseServer } from "../lib/supabase-server";
import { MOCK_PROPERTIES } from "../lib/data";

async function getProperties(searchParams) {
    try {
        const supabase = await getSupabaseServer();
        let query = supabase
            .from("properties")
            .select("*", { count: "exact" })
            .eq("is_published", true)
            .eq("admin_status", "approved");

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
                        <h1 style={{ fontSize: 32, marginBottom: 8 }}>Properties in Japan</h1>
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
                </div>
            </main>
            <Footer />
        </>
    );
}
