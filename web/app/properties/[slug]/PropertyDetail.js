"use client";

import { useState } from "react";
import Link from "next/link";
import Nav from "../../components/Nav";
import Footer from "../../components/Footer";
import SaveButton from "../../components/SaveButton";
import TotalCostCalculator from "../../components/TotalCostCalculator";
import RenovationEstimator from "../../components/RenovationEstimator";
import { LIVING_PROFILES } from "../../lib/data";

export default function PropertyDetail({ property }) {
    const [selectedImage, setSelectedImage] = useState(0);

    const {
        title_en, original_title, summary_en, original_description,
        price_jpy, price_display, prefecture, city, region,
        building_sqm, land_sqm, year_built, rooms, floors,
        building_type, structure, condition_rating, renovation_estimate,
        images, quality_score, hazard_scores, lifestyle_tags,
        whats_attractive, whats_unclear, whats_risky, what_to_verify,
        freshness_label, original_url, source_url, thumbnail_url,
        slug, latitude, longitude, primary_source_slug,
    } = property;

    const displayTitle = title_en || original_title || "Untitled Property";
    const displaySummary = summary_en || original_description || "";
    const displaySourceUrl = original_url || source_url || "#";

    const imageList = Array.isArray(images) && images.length > 0
        ? images.map((img) => (typeof img === "string" ? { url: img } : img))
        : thumbnail_url ? [{ url: thumbnail_url }] : [];

    const parsedHazards = hazard_scores && typeof hazard_scores === "object" && Object.keys(hazard_scores).length > 0
        ? hazard_scores : null;
    const parsedTags = Array.isArray(lifestyle_tags) ? lifestyle_tags : [];

    const SOURCE_NAMES = {
        "old-houses-japan": "Old Houses Japan",
        "all-akiyas": "AllAkiyas",
        "cheap-houses-japan": "Cheap Houses Japan",
    };
    const sourceName = SOURCE_NAMES[primary_source_slug] || primary_source_slug || "Unknown";

    const hasLlmWtk = whats_attractive?.length || whats_unclear?.length || whats_risky?.length || what_to_verify?.length;
    const fallbackWtk = hasLlmWtk ? null : (() => {
        const attractive = [], unclear = [], risky = [];
        const verify = ["Verify the property is still available before visiting", "Check local hazard maps at the municipal office"];
        if (price_jpy && price_jpy < 500000) attractive.push(`Very affordable at ¥${price_jpy.toLocaleString()}`);
        if (land_sqm && land_sqm > 300) attractive.push(`Large lot (${land_sqm} m²)`);
        if (building_sqm && building_sqm > 100) attractive.push(`Spacious building (${building_sqm} m²)`);
        if (!building_sqm) unclear.push("Building size not specified");
        if (!year_built) unclear.push("Year built is unknown");
        if (condition_rating === "unknown") unclear.push("Property condition is unclear");
        if (year_built && year_built < 1981) risky.push(`Built in ${year_built} — before 1981 earthquake code revision`);
        if (condition_rating === "needs_work" || condition_rating === "significant_renovation") risky.push("Property condition indicates renovation needed");
        verify.push("Request a copy of the property registration");
        verify.push("Confirm water, electricity, and sewage connections are active");
        return { attractive, unclear, risky, verify };
    })();

    const WtkSection = ({ title, color, items }) => (
        items?.length > 0 && (
            <div className="glass-card" style={{ padding: 20 }}>
                <h4 style={{ fontSize: 13, fontWeight: 600, color, marginBottom: 12, fontFamily: "var(--font-sans)", display: "flex", alignItems: "center" }}>
                    <span className="wtk-dot" style={{ background: color }} />
                    {title}
                </h4>
                <ul style={{ listStyle: "none", fontSize: 13, color: "var(--text-secondary)" }}>
                    {items.map((item, i) => <li key={i} style={{ padding: "6px 0", lineHeight: 1.5 }}>{item}</li>)}
                </ul>
            </div>
        )
    );

    return (
        <>
            <Nav />
            <main style={{ paddingTop: 80, minHeight: "100vh" }}>
                <div className="container" style={{ paddingTop: 32, paddingBottom: 64 }}>
                    {/* Breadcrumb */}
                    <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 24, letterSpacing: "0.02em" }}>
                        <Link href="/properties" style={{ color: "var(--text-secondary)" }}>Properties</Link>
                        {" / "}
                        <span>{prefecture || "Unknown"}</span>
                        {city && <>{" / "}<span>{city}</span></>}
                    </div>

                    <div className="property-detail-grid" style={{ display: "grid", gridTemplateColumns: "1fr 380px", gap: 48, alignItems: "start" }}>
                        {/* ── LEFT COLUMN ── */}
                        <div style={{ minWidth: 0, overflow: "hidden" }}>
                            {/* Image gallery */}
                            <div style={{ marginBottom: 40 }}>
                                <div style={{
                                    width: "100%", height: 480, borderRadius: "var(--radius-lg)",
                                    overflow: "hidden", marginBottom: 12, background: "var(--bg-secondary)",
                                    display: "flex", alignItems: "center", justifyContent: "center",
                                }}>
                                    {imageList.length > 0 ? (
                                        <img
                                            src={imageList[selectedImage]?.url}
                                            alt={displayTitle}
                                            style={{ width: "100%", height: "100%", objectFit: "cover" }}
                                        />
                                    ) : (
                                        <div style={{ fontSize: 14, color: "var(--text-muted)" }}>No image available</div>
                                    )}
                                </div>
                                {imageList.length > 1 && (
                                    <div style={{ display: "flex", gap: 8, overflowX: "auto" }}>
                                        {imageList.map((img, i) => (
                                            <button
                                                key={i}
                                                onClick={() => setSelectedImage(i)}
                                                style={{
                                                    width: 72, height: 52, borderRadius: "var(--radius-sm)", overflow: "hidden",
                                                    border: selectedImage === i ? "2px solid var(--accent-gold)" : "2px solid transparent",
                                                    cursor: "pointer", flexShrink: 0, background: "none", padding: 0, opacity: selectedImage === i ? 1 : 0.6,
                                                    transition: "opacity 0.2s",
                                                }}
                                            >
                                                <img src={img.url} alt="" style={{ width: "100%", height: "100%", objectFit: "cover" }} />
                                            </button>
                                        ))}
                                    </div>
                                )}
                            </div>

                            {/* Title & Location */}
                            <h1 style={{ fontSize: "clamp(24px, 3vw, 32px)", marginBottom: 8, fontWeight: 400 }}>{displayTitle}</h1>
                            <div style={{ fontSize: 14, color: "var(--text-secondary)", marginBottom: 32 }}>
                                {city || "Unknown"}, {prefecture || "Unknown"}{region ? ` · ${region}` : ""}
                            </div>

                            {/* Summary */}
                            {displaySummary && (
                                <p style={{ color: "var(--text-secondary)", lineHeight: 1.8, marginBottom: 40, fontSize: 15, overflowWrap: "break-word", wordBreak: "break-word" }}>
                                    {displaySummary}
                                </p>
                            )}

                            {/* Property specs */}
                            <div className="glass-card" style={{ padding: 28, marginBottom: 40 }}>
                                <h3 style={{ fontSize: 11, fontWeight: 500, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--text-muted)", marginBottom: 20, fontFamily: "var(--font-sans)" }}>
                                    Property Details
                                </h3>
                                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(160px, 1fr))", gap: 20 }}>
                                    {[
                                        { label: "Price", value: price_display || (price_jpy ? `¥${price_jpy.toLocaleString()}` : "TBD") },
                                        { label: "Building", value: building_sqm ? `${building_sqm} m²` : "—" },
                                        { label: "Land", value: land_sqm ? `${land_sqm} m²` : "—" },
                                        { label: "Layout", value: rooms || "—" },
                                        { label: "Year Built", value: year_built || "—" },
                                        { label: "Floors", value: floors || "—" },
                                        { label: "Structure", value: structure || "—" },
                                        { label: "Condition", value: condition_rating ? condition_rating.replace("_", " ") : "—" },
                                    ].map((spec) => (
                                        <div key={spec.label}>
                                            <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 4, letterSpacing: "0.05em", textTransform: "uppercase" }}>{spec.label}</div>
                                            <div style={{ fontSize: 15, fontWeight: 500, textTransform: "capitalize" }}>{spec.value}</div>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* Source attribution */}
                            <div className="glass-card" style={{ padding: 20, marginBottom: 40, borderLeft: "2px solid var(--accent-gold)" }}>
                                <div style={{ fontSize: 13, fontWeight: 500, marginBottom: 4 }}>Listed by {sourceName}</div>
                                <div style={{ fontSize: 12, color: "var(--text-secondary)", marginBottom: 8 }}>
                                    Originally published on {sourceName}.
                                </div>
                                <a href={displaySourceUrl} target="_blank" rel="noopener noreferrer" style={{ fontSize: 12, color: "var(--accent-gold)" }}>
                                    View original listing &rarr;
                                </a>
                            </div>

                            {/* Calculators */}
                            <TotalCostCalculator property={property} isPremium={true} />
                            <RenovationEstimator property={property} isPremium={true} />

                            {/* Map */}
                            <div style={{ marginBottom: 40 }}>
                                <h2 style={{ fontSize: 11, fontWeight: 500, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--text-muted)", marginBottom: 20, fontFamily: "var(--font-sans)" }}>
                                    Location
                                </h2>
                                {latitude && longitude ? (
                                    <>
                                        <div style={{ borderRadius: "var(--radius-lg)", overflow: "hidden", marginBottom: 12 }}>
                                            <iframe
                                                src={`https://www.openstreetmap.org/export/embed.html?bbox=${longitude - 0.01},${latitude - 0.01},${longitude + 0.01},${latitude + 0.01}&layer=mapnik&marker=${latitude},${longitude}`}
                                                width="100%" height="400" style={{ border: 0, display: "block" }}
                                                loading="lazy" title="Property location"
                                            />
                                        </div>
                                        <a href={`https://www.google.com/maps?q=${latitude},${longitude}`}
                                            target="_blank" rel="noopener noreferrer"
                                            style={{ fontSize: 13, color: "var(--accent-gold)" }}>
                                            Open in Google Maps &rarr;
                                        </a>
                                    </>
                                ) : (
                                    <div className="glass-card" style={{ padding: 24 }}>
                                        <div style={{ fontSize: 14, color: "var(--text-secondary)", marginBottom: 8 }}>
                                            {city || "Unknown"}, {prefecture || "Unknown"}
                                        </div>
                                        <a href={`https://www.google.com/maps/search/${encodeURIComponent([city, prefecture, "Japan"].filter(Boolean).join(", "))}`}
                                            target="_blank" rel="noopener noreferrer"
                                            style={{ fontSize: 13, color: "var(--accent-gold)" }}>
                                            Search area on Google Maps &rarr;
                                        </a>
                                    </div>
                                )}
                            </div>

                            {/* What to Know */}
                            {(hasLlmWtk || fallbackWtk) && (
                                <div style={{ marginBottom: 40 }}>
                                    <h2 style={{ fontSize: 11, fontWeight: 500, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--text-muted)", marginBottom: 20, fontFamily: "var(--font-sans)" }}>
                                        Assessment
                                    </h2>
                                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
                                        <WtkSection title="Attractive" color="var(--accent-green)" items={hasLlmWtk ? whats_attractive : fallbackWtk?.attractive} />
                                        <WtkSection title="Unclear" color="var(--accent-amber)" items={hasLlmWtk ? whats_unclear : fallbackWtk?.unclear} />
                                        <WtkSection title="Risks" color="var(--accent-rose)" items={hasLlmWtk ? whats_risky : fallbackWtk?.risky} />
                                        <WtkSection title="Verify" color="var(--accent-blue)" items={hasLlmWtk ? what_to_verify : fallbackWtk?.verify} />
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* ── RIGHT SIDEBAR ── */}
                        <div style={{ position: "sticky", top: 100 }}>
                            {/* Price */}
                            <div className="glass-card" style={{ padding: 28, marginBottom: 20 }}>
                                <div style={{ fontSize: 28, fontWeight: 600, fontFamily: "var(--font-display)", color: "var(--accent-gold)", marginBottom: 4 }}>
                                    {price_jpy ? `¥${price_jpy.toLocaleString()}` : "Price TBD"}
                                </div>
                                {price_jpy && (
                                    <div style={{ fontSize: 13, color: "var(--text-muted)", marginBottom: 20 }}>
                                        ~${Math.round(price_jpy / 150).toLocaleString()} USD
                                    </div>
                                )}
                                <a href={displaySourceUrl} target="_blank" rel="noopener noreferrer" className="btn btn-primary" style={{ width: "100%", marginBottom: 10 }}>
                                    View Original Listing
                                </a>
                                <div className="btn btn-secondary" style={{ width: "100%", justifyContent: "center" }}>
                                    <SaveButton propertyId={property.id} size={16} /> Save
                                </div>
                            </div>

                            {/* Report */}
                            <div className="glass-card" style={{ padding: 16, marginBottom: 20, textAlign: "center" }}>
                                <button className="btn btn-secondary" style={{ width: "100%", fontSize: 13 }}
                                    onClick={() => alert('PDF reports are coming soon.')}>
                                    Download Report
                                </button>
                            </div>

                            {/* Hazards */}
                            <div className="glass-card" style={{ padding: 20, marginBottom: 20 }}>
                                <h4 style={{ fontSize: 11, fontWeight: 500, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--text-muted)", marginBottom: 16, fontFamily: "var(--font-sans)" }}>
                                    Hazard Assessment
                                </h4>
                                {parsedHazards ? (
                                    Object.entries(parsedHazards).map(([type, data]) => {
                                        const level = data?.level || "none";
                                        const fillWidth = level === "high" ? "90%" : level === "moderate" ? "50%" : level === "low" ? "25%" : "5%";
                                        const fillColor = level === "high" ? "var(--accent-rose)" : level === "moderate" ? "var(--accent-amber)" : "var(--accent-green)";
                                        return (
                                            <div key={type}>
                                                <div className="hazard-bar">
                                                    <span className="hazard-bar-label">{type}</span>
                                                    <div className="hazard-bar-track">
                                                        <div className="hazard-bar-fill" style={{ width: fillWidth, background: fillColor }} />
                                                    </div>
                                                    <span className="hazard-bar-level" style={{ color: fillColor }}>{level}</span>
                                                </div>
                                                {data.summary && <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: -6, marginBottom: 8, paddingLeft: 102 }}>{data.summary}</div>}
                                            </div>
                                        );
                                    })
                                ) : (
                                    <p style={{ fontSize: 13, color: "var(--text-muted)" }}>Hazard data pending</p>
                                )}
                            </div>

                            {/* Lifestyle */}
                            {parsedTags.length > 0 && (
                                <div className="glass-card" style={{ padding: 20, marginBottom: 20 }}>
                                    <h4 style={{ fontSize: 11, fontWeight: 500, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--text-muted)", marginBottom: 16, fontFamily: "var(--font-sans)" }}>
                                        Living Profiles
                                    </h4>
                                    {parsedTags.map((t) => {
                                        const profile = LIVING_PROFILES[t.tag];
                                        if (!profile) return null;
                                        return (
                                            <div key={t.tag} style={{ marginBottom: 12, paddingBottom: 12, borderBottom: "1px solid var(--border-subtle)" }}>
                                                <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                                                    <span className={`badge badge-${profile.color}`}>{profile.label}</span>
                                                    <span style={{ fontSize: 11, color: "var(--text-muted)" }}>{Math.round((t.confidence || 0) * 100)}% match</span>
                                                </div>
                                                {t.reason && <div style={{ fontSize: 12, color: "var(--text-secondary)" }}>{t.reason}</div>}
                                            </div>
                                        );
                                    })}
                                </div>
                            )}

                            {/* Renovation */}
                            {renovation_estimate && renovation_estimate !== "unknown" && (
                                <div className="glass-card" style={{ padding: 20 }}>
                                    <h4 style={{ fontSize: 11, fontWeight: 500, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--text-muted)", marginBottom: 12, fontFamily: "var(--font-sans)" }}>
                                        Renovation Estimate
                                    </h4>
                                    <span className={`badge ${renovation_estimate === "light" ? "badge-green" : renovation_estimate === "moderate" ? "badge-amber" : "badge-rose"}`}>
                                        {renovation_estimate.charAt(0).toUpperCase() + renovation_estimate.slice(1)}
                                    </span>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </main>
            <Footer />
        </>
    );
}
