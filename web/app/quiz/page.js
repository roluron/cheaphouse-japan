"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { getSupabaseBrowser } from "../lib/supabase-browser";

const QUESTIONS = [
    {
        id: "budget",
        title: "What's your budget range?",
        subtitle: "Property prices in Japan can start incredibly low",
        options: [
            { value: "under-1m", label: "Under ¥1M", desc: "~$6,700" },
            { value: "1-3m", label: "¥1–3M", desc: "~$6,700–$20,000" },
            { value: "3-5m", label: "¥3–5M", desc: "~$20,000–$33,000" },
            { value: "5-10m", label: "¥5–10M", desc: "~$33,000–$67,000" },
            { value: "10-20m", label: "¥10–20M", desc: "~$67,000–$133,000" },
            { value: "over-20m", label: "Over ¥20M", desc: "$133,000+" },
        ],
    },
    {
        id: "purpose",
        title: "What will this home be for?",
        subtitle: "This helps us match lifestyle features to your needs",
        options: [
            { value: "primary-residence", label: "Primary Residence", desc: "Your main home" },
            { value: "second-home", label: "Second Home", desc: "Weekend getaway" },
            { value: "vacation-retreat", label: "Vacation Retreat", desc: "Seasonal escape" },
            { value: "creative-studio", label: "Creative Studio", desc: "Workshop or studio" },
            { value: "investment", label: "Investment", desc: "Rental or flip" },
            { value: "not-sure", label: "Not Sure Yet", desc: "Just exploring" },
        ],
    },
    {
        id: "renovation",
        title: "How much work are you willing to do?",
        subtitle: "Many cheap properties in Japan need some renovation",
        options: [
            { value: "move-in-ready", label: "Move-in Ready Only", desc: "No renovation work" },
            { value: "minor-cosmetic", label: "Minor Cosmetic Work", desc: "Paint, floors, fixtures" },
            { value: "moderate-renovation", label: "Moderate Renovation", desc: "Kitchen, bath updates" },
            { value: "major-renovation", label: "Major Renovation OK", desc: "Structural work fine" },
        ],
    },
    {
        id: "animals",
        title: "Do you have or plan to have pets?",
        subtitle: "We'll match properties with suitable outdoor space",
        options: [
            { value: "dogs", label: "Yes, Dogs", desc: "Need yard space" },
            { value: "cats", label: "Yes, Cats", desc: "Indoor-friendly" },
            { value: "other", label: "Yes, Other Animals", desc: "Farm animals, etc." },
            { value: "no-pets", label: "No Pets", desc: "" },
        ],
    },
    {
        id: "transport",
        title: "How important is public transport?",
        subtitle: "Japan has excellent rail — but rural areas may be limited",
        options: [
            { value: "must-near-station", label: "Must Be Near Station", desc: "Walking distance" },
            { value: "occasional", label: "Occasional Access Fine", desc: "Bus or short drive" },
            { value: "have-car", label: "I'll Have a Car", desc: "Don't need transit" },
            { value: "full-remote", label: "Full Remoteness OK", desc: "Off the grid" },
        ],
    },
    {
        id: "risk_tolerance",
        title: "How do you feel about natural hazard zones?",
        subtitle: "Japan has earthquake, flood, and landslide risk areas",
        options: [
            { value: "minimal", label: "Minimal Risk Only", desc: "Safety first" },
            { value: "some-ok", label: "Some Risk is OK", desc: "If the deal is good" },
            { value: "unconcerned", label: "Doesn't Concern Me", desc: "Price matters more" },
        ],
    },
    {
        id: "environment",
        title: "What setting appeals to you most?",
        subtitle: "Japan offers incredible variety of landscapes",
        options: [
            { value: "city", label: "City or Near City", desc: "Urban convenience" },
            { value: "suburban", label: "Suburban", desc: "Quiet but connected" },
            { value: "countryside", label: "Countryside", desc: "Rural, open spaces" },
            { value: "mountain", label: "Mountain Area", desc: "Elevated, forested" },
            { value: "coastal", label: "Coastal", desc: "Near the ocean" },
            { value: "forest", label: "Deep Forest", desc: "Maximum seclusion" },
        ],
    },
];

