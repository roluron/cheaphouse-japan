import { getSupabaseServer } from "./lib/supabase-server";

export default async function sitemap() {
    const supabase = await getSupabaseServer();
    const { data: properties } = await supabase
        .from("properties")
        .select("slug, updated_at")
        .eq("is_published", true)
        .eq("admin_status", "approved")
        .eq("listing_status", "active");

    const propertyUrls = (properties || []).map((p) => ({
        url: `https://cheaphouse.app/properties/${p.slug}`,
        lastModified: p.updated_at || new Date().toISOString(),
        changeFrequency: "weekly",
        priority: 0.8,
    }));

    return [
        { url: "https://cheaphouse.app", lastModified: new Date(), changeFrequency: "daily", priority: 1 },
        { url: "https://cheaphouse.app/properties", lastModified: new Date(), changeFrequency: "daily", priority: 0.9 },
        { url: "https://cheaphouse.app/pricing", changeFrequency: "monthly", priority: 0.6 },
        { url: "https://cheaphouse.app/quiz", changeFrequency: "monthly", priority: 0.7 },
        ...propertyUrls,
    ];
}
