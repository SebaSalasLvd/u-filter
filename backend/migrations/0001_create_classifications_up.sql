-- Migration: 0001_create_classifications_up.sql
-- Crea la tabla classifications para almacenar resultados del backend

CREATE TABLE IF NOT EXISTS classifications (
  id BIGSERIAL PRIMARY KEY,
  post_dom_id TEXT NULL,
  post_external_id TEXT NULL,
  post_url TEXT NULL,
  title TEXT NULL,
  input_text TEXT NULL,
  author TEXT NULL,
  post_date TIMESTAMPTZ NULL,

  -- clasificacion
  model_name TEXT NULL,
  label TEXT NULL,
  score DOUBLE PRECISION NULL,
  candidate_labels JSONB NULL,

  -- datos libres y raw
  metadata JSONB DEFAULT '{}'::jsonb,
  raw JSONB NULL,

  user_id UUID NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
