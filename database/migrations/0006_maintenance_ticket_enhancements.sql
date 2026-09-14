-- Member 3 enhancements: photo attachment + persisted triage reason for ticket detail view.
ALTER TABLE maintenance_tickets
    ADD COLUMN IF NOT EXISTS photo_data_url TEXT,
    ADD COLUMN IF NOT EXISTS triage_reason TEXT;
