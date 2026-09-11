-- Member 3 story: Submit, Track & Triage Maintenance.
-- Owned table (Design Contract §5.5, §7, §8). Do not rename columns/enums without team agreement.
CREATE TABLE IF NOT EXISTS maintenance_tickets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    unit_id UUID NOT NULL REFERENCES units (id),
    guest_id UUID NOT NULL REFERENCES guests (id),
    issue_type VARCHAR(50) NOT NULL
        CHECK (issue_type IN ('plumbing', 'electrical', 'hvac', 'appliance', 'general', 'other')),
    description TEXT NOT NULL,
    priority VARCHAR(20) NOT NULL DEFAULT 'medium'
        CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
    status VARCHAR(30) NOT NULL DEFAULT 'open'
        CHECK (status IN ('open', 'assigned', 'in_progress', 'resolved', 'cancelled')),
    vendor_queue VARCHAR(100),
    escalated BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at TIMESTAMPTZ
);

-- Indexes required by Design Contract §7.
CREATE INDEX IF NOT EXISTS ix_maintenance_tickets_guest_id ON maintenance_tickets (guest_id);
CREATE INDEX IF NOT EXISTS ix_maintenance_tickets_unit_id ON maintenance_tickets (unit_id);
CREATE INDEX IF NOT EXISTS ix_maintenance_tickets_status ON maintenance_tickets (status);
CREATE INDEX IF NOT EXISTS ix_maintenance_tickets_priority ON maintenance_tickets (priority);

-- Keep updated_at current on every row change (mirrors the shared UTC timestamp convention).
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_maintenance_tickets_updated_at ON maintenance_tickets;
CREATE TRIGGER trg_maintenance_tickets_updated_at
    BEFORE UPDATE ON maintenance_tickets
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();
