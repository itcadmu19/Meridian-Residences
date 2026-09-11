-- Seed data for local development/testing (Design Contract §22 seed contract).
-- Logical labels below (GUEST-001 etc.) are documentation aliases; actual PKs are UUIDs.

INSERT INTO guests (id, name, email, phone, loyalty_tier)
VALUES ('11111111-1111-1111-1111-111111111111', 'Anu Sharma', 'anu.sharma@example.com', '+91-9000000001', 'silver')
ON CONFLICT (id) DO NOTHING;

INSERT INTO properties (id, name, brand, address, timezone)
VALUES ('22222222-2222-2222-2222-222222222222', 'Meridian Residences', 'Meridian', '1 Meridian Way', 'UTC')
ON CONFLICT (id) DO NOTHING;

INSERT INTO units (id, property_id, unit_number, unit_type, status)
VALUES ('33333333-3333-3333-3333-333333333333', '22222222-2222-2222-2222-222222222222', '101', '2BHK', 'occupied')
ON CONFLICT (id) DO NOTHING;

-- TICKET-001: open/high (matches seed contract)
INSERT INTO maintenance_tickets (id, unit_id, guest_id, issue_type, description, priority, status, vendor_queue, escalated)
VALUES (
    '44444444-4444-4444-4444-444444444444',
    '33333333-3333-3333-3333-333333333333',
    '11111111-1111-1111-1111-111111111111',
    'plumbing',
    'Kitchen sink is leaking',
    'high',
    'open',
    NULL,
    false
)
ON CONFLICT (id) DO NOTHING;

-- TICKET-002: resolved (matches seed contract)
INSERT INTO maintenance_tickets (id, unit_id, guest_id, issue_type, description, priority, status, vendor_queue, escalated, resolved_at)
VALUES (
    '55555555-5555-5555-5555-555555555555',
    '33333333-3333-3333-3333-333333333333',
    '11111111-1111-1111-1111-111111111111',
    'electrical',
    'Living room outlet not working',
    'medium',
    'resolved',
    'electrical-standard',
    false,
    now() - interval '2 days'
)
ON CONFLICT (id) DO NOTHING;
