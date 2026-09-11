-- Lightweight resident authentication, scoped to unblock Story 3 authorization.
-- Not a replacement for a future shared auth story; team may consolidate later.
CREATE TABLE IF NOT EXISTS resident_credentials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    guest_id UUID NOT NULL UNIQUE REFERENCES guests (id),
    unit_id UUID NOT NULL REFERENCES units (id),
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'resident'
        CHECK (role IN ('resident', 'staff', 'admin')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_resident_credentials_guest_id ON resident_credentials (guest_id);
