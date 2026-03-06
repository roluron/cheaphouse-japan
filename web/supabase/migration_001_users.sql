-- ══════════════════════════════════════════════════════════
-- CheapHouse Japan — Migration 001: User tables + property updates
-- Run this AFTER the base schema.sql from /ingestion/schema.sql
-- Safe to run multiple times (uses IF NOT EXISTS / IF NOT EXISTS)
-- ══════════════════════════════════════════════════════════

-- ────────────────────────────────────────────────────────
-- 1. USER PROFILES (extends Supabase auth.users)
-- ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.user_profiles (
    id                      UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    display_name            TEXT,
    subscription_status     TEXT NOT NULL DEFAULT 'free'
        CHECK (subscription_status IN ('free', 'active', 'cancelled', 'past_due')),
    stripe_customer_id      TEXT,
    stripe_subscription_id  TEXT,
    quiz_answers            JSONB DEFAULT '{}'::jsonb,
    created_at              TIMESTAMPTZ DEFAULT now(),
    updated_at              TIMESTAMPTZ DEFAULT now()
);

-- Auto-create profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger AS $$
BEGIN
    INSERT INTO public.user_profiles (id, display_name)
    VALUES (
        NEW.id,
        COALESCE(NEW.raw_user_meta_data->>'display_name', NEW.raw_user_meta_data->>'full_name', split_part(NEW.email, '@', 1))
    )
    ON CONFLICT (id) DO NOTHING;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Drop existing trigger if any, then create
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- RLS
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users read own profile" ON public.user_profiles;
CREATE POLICY "Users read own profile" ON public.user_profiles
    FOR SELECT USING (auth.uid() = id);

DROP POLICY IF EXISTS "Users update own profile" ON public.user_profiles;
CREATE POLICY "Users update own profile" ON public.user_profiles
    FOR UPDATE USING (auth.uid() = id);

-- ────────────────────────────────────────────────────────
-- 2. SAVED PROPERTIES
-- ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.saved_properties (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    property_id     UUID NOT NULL REFERENCES public.properties(id) ON DELETE CASCADE,
    notes           TEXT,
    saved_at        TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id, property_id)
);

CREATE INDEX IF NOT EXISTS idx_saved_properties_user ON public.saved_properties(user_id);
CREATE INDEX IF NOT EXISTS idx_saved_properties_property ON public.saved_properties(property_id);

-- RLS
ALTER TABLE public.saved_properties ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users manage own saves" ON public.saved_properties;
CREATE POLICY "Users manage own saves" ON public.saved_properties
    FOR ALL USING (auth.uid() = user_id);

-- ────────────────────────────────────────────────────────
-- 3. PROPERTY TABLE ADDITIONS
-- ────────────────────────────────────────────────────────
ALTER TABLE public.properties ADD COLUMN IF NOT EXISTS slug TEXT;
ALTER TABLE public.properties ADD COLUMN IF NOT EXISTS is_published BOOLEAN DEFAULT false;
ALTER TABLE public.properties ADD COLUMN IF NOT EXISTS view_count INT DEFAULT 0;
ALTER TABLE public.properties ADD COLUMN IF NOT EXISTS save_count INT DEFAULT 0;

-- Unique index on slug (only for non-null slugs)
CREATE UNIQUE INDEX IF NOT EXISTS idx_properties_slug ON public.properties(slug) WHERE slug IS NOT NULL;

-- Index for published properties (the main public query)
CREATE INDEX IF NOT EXISTS idx_properties_published ON public.properties(is_published, admin_status)
    WHERE is_published = true AND admin_status = 'approved';

-- ────────────────────────────────────────────────────────
-- 4. PROPERTIES RLS (public read for published)
-- ────────────────────────────────────────────────────────
ALTER TABLE public.properties ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Public read published properties" ON public.properties;
CREATE POLICY "Public read published properties" ON public.properties
    FOR SELECT USING (is_published = true AND admin_status = 'approved');

-- Admin full access (service role bypasses RLS, so this is mainly for clarity)
DROP POLICY IF EXISTS "Service role full access" ON public.properties;
CREATE POLICY "Service role full access" ON public.properties
    FOR ALL USING (auth.role() = 'service_role');

-- ────────────────────────────────────────────────────────
-- 5. HELPER: Generate slug from title
-- ────────────────────────────────────────────────────────
-- Run this to generate slugs for existing properties:
-- UPDATE properties
-- SET slug = lower(
--     regexp_replace(
--         regexp_replace(
--             coalesce(title_en, 'property-' || left(id::text, 8)),
--             '[^a-zA-Z0-9\s-]', '', 'g'
--         ),
--         '\s+', '-', 'g'
--     )
-- )
-- WHERE slug IS NULL;

-- ────────────────────────────────────────────────────────
-- 6. UPDATED ADMIN REVIEW QUEUE VIEW
-- ────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW admin_review_queue AS
SELECT
    id,
    slug,
    title_en,
    original_title,
    prefecture,
    city,
    price_jpy,
    price_display,
    quality_score,
    hazard_scores,
    lifestyle_tags,
    admin_status,
    listing_status,
    freshness_label,
    is_published,
    original_url,
    thumbnail_url,
    created_at
FROM properties
WHERE admin_status = 'pending_review'
ORDER BY quality_score DESC, created_at DESC;
