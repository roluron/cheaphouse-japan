CREATE TABLE IF NOT EXISTS public.verification_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    listing_url TEXT NOT NULL,
    email TEXT NOT NULL,
    buyer_goal TEXT NOT NULL DEFAULT 'unknown',
    notes TEXT,
    status TEXT NOT NULL DEFAULT 'new' CHECK (status IN ('new', 'accepted', 'paid', 'delivered', 'declined')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE public.verification_requests ENABLE ROW LEVEL SECURITY;

CREATE INDEX IF NOT EXISTS idx_verification_requests_status_created
    ON public.verification_requests(status, created_at DESC);

