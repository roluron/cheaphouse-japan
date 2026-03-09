/**
 * Compute a match score between quiz answers and a property.
 * Returns { score: 0-1, breakdown: { ... } }
 */

const BUDGET_BRACKETS = [
    { label: "under-1m", min: 0, max: 1_000_000 },
    { label: "1-3m", min: 1_000_000, max: 3_000_000 },
    { label: "3-5m", min: 3_000_000, max: 5_000_000 },
    { label: "5-10m", min: 5_000_000, max: 10_000_000 },
    { label: "10-20m", min: 10_000_000, max: 20_000_000 },
    { label: "over-20m", min: 20_000_000, max: Infinity },
];

const WEIGHTS = {
    budget_fit: 3,
    lifestyle_match: 2,
    risk_tolerance: 2,
    condition_fit: 2,
    transport_fit: 1,
    environment_fit: 1,
};

export function computeMatchScore(quizAnswers, property) {
    if (!quizAnswers || !property) return { score: 0, breakdown: {} };

    const breakdown = {};

    // 1. Budget fit
    const userBracketIdx = BUDGET_BRACKETS.findIndex(b => b.label === quizAnswers.budget);
    const price = property.price_jpy || 0;
    const propertyBracketIdx = BUDGET_BRACKETS.findIndex(b => price >= b.min && price < b.max);

    if (userBracketIdx >= 0 && propertyBracketIdx >= 0) {
        const diff = Math.abs(userBracketIdx - propertyBracketIdx);
        const score = diff === 0 ? 1.0 : diff === 1 ? 0.7 : diff === 2 ? 0.3 : 0;
        const reason = diff === 0 ? "Within your budget range" : diff === 1 ? "Close to your budget" : diff === 2 ? "Outside your budget" : "Far outside your budget";
        breakdown.budget_fit = { score, reason };
    } else {
        breakdown.budget_fit = { score: 0.5, reason: "Budget data incomplete" };
    }

    // 2. Lifestyle match
    const tags = Array.isArray(property.lifestyle_tags) ? property.lifestyle_tags : [];
    const tagNames = tags.map(t => t.tag || t);
    let lifestyleScore = 0.5;
    let lifestyleReason = "No lifestyle data available";

    const desiredTags = [];
    if (quizAnswers.purpose === "primary-residence") desiredTags.push("family-ready", "retirement-pace");
    if (quizAnswers.purpose === "vacation-retreat") desiredTags.push("weekend-retreat", "artist-retreat");
    if (quizAnswers.purpose === "creative-studio") desiredTags.push("artist-retreat", "remote-work");
    if (quizAnswers.purpose === "investment") desiredTags.push("near-station");
    if (quizAnswers.animals === "dogs") desiredTags.push("dog-friendly");
    if (quizAnswers.animals === "cats" || quizAnswers.animals === "other") desiredTags.push("dog-friendly");

    if (desiredTags.length > 0 && tags.length > 0) {
        const matches = desiredTags.filter(d => tagNames.includes(d)).length;
        lifestyleScore = Math.min(1, matches / Math.max(1, desiredTags.length) + 0.2);
        lifestyleReason = matches > 0 ? `Matches ${matches} of your lifestyle preferences` : "No matching lifestyle tags";
    }
    breakdown.lifestyle_match = { score: lifestyleScore, reason: lifestyleReason };

    // 3. Risk tolerance
    const hazards = property.hazard_scores || {};
    const levels = Object.values(hazards).map(h => h?.level || "none");
    const maxLevel = levels.includes("high") ? "high" : levels.includes("moderate") ? "moderate" : levels.includes("low") ? "low" : "none";
    const riskMap = { "minimal": { none: 1, low: 0.8, moderate: 0.3, high: 0 }, "some-ok": { none: 1, low: 1, moderate: 0.7, high: 0.3 }, "unconcerned": { none: 1, low: 1, moderate: 1, high: 0.8 } };
    const riskTable = riskMap[quizAnswers.risk_tolerance] || riskMap["some-ok"];
    const riskScore = riskTable[maxLevel] ?? 0.5;
    breakdown.risk_tolerance = { score: riskScore, reason: maxLevel === "none" ? "No hazard risks detected" : `${maxLevel} hazard level vs your ${quizAnswers.risk_tolerance || "moderate"} tolerance` };

    // 4. Condition fit
    const condMap = { "move-in-ready": { good: 1, fair: 0.7, needs_work: 0.2, significant_renovation: 0, unknown: 0.4 }, "minor-cosmetic": { good: 1, fair: 1, needs_work: 0.5, significant_renovation: 0.2, unknown: 0.5 }, "moderate-renovation": { good: 1, fair: 1, needs_work: 1, significant_renovation: 0.5, unknown: 0.6 }, "major-renovation": { good: 1, fair: 1, needs_work: 1, significant_renovation: 1, unknown: 0.7 } };
    const condTable = condMap[quizAnswers.renovation] || condMap["moderate-renovation"];
    const condScore = condTable[property.condition_rating] ?? 0.5;
    breakdown.condition_fit = { score: condScore, reason: `Property condition "${property.condition_rating || "unknown"}" vs your preference "${quizAnswers.renovation || "flexible"}"` };

    // 5. Transport fit
    const nearStation = tagNames.includes("near-station") || (property.station_distance && parseFloat(property.station_distance) < 2);
    const transportMap = { "must-near-station": nearStation ? 1 : 0.2, "occasional": nearStation ? 1 : 0.6, "have-car": 0.8, "full-remote": 1 };
    const transportScore = transportMap[quizAnswers.transport] ?? 0.7;
    breakdown.transport_fit = { score: transportScore, reason: nearStation ? "Near a train station" : "Limited public transport access" };

    // 6. Environment fit
    let envScore = 0.6;
    const envReason = `Located in ${property.region || property.prefecture || "Japan"}`;
    const ruralPrefectures = ["Hokkaido", "Akita", "Iwate", "Nagano", "Tottori", "Shimane", "Kochi", "Tokushima"];
    const coastalPrefectures = ["Okinawa", "Kanagawa", "Chiba", "Shizuoka", "Mie", "Wakayama"];
    const isRural = ruralPrefectures.includes(property.prefecture);
    const isCoastal = coastalPrefectures.includes(property.prefecture);

    if (quizAnswers.environment === "countryside" && isRural) envScore = 1;
    else if (quizAnswers.environment === "coastal" && isCoastal) envScore = 1;
    else if (quizAnswers.environment === "city" && !isRural) envScore = 0.7;
    else if (quizAnswers.environment === "mountain" && ["Nagano", "Yamanashi", "Gifu"].includes(property.prefecture)) envScore = 1;
    breakdown.environment_fit = { score: envScore, reason: envReason };

    // Weighted average
    let totalWeight = 0;
    let weightedSum = 0;
    for (const [key, weight] of Object.entries(WEIGHTS)) {
        const dim = breakdown[key];
        if (dim) {
            weightedSum += dim.score * weight;
            totalWeight += weight;
        }
    }
    const score = totalWeight > 0 ? weightedSum / totalWeight : 0;

    return { score: Math.round(score * 100) / 100, breakdown };
}
