import { NextResponse } from 'next/server';
import Stripe from 'stripe';
import { createClient } from '@supabase/supabase-js';

export async function POST(request) {
    const stripeSecretKey = process.env.STRIPE_SECRET_KEY;
    const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET;
    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
    const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
    const sig = request.headers.get('stripe-signature');

    if (!stripeSecretKey || !webhookSecret || !supabaseUrl || !serviceRoleKey || !sig) {
        return NextResponse.json({ error: 'Webhook is not securely configured' }, { status: 503 });
    }

    const stripe = new Stripe(stripeSecretKey);
    const supabase = createClient(supabaseUrl, serviceRoleKey);
    const body = await request.text();

    let event;
    try {
        event = stripe.webhooks.constructEvent(body, sig, webhookSecret);
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
