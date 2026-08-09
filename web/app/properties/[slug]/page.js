import { notFound } from "next/navigation";
import { getSupabaseServer } from "../../lib/supabase-server";
import { getAvailability } from "../../lib/availability";
import PropertyDetail from "./PropertyDetail";

async function getPropertyBySlug(slug) {
    try {
        const supabase = await getSupabaseServer();
        const { data, error } = await supabase
            .from("properties")
            .select("*")
            .eq("slug", slug)
            .eq("is_published", true)
            .eq("country", "japan")
            .single();
        return error ? null : data;
    } catch {
        return null;
    }
}

export const revalidate = 900;

export async function generateMetadata({ params }) {
    const { slug } = await params;
    const property = await getPropertyBySlug(slug);
    if (!property) return { title: "Property Not Found — CheapHouse Japan" };
    return {
        title: `${property.title_en || property.original_title || "Property"} — CheapHouse Japan`,
        description: property.summary_en || `Evidence dossier for a property in ${property.prefecture || "Japan"}.`,
    };
}

export default async function PropertyDetailPage({ params }) {
    const { slug } = await params;
    const property = await getPropertyBySlug(slug);
    if (!property) notFound();

    const availability = getAvailability(property);
    const schemaAvailability = availability.key === "verified"
        ? "https://schema.org/InStock"
        : availability.key === "sold" || availability.key === "removed"
            ? "https://schema.org/SoldOut"
            : "https://schema.org/LimitedAvailability";
    const jsonLd = {
        "@context": "https://schema.org",
        "@type": "Product",
        name: property.title_en || property.original_title || "Property",
        description: property.summary_en || "",
        image: property.thumbnail_url || undefined,
        offers: {
            "@type": "Offer",
            price: property.price_jpy || 0,
            priceCurrency: "JPY",
            availability: schemaAvailability,
        },
    };

    return (
        <>
            <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />
            <PropertyDetail property={property} />
        </>
    );
}
