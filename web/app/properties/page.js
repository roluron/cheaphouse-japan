"use client";

import { useState, useMemo } from "react";
import Nav from "../components/Nav";
import Footer from "../components/Footer";
import PropertyCard from "../components/PropertyCard";
import { MOCK_PROPERTIES, PREFECTURES, LIVING_PROFILES } from "../lib/data";

const SORT_OPTIONS = [
    { value: "price-asc", label: "Price: Low → High" },
    { value: "price-desc", label: "Price: High → Low" },
    { value: "quality-desc", label: "Quality Score" },
    { value: "newest", label: "Newest First" },
    { value: "size-desc", label: "Largest First" },
];

const PRICE_RANGES = [
    { value: "all", label: "Any Price" },
    { value: "0-100000", label: "Under ¥100,000" },
    { value: "100000-500000", label: "¥100K – ¥500K" },
    { value: "500000-2000000", label: "¥500K – ¥2M" },
    { value: "2000000-5000000", label: "¥2M – ¥5M" },
    { value: "5000000-99999999", label: "Over ¥5M" },
];

export default function PropertiesPage() {
    const [prefecture, setPrefecture] = useState("All Prefectures");
    const [priceRange, setPriceRange] = useState("all");
    const [sort, setSort] = useState("quality-desc");
    const [lifestyleFilter, setLifestyleFilter] = useState("");
    const [searchQuery, setSearchQuery] = useState("");

    const filtered = useMemo(() => {
        let results = [...MOCK_PROPERTIES];

        // Prefecture filter
        if (prefecture !== "All Prefectures") {
            results = results.filter((p) => p.prefecture === prefecture);
        }

        // Price range
        if (priceRange !== "all") {
            const [min, max] = priceRange.split("-").map(Number);
            results = results.filter((p) => {
                const price = p.price_jpy || 0;
                return price >= min && price <= max;
            });
        }

        // Lifestyle filter
        if (lifestyleFilter) {
            results = results.filter(
                (p) =>
                    p.lifestyle_tags &&
                    p.lifestyle_tags.some((t) => t.tag === lifestyleFilter)
            );
        }

        // Search
        if (searchQuery.trim()) {
            const q = searchQuery.toLowerCase();
            results = results.filter(
                (p) =>
                    (p.title_en || "").toLowerCase().includes(q) ||
                    (p.city || "").toLowerCase().includes(q) ||
                    (p.prefecture || "").toLowerCase().includes(q)
            );
        }

        // Sort
        switch (sort) {
            case "price-asc":
                results.sort((a, b) => (a.price_jpy || 0) - (b.price_jpy || 0));
                break;
            case "price-desc":
                results.sort((a, b) => (b.price_jpy || 0) - (a.price_jpy || 0));
                break;
            case "quality-desc":
                results.sort(
                    (a, b) => (b.quality_score || 0) - (a.quality_score || 0)
                );
                break;
            case "size-desc":
                results.sort(
                    (a, b) => (b.building_sqm || 0) - (a.building_sqm || 0)
                );
                break;
            default:
                break;
        }

        return results;
    }, [prefecture, priceRange, sort, lifestyleFilter, searchQuery]);

    return (
        <>
            <Nav />
            <main style={{ paddingTop: 80, minHeight: "100vh" }}>
                <div className="container" style={{ paddingTop: 32 }}>
                    {/* Page header */}
                    <div style={{ marginBottom: 8 }}>
                        <h1 style={{ fontSize: 32, marginBottom: 8 }}>
                            Properties in Japan
                        </h1>
                        <p style={{ color: "var(--text-secondary)", marginBottom: 24 }}>
                            {filtered.length} {filtered.length === 1 ? "property" : "properties"} found
                        </p>
                    </div>

                    {/* Filter bar */}
                    <div className="filter-bar" id="property-filters">
                        <input
                            className="filter-input"
                            type="text"
                            placeholder="🔍 Search by city, prefecture..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            style={{ minWidth: 200, flex: 1 }}
                            id="filter-search"
                        />

                        <select
                            className="filter-select"
                            value={prefecture}
                            onChange={(e) => setPrefecture(e.target.value)}
                            id="filter-prefecture"
                        >
                            {PREFECTURES.map((p) => (
                                <option key={p} value={p}>
                                    {p}
                                </option>
                            ))}
                        </select>

                        <select
                            className="filter-select"
                            value={priceRange}
                            onChange={(e) => setPriceRange(e.target.value)}
                            id="filter-price"
                        >
                            {PRICE_RANGES.map((r) => (
                                <option key={r.value} value={r.value}>
                                    {r.label}
                                </option>
                            ))}
                        </select>

                        <select
                            className="filter-select"
                            value={lifestyleFilter}
                            onChange={(e) => setLifestyleFilter(e.target.value)}
                            id="filter-lifestyle"
                        >
                            <option value="">All Lifestyles</option>
                            {Object.entries(LIVING_PROFILES).map(([key, profile]) => (
                                <option key={key} value={key}>
                                    {profile.label}
                                </option>
                            ))}
                        </select>

                        <select
                            className="filter-select"
                            value={sort}
                            onChange={(e) => setSort(e.target.value)}
                            id="filter-sort"
                        >
                            {SORT_OPTIONS.map((s) => (
                                <option key={s.value} value={s.value}>
                                    {s.label}
                                </option>
                            ))}
                        </select>
                    </div>

                    {/* Property grid */}
                    {filtered.length > 0 ? (
                        <div className="property-grid" style={{ marginBottom: 48 }}>
                            {filtered.map((p) => (
                                <PropertyCard key={p.id} property={p} />
                            ))}
                        </div>
                    ) : (
                        <div
                            style={{
                                textAlign: "center",
                                padding: 80,
                                color: "var(--text-muted)",
                            }}
                        >
                            <div style={{ fontSize: 48, marginBottom: 16 }}>🏚️</div>
                            <h3 style={{ marginBottom: 8 }}>No properties match your filters</h3>
                            <p>Try broadening your search or clearing some filters.</p>
                        </div>
                    )}
                </div>
            </main>
            <Footer />
        </>
    );
}
