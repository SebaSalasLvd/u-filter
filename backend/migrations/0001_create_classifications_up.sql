-- Migration: 0001_create_classifications_up.sql
-- Crea la tabla posts para almacenar resultados del backend

CREATE TABLE IF NOT EXISTS links (
    id BIGSERIAL PRIMARY KEY,
    url TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS posts (
    id BIGSERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    author TEXT,
    post_date TEXT,
    classification_label TEXT,
    classification_score DOUBLE PRECISION,
    model_used TEXT,
    link_id BIGINT REFERENCES links(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
