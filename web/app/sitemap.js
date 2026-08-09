import { getSupabaseServer } from "./lib/supabase-server";
import { getVerifiedCutoff } from "./lib/availability";

export default async function sitemap() {
    const baseUrl = process.env.NEXT_PUBLIC_SITE_URL || "https://cheaphouse.app";
    let properties = [];

    try {
        const supabase = await getSupabaseServer();
        const { data, error } = await supabase
            .from("properties")
            .select("slug, updated_at")
            .eq("is_published", true)
            .eq("admin_status", "approved")
            .eq("country", "japan")
            .eq("listing_status", "active")
            .gte("last_checked_at", getVerifiedCutoff());
        if (!error) properties = data || [];
    } catch {
        properties = [];
    }

    const propertyUrls = properties.map((property) => ({
        url: `${baseUrl}/properties/${property.slug}`,
        lastModified: property.updated_at || new Date().toISOString(),
        changeFrequency: "daily",
        priority: 0.8,
    }));

    return [
        { url: baseUrl, lastModified: new Date(), changeFrequency: "daily", priority: 1 },
        { url: `${baseUrl}/properties`, lastModified: new Date(), changeFrequency: "daily", priority: 0.9 },
        { url: `${baseUrl}/verify`, lastModified: new Date(), changeFrequency: "weekly", priority: 0.9 },
        ...propertyUrls,
    ];
}
