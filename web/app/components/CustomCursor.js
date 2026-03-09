"use client";

import { useEffect, useRef } from "react";

export default function CustomCursor() {
    const cursorRef = useRef(null);
    const dotRef = useRef(null);

    useEffect(() => {
        // Skip on touch devices
        if ("ontouchstart" in window || navigator.maxTouchPoints > 0) return;

        const cursor = cursorRef.current;
        const dot = dotRef.current;
        if (!cursor || !dot) return;

        let mouseX = -100, mouseY = -100;
        let isHovering = false;

        const onMouseMove = (e) => {
            mouseX = e.clientX;
            mouseY = e.clientY;
            // Dot follows instantly
            dot.style.transform = `translate(${mouseX - 3}px, ${mouseY - 3}px)`;
            // Ring follows with slight CSS transition
            cursor.style.transform = `translate(${mouseX - (isHovering ? 20 : 8)}px, ${mouseY - (isHovering ? 20 : 8)}px)`;
        };

        const onMouseOver = (e) => {
            const target = e.target.closest("a, button, .property-card, [role='button'], input, select, textarea");
            if (target) {
                isHovering = true;
                cursor.style.width = "40px";
                cursor.style.height = "40px";
                cursor.style.borderColor = "rgba(56, 189, 248, 0.3)";
                cursor.style.background = "rgba(56, 189, 248, 0.05)";
            }
        };

        const onMouseOut = (e) => {
            const target = e.target.closest("a, button, .property-card, [role='button'], input, select, textarea");
            if (target) {
                isHovering = false;
                cursor.style.width = "16px";
                cursor.style.height = "16px";
                cursor.style.borderColor = "rgba(56, 189, 248, 0.5)";
                cursor.style.background = "transparent";
            }
        };

        document.addEventListener("mousemove", onMouseMove, { passive: true });
        document.addEventListener("mouseover", onMouseOver, { passive: true });
        document.addEventListener("mouseout", onMouseOut, { passive: true });

        // Hide default cursor
        const style = document.createElement("style");
        style.textContent = "@media (pointer: fine) { *, *::before, *::after { cursor: none !important; } }";
        document.head.appendChild(style);

        return () => {
            document.removeEventListener("mousemove", onMouseMove);
            document.removeEventListener("mouseover", onMouseOver);
            document.removeEventListener("mouseout", onMouseOut);
            style.remove();
        };
    }, []);

    // Don't render on SSR
    return (
        <>
            {/* Outer ring */}
            <div
                ref={cursorRef}
                style={{
                    position: "fixed", top: 0, left: 0,
                    width: 16, height: 16, borderRadius: "50%",
                    border: "1.5px solid rgba(56, 189, 248, 0.5)",
                    background: "transparent",
                    pointerEvents: "none", zIndex: 9999,
                    transition: "width 0.2s, height 0.2s, background 0.2s, border-color 0.2s, transform 0.06s linear",
                    willChange: "transform",
                }}
            />
            {/* Inner dot */}
            <div
                ref={dotRef}
                style={{
                    position: "fixed", top: 0, left: 0,
                    width: 6, height: 6, borderRadius: "50%",
                    background: "rgba(56, 189, 248, 0.8)",
                    pointerEvents: "none", zIndex: 9999,
                    willChange: "transform",
                }}
            />
        </>
    );
}
