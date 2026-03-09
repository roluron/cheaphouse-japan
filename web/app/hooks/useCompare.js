"use client";

import { useState, useEffect, useCallback } from "react";

const MAX_COMPARE = 3;
const STORAGE_KEY = "cheaphouse_compare";

export function useCompare() {
    const [compareIds, setCompareIds] = useState([]);

    useEffect(() => {
        try {
            const stored = localStorage.getItem(STORAGE_KEY);
            if (stored) setCompareIds(JSON.parse(stored));
        } catch { }
    }, []);

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
