import { NextResponse } from 'next/server';
import Stripe from 'stripe';
import { getSupabaseServer } from '../../../lib/supabase-server';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY || 'sk_test_placeholder');

export async function POST() {
    try {
        const supabase = await getSupabaseServer();
        const { data: { user } } = await supabase.auth.getUser();

        if (!user) {
            return NextResponse.json({ error: 'Not authenticated' }, { status: 401 });
        }

        const { data: profile } = await supabase
            .from('user_profiles')
            .select('stripe_customer_id')
            .eq('id', user.id)
            .single();

        if (!profile?.stripe_customer_id) {
            return NextResponse.json({ error: 'No subscription found' }, { status: 400 });
        }

        const session = await stripe.billingPortal.sessions.create({
            customer: profile.stripe_customer_id,
            return_url: `${process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3000'}/account`,
        });

        return NextResponse.redirect(session.url, 303);
    } catch (error) {
        console.error('Portal error:', error);
        return NextResponse.json({ error: 'Failed to create portal session' }, { status: 500 });
    }
}
