"use client";

import { use } from "react";
import { useState } from "react";
import Link from "next/link";
import Nav from "../../components/Nav";
import Footer from "../../components/Footer";
import { getProperty, LIVING_PROFILES, formatArea } from "../../lib/data";

export default function PropertyDetailPage({ params }) {
    const { slug } = use(params);
    const property = getProperty(slug);
    const [selectedImage, setSelectedImage] = useState(0);

    if (!property) {
        return (
            <>
                <Nav />
                <main style={{ paddingTop: 120, minHeight: "100vh", textAlign: "center" }}>
                    <div style={{ fontSize: 64, marginBottom: 16 }}>🏚️</div>
                    <h1 style={{ marginBottom: 8 }}>Property Not Found</h1>
                    <p style={{ color: "var(--text-secondary)", marginBottom: 32 }}>
                        This listing may have been removed or the URL is incorrect.
                    </p>
                    <Link href="/properties" className="btn btn-primary">
                        ← Back to Properties
                    </Link>
                </main>
                <Footer />
            </>
        );
    }

    const {
        title_en,
        summary_en,
        price_jpy,
        price_display,
        prefecture,
        city,
        region,
        building_sqm,
        land_sqm,
        year_built,
        rooms,
        floors,
        building_type,
        structure,
        condition_rating,
        renovation_estimate,
        images,
        quality_score,
        hazard_scores,
        lifestyle_tags,
        whats_attractive,
        whats_unclear,
        whats_risky,
        what_to_verify,
        freshness_label,
        source_url,
    } = property;

    const qualityColor =
        quality_score >= 0.7 ? "var(--accent-green)" : quality_score >= 0.5 ? "var(--accent-amber)" : "var(--accent-rose)";

    return (
        <>
            <Nav />
            <main style={{ paddingTop: 80, minHeight: "100vh" }}>
                <div className="container" style={{ paddingTop: 24, paddingBottom: 48 }}>
                    {/* Breadcrumb */}
                    <div style={{ fontSize: 13, color: "var(--text-muted)", marginBottom: 20 }}>
                        <Link href="/properties" style={{ color: "var(--accent-blue)" }}>
                            Properties
                        </Link>
                        {" / "}
                        <span>{prefecture}</span>
                        {city && <>{" / "}<span>{city}</span></>}
                    </div>

                    <div style={{ display: "grid", gridTemplateColumns: "1fr 380px", gap: 32, alignItems: "start" }}>
                        {/* ── LEFT COLUMN ── */}
                        <div>
                            {/* Image gallery */}
                            <div style={{ marginBottom: 32 }}>
                                <div
                                    style={{
                                        width: "100%",
                                        height: 440,
                                        borderRadius: "var(--radius-lg)",
                                        overflow: "hidden",
                                        marginBottom: 12,
                                        background: "var(--bg-secondary)",
                                    }}
                                >
                                    {images && images.length > 0 && (
                                        <img
                                            src={images[selectedImage]?.url}
                                            alt={images[selectedImage]?.caption || title_en}
                                            style={{ width: "100%", height: "100%", objectFit: "cover" }}
                                        />
                                    )}
                                </div>
                                {images && images.length > 1 && (
                                    <div style={{ display: "flex", gap: 8, overflowX: "auto" }}>
                                        {images.map((img, i) => (
                                            <button
                                                key={i}
                                                onClick={() => setSelectedImage(i)}
                                                style={{
                                                    width: 80,
                                                    height: 60,
                                                    borderRadius: "var(--radius-sm)",
                                                    overflow: "hidden",
                                                    border: selectedImage === i ? "2px solid var(--accent-blue)" : "2px solid transparent",
                                                    cursor: "pointer",
                                                    flexShrink: 0,
                                                    background: "none",
                                                    padding: 0,
                                                }}
                                            >
                                                <img
                                                    src={img.url}
                                                    alt={img.caption || ""}
                                                    style={{ width: "100%", height: "100%", objectFit: "cover" }}
                                                />
                                            </button>
                                        ))}
                                    </div>
                                )}
                            </div>

                            {/* Title & Summary */}
                            <h1 style={{ fontSize: 28, marginBottom: 8 }} id="property-title">{title_en}</h1>
                            <div style={{ fontSize: 14, color: "var(--text-secondary)", marginBottom: 24 }}>
                                📍 {city || "Unknown"}, {prefecture || "Unknown"}{region ? ` • ${region}` : ""}
                            </div>
                            <p style={{ color: "var(--text-secondary)", lineHeight: 1.8, marginBottom: 32, fontSize: 15 }}>
                                {summary_en}
                            </p>

                            {/* Property specs grid */}
                            <div
                                className="glass-card"
                                style={{ padding: 24, marginBottom: 32 }}
                                id="property-specs"
                            >
                                <h3 style={{ fontSize: 16, marginBottom: 16 }}>Property Details</h3>
                                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(160px, 1fr))", gap: 16 }}>
                                    {[
                                        { label: "Price", value: price_display || "TBD", icon: "💰" },
                                        { label: "Building", value: building_sqm ? `${building_sqm} m²` : "Unknown", icon: "📐" },
                                        { label: "Land", value: land_sqm ? `${land_sqm} m²` : "Unknown", icon: "🌿" },
                                        { label: "Layout", value: rooms || "Unknown", icon: "🏠" },
                                        { label: "Year Built", value: year_built || "Unknown", icon: "📅" },
                                        { label: "Floors", value: floors || "Unknown", icon: "🏗️" },
                                        { label: "Structure", value: structure || "Unknown", icon: "🧱" },
                                        { label: "Condition", value: condition_rating ? condition_rating.replace("_", " ") : "Unknown", icon: "🔧" },
                                    ].map((spec) => (
                                        <div key={spec.label}>
                                            <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 4 }}>
                                                {spec.icon} {spec.label}
                                            </div>
                                            <div style={{ fontSize: 15, fontWeight: 600, textTransform: "capitalize" }}>
                                                {spec.value}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* ── WHAT TO KNOW ── */}
                            <div id="what-to-know" style={{ marginBottom: 32 }}>
                                <h2 style={{ fontSize: 22, marginBottom: 20 }}>
                                    📋 What to Know
                                </h2>

                                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
                                    {/* Attractive */}
                                    <div className="glass-card" style={{ padding: 20 }}>
                                        <h4 style={{ color: "var(--accent-green)", fontSize: 14, marginBottom: 12 }}>
                                            ✅ What's Attractive
                                        </h4>
                                        <ul style={{ listStyle: "none", fontSize: 13, color: "var(--text-secondary)" }}>
                                            {(whats_attractive || []).map((item, i) => (
                                                <li key={i} style={{ padding: "6px 0", lineHeight: 1.5 }}>
                                                    • {item}
                                                </li>
                                            ))}
                                        </ul>
                                    </div>

                                    {/* Unclear */}
                                    <div className="glass-card" style={{ padding: 20 }}>
                                        <h4 style={{ color: "var(--accent-amber)", fontSize: 14, marginBottom: 12 }}>
                                            ❓ What's Unclear
                                        </h4>
                                        <ul style={{ listStyle: "none", fontSize: 13, color: "var(--text-secondary)" }}>
                                            {(whats_unclear || []).map((item, i) => (
                                                <li key={i} style={{ padding: "6px 0", lineHeight: 1.5 }}>
                                                    • {item}
                                                </li>
                                            ))}
                                        </ul>
                                    </div>

                                    {/* Risky */}
                                    <div className="glass-card" style={{ padding: 20 }}>
                                        <h4 style={{ color: "var(--accent-rose)", fontSize: 14, marginBottom: 12 }}>
                                            ⚠️ What's Risky
                                        </h4>
                                        <ul style={{ listStyle: "none", fontSize: 13, color: "var(--text-secondary)" }}>
                                            {(whats_risky || []).map((item, i) => (
                                                <li key={i} style={{ padding: "6px 0", lineHeight: 1.5 }}>
                                                    • {item}
                                                </li>
                                            ))}
                                        </ul>
                                    </div>

                                    {/* Verify */}
                                    <div className="glass-card" style={{ padding: 20 }}>
                                        <h4 style={{ color: "var(--accent-blue)", fontSize: 14, marginBottom: 12 }}>
                                            🔍 What to Verify
                                        </h4>
                                        <ul style={{ listStyle: "none", fontSize: 13, color: "var(--text-secondary)" }}>
                                            {(what_to_verify || []).map((item, i) => (
                                                <li key={i} style={{ padding: "6px 0", lineHeight: 1.5 }}>
                                                    • {item}
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* ── RIGHT SIDEBAR ── */}
                        <div style={{ position: "sticky", top: 96 }}>
                            {/* Price card */}
                            <div className="glass-card" style={{ padding: 24, marginBottom: 24 }}>
                                <div style={{ fontSize: 28, fontWeight: 800, fontFamily: "var(--font-display)", color: "var(--accent-blue)", marginBottom: 4 }}>
                                    {price_jpy ? `¥${price_jpy.toLocaleString()}` : "Price TBD"}
                                </div>
                                {price_jpy && (
                                    <div style={{ fontSize: 13, color: "var(--text-muted)", marginBottom: 16 }}>
                                        ~${Math.round(price_jpy / 150).toLocaleString()} USD
                                    </div>
                                )}

                                <a
                                    href={source_url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="btn btn-primary"
                                    style={{ width: "100%", marginBottom: 12 }}
                                >
                                    View Original Listing ↗
                                </a>
                                <button className="btn btn-secondary" style={{ width: "100%" }}>
                                    ♡ Save to Shortlist
                                </button>
                            </div>

                            {/* Quality score */}
                            <div className="glass-card" style={{ padding: 20, marginBottom: 24 }}>
                                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                                    <span style={{ fontSize: 13, color: "var(--text-muted)" }}>Data Quality</span>
                                    <span style={{ fontSize: 15, fontWeight: 700, color: qualityColor }}>
                                        {Math.round((quality_score || 0) * 100)}%
                                    </span>
                                </div>
                                <div className="quality-bar">
                                    <div
                                        className="quality-bar-fill"
                                        style={{
                                            width: `${(quality_score || 0) * 100}%`,
                                            background: qualityColor,
                                        }}
                                    />
                                </div>
                                <p style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 8 }}>
                                    Based on {Math.round((quality_score || 0) * 13)} of 13 data completeness checks
                                </p>
                            </div>

                            {/* Hazard scores */}
                            <div className="glass-card" style={{ padding: 20, marginBottom: 24 }} id="hazard-section">
                                <h4 style={{ fontSize: 14, marginBottom: 12 }}>🌊 Hazard Assessment</h4>
                                {hazard_scores &&
                                    Object.entries(hazard_scores).map(([type, data]) => (
                                        <div
                                            key={type}
                                            className={`hazard-indicator hazard-${data.level}`}
                                            style={{ marginBottom: 8 }}
                                        >
                                            <span style={{ fontSize: 16 }}>
                                                {type === "flood" ? "🌊" : type === "landslide" ? "⛰️" : "🌊"}
                                            </span>
                                            <div style={{ flex: 1 }}>
                                                <div style={{ fontWeight: 600, textTransform: "capitalize", fontSize: 13 }}>
                                                    {type}: {data.level}
                                                </div>
                                                <div style={{ fontSize: 11, opacity: 0.8, marginTop: 2 }}>{data.summary}</div>
                                            </div>
                                        </div>
                                    ))}
                            </div>

                            {/* Lifestyle tags */}
                            {lifestyle_tags && lifestyle_tags.length > 0 && (
                                <div className="glass-card" style={{ padding: 20, marginBottom: 24 }} id="lifestyle-section">
                                    <h4 style={{ fontSize: 14, marginBottom: 12 }}>🏷️ Living Profiles</h4>
                                    {lifestyle_tags.map((t) => {
                                        const profile = LIVING_PROFILES[t.tag];
                                        if (!profile) return null;
                                        return (
                                            <div key={t.tag} style={{ marginBottom: 12, paddingBottom: 12, borderBottom: "1px solid var(--border-subtle)" }}>
                                                <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                                                    <span className={`badge badge-${profile.color}`}>{profile.label}</span>
                                                    <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
                                                        {Math.round(t.confidence * 100)}% match
                                                    </span>
                                                </div>
                                                <div style={{ fontSize: 12, color: "var(--text-secondary)" }}>
                                                    {t.reason}
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            )}

                            {/* Renovation estimate */}
                            {renovation_estimate && renovation_estimate !== "unknown" && (
                                <div className="glass-card" style={{ padding: 20 }}>
                                    <h4 style={{ fontSize: 14, marginBottom: 8 }}>🔧 Renovation Estimate</h4>
                                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                                        <span
                                            className={`badge ${renovation_estimate === "light"
                                                    ? "badge-green"
                                                    : renovation_estimate === "moderate"
                                                        ? "badge-amber"
                                                        : "badge-rose"
                                                }`}
                                        >
                                            {renovation_estimate.charAt(0).toUpperCase() + renovation_estimate.slice(1)}
                                        </span>
                                        <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
                                            {renovation_estimate === "light" && "Cosmetic updates likely sufficient"}
                                            {renovation_estimate === "moderate" && "Kitchen, bath, and systems updates likely"}
                                            {renovation_estimate === "heavy" && "Structural work and full systems replacement"}
                                        </span>
                                    </div>
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
