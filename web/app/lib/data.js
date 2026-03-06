/**
 * Mock property data for frontend development.
 * Replace with Supabase queries when the database is live.
 */

export const MOCK_PROPERTIES = [
    {
        id: "1",
        slug: "spacious-3ldk-sorachi",
        title_en: "Spacious 3LDK Home on a Large Lot in Sorachi District",
        summary_en:
            "This incredibly affordable 3LDK home in Kamisunagawachō, Sorachi-gun offers a rare chance to own a large Hokkaido property. Built in 1961, the home features 184.83 m² of living space on a generous lot. The area offers peaceful rural living with good access to local amenities. Renovation will be needed given the age, but the price makes this an attractive project property.",
        price_jpy: 100000,
        price_usd: 666,
        price_display: "¥100,000 (10万円, ~$666)",
        prefecture: "Hokkaido",
        city: "Kamisunagawachō",
        region: "Hokkaido",
        building_sqm: 184.83,
        land_sqm: 425.52,
        year_built: 1961,
        rooms: "3LDK",
        floors: 2,
        building_type: "detached",
        structure: "Wooden",
        condition_rating: "significant_renovation",
        renovation_estimate: "heavy",
        thumbnail_url:
            "https://images.unsplash.com/photo-1480074568708-e7b720bb3f09?w=600&h=400&fit=crop",
        images: [
            { url: "https://images.unsplash.com/photo-1480074568708-e7b720bb3f09?w=1200&h=800&fit=crop", caption: "Front exterior" },
            { url: "https://images.unsplash.com/photo-1513694203232-719a280e022f?w=1200&h=800&fit=crop", caption: "Living area" },
            { url: "https://images.unsplash.com/photo-1523217582562-09d0def993a6?w=1200&h=800&fit=crop", caption: "Garden view" },
        ],
        quality_score: 0.77,
        hazard_scores: {
            flood: { level: "low", summary: "Property is outside major flood-predicted areas." },
            landslide: { level: "none", summary: "No landslide warning zones near this property." },
            tsunami: { level: "none", summary: "Property is inland — tsunami risk does not apply." },
        },
        lifestyle_tags: [
            { tag: "pet-friendly", confidence: 0.8, reason: "Detached home with 425sqm land (garden space likely)" },
            { tag: "rural-retreat", confidence: 0.7, reason: "Located in Hokkaido prefecture countryside" },
            { tag: "retirement", confidence: 0.6, reason: "Affordable at ¥100,000 with 3LDK layout" },
        ],
        whats_attractive: [
            "Extremely affordable at just ¥100,000",
            "Spacious 3LDK layout with 184 sqm of living space",
            "Large lot (425 sqm) with garden potential",
        ],
        whats_unclear: [
            "Exact interior condition not described",
            "Insulation and heating system details unknown",
        ],
        whats_risky: [
            "Built in 1961 — before Japan's 1981 earthquake-resistance building code revision",
            "Heavy renovation likely needed given the age and price",
            "Remote area may have limited services and infrastructure",
        ],
        what_to_verify: [
            "Verify the property is still available before making plans",
            "Inspect for structural integrity, roof condition, and plumbing",
            "Check snow load requirements for Hokkaido properties",
            "Verify access road conditions in winter",
        ],
        freshness_label: "new",
        source_url: "https://www.oldhousesjapan.com/properties-2/spacious-3ldk-home-on-a-large-lot-in-sorachi-district",
    },
    {
        id: "2",
        slug: "classic-4ldk-otaru",
        title_en: "Classic 4LDK Home in Otaru, Hokkaido",
        summary_en:
            "This house is located in a quiet residential neighborhood of Otaru, giving you the feel of peaceful Hokkaido living while being just a short trip from Sapporo. Otaru is known for its historic canal, glasswork shops, and fresh seafood.",
        price_jpy: 768300,
        price_usd: 5122,
        price_display: "¥768,300 (76万円, ~$5,122)",
        prefecture: "Hokkaido",
        city: "Otaru",
        region: "Hokkaido",
        building_sqm: null,
        land_sqm: null,
        year_built: null,
        rooms: "4LDK",
        floors: 2,
        building_type: "detached",
        structure: "Wooden",
        condition_rating: "unknown",
        renovation_estimate: "unknown",
        thumbnail_url:
            "https://images.unsplash.com/photo-1570129477492-45c003edd2be?w=600&h=400&fit=crop",
        images: [
            { url: "https://images.unsplash.com/photo-1570129477492-45c003edd2be?w=1200&h=800&fit=crop", caption: "Street view" },
            { url: "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=1200&h=800&fit=crop", caption: "Exterior" },
        ],
        quality_score: 0.46,
        hazard_scores: {
            flood: { level: "low", summary: "Outside major flood-predicted areas." },
            landslide: { level: "moderate", summary: "Near a landslide caution zone due to hilly terrain." },
            tsunami: { level: "low", summary: "Low tsunami risk based on distance from coast." },
        },
        lifestyle_tags: [
            { tag: "family-ready", confidence: 0.6, reason: "4LDK layout with 4+ rooms" },
            { tag: "remote-work", confidence: 0.7, reason: "Otaru has good internet infrastructure" },
        ],
        whats_attractive: [
            "Located in charming Otaru — historic canal town near Sapporo",
            "4LDK layout suitable for families or remote workers",
            "Affordable by Japanese standards",
        ],
        whats_unclear: [
            "Building size is not listed",
            "Year built is not specified",
            "Property condition is not described",
        ],
        whats_risky: [
            "Missing key details (size, year, condition) make evaluation difficult",
            "Otaru has heavy snowfall — maintenance costs may be higher",
        ],
        what_to_verify: [
            "Request building size and year built from the listing source",
            "Inspect roof condition and snow damage",
            "Check local hazard maps at the municipal office",
        ],
        freshness_label: "new",
        source_url: "https://www.oldhousesjapan.com/properties-2/classic-4ldk-home-in-otaru",
    },
    {
        id: "3",
        slug: "coastal-muroran-home",
        title_en: "Wooden Home in Coastal Muroran, Hokkaido",
        summary_en:
            "This house is located in Muroran City, a coastal city in Hokkaido. Muroran offers a balance of urban convenience and access to nature, with dramatic coastal scenery and hot springs nearby.",
        price_jpy: 288150,
        price_usd: 1921,
        price_display: "¥288,150 (28万円, ~$1,921)",
        prefecture: "Hokkaido",
        city: "Muroran City",
        region: "Hokkaido",
        building_sqm: 110,
        land_sqm: 200,
        year_built: null,
        rooms: null,
        floors: null,
        building_type: "detached",
        structure: "Wooden",
        condition_rating: "needs_work",
        renovation_estimate: "moderate",
        thumbnail_url:
            "https://images.unsplash.com/photo-1568605114967-8130f3a36994?w=600&h=400&fit=crop",
        images: [
            { url: "https://images.unsplash.com/photo-1568605114967-8130f3a36994?w=1200&h=800&fit=crop", caption: "Front" },
        ],
        quality_score: 0.54,
        hazard_scores: {
            flood: { level: "low", summary: "Outside major flood-predicted areas." },
            landslide: { level: "low", summary: "Outside designated landslide warning zones." },
            tsunami: { level: "moderate", summary: "Coastal area with moderate tsunami risk." },
        },
        lifestyle_tags: [
            { tag: "rural-retreat", confidence: 0.6, reason: "Coastal Hokkaido setting" },
            { tag: "retirement", confidence: 0.5, reason: "Affordable at ¥288,150" },
        ],
        whats_attractive: [
            "Affordable coastal living at under ¥300,000",
            "110 sqm of living space on 200 sqm lot",
            "Muroran has hot springs and dramatic scenery",
        ],
        whats_unclear: [
            "Year built is not specified",
            "Room layout is not listed",
            "Interior condition not described",
        ],
        whats_risky: [
            "Coastal location means moderate tsunami risk",
            "Muroran's industrial economy has been declining",
        ],
        what_to_verify: [
            "Check tsunami evacuation routes from the property",
            "Verify distance to nearest hospital and grocery store",
            "Inspect for salt air corrosion damage",
        ],
        freshness_label: "recent",
        source_url: "https://www.oldhousesjapan.com/properties-2/wooden-home-in-coastal-muroran",
    },
    {
        id: "4",
        slug: "traditional-hofu-yamaguchi",
        title_en: "Traditional 7DK House in Hofu, Yamaguchi",
        summary_en:
            "A Japanese-style two-story house with wooden tiles where you can enjoy a slow life surrounded by nature. There are two sunrooms on a large 659 sqm site. The property features 133 sqm of building space built in 1975. A characterful home for someone wanting authentic rural Japanese living.",
        price_jpy: 2300000,
        price_usd: 14746,
        price_display: "¥2,300,000 (230万円, ~$14,746)",
        prefecture: "Yamaguchi",
        city: "Hofu Shi",
        region: "Chugoku",
        building_sqm: 133,
        land_sqm: 659,
        year_built: 1975,
        rooms: "7DK + 2 solariums",
        floors: 2,
        building_type: "detached",
        structure: "Wooden tile roof",
        condition_rating: "fair",
        renovation_estimate: "moderate",
        thumbnail_url:
            "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=600&h=400&fit=crop",
        images: [
            { url: "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=1200&h=800&fit=crop", caption: "Traditional facade" },
            { url: "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=1200&h=800&fit=crop", caption: "Garden" },
            { url: "https://images.unsplash.com/photo-1600566753086-00f18fb6b3ea?w=1200&h=800&fit=crop", caption: "Interior" },
            { url: "https://images.unsplash.com/photo-1600573472591-ee6c563cb8a0?w=1200&h=800&fit=crop", caption: "Kitchen area" },
        ],
        quality_score: 0.85,
        hazard_scores: {
            flood: { level: "low", summary: "Outside major flood-predicted areas." },
            landslide: { level: "low", summary: "No landslide warning zones nearby." },
            tsunami: { level: "none", summary: "Property is inland." },
        },
        lifestyle_tags: [
            { tag: "pet-friendly", confidence: 0.85, reason: "Detached with 659sqm land and nature surroundings" },
            { tag: "artist-retreat", confidence: 0.7, reason: "Sunrooms and large lot in nature" },
            { tag: "family-ready", confidence: 0.7, reason: "7DK layout with ample space" },
            { tag: "rural-retreat", confidence: 0.8, reason: "Nature-surrounded setting in Yamaguchi" },
        ],
        whats_attractive: [
            "Traditional Japanese architecture with character",
            "Very large lot (659 sqm) with two sunrooms",
            "7 rooms plus solariums — enormous space for the price",
            "Surrounded by nature, ideal for slow living",
        ],
        whats_unclear: [
            "Exact renovation status not detailed",
            "Internet connectivity in rural area unknown",
        ],
        whats_risky: [
            "Built in 1975 — before the 1981 seismic code update",
            "Wooden tile roof may need replacement or repair",
            "Rural location may mean limited English-language services",
        ],
        what_to_verify: [
            "Inspect the roof, especially wooden tile condition",
            "Check for termite damage — critical for wooden homes in western Japan",
            "Verify internet availability (fiber, satellite options)",
            "Visit Hofu to understand the local community",
        ],
        freshness_label: "new",
        source_url: "https://www.allakiyas.com/en/yamaguchi-ken/traditional-house/for-sale/",
    },
    {
        id: "5",
        slug: "countryside-joetsu-niigata",
        title_en: "Countryside Home in Jōetsu, Niigata",
        summary_en:
            "An enormous amount of space, privacy, and rural charm for practically nothing. This 10K home offers 126 sqm of living space in a quiet countryside setting. The listing is part of a growing trend of ultra-affordable akiya in Niigata prefecture.",
        price_jpy: 1050,
        price_usd: 7,
        price_display: "¥1,050 (~$7)",
        prefecture: "Niigata",
        city: "Jōetsu",
        region: "Chubu",
        building_sqm: 126.39,
        land_sqm: 380,
        year_built: null,
        rooms: "10K",
        floors: 2,
        building_type: "detached",
        structure: "Wooden",
        condition_rating: "significant_renovation",
        renovation_estimate: "heavy",
        thumbnail_url:
            "https://images.unsplash.com/photo-1605276374104-dee2a0ed3cd6?w=600&h=400&fit=crop",
        images: [
            { url: "https://images.unsplash.com/photo-1605276374104-dee2a0ed3cd6?w=1200&h=800&fit=crop", caption: "Property view" },
            { url: "https://images.unsplash.com/photo-1599427303058-f04cbcf4756f?w=1200&h=800&fit=crop", caption: "Surroundings" },
        ],
        quality_score: 0.62,
        hazard_scores: {
            flood: { level: "moderate", summary: "Located in Niigata — some flood risk during heavy rain." },
            landslide: { level: "low", summary: "Outside designated warning zones." },
            tsunami: { level: "none", summary: "Inland location." },
        },
        lifestyle_tags: [
            { tag: "rural-retreat", confidence: 0.9, reason: "Remote Niigata countryside setting" },
            { tag: "pet-friendly", confidence: 0.7, reason: "Large lot with garden space" },
            { tag: "artist-retreat", confidence: 0.6, reason: "10 rooms provides studio/workshop potential" },
        ],
        whats_attractive: [
            "Listed at just ¥1,050 — essentially free",
            "10-room layout offers enormous creative flexibility",
            "126 sqm building on 380 sqm lot",
            "Peaceful countryside location in Niigata",
        ],
        whats_unclear: [
            "Year built is not specified — could be very old",
            "Interior condition not described at all",
            "Whether water, electricity, and gas are connected",
        ],
        whats_risky: [
            "Price near zero suggests significant hidden costs (renovation, clearing)",
            "Niigata receives heavy snowfall — structural concerns likely",
            "May be in a declining community with aging population",
            "Heavy renovation will be expensive regardless of purchase price",
        ],
        what_to_verify: [
            "Visit the property in person — at this price, surprises are likely",
            "Verify all utilities are connected and functional",
            "Get a structural assessment before committing to renovation",
            "Check local municipality for any financial support programs",
        ],
        freshness_label: "new",
        source_url: "https://www.oldhousesjapan.com/properties-2/a-rare-1-000-yen-countryside-home-in-joetsu",
    },
    {
        id: "6",
        slug: "nagato-coastal-yamaguchi",
        title_en: "Coastal 6K Home near Aomi Island, Yamaguchi",
        summary_en:
            "A two-story building in the Aomi Island area, facing the street for easy access. The building is in relatively good condition compared to other akiya bank listings. The scenic 'Wave Bridge' is nearby.",
        price_jpy: 2980000,
        price_usd: 19866,
        price_display: "¥2,980,000 (298万円, ~$19,866)",
        prefecture: "Yamaguchi",
        city: "Nagato Shi",
        region: "Chugoku",
        building_sqm: 112,
        land_sqm: 153,
        year_built: 1985,
        rooms: "6K",
        floors: 2,
        building_type: "detached",
        structure: "Wooden tile roof",
        condition_rating: "fair",
        renovation_estimate: "light",
        thumbnail_url:
            "https://images.unsplash.com/photo-1588880331179-bc9b93a8cb5e?w=600&h=400&fit=crop",
        images: [
            { url: "https://images.unsplash.com/photo-1588880331179-bc9b93a8cb5e?w=1200&h=800&fit=crop", caption: "View" },
            { url: "https://images.unsplash.com/photo-1600047509807-ba8f99d2cdde?w=1200&h=800&fit=crop", caption: "Interior" },
        ],
        quality_score: 0.69,
        hazard_scores: {
            flood: { level: "low", summary: "Outside flood zones." },
            landslide: { level: "low", summary: "No warning zones nearby." },
            tsunami: { level: "moderate", summary: "Coastal area — moderate tsunami risk." },
        },
        lifestyle_tags: [
            { tag: "low-renovation", confidence: 0.7, reason: "Condition fair, built in 1985" },
            { tag: "retirement", confidence: 0.6, reason: "Scenic coastal location, affordable" },
        ],
        whats_attractive: [
            "Scenic coastal location near Aomi Island",
            "Relatively good condition for an akiya bank listing",
            "Street-facing for easy access",
            "Built in 1985 — post-earthquake code",
        ],
        whats_unclear: [
            "Room layout details beyond '6K' not specified",
            "Parking situation unclear",
        ],
        whats_risky: [
            "Moderate tsunami risk due to coastal location",
            "Nagato is a small city with limited services",
        ],
        what_to_verify: [
            "Check tsunami evacuation routes",
            "Verify proximity to Wave Bridge scenic area",
            "Inspect for salt air corrosion on the exterior",
        ],
        freshness_label: "recent",
        source_url: "https://www.allakiyas.com/en/yamaguchi-ken/traditional-house/for-sale/",
    },
];

