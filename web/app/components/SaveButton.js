"use client";

import { useState, useEffect } from "react";
import { getSupabaseBrowser } from "../lib/supabase-browser";

export default function SaveButton({ propertyId, size = 20 }) {
    const [saved, setSaved] = useState(false);
    const [user, setUser] = useState(null);
    const [showTooltip, setShowTooltip] = useState(false);

    useEffect(() => {
        const supabase = getSupabaseBrowser();
        supabase.auth.getUser().then(({ data: { user } }) => {
            setUser(user);
            if (user && propertyId) {
                supabase
                    .from("saved_properties")
                    .select("id")
                    .eq("user_id", user.id)
                    .eq("property_id", propertyId)
                    .maybeSingle()
                    .then(({ data }) => setSaved(!!data));
            }
        });
    }, [propertyId]);

    const handleToggle = async (e) => {
        e.preventDefault();
        e.stopPropagation();

        if (!user) {
            setShowTooltip(true);
            setTimeout(() => setShowTooltip(false), 2500);
            return;
        }

        // Optimistic update
        setSaved(!saved);
        const supabase = getSupabaseBrowser();

        try {
            if (saved) {
                await supabase.from("saved_properties").delete().eq("user_id", user.id).eq("property_id", propertyId);
            } else {
                await supabase.from("saved_properties").insert({ user_id: user.id, property_id: propertyId });
            }
        } catch {
            setSaved(saved); // revert on error
        }
    };

    return (
        <div style={{ position: "relative", display: "inline-flex" }}>
            <button
                onClick={handleToggle}
                aria-label={saved ? "Unsave property" : "Save property"}
                style={{
                    background: "none", border: "none", cursor: "pointer", padding: 4,
                    color: saved ? "var(--accent-rose)" : "var(--text-muted)",
                    fontSize: size, lineHeight: 1, transition: "transform 0.2s, color 0.2s",
                    transform: saved ? "scale(1.1)" : "scale(1)",
                }}
            >
                {saved ? "♥" : "♡"}
            </button>
            {showTooltip && (
                <div style={{
                    position: "absolute", bottom: "calc(100% + 8px)", left: "50%", transform: "translateX(-50%)",
                    background: "var(--bg-tertiary)", border: "1px solid var(--border-subtle)",
                    borderRadius: "var(--radius-md)", padding: "8px 12px", fontSize: 12,
                    color: "var(--text-secondary)", whiteSpace: "nowrap", zIndex: 10,
                }}>
                    <a href="/login" style={{ color: "var(--accent-blue)" }}>Sign in</a> to save properties
                </div>
            )}
        </div>
    );
}
