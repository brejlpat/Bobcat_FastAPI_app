CREATE TABLE IF NOT EXISTS users_ad (
    id SERIAL PRIMARY KEY,
    username TEXT,
    email TEXT NOT NULL UNIQUE,
    role TEXT DEFAULT 'user',
    registry_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dummy záznam admina, aby bylo možné se přihlásit
INSERT INTO users_ad (username, email, role)
VALUES ('patrikbrejla', 'patrik.brejla@doosan.com', 'admin')
ON CONFLICT (email) DO NOTHING;

CREATE TABLE IF NOT EXISTS login (
    id SERIAL PRIMARY KEY,
    username TEXT,
    token_expiration TEXT,
    login_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS device_edit (
    id SERIAL PRIMARY KEY,
    username TEXT,
    channel_name TEXT,
    payload JSONB,
    device_edit_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    action TEXT,
    driver TEXT
);

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS embeddings (
    id SERIAL PRIMARY KEY,
    name TEXT,
    embedding VECTOR(384)
);
