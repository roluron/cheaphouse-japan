import Nav from "../components/Nav";
import Footer from "../components/Footer";
import Link from "next/link";
import { getSupabaseServer } from "../lib/supabase-server";

export const metadata = { title: "Compare Properties — CheapHouse" };

export default async function ComparePage({ searchParams }) {
    const sp = await searchParams;
    const ids = (sp?.ids || "").split(",").filter(Boolean).slice(0, 3);

    let properties = [];
    if (ids.length > 0) {
        const supabase = await getSupabaseServer();
        const { data } = await supabase
            .from("properties")
            .select("*")
            .in("id", ids)
            .eq("is_published", true);
        properties = data || [];
    }

    if (properties.length === 0) {
        return (
            <>
                <Nav />
                <main style={{ paddingTop: 80, minHeight: "100vh" }}>
                    <div className="container" style={{ paddingTop: 40, paddingBottom: 80, textAlign: "center" }}>
                        <h1 style={{ fontSize: 24, marginBottom: 8, fontWeight: 400 }}>No properties to compare</h1>
                        <p style={{ color: "var(--text-secondary)", marginBottom: 24 }}>Select 2-3 properties from the browse page to compare them side by side.</p>
                        <Link href="/properties" className="btn btn-primary" style={{ padding: "10px 24px" }}>Browse Properties</Link>
                    </div>
                </main>
                <Footer />
            </>
        );
    }

    const rows = [
        { label: "Price", render: (p) => p.price_jpy ? `¥${p.price_jpy.toLocaleString()}` : "TBD", compare: "low" },
        { label: "Prefecture", render: (p) => p.prefecture || "—" },
        { label: "City", render: (p) => p.city || "—" },
        { label: "Building", render: (p) => p.building_sqm ? `${p.building_sqm} m²` : "—", compare: "high" },
        { label: "Land", render: (p) => p.land_sqm ? `${p.land_sqm} m²` : "—", compare: "high" },
        { label: "Year Built", render: (p) => p.year_built || "—", compare: "high" },
        { label: "Rooms", render: (p) => p.rooms || "—" },
        { label: "Condition", render: (p) => (p.condition_rating || "—").replace("_", " ") },
        { label: "Flood Risk", render: (p) => p.hazard_scores?.flood?.level || "—" },
        { label: "Landslide Risk", render: (p) => p.hazard_scores?.landslide?.level || "—" },
        { label: "Tsunami Risk", render: (p) => p.hazard_scores?.tsunami?.level || "—" },
    ];

    const getBestIdx = (row) => {
        if (!row.compare) return -1;
        const vals = properties.map((p) => {
            const v = row.label === "Price" ? p.price_jpy : row.label === "Building" ? p.building_sqm : row.label === "Land" ? p.land_sqm : row.label === "Year Built" ? p.year_built : null;
            return typeof v === "number" ? v : null;
        });
        const filtered = vals.filter((v) => v !== null);
        if (filtered.length < 2) return -1;
        const target = row.compare === "high" ? Math.max(...filtered) : Math.min(...filtered);
        return vals.indexOf(target);
    };

    return (
        <>
            <Nav />
            <main style={{ paddingTop: 80, minHeight: "100vh" }}>
                <div className="container" style={{ paddingTop: 40, paddingBottom: 80 }}>
                    <h1 style={{ fontSize: "clamp(24px, 3vw, 32px)", fontWeight: 400, marginBottom: 32 }}>
                        Compare Properties
                    </h1>

                    <div style={{ overflowX: "auto" }}>
                        <table style={{ width: "100%", borderCollapse: "separate", borderSpacing: 0, minWidth: 600 }}>
                            <thead>
                                <tr>
                                    <th style={{ width: 140, padding: 8 }}></th>
                                    {properties.map((p) => (
                                        <th key={p.id} style={{ padding: 8, verticalAlign: "top" }}>
                                            <div className="glass-card" style={{ padding: 12, textAlign: "center" }}>
                                                <div style={{ height: 120, borderRadius: "var(--radius-md)", overflow: "hidden", marginBottom: 8, background: "var(--bg-secondary)" }}>
                                                    {p.thumbnail_url ? (
                                                        <img src={p.thumbnail_url} alt="" style={{ width: "100%", height: "100%", objectFit: "cover" }} />
                                                    ) : (
                                                        <div style={{ height: "100%", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 13, color: "var(--text-muted)" }}>No image</div>
                                                    )}
                                                </div>
                                                <Link href={`/properties/${p.slug}`} style={{ fontSize: 13, fontWeight: 500, color: "var(--accent-gold)", textDecoration: "none" }}>
                                                    {p.title_en || p.original_title || "Property"}
                                                </Link>
                                            </div>
                                        </th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody>
                                {rows.map((row) => {
                                    const bestIdx = getBestIdx(row);
                                    return (
                                        <tr key={row.label}>
                                            <td style={{ padding: "10px 8px", fontSize: 12, color: "var(--text-muted)", whiteSpace: "nowrap", letterSpacing: "0.05em", textTransform: "uppercase" }}>
                                                {row.label}
                                            </td>
                                            {properties.map((p, i) => (
                                                <td
                                                    key={p.id}
                                                    style={{
                                                        padding: "10px 12px", fontSize: 14, textAlign: "center",
                                                        textTransform: "capitalize", fontWeight: bestIdx === i ? 500 : 400,
                                                        color: bestIdx === i ? "var(--accent-green)" : "var(--text-secondary)",
                                                        borderBottom: "1px solid var(--border-subtle)",
                                                    }}
                                                >
                                                    {row.render(p)}
                                                </td>
                                            ))}
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>
                </div>
            </main>
            <Footer />
        </>
    );
}
