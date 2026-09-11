-- Member 1 story: View Lease Details (Design Contract §5.2).
CREATE TABLE IF NOT EXISTS lease_agreements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    unit_id UUID NOT NULL REFERENCES units (id),
    guest_id UUID NOT NULL REFERENCES guests (id),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    monthly_rate NUMERIC(12,2) NOT NULL CHECK (monthly_rate > 0),
    renewal_date DATE,
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'active', 'expired', 'terminated')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_lease_agreements_guest_id ON lease_agreements (guest_id);
CREATE INDEX IF NOT EXISTS ix_lease_agreements_unit_id ON lease_agreements (unit_id);
CREATE INDEX IF NOT EXISTS ix_lease_agreements_status ON lease_agreements (status);

DROP TRIGGER IF EXISTS trg_lease_agreements_updated_at ON lease_agreements;
CREATE TRIGGER trg_lease_agreements_updated_at
    BEFORE UPDATE ON lease_agreements
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();
