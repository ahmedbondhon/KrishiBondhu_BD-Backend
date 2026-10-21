-- ============================================================================
-- Migration: 012_market_tables.sql
-- Project: KrishiBondhu Bangladesh
-- Description: HaatDor market intelligence and group selling tables in the
--              'market' schema, capturing local market prices, haat locations,
--              and farmer crop aggregation offers.
-- ============================================================================

-- 1. Local Markets / Bazaars Registry Table
CREATE TABLE IF NOT EXISTS market.markets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name_en VARCHAR(150) NOT NULL,
    name_bn VARCHAR(150) NOT NULL,
    market_type VARCHAR(50) DEFAULT 'haat' NOT NULL, -- e.g., 'haat', 'wholesale', 'retail', 'procurement_center'
    division_id UUID REFERENCES geo.divisions(id) ON DELETE SET NULL,
    district_id UUID REFERENCES geo.districts(id) ON DELETE SET NULL,
    upazila_id UUID REFERENCES geo.upazilas(id) ON DELETE SET NULL,
    union_id UUID REFERENCES geo.unions(id) ON DELETE SET NULL,
    location GEOMETRY(Point, 4326),
    operating_days VARCHAR(100), -- e.g., 'Sunday, Wednesday'
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 2. Daily Commodity Market Prices Table
CREATE TABLE IF NOT EXISTS market.daily_prices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    market_id UUID NOT NULL REFERENCES market.markets(id) ON DELETE CASCADE,
    crop_id UUID NOT NULL REFERENCES catalog.crops(id) ON DELETE CASCADE,
    variety_id UUID REFERENCES catalog.crop_varieties(id) ON DELETE SET NULL,
    price_date DATE NOT NULL,
    min_price_bdt NUMERIC(10, 2) NOT NULL,
    max_price_bdt NUMERIC(10, 2) NOT NULL,
    avg_price_bdt NUMERIC(10, 2) NOT NULL,
    unit VARCHAR(20) DEFAULT 'kg' NOT NULL, -- e.g., 'kg', 'maund', 'mon', 'piece'
    source VARCHAR(50) DEFAULT 'dam' NOT NULL, -- e.g., 'dam' (Dept of Agricultural Marketing), 'field_agent', 'crowdsourced'
    recorded_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT uq_market_crop_date UNIQUE (market_id, crop_id, price_date)
);

-- 3. Group Selling / Produce Aggregation Offers Table (HaatDor Feature)
CREATE TABLE IF NOT EXISTS market.group_selling_offers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    offer_code VARCHAR(50) UNIQUE NOT NULL,
    initiator_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    crop_id UUID NOT NULL REFERENCES catalog.crops(id) ON DELETE RESTRICT,
    variety_id UUID REFERENCES catalog.crop_varieties(id) ON DELETE SET NULL,
    target_market_id UUID REFERENCES market.markets(id) ON DELETE SET NULL,
    union_id UUID REFERENCES geo.unions(id) ON DELETE SET NULL,
    target_quantity_kg NUMERIC(12, 2) NOT NULL,
    min_participant_quantity_kg NUMERIC(10, 2) DEFAULT 50.00,
    expected_price_per_kg_bdt NUMERIC(10, 2),
    current_aggregated_kg NUMERIC(12, 2) DEFAULT 0.00 NOT NULL,
    status VARCHAR(50) DEFAULT 'open' NOT NULL, -- 'open', 'target_reached', 'negotiating', 'completed', 'cancelled'
    closing_date DATE NOT NULL,
    notes TEXT,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    deleted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 4. Group Selling Offer Participants Table
CREATE TABLE IF NOT EXISTS market.offer_participants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    offer_id UUID NOT NULL REFERENCES market.group_selling_offers(id) ON DELETE CASCADE,
    farmer_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    plot_crop_id UUID REFERENCES farm.plot_crops(id) ON DELETE SET NULL,
    offered_quantity_kg NUMERIC(10, 2) NOT NULL,
    agreed_price_per_kg_bdt NUMERIC(10, 2),
    status VARCHAR(50) DEFAULT 'pledged' NOT NULL, -- 'pledged', 'confirmed', 'delivered', 'withdrawn'
    pledged_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT uq_offer_farmer UNIQUE (offer_id, farmer_id)
);