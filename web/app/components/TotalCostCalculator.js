"use client";

import { useState } from "react";

function calcAgentFee(price) {
    if (price >= 4_000_000) return Math.round(price * 0.033);
    if (price >= 2_000_000) return Math.round(price * 0.044);
    return Math.round(price * 0.055);
}

function calcStampDuty(price) {
    if (price < 5_000_000) return 1000;
    if (price < 10_000_000) return 5000;
    if (price < 50_000_000) return 10000;
    return 30000;
}

function calcRenovation(conditionRating, buildingSqm) {
    const sqm = buildingSqm || 80;
    if (conditionRating === "needs_work") return sqm * 30000;
    if (conditionRating === "significant_renovation") return sqm * 80000;
    return 0;
}

export default function TotalCostCalculator({ property, isPremium = false }) {
    const price = property?.price_jpy || 0;
    const [inputs, setInputs] = useState({
        purchasePrice: price,
        agentFee: calcAgentFee(price),
        registrationTax: Math.round(price * 0.02),
        acquisitionTax: Math.round(price * 0.03),
        stampDuty: calcStampDuty(price),
        legalFees: 300000,
        renovation: calcRenovation(property?.condition_rating, property?.building_sqm),
    });

    const total = Object.values(inputs).reduce((sum, v) => sum + (v || 0), 0);

    const items = [
        { key: "purchasePrice", label: "Purchase Price", editable: false },
        { key: "agentFee", label: "Agent Fee (3%+tax)" },
        { key: "registrationTax", label: "Registration Tax (2%)" },
        { key: "acquisitionTax", label: "Acquisition Tax (3%)" },
        { key: "stampDuty", label: "Stamp Duty" },
        { key: "legalFees", label: "Legal/Notary Fees" },
        { key: "renovation", label: "Renovation Estimate" },
    ];

    if (!isPremium) {
        return (
            <div className="glass-card" style={{ padding: 24, marginBottom: 32, position: "relative", overflow: "hidden" }}>
                <h3 style={{ fontSize: 11, fontWeight: 500, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--text-muted)", marginBottom: 16, fontFamily: "var(--font-sans)" }}>True Cost Calculator</h3>
                <div style={{ filter: "blur(6px)", pointerEvents: "none" }}>
                    {items.slice(0, 4).map(item => (
                        <div key={item.key} style={{ display: "flex", justifyContent: "space-between", padding: "8px 0", fontSize: 14 }}>
                            <span>{item.label}</span>
                            <span>{(inputs[item.key] || 0).toLocaleString()}</span>
                        </div>
                    ))}
                </div>
                <div style={{
                    position: "absolute", inset: 0, display: "flex", flexDirection: "column",
                    alignItems: "center", justifyContent: "center", background: "rgba(0,0,0,0.6)",
                    borderRadius: "var(--radius-lg)", padding: 24,
                }}>
                    <p style={{ fontSize: 14, fontWeight: 500, marginBottom: 12, textAlign: "center" }}>
                        Subscribe to see the full cost analysis
                    </p>
                    <a href="/pricing" className="btn btn-primary" style={{ padding: "10px 20px", fontSize: 13 }}>
                        Upgrade to Pro
                    </a>
                </div>
            </div>
        );
    }

    return (
        <div className="glass-card" style={{ padding: 28, marginBottom: 40 }}>
            <h3 style={{ fontSize: 11, fontWeight: 500, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--text-muted)", marginBottom: 20, fontFamily: "var(--font-sans)" }}>True Cost Calculator</h3>

            {items.map(item => (
                <div key={item.key} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "10px 0", borderBottom: "1px solid var(--border-subtle)" }}>
                    <span style={{ fontSize: 13, color: "var(--text-secondary)" }}>{item.label}</span>
                    {item.editable === false ? (
                        <span style={{ fontSize: 14, fontWeight: 500 }}>{(inputs[item.key] || 0).toLocaleString()}</span>
                    ) : (
                        <input
                            type="number"
                            value={inputs[item.key]}
                            onChange={e => setInputs(prev => ({ ...prev, [item.key]: parseInt(e.target.value) || 0 }))}
                            style={{
                                width: 120, padding: "4px 8px", textAlign: "right", fontSize: 13,
                                borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)",
                                background: "var(--bg-secondary)", color: "var(--text-primary)", outline: "none",
                            }}
                        />
                    )}
                </div>
            ))}

            <div style={{ display: "flex", justifyContent: "space-between", padding: "16px 0", marginTop: 8 }}>
                <span style={{ fontSize: 15, fontWeight: 600 }}>Total Estimated Cost</span>
                <span style={{ fontSize: 18, fontWeight: 600, color: "var(--accent-gold)" }}>
                    ¥{total.toLocaleString()}
                </span>
            </div>

            <div style={{ display: "flex", height: 4, borderRadius: 2, overflow: "hidden", marginTop: 4, marginBottom: 12 }}>
                {items.map(item => {
                    const pct = total > 0 ? ((inputs[item.key] || 0) / total) * 100 : 0;
                    const colors = { purchasePrice: "#C9A96E", agentFee: "#5B9BD5", registrationTax: "#6BAF7A", acquisitionTax: "#D4A04A", stampDuty: "#8e8e93", legalFees: "#C27070", renovation: "#48484a" };
                    return pct > 0.5 ? <div key={item.key} style={{ width: `${pct}%`, background: colors[item.key] }} title={item.label} /> : null;
                })}
            </div>

            <p style={{ fontSize: 11, color: "var(--text-muted)" }}>
                This is an estimate. Actual costs may vary. Consult a licensed professional.
            </p>
        </div>
    );
}
