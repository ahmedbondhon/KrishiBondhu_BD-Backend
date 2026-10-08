-- ============================================================================
-- Migration: 011_climate_tables.sql
-- Project: KrishiBondhu Bangladesh
-- Description: DeltaShield climate module tables in the 'climate' schema,
--              storing weather forecasts, extreme weather alerts, and
--              climate-smart agricultural advisories.
-- ============================================================================

-- 1. Regional Weather Forecasts & Conditions Table
CREATE TABLE IF NOT EXISTS climate.weather_forecasts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    division_id UUID REFERENCES geo.divisions(id) ON DELETE SET NULL,
    district_id UUID REFERENCES geo.districts(id) ON DELETE SET NULL,
    upazila_id UUID REFERENCES geo.upazilas(id) ON DELETE SET NULL,
    union_id UUID REFERENCES geo.unions(id) ON DELETE SET NULL,
    forecast_date DATE NOT NULL,
    temp_min_c NUMERIC(5, 2),
    temp_max_c NUMERIC(5, 2),
    humidity_pct NUMERIC(5, 2),
    rainfall_mm NUMERIC(6, 2),
    wind_speed_kmh NUMERIC(5, 2),
    weather_condition VARCHAR(100), -- e.g., 'heavy_rain', 'sunny', 'cloudy', 'foggy'
    raw_forecast_data JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT uq_weather_location_date UNIQUE (union_id, upazila_id, forecast_date)
);

-- 2. Extreme Weather & Climate Risk Alerts Table
CREATE TABLE IF NOT EXISTS climate.weather_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_code VARCHAR(50) NOT NULL,
    title_bn VARCHAR(255) NOT NULL,
    title_en VARCHAR(255),
    alert_type VARCHAR(50) NOT NULL, -- e.g., 'cyclone', 'flood', 'drought', 'heatwave', 'cold_wave', 'heavy_rain'
    severity VARCHAR(20) DEFAULT 'medium' NOT NULL, -- 'low', 'medium', 'high', 'critical'
    description_bn TEXT NOT NULL,
    description_en TEXT,
    action_advisory_bn TEXT,
    division_id UUID REFERENCES geo.divisions(id) ON DELETE SET NULL,
    district_id UUID REFERENCES geo.districts(id) ON DELETE SET NULL,
    upazila_id UUID REFERENCES geo.upazilas(id) ON DELETE SET NULL,
    union_id UUID REFERENCES geo.unions(id) ON DELETE SET NULL,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 3. Climate-Smart Crop Advisories Table
CREATE TABLE IF NOT EXISTS climate.crop_climate_advisories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    crop_id UUID NOT NULL REFERENCES catalog.crops(id) ON DELETE CASCADE,
    growth_stage_id UUID REFERENCES catalog.growth_stages(id) ON DELETE CASCADE,
    climate_condition VARCHAR(50) NOT NULL, -- e.g., 'excess_humidity', 'prolonged_drought', 'unseasonal_rain'
    title_bn VARCHAR(255) NOT NULL,
    recommendation_bn TEXT NOT NULL,
    recommendation_en TEXT,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);