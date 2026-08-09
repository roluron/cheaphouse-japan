import Nav from "../components/Nav";
import Footer from "../components/Footer";
import PropertyFilters from "./PropertyFilters";
import { getSupabaseServer } from "../lib/supabase-server";
import { getVerifiedCutoff } from "../lib/availability";

export const revalidate = 900;

export const metadata = {
    title: "Recently Verified Japanese Properties — CheapHouse",
    description: "Japanese property listings whose original source was confirmed active within the last 72 hours.",
};

async function getProperties() {
    try {
        const supabase = await getSupabaseServer();
        const { data, error, count } = await supabase
            .from("properties")
            .select("*", { count: "exact" })
            .eq("is_published", true)
            .eq("admin_status", "approved")
            .eq("country", "japan")
            .eq("listing_status", "active")
            .gte("last_checked_at", getVerifiedCutoff())
            .order("last_checked_at", { ascending: false })
            .limit(50);

        if (error) return { properties: [], count: 0, dataState: "unavailable" };
        return { properties: data || [], count: count || data?.length || 0, dataState: "ready" };
    } catch {
        return { properties: [], count: 0, dataState: "unavailable" };
    }
}

export default async function PropertiesPage() {
    const { properties, count, dataState } = await getProperties();

    return (
        <>
            <Nav />
            <main className="page-shell">
                <div className="container">
                    <div className="page-intro">
                        <div className="eyebrow">Japan only · source checked within 72 hours</div>
                        <h1>Verified listings</h1>
                        <p>{count} {count === 1 ? "listing" : "listings"} currently pass the availability rule.</p>
                    </div>

                    {dataState === "unavailable" ? (
                        <div className="intentional-empty">
                            <h2>Live data is temporarily unavailable</h2>
                            <p>No sample properties are being substituted. Try again later or submit a specific listing.</p>
                            <a href="/verify" className="btn btn-primary">Check a listing</a>
                        </div>
                    ) : properties.length > 0 ? (
                        <PropertyFilters properties={properties} />
                    ) : (
                        <div className="intentional-empty">
                            <h2>No listing currently passes verification</h2>
                            <p>Expired and unconfirmed listings are hidden until their original source can be checked again.</p>
                            <a href="/verify" className="btn btn-primary">Submit a listing</a>
                        </div>
                    )}
                </div>
            </main>
            <Footer />
        </>
    );
}
