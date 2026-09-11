-- Demo login for local development: anu.sharma@example.com / ResidentPass123!
INSERT INTO resident_credentials (id, guest_id, unit_id, email, password_hash, role)
VALUES (
    '66666666-6666-6666-6666-666666666666',
    '11111111-1111-1111-1111-111111111111',
    '33333333-3333-3333-3333-333333333333',
    'anu.sharma@example.com',
    '$2b$12$ZfwVwQDPjCziyN4uV.B.pulpwmTsHp8Y0dGFr5nlrPWOaS1umUUbe',
    'resident'
)
ON CONFLICT (id) DO NOTHING;
