-- ============================================================================
-- Migration: 003_geo_tables.sql
-- Project: KrishiBondhu Bangladesh
-- Description: Administrative geographic hierarchy tables (Divisions, Districts,
--              Upazilas, Unions) with PostGIS spatial support and BBS geo-coding.
-- ============================================================================

-- 1. Divisions Table
CREATE TABLE IF NOT EXISTS geo.divisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bbs_code VARCHAR(10) UNIQUE NOT NULL,
    name_en VARCHAR(100) NOT NULL,
    name_bn VARCHAR(100) NOT NULL,
    coordinates GEOMETRY(Point, 4326),
    boundary GEOMETRY(MultiPolygon, 4326),
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 2. Districts Table
CREATE TABLE IF NOT EXISTS geo.districts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    division_id UUID NOT NULL REFERENCES geo.divisions(id) ON DELETE RESTRICT,
    bbs_code VARCHAR(10) UNIQUE NOT NULL,
    name_en VARCHAR(100) NOT NULL,
    name_bn VARCHAR(100) NOT NULL,
    coordinates GEOMETRY(Point, 4326),
    boundary GEOMETRY(MultiPolygon, 4326),
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 3. Upazilas Table
CREATE TABLE IF NOT EXISTS geo.upazilas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    district_id UUID NOT NULL REFERENCES geo.districts(id) ON DELETE RESTRICT,
    bbs_code VARCHAR(10) UNIQUE NOT NULL,
    name_en VARCHAR(100) NOT NULL,
    name_bn VARCHAR(100) NOT NULL,
    coordinates GEOMETRY(Point, 4326),
    boundary GEOMETRY(MultiPolygon, 4326),
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 4. Unions Table
CREATE TABLE IF NOT EXISTS geo.unions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    upazila_id UUID NOT NULL REFERENCES geo.upazilas(id) ON DELETE RESTRICT,
    bbs_code VARCHAR(10) NOT NULL,
    name_en VARCHAR(100) NOT NULL,
    name_bn VARCHAR(100) NOT NULL,
    coordinates GEOMETRY(Point, 4326),
    boundary GEOMETRY(MultiPolygon, 4326),
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT uq_unions_upazila_bbs UNIQUE (upazila_id, bbs_code)
);

-- 5. Add Foreign Key Constraints to auth.users for Geo Location
ALTER TABLE auth.users
    ADD CONSTRAINT fk_users_division FOREIGN KEY (division_id) REFERENCES geo.divisions(id) ON DELETE SET NULL,
    ADD CONSTRAINT fk_users_district FOREIGN KEY (district_id) REFERENCES geo.districts(id) ON DELETE SET NULL,
    ADD CONSTRAINT fk_users_upazila FOREIGN KEY (upazila_id) REFERENCES geo.upazilas(id) ON DELETE SET NULL,
    ADD CONSTRAINT fk_users_union FOREIGN KEY (union_id) REFERENCES geo.unions(id) ON DELETE SET NULL;