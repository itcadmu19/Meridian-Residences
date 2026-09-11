-- Seed records matching the shared contract's logical LEASE-001 / INV-001..003 fixtures.
INSERT INTO lease_agreements (
    id, unit_id, guest_id, start_date, end_date, monthly_rate, renewal_date, status
)
VALUES (
    '77777777-7777-7777-7777-777777777777',
    '33333333-3333-3333-3333-333333333333',
    '11111111-1111-1111-1111-111111111111',
    '2026-01-01', '2026-12-31', 45000.00, '2026-12-01', 'active'
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO recurring_invoices (
    id, lease_id, billing_period_start, billing_period_end, amount, due_date,
    payment_status, generated_at, paid_at
)
VALUES
    ('88888888-8888-8888-8888-888888888888', '77777777-7777-7777-7777-777777777777',
     '2026-06-01', '2026-06-30', 45000.00, '2026-07-10', 'paid',
     '2026-06-01T00:00:00Z', '2026-07-05T00:00:00Z'),
    ('99999999-9999-9999-9999-999999999999', '77777777-7777-7777-7777-777777777777',
     '2026-07-01', '2026-07-31', 45000.00, '2026-08-10', 'paid',
     '2026-07-01T00:00:00Z', '2026-08-05T00:00:00Z'),
    ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', '77777777-7777-7777-7777-777777777777',
     '2026-08-01', '2026-08-31', 45000.00, '2026-09-10', 'overdue',
     '2026-08-01T00:00:00Z', NULL)
ON CONFLICT (id) DO NOTHING;
