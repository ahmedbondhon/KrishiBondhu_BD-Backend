-- ============================================================================
-- Migration: 001_extensions_and_schemas.sql
-- Project: KrishiBondhu Bangladesh
-- Description: Enable required PostgreSQL extensions and initialize schemas
--              for MVP modules (auth, geo, catalog, farm, system, ai, advisory,
--              case_mgmt) and future modules (climate, market).
-- ============================================================================

-- Enable Required Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
-- PostGIS (available on Neon - if this fails, comment it out)
CREATE EXTENSION IF NOT EXISTS "postgis";

-- Initialize Core MVP Schemas
CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS geo;
CREATE SCHEMA IF NOT EXISTS catalog;
CREATE SCHEMA IF NOT EXISTS farm;
CREATE SCHEMA IF NOT EXISTS system;
CREATE SCHEMA IF NOT EXISTS ai;
CREATE SCHEMA IF NOT EXISTS advisory;
CREATE SCHEMA IF NOT EXISTS case_mgmt;

-- Initialize Roadmap Expansion Schemas
CREATE SCHEMA IF NOT EXISTS climate;
CREATE SCHEMA IF NOT EXISTS market;

-- Grant Schema Usage to the current database user (Neon-compatible)
DO $$
DECLARE
    current_user_name TEXT := current_user;
BEGIN
    EXECUTE 'GRANT USAGE ON SCHEMA auth TO ' || current_user_name;
    EXECUTE 'GRANT USAGE ON SCHEMA geo TO ' || current_user_name;
    EXECUTE 'GRANT USAGE ON SCHEMA catalog TO ' || current_user_name;
    EXECUTE 'GRANT USAGE ON SCHEMA farm TO ' || current_user_name;
    EXECUTE 'GRANT USAGE ON SCHEMA system TO ' || current_user_name;
    EXECUTE 'GRANT USAGE ON SCHEMA ai TO ' || current_user_name;
    EXECUTE 'GRANT USAGE ON SCHEMA advisory TO ' || current_user_name;
    EXECUTE 'GRANT USAGE ON SCHEMA case_mgmt TO ' || current_user_name;
    EXECUTE 'GRANT USAGE ON SCHEMA climate TO ' || current_user_name;
    EXECUTE 'GRANT USAGE ON SCHEMA market TO ' || current_user_name;
END $$;

-- Set default search path for the current database
SELECT pg_catalog.set_config('search_path',
    'public, auth, geo, catalog, farm, system, ai, advisory, case_mgmt, climate, market',
    false);
