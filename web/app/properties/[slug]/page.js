import { notFound } from "next/navigation";
import { getSupabaseServer } from "../../lib/supabase-server";
import { getProperty as getMockProperty } from "../../lib/data";
import PropertyDetail from "./PropertyDetail";

async function getPropertyBySlug(slug) {
    try {
        const supabase = await getSupabaseServer();
        const { data, error } = await supabase
            .from("properties")
            .select("*")
            .eq("slug", slug)
            .eq("is_published", true)
            .single();

        if (error || !data) {
            // Fallback to mock data
            const mock = getMockProperty(slug);
            return mock || null;
        }
        return data;
    } catch {
        const mock = getMockProperty(slug);
        return mock || null;
    }
}

export const revalidate = 1800;

export async function generateMetadata({ params }) {
    const { slug } = await params;
    const property = await getPropertyBySlug(slug);
    if (!property) {
        return { title: "Property Not Found — CheapHouse" };
    }
    const title = `${property.title_en || property.original_title || "Property"} — CheapHouse`;
    const description = property.summary_en || `${property.prefecture || "Japan"} property listing — ¥${(property.price_jpy || 0).toLocaleString()}`;
    const ogImage = property.thumbnail_url || (Array.isArray(property.images) && property.images[0]?.url) || null;
    return {
        title,
        description,
        openGraph: {
            title,
            description,
            type: "article",
            ...(ogImage ? { images: [{ url: ogImage }] } : {}),
        },
    };
}

export default async function PropertyDetailPage({ params }) {
    const { slug } = await params;
    const property = await getPropertyBySlug(slug);

    if (!property) {
        notFound();
    }

    // JSON-LD Structured Data
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
            availability: "https://schema.org/InStock",
        },
        ...(property.prefecture ? { areaServed: { "@type": "Place", name: `${property.city || ""}, ${property.prefecture}, Japan` } } : {}),
    };

    return (
        <>
            <script
                type="application/ld+json"
                dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
            />
            <PropertyDetail property={property} />
        </>
    );
}
