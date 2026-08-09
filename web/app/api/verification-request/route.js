import { NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

function validHttpUrl(value) {
    try {
        const url = new URL(value);
        return url.protocol === "http:" || url.protocol === "https:";
    } catch {
        return false;
    }
}

export async function POST(request) {
    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
    const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
    if (!supabaseUrl || !serviceRoleKey) {
        return NextResponse.json({ error: "Request intake is temporarily unavailable." }, { status: 503 });
    }

    let payload;
    try {
        payload = await request.json();
    } catch {
        return NextResponse.json({ error: "Invalid request." }, { status: 400 });
    }

    const listingUrl = String(payload.listing_url || "").trim();
    const email = String(payload.email || "").trim().toLowerCase();
    const buyerGoal = String(payload.buyer_goal || "unknown").slice(0, 50);
    const notes = String(payload.notes || "").trim().slice(0, 2000);

    if (!validHttpUrl(listingUrl) || !/^\S+@\S+\.\S+$/.test(email)) {
        return NextResponse.json({ error: "Enter a valid listing URL and email." }, { status: 400 });
    }

    const supabase = createClient(supabaseUrl, serviceRoleKey, {
        auth: { persistSession: false, autoRefreshToken: false },
    });
    const { error } = await supabase.from("verification_requests").insert({
        listing_url: listingUrl,
        email,
        buyer_goal: buyerGoal,
        notes: notes || null,
        status: "new",
    });

    if (error) {
        console.error("Verification request insert failed:", error.message);
        return NextResponse.json({ error: "Request intake is temporarily unavailable." }, { status: 503 });
    }

    return NextResponse.json({ received: true }, { status: 201 });
}

