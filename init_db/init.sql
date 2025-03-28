CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    username VARCHAR(50) NOT NULL,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(100) NOT NULL,
    registry_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    role VARCHAR(50) DEFAULT 'user'
    ON CONFLICT DO NOTHING
);

INSERT INTO users (name, username, password, email, role)
VALUES ('Testovací Uživatel', 'test', 'test_password', 'test@example.com', 'admin')
ON CONFLICT DO NOTHING;