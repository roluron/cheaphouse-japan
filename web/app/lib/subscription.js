import { getSupabaseServer } from './supabase-server';

/**
 * Check if a user has an active subscription.
 */
export async function isSubscribed(userId) {
    if (!userId) return false;
    try {
        const supabase = await getSupabaseServer();
        const { data } = await supabase
            .from('user_profiles')
            .select('subscription_status')
            .eq('id', userId)
            .single();
        return data?.subscription_status === 'active';
    } catch {
        return false;
    }
}
