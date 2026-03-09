import { getSupabaseServer } from './supabase-server';
import { redirect } from 'next/navigation';

/**
 * Get the current user (server-side). Returns user or null.
 */
export async function getCurrentUser() {
    try {
        const supabase = await getSupabaseServer();
        const { data: { user }, error } = await supabase.auth.getUser();
        if (error || !user) return null;
        return user;
    } catch {
        return null;
    }
}

/**
 * Require authentication. Redirects to /login if not authenticated.
 * Returns the authenticated user.
 */
export async function requireAuth() {
    const user = await getCurrentUser();
    if (!user) {
        redirect('/login');
    }
    return user;
}

/**
 * Require an active subscription. Redirects to /pricing if user is free tier.
 * Returns the user profile with subscription info.
 */
export async function requireSubscription() {
    const user = await requireAuth();
    const supabase = await getSupabaseServer();

    const { data: profile } = await supabase
        .from('user_profiles')
        .select('subscription_status')
        .eq('id', user.id)
        .single();

    if (!profile || profile.subscription_status !== 'active') {
        redirect('/pricing');
    }

    return { user, profile };
}

/**
 * Get user profile with subscription info. Returns null if not found.
 */
export async function getUserProfile(userId) {
    try {
        const supabase = await getSupabaseServer();
        const { data } = await supabase
            .from('user_profiles')
            .select('*')
            .eq('id', userId)
            .single();
        return data;
    } catch {
        return null;
    }
}
