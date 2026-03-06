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

export async function generateMetadata({ params }) {
    const { slug } = await params;
    const property = await getPropertyBySlug(slug);
    if (!property) {
        return { title: "Property Not Found — CheapHouse Japan" };
    }
    return {
        title: `${property.title_en || property.original_title || "Property"} — CheapHouse Japan`,
        description: property.summary_en || `Property listing in ${property.prefecture || "Japan"}`,
    };
}

export default async function PropertyDetailPage({ params }) {
    const { slug } = await params;
    const property = await getPropertyBySlug(slug);

    if (!property) {
        notFound();
    }

    return <PropertyDetail property={property} />;
}
