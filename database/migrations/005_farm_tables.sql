-- ============================================================================
-- Migration: 005_farm_tables.sql
-- Project: KrishiBondhu Bangladesh
-- Description: Farm management tables including land plots, active plot crops,
--              cultivation cycles, and plot geo-spatial boundaries in 'farm' schema.
-- ============================================================================

-- 1. Farm Plots Table
CREATE TABLE IF NOT EXISTS farm.plots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    area_bigha NUMERIC(10, 2),
    area_sqm NUMERIC(12, 2),
    soil_type VARCHAR(50),
    irrigation_source VARCHAR(50),
    division_id UUID REFERENCES geo.divisions(id) ON DELETE SET NULL,
    district_id UUID REFERENCES geo.districts(id) ON DELETE SET NULL,
    upazila_id UUID REFERENCES geo.upazilas(id) ON DELETE SET NULL,
    union_id UUID REFERENCES geo.unions(id) ON DELETE SET NULL,
    location GEOMETRY(Point, 4326),
    boundary GEOMETRY(Polygon, 4326),
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    deleted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 2. Plot Crops (Cultivation Cycles) Table
CREATE TABLE IF NOT EXISTS farm.plot_crops (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plot_id UUID NOT NULL REFERENCES farm.plots(id) ON DELETE CASCADE,
    crop_id UUID NOT NULL REFERENCES catalog.crops(id) ON DELETE RESTRICT,
    variety_id UUID REFERENCES catalog.crop_varieties(id) ON DELETE SET NULL,
    current_stage_id UUID REFERENCES catalog.growth_stages(id) ON DELETE SET NULL,
    sowing_date DATE,
    expected_harvest_date DATE,
    actual_harvest_date DATE,
    status VARCHAR(50) DEFAULT 'active' NOT NULL, -- 'planned', 'active', 'harvested', 'failed'
    yield_kg NUMERIC(10, 2),
    notes TEXT,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    deleted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);