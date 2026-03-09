"use client";

import { useEffect } from "react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

if (typeof window !== "undefined") {
    gsap.registerPlugin(ScrollTrigger);
}

export default function ScrollAnimations() {
    useEffect(() => {
        // Reduce motion check
        if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
        // Skip on mobile
        if (window.innerWidth < 768) return;

        const ctx = gsap.context(() => {
            // Fade up section headings
            gsap.utils.toArray("h2").forEach((el) => {
                gsap.from(el, {
                    y: 40,
                    opacity: 0,
                    duration: 0.8,
                    ease: "power3.out",
                    scrollTrigger: {
                        trigger: el,
                        start: "top 85%",
                        once: true,
                    },
                });
            });

            // Fade up glass-cards with stagger
            gsap.utils.toArray(".glass-card").forEach((el, i) => {
                gsap.from(el, {
                    y: 30,
                    opacity: 0,
                    duration: 0.6,
                    delay: (i % 3) * 0.1,
                    ease: "power2.out",
                    scrollTrigger: {
                        trigger: el,
                        start: "top 90%",
                        once: true,
                    },
                });
            });

            // Property cards stagger
            gsap.utils.toArray(".property-card").forEach((el, i) => {
                gsap.from(el, {
                    y: 40,
                    opacity: 0,
                    duration: 0.6,
                    delay: (i % 3) * 0.1,
                    ease: "power2.out",
                    scrollTrigger: {
                        trigger: el,
                        start: "top 90%",
                        once: true,
                    },
                });
            });
        });

        return () => ctx.revert();
    }, []);

    return null;
}
