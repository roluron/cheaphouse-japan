import Link from "next/link";
import { LIVING_PROFILES, formatPrice, formatArea } from "../lib/data";

export default function PropertyCard({ property }) {
    const {
        id,
        slug,
        title_en,
        original_title,
        price_jpy,
        price_display,
        prefecture,
        city,
        building_sqm,
        land_sqm,
        rooms,
        year_built,
        thumbnail_url,
        images,
        quality_score,
        lifestyle_tags,
        freshness_label,
        hazard_scores,
    } = property;

    const displayTitle = title_en || original_title || "Untitled Property";
    const displaySlug = slug || id;
    const imgUrl = thumbnail_url ||
        (Array.isArray(images) && images.length > 0 ? (typeof images[0] === "string" ? images[0] : images[0]?.url) : null);

    const qualityColor =
        (quality_score || 0) >= 0.7
            ? "var(--accent-green)"
            : (quality_score || 0) >= 0.5
                ? "var(--accent-amber)"
                : "var(--accent-rose)";

    const worstHazard = hazard_scores
        ? Object.values(hazard_scores).reduce((worst, h) => {
            const levels = { none: 0, low: 1, moderate: 2, high: 3 };
            return (levels[h.level] || 0) > (levels[worst.level] || 0) ? h : worst;
        }, { level: "none" })
        : null;

    return (
        <Link href={`/properties/${displaySlug}`} id={`property-${displaySlug}`}>
            <article className="property-card">
                <div className="property-card-image">
                    {imgUrl ? (
                        <img
                            src={imgUrl}
                            alt={displayTitle}
                            loading="lazy"
                        />
                    ) : (
                        <div style={{ width: '100%', height: '100%', background: 'linear-gradient(135deg, var(--bg-secondary), var(--bg-tertiary))', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 48, opacity: 0.3 }}>🏠</div>
                    )}
                    {freshness_label === "new" && (
                        <span
                            className="badge badge-blue"
                            style={{
                                position: "absolute",
                                top: 12,
                                left: 12,
                            }}
                        >
                            ✨ New
                        </span>
                    )}
                    {worstHazard && worstHazard.level !== "none" && worstHazard.level !== "low" && (
                        <span
                            className={`badge ${worstHazard.level === "high" ? "badge-rose" : "badge-amber"
                                }`}
                            style={{
                                position: "absolute",
                                top: 12,
                                right: 12,
                            }}
                        >
                            ⚠ {worstHazard.level} risk
                        </span>
                    )}
                    <div
                        style={{
                            position: "absolute",
                            bottom: 0,
                            left: 0,
                            right: 0,
                            height: 60,
                            background: "linear-gradient(transparent, rgba(0,0,0,0.6))",
                        }}
                    />
                </div>

                <div className="property-card-body">
                    <div className="property-card-price">
                        {price_jpy
                            ? `¥${price_jpy.toLocaleString()}`
                            : "Price TBD"}
                    </div>
                    <h3 className="property-card-title">{displayTitle}</h3>
                    <div className="property-card-location">
                        📍 {city || "Unknown"}, {prefecture || "Unknown"}
                    </div>

                    <div className="property-card-meta">
                        {rooms && <span>🏠 {rooms}</span>}
                        {building_sqm && <span>📐 {building_sqm} m²</span>}
                        {land_sqm && <span>🌿 {land_sqm} m²</span>}
                        {year_built && <span>📅 {year_built}</span>}
                    </div>

                    {lifestyle_tags && lifestyle_tags.length > 0 && (
                        <div className="property-card-tags">
                            {lifestyle_tags.slice(0, 3).map((t) => {
                                const profile = LIVING_PROFILES[t.tag];
                                if (!profile) return null;
                                const badgeClass = `badge badge-${profile.color}`;
                                return (
                                    <span key={t.tag} className={badgeClass}>
                                        {profile.label}
                                    </span>
                                );
                            })}
                        </div>
                    )}

                    <div
                        style={{
                            display: "flex",
                            alignItems: "center",
                            gap: 8,
                            marginTop: 12,
                            fontSize: 12,
                            color: "var(--text-muted)",
                        }}
                    >
                        <span>Quality</span>
                        <div className="quality-bar" style={{ flex: 1 }}>
                            <div
                                className="quality-bar-fill"
                                style={{
                                    width: `${(quality_score || 0) * 100}%`,
                                    background: qualityColor,
                                }}
                            />
                        </div>
                        <span style={{ color: qualityColor }}>
                            {Math.round((quality_score || 0) * 100)}%
                        </span>
                    </div>
                </div>
            </article>
        </Link>
    );
}