export const PREFECTURES = [
    "All Prefectures",
    "Hokkaido",
    "Aomori",
    "Akita",
    "Iwate",
    "Yamagata",
    "Niigata",
    "Nagano",
    "Kyoto",
    "Nara",
    "Wakayama",
    "Tottori",
    "Shimane",
    "Okayama",
    "Hiroshima",
    "Yamaguchi",
    "Ehime",
    "Kochi",
    "Oita",
    "Kumamoto",
    "Miyazaki",
    "Kagoshima",
];

export const LIVING_PROFILES = {
    "pet-friendly": { label: "🐕 Dog-Friendly", color: "green" },
    "artist-retreat": { label: "🎨 Artist Retreat", color: "violet" },
    "remote-work": { label: "💻 Remote Work", color: "blue" },
    "low-renovation": { label: "🔧 Low-Stress Move-In", color: "green" },
    "near-station": { label: "🚉 Near Station", color: "blue" },
    "rural-retreat": { label: "🏔️ Rural Retreat", color: "green" },
    "family-ready": { label: "👨‍👩‍👧 Family Ready", color: "amber" },
    "retirement": { label: "🏖️ Retirement Pace", color: "amber" },
};

export function getProperty(slug) {
    return MOCK_PROPERTIES.find((p) => p.slug === slug);
}

export function formatPrice(price_jpy) {
    if (!price_jpy) return "Price TBD";
    if (price_jpy >= 10000) {
        const man = Math.round(price_jpy / 10000);
        return `¥${price_jpy.toLocaleString()} (${man}万円)`;
    }
    return `¥${price_jpy.toLocaleString()}`;
}

export function formatArea(sqm) {
    if (!sqm) return "—";
    return `${sqm.toLocaleString()} m²`;
}
