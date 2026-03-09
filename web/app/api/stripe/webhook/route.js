import { NextResponse } from 'next/server';
import Stripe from 'stripe';
import { createClient } from '@supabase/supabase-js';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY || 'sk_test_placeholder');
const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET;

// Use service role client for webhook (no user session)
const supabase = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL,
    process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
);

export async function POST(request) {
    const body = await request.text();
    const sig = request.headers.get('stripe-signature');

    let event;
    try {
        if (webhookSecret && sig) {
            event = stripe.webhooks.constructEvent(body, sig, webhookSecret);
        } else {
            event = JSON.parse(body);
        }
    } catch (err) {
        console.error('Webhook signature verification failed:', err.message);
        return NextResponse.json({ error: 'Invalid signature' }, { status: 400 });
    }

    try {
        switch (event.type) {
            case 'checkout.session.completed': {
                const session = event.data.object;
                const userId = session.client_reference_id;
                if (userId) {
                    await supabase.from('user_profiles').update({
                        subscription_status: 'active',
                        stripe_customer_id: session.customer,
                        stripe_subscription_id: session.subscription,
                    }).eq('id', userId);
                }
                break;
            }
            case 'customer.subscription.updated': {
                const sub = event.data.object;
                const status = sub.status === 'active' ? 'active' : sub.status === 'past_due' ? 'past_due' : 'inactive';
                await supabase.from('user_profiles').update({
                    subscription_status: status,
                }).eq('stripe_subscription_id', sub.id);
                break;
            }
            case 'customer.subscription.deleted': {
                const sub = event.data.object;
                await supabase.from('user_profiles').update({
                    subscription_status: 'cancelled',
                }).eq('stripe_subscription_id', sub.id);
                break;
            }
        }
    } catch (err) {
        console.error('Webhook handler error:', err);
        return NextResponse.json({ error: 'Handler failed' }, { status: 500 });
    }

    return NextResponse.json({ received: true });
}
