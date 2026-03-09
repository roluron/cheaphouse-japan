"use client";

import { useState } from "react";

const RENO_ITEMS = [
    { key: "structural", label: "Structural Reinforcement", condition: (p) => p.year_built && p.year_built < 1981, costPerSqm: [20000, 50000] },
    { key: "roof", label: "Roof Repair/Replacement", condition: () => true, fixed: [500000, 2000000] },
    { key: "kitchen", label: "Kitchen Renovation", condition: () => true, fixed: [500000, 2500000] },
    { key: "bathroom", label: "Bathroom Renovation", condition: () => true, fixed: [300000, 1500000] },
    { key: "flooring", label: "Flooring (Tatami/Wood)", condition: () => true, costPerSqm: [5000, 15000] },
    { key: "insulation", label: "Insulation Upgrade", condition: () => true, costPerSqm: [3000, 8000] },
    { key: "electrical", label: "Electrical Rewiring", condition: (p) => p.year_built && p.year_built < 1990, fixed: [300000, 800000] },
    { key: "plumbing", label: "Plumbing", condition: (p) => p.year_built && p.year_built < 1980, fixed: [500000, 1500000] },
];

export default function RenovationEstimator({ property, isPremium = false }) {
    const sqm = property?.building_sqm || 80;
    const [checked, setChecked] = useState(() => {
        const initial = {};
        RENO_ITEMS.forEach(item => {
            initial[item.key] = item.condition(property || {});
        });
        return initial;
    });

    const getItemCost = (item) => {
        if (item.costPerSqm) {
            const avg = (item.costPerSqm[0] + item.costPerSqm[1]) / 2;
            return Math.round(sqm * avg);
        }
        return Math.round((item.fixed[0] + item.fixed[1]) / 2);
    };

    const total = RENO_ITEMS.reduce((sum, item) => {
        return sum + (checked[item.key] ? getItemCost(item) : 0);
    }, 0);

    if (!isPremium) {
        return (
            <div className="glass-card" style={{ padding: 24, marginBottom: 32, position: "relative", overflow: "hidden" }}>
                <h3 style={{ fontSize: 11, fontWeight: 500, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--text-muted)", marginBottom: 16, fontFamily: "var(--font-sans)" }}>Renovation Cost Estimator</h3>
                <div style={{ filter: "blur(6px)", pointerEvents: "none" }}>
                    {RENO_ITEMS.slice(0, 3).map(item => (
                        <div key={item.key} style={{ padding: "8px 0", fontSize: 13 }}>{item.label}</div>
                    ))}
                </div>
                <div style={{
                    position: "absolute", inset: 0, display: "flex", flexDirection: "column",
                    alignItems: "center", justifyContent: "center", background: "rgba(0,0,0,0.6)",
                    borderRadius: "var(--radius-lg)", padding: 24,
                }}>
                    <p style={{ fontSize: 14, fontWeight: 500, marginBottom: 12 }}>Subscribe for renovation estimates</p>
                    <a href="/pricing" className="btn btn-primary" style={{ padding: "10px 20px", fontSize: 13 }}>Upgrade to Pro</a>
                </div>
            </div>
        );
    }

    return (
        <div className="glass-card" style={{ padding: 28, marginBottom: 40 }}>
            <h3 style={{ fontSize: 11, fontWeight: 500, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--text-muted)", marginBottom: 4, fontFamily: "var(--font-sans)" }}>Renovation Cost Estimator</h3>
            <p style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 20 }}>
                Based on {sqm} m² building. Toggle items you plan to renovate.
            </p>

            {RENO_ITEMS.map(item => {
                const cost = getItemCost(item);
                const range = item.costPerSqm
                    ? `¥${(sqm * item.costPerSqm[0]).toLocaleString()}–¥${(sqm * item.costPerSqm[1]).toLocaleString()}`
                    : `¥${item.fixed[0].toLocaleString()}–¥${item.fixed[1].toLocaleString()}`;
                return (
                    <label
                        key={item.key}
                        style={{
                            display: "flex", justifyContent: "space-between", alignItems: "center",
                            padding: "10px 0", borderBottom: "1px solid var(--border-subtle)", cursor: "pointer",
                        }}
                    >
                        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                            <input
                                type="checkbox"
                                checked={checked[item.key]}
                                onChange={() => setChecked(prev => ({ ...prev, [item.key]: !prev[item.key] }))}
                                style={{ accentColor: "var(--accent-gold)" }}
                            />
                            <span style={{ fontSize: 13 }}>{item.label}</span>
                        </div>
                        <div style={{ textAlign: "right" }}>
                            <div style={{ fontSize: 13, fontWeight: checked[item.key] ? 500 : 400, color: checked[item.key] ? "var(--text-primary)" : "var(--text-muted)" }}>
                                ¥{cost.toLocaleString()}
                            </div>
                            <div style={{ fontSize: 10, color: "var(--text-muted)" }}>{range}</div>
                        </div>
                    </label>
                );
            })}

            <div style={{ display: "flex", justifyContent: "space-between", padding: "16px 0", marginTop: 8 }}>
                <span style={{ fontSize: 15, fontWeight: 600 }}>Estimated Renovation Total</span>
                <span style={{ fontSize: 18, fontWeight: 600, color: "var(--accent-gold)" }}>¥{total.toLocaleString()}</span>
            </div>
            <p style={{ fontSize: 11, color: "var(--text-muted)" }}>
                Estimates only. Consult a licensed professional for accurate quotes.
            </p>
        </div>
    );
}
