CREATE TABLE IF NOT EXISTS users_ad (
    id SERIAL PRIMARY KEY,
    username TEXT,
    email TEXT NOT NULL UNIQUE,
    role TEXT DEFAULT 'user',
    registry_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ON CONFLICT DO NOTHING
);

INSERT INTO users_ad (email, role)
VALUES ('patrik.brejla@doosan.com', 'admin')
ON CONFLICT DO NOTHING;