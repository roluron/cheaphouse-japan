import Nav from "../components/Nav";
import Footer from "../components/Footer";
import Link from "next/link";
import PropertyCard from "../components/PropertyCard";
import { getCurrentUser } from "../lib/auth";
import { getSupabaseServer } from "../lib/supabase-server";
import { redirect } from "next/navigation";

export const metadata = { title: "Saved Properties — CheapHouse" };

export default async function SavedPage() {
    const user = await getCurrentUser();
    if (!user) redirect("/login");

    const supabase = await getSupabaseServer();
    const { data: saved } = await supabase
        .from("saved_properties")
        .select("*, property:properties(*)")
        .eq("user_id", user.id)
        .order("created_at", { ascending: false });

    const properties = (saved || []).map((s) => s.property).filter(Boolean);

    return (
        <>
            <Nav />
            <main style={{ paddingTop: 80, minHeight: "100vh" }}>
                <div className="container" style={{ paddingTop: 40, paddingBottom: 80 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 32 }}>
                        <h1 style={{ fontSize: 28, fontWeight: 700, fontFamily: "var(--font-display)" }}>
                            Saved Properties
                        </h1>
                        {properties.length >= 2 && (
                            <Link
                                href={`/compare?ids=${properties.slice(0, 3).map(p => p.id).join(",")}`}
                                className="btn btn-secondary"
                                style={{ padding: "8px 16px", fontSize: 13 }}
                            >
                                Compare ({Math.min(properties.length, 3)})
                            </Link>
                        )}
                    </div>

                    {properties.length > 0 ? (
                        <div className="property-grid">
                            {properties.map((property) => (
                                <PropertyCard key={property.id} property={property} />
                            ))}
                        </div>
                    ) : (
                        <div className="glass-card" style={{ padding: 48, textAlign: "center" }}>
                            <div style={{ fontSize: 48, marginBottom: 16 }}>♡</div>
                            <h2 style={{ fontSize: 20, marginBottom: 8 }}>No saved properties yet</h2>
                            <p style={{ color: "var(--text-secondary)", fontSize: 14, marginBottom: 24 }}>
                                Browse properties and click the heart icon to save your favorites.
                            </p>
                            <Link href="/properties" className="btn btn-primary" style={{ padding: "10px 24px" }}>
                                Browse Properties
                            </Link>
                        </div>
                    )}
                </div>
            </main>
            <Footer />
        </>
    );
}
