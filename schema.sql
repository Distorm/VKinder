-- Схема БД VKinder для PostgreSQL.
-- В проекте таблицы также создаются автоматически через SQLAlchemy.

CREATE TABLE IF NOT EXISTS candidates (
    id SERIAL PRIMARY KEY,
    vk_id INTEGER NOT NULL UNIQUE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    sex INTEGER,
    city_id INTEGER,
    city_title VARCHAR(150),
    bdate VARCHAR(20),
    age INTEGER,
    domain VARCHAR(150),
    profile_url VARCHAR(255) NOT NULL,
    photos_json TEXT,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_candidates_vk_id ON candidates (vk_id);
CREATE INDEX IF NOT EXISTS ix_candidates_sex ON candidates (sex);
CREATE INDEX IF NOT EXISTS ix_candidates_city_id ON candidates (city_id);

CREATE TABLE IF NOT EXISTS vk_users (
    id SERIAL PRIMARY KEY,
    vk_id INTEGER NOT NULL UNIQUE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    sex INTEGER,
    city_id INTEGER,
    city_title VARCHAR(150),
    bdate VARCHAR(20),
    age INTEGER,
    search_offset INTEGER NOT NULL DEFAULT 0,
    current_candidate_id INTEGER REFERENCES candidates (id),
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_vk_users_vk_id ON vk_users (vk_id);
CREATE INDEX IF NOT EXISTS ix_vk_users_city_id ON vk_users (city_id);

CREATE TABLE IF NOT EXISTS shown_candidates (
    id SERIAL PRIMARY KEY,
    owner_user_id INTEGER NOT NULL REFERENCES vk_users (id),
    candidate_id INTEGER NOT NULL REFERENCES candidates (id),
    shown_at TIMESTAMP NOT NULL,
    CONSTRAINT uq_shown_owner_candidate UNIQUE (owner_user_id, candidate_id)
);

CREATE TABLE IF NOT EXISTS favorites (
    id SERIAL PRIMARY KEY,
    owner_user_id INTEGER NOT NULL REFERENCES vk_users (id),
    candidate_id INTEGER NOT NULL REFERENCES candidates (id),
    created_at TIMESTAMP NOT NULL,
    CONSTRAINT uq_favorite_owner_candidate UNIQUE (owner_user_id, candidate_id)
);

CREATE TABLE IF NOT EXISTS blacklist (
    id SERIAL PRIMARY KEY,
    owner_user_id INTEGER NOT NULL REFERENCES vk_users (id),
    candidate_id INTEGER NOT NULL REFERENCES candidates (id),
    created_at TIMESTAMP NOT NULL,
    CONSTRAINT uq_blacklist_owner_candidate UNIQUE (owner_user_id, candidate_id)
);
