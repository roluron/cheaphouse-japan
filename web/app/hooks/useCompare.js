"use client";

import { useState, useCallback } from "react";

const MAX_COMPARE = 3;
const STORAGE_KEY = "cheaphouse_compare";

export function useCompare() {
    const [compareIds, setCompareIds] = useState(() => {
        try {
            if (typeof window === "undefined") return [];
            const stored = localStorage.getItem(STORAGE_KEY);
            return stored ? JSON.parse(stored) : [];
        } catch { return []; }
    });

    const persist = useCallback((ids) => {
        setCompareIds(ids);
        try { localStorage.setItem(STORAGE_KEY, JSON.stringify(ids)); } catch { }
    }, []);

    const addToCompare = useCallback((id) => {
        setCompareIds((prev) => {
            if (prev.includes(id) || prev.length >= MAX_COMPARE) return prev;
            const next = [...prev, id];
            try { localStorage.setItem(STORAGE_KEY, JSON.stringify(next)); } catch { }
            return next;
        });
    }, []);

    const removeFromCompare = useCallback((id) => {
        setCompareIds((prev) => {
            const next = prev.filter((x) => x !== id);
            try { localStorage.setItem(STORAGE_KEY, JSON.stringify(next)); } catch { }
            return next;
        });
    }, []);

    const clearCompare = useCallback(() => {
        persist([]);
    }, [persist]);

    const isInCompare = useCallback((id) => compareIds.includes(id), [compareIds]);

    return { compareIds, addToCompare, removeFromCompare, clearCompare, isInCompare };
}