export default function QuizPage() {
    const router = useRouter();
    const [step, setStep] = useState(0);
    const [answers, setAnswers] = useState({});
    const [direction, setDirection] = useState(1); // 1=forward, -1=back

    const question = QUESTIONS[step];
    const progress = ((step + 1) / QUESTIONS.length) * 100;

    const handleSelect = (value) => {
        setAnswers((prev) => ({ ...prev, [question.id]: value }));
    };

    const handleNext = () => {
        if (step < QUESTIONS.length - 1) {
            setDirection(1);
            setStep(step + 1);
        } else {
            handleComplete();
        }
    };

    const handleBack = () => {
        if (step > 0) {
            setDirection(-1);
            setStep(step - 1);
        }
    };

    const handleComplete = async () => {
        // Save to Supabase if logged in, otherwise localStorage
        try {
            const supabase = getSupabaseBrowser();
            const { data: { user } } = await supabase.auth.getUser();
            if (user) {
                await supabase
                    .from("user_profiles")
                    .update({ quiz_answers: answers })
                    .eq("id", user.id);
            }
        } catch { }
        localStorage.setItem("cheaphouse_quiz", JSON.stringify(answers));
        router.push("/properties");
    };

    const isSelected = answers[question.id];

    return (
        <div style={{ minHeight: "100vh", background: "var(--bg-primary)", display: "flex", flexDirection: "column" }}>
            {/* Progress bar */}
            <div style={{ position: "fixed", top: 0, left: 0, right: 0, height: 4, background: "var(--bg-tertiary)", zIndex: 100 }}>
                <div style={{ height: "100%", width: `${progress}%`, background: "var(--gradient-primary)", transition: "width 0.4s ease" }} />
            </div>

            {/* Header */}
            <div style={{ padding: "24px 32px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <Link href="/" style={{ textDecoration: "none", fontFamily: "var(--font-display)", fontSize: 18 }}>
                    <span className="text-gradient">Cheap</span>House Japan
                </Link>
                <span style={{ fontSize: 13, color: "var(--text-muted)" }}>
                    {step + 1} of {QUESTIONS.length}
                </span>
            </div>

            {/* Question */}
            <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", padding: "0 24px" }}>
                <div
                    key={step}
                    style={{
                        maxWidth: 640, width: "100%", textAlign: "center",
                        animation: `fadeSlide${direction > 0 ? "Right" : "Left"} 0.35s ease`,
                    }}
                >
                    <h1 style={{ fontSize: 32, fontWeight: 700, marginBottom: 8, fontFamily: "var(--font-display)" }}>
                        {question.title}
                    </h1>
                    <p style={{ color: "var(--text-secondary)", fontSize: 15, marginBottom: 40 }}>
                        {question.subtitle}
                    </p>

                    <div style={{
                        display: "grid",
                        gridTemplateColumns: question.options.length <= 4 ? "1fr 1fr" : "1fr 1fr 1fr",
                        gap: 12,
                        maxWidth: 520,
                        margin: "0 auto",
                    }}>
                        {question.options.map((opt) => (
                            <button
                                key={opt.value}
                                onClick={() => handleSelect(opt.value)}
                                className="glass-card"
                                style={{
                                    padding: "20px 16px",
                                    textAlign: "center",
                                    cursor: "pointer",
                                    border: answers[question.id] === opt.value
                                        ? "2px solid var(--accent-blue)"
                                        : "2px solid transparent",
                                    background: answers[question.id] === opt.value
                                        ? "rgba(56,189,248,0.08)"
                                        : undefined,
                                    transition: "all 0.2s ease",
                                    fontFamily: "inherit",
                                    color: "inherit",
                                }}
                            >
                                <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 4 }}>{opt.label}</div>
                                {opt.desc && <div style={{ fontSize: 12, color: "var(--text-muted)" }}>{opt.desc}</div>}
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            {/* Navigation */}
            <div style={{ padding: "24px 32px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <button
                    onClick={handleBack}
                    disabled={step === 0}
                    style={{
                        background: "none", border: "none", color: step === 0 ? "var(--text-muted)" : "var(--text-secondary)",
                        cursor: step === 0 ? "default" : "pointer", fontSize: 14, fontFamily: "inherit",
                    }}
                >
                    ← Back
                </button>
                <button
                    onClick={handleNext}
                    disabled={!isSelected}
                    className="btn btn-primary"
                    style={{
                        padding: "12px 32px", opacity: isSelected ? 1 : 0.4,
                        cursor: isSelected ? "pointer" : "default",
                    }}
                >
                    {step === QUESTIONS.length - 1 ? "See My Matches →" : "Next →"}
                </button>
            </div>

            <style>{`
                @keyframes fadeSlideRight {
                    from { opacity: 0; transform: translateX(30px); }
                    to { opacity: 1; transform: translateX(0); }
                }
                @keyframes fadeSlideLeft {
                    from { opacity: 0; transform: translateX(-30px); }
                    to { opacity: 1; transform: translateX(0); }
                }
            `}</style>
        </div>
    );
}
