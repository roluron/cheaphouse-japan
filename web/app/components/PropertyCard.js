"use client";

import Link from "next/link";
import { convertPrice, formatCurrency } from "../lib/currencies";
import { LIVING_PROFILES } from "../lib/data";
import { useState, useEffect } from "react";

function getWorstHazard(hazard_scores) {
    if (!hazard_scores || typeof hazard_scores !== "object") return null;
    let worst = null;
    let worstType = null;
    const levels = { none: 0, low: 1, moderate: 2, high: 3 };
    for (const [type, data] of Object.entries(hazard_scores)) {
        const level = data?.level || "none";
        if (!worst || (levels[level] || 0) > (levels[worst] || 0)) {
            worst = level;
            worstType = type;
        }
    }
    return { level: worst, type: worstType };
}

export default function PropertyCard({ property }) {
    const [currency, setCurrency] = useState("USD");

    useEffect(() => {
        setCurrency(localStorage.getItem("ch-currency") || "USD");
        const handler = (e) => setCurrency(e.detail);
        window.addEventListener("currencyChange", handler);
        return () => window.removeEventListener("currencyChange", handler);
    }, []);

    const {
        slug,
        title_en,
        original_title,
        prefecture,
        city,
        price_jpy,
        thumbnail_url,
        images,
        hazard_scores,
        quality_score,
        lifestyle_tags,
    } = property;

    const displayTitle = title_en || original_title || "Untitled Property";
    const imageUrl = thumbnail_url || (Array.isArray(images) && images[0]?.url) || null;
    const priceDisplay = price_jpy ? `¥${price_jpy.toLocaleString()}` : "Price TBD";
    const convertedPrice = price_jpy && currency !== "JPY"
        ? formatCurrency(convertPrice(price_jpy, currency), currency)
        : null;
    const location = [city, prefecture].filter(Boolean).join(", ") || "Japan";

    // Risk dot
    const worstHazard = getWorstHazard(hazard_scores);
    const showDot = worstHazard && (worstHazard.level === "moderate" || worstHazard.level === "high");
    const dotColor = worstHazard?.level === "high" ? "var(--accent-rose)" : "var(--accent-amber)";
    const dotTooltip = worstHazard ? `${worstHazard.level.charAt(0).toUpperCase() + worstHazard.level.slice(1)} ${worstHazard.type} risk` : "";

    // Quality border
    const qualityLevel = (quality_score || 0) >= 0.7 ? "high" : (quality_score || 0) >= 0.5 ? "medium" : undefined;

    // Lifestyle tags — top 2
    const parsedTags = Array.isArray(lifestyle_tags) ? lifestyle_tags : [];
    const topTags = parsedTags
        .slice(0, 2)
        .map(t => LIVING_PROFILES[t.tag]?.label || t.tag?.replace(/-/g, " "))
        .filter(Boolean);

    return (
        <Link href={`/properties/${slug}`} style={{ textDecoration: "none" }}>
            <div className="property-card" data-quality={qualityLevel}>
                <div className="property-card-image" style={{ position: "relative" }}>
                    {showDot && (
                        <div
                            className="risk-dot"
                            style={{ background: dotColor }}
                            data-tooltip={dotTooltip}
                        />
                    )}
                    {imageUrl ? (
                        <img src={imageUrl} alt={displayTitle} loading="lazy" />
                    ) : (
                        <div style={{ width: "100%", height: "100%", display: "flex", alignItems: "center", justifyContent: "center", color: "var(--text-muted)", fontSize: 14 }}>
                            No image
                        </div>
                    )}
                </div>
                <div className="property-card-body">
                    <div className="property-card-price">
                        {priceDisplay}
                        {convertedPrice && (
                            <span style={{ fontSize: 14, fontWeight: 400, color: "var(--text-secondary)", marginLeft: 8 }}>
                                ~{convertedPrice}
                            </span>
                        )}
                    </div>
                    <div className="property-card-title">{displayTitle}</div>
                    <div className="property-card-location">{location}</div>
                    {topTags.length > 0 && (
                        <div style={{
                            fontSize: 11,
                            textTransform: "uppercase",
                            letterSpacing: "0.08em",
                            color: "var(--text-muted)",
                            marginTop: 6,
                        }}>
                            {topTags.join(" · ")}
                        </div>
                    )}
                </div>
            </div>
        </Link>
    );
}
