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

-- Grant Schema Usage (Standard permissions for Supabase / database roles)
GRANT USAGE ON SCHEMA auth TO postgres, anon, authenticated, service_role;
GRANT USAGE ON SCHEMA geo TO postgres, anon, authenticated, service_role;
GRANT USAGE ON SCHEMA catalog TO postgres, anon, authenticated, service_role;
GRANT USAGE ON SCHEMA farm TO postgres, anon, authenticated, service_role;
GRANT USAGE ON SCHEMA system TO postgres, anon, authenticated, service_role;
GRANT USAGE ON SCHEMA ai TO postgres, anon, authenticated, service_role;
GRANT USAGE ON SCHEMA advisory TO postgres, anon, authenticated, service_role;
GRANT USAGE ON SCHEMA case_mgmt TO postgres, anon, authenticated, service_role;
GRANT USAGE ON SCHEMA climate TO postgres, anon, authenticated, service_role;
GRANT USAGE ON SCHEMA market TO postgres, anon, authenticated, service_role;

-- Set default search path
ALTER DATABASE postgres SET search_path TO public, auth, geo, catalog, farm, system, ai, advisory, case_mgmt, climate, market;
