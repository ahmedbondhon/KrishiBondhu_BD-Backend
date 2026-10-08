-- ============================================================================
-- Migration: 004_catalog_tables.sql
-- Project: KrishiBondhu Bangladesh
-- Description: Master catalog tables defining agricultural crops, varieties,
--              growth stages, crop issues (diseases/pests/deficiencies),
--              and recommended remedies/treatments in 'catalog' schema.
-- ============================================================================

-- 1. Crops Master Table
CREATE TABLE IF NOT EXISTS catalog.crops (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) UNIQUE NOT NULL,
    name_en VARCHAR(100) NOT NULL,
    name_bn VARCHAR(100) NOT NULL,
    scientific_name VARCHAR(150),
    description TEXT,
    icon_url TEXT,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 2. Crop Varieties Table
CREATE TABLE IF NOT EXISTS catalog.crop_varieties (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    crop_id UUID NOT NULL REFERENCES catalog.crops(id) ON DELETE CASCADE,
    code VARCHAR(50) NOT NULL,
    name_en VARCHAR(100) NOT NULL,
    name_bn VARCHAR(100) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT uq_crop_varieties_code UNIQUE (crop_id, code)
);

-- 3. Crop Growth Stages Table
CREATE TABLE IF NOT EXISTS catalog.growth_stages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    crop_id UUID NOT NULL REFERENCES catalog.crops(id) ON DELETE CASCADE,
    stage_code VARCHAR(50) NOT NULL,
    name_en VARCHAR(100) NOT NULL,
    name_bn VARCHAR(100) NOT NULL,
    sequence_order INT NOT NULL DEFAULT 1,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT uq_growth_stage_crop_order UNIQUE (crop_id, sequence_order)
);

-- 4. Crop Issues Master Table (Diseases, Pests, Deficiencies)
CREATE TABLE IF NOT EXISTS catalog.issues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    crop_id UUID NOT NULL REFERENCES catalog.crops(id) ON DELETE CASCADE,
    code VARCHAR(50) UNIQUE NOT NULL,
    name_en VARCHAR(150) NOT NULL,
    name_bn VARCHAR(150) NOT NULL,
    category VARCHAR(50) NOT NULL, -- e.g., 'disease', 'pest', 'deficiency', 'environmental'
    scientific_name VARCHAR(150),
    symptoms_bn TEXT,
    symptoms_en TEXT,
    severity_level VARCHAR(20) DEFAULT 'medium' NOT NULL, -- e.g., 'low', 'medium', 'high', 'critical'
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 5. Issue Susceptibility Mapping (Susceptible Growth Stages)
CREATE TABLE IF NOT EXISTS catalog.issue_growth_stages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    issue_id UUID NOT NULL REFERENCES catalog.issues(id) ON DELETE CASCADE,
    growth_stage_id UUID NOT NULL REFERENCES catalog.growth_stages(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT uq_issue_growth_stage UNIQUE (issue_id, growth_stage_id)
);

-- 6. Remedies and Treatment Guidelines
CREATE TABLE IF NOT EXISTS catalog.remedies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    issue_id UUID NOT NULL REFERENCES catalog.issues(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL, -- e.g., 'chemical', 'organic', 'cultural', 'preventive'
    title_bn VARCHAR(255) NOT NULL,
    title_en VARCHAR(255),
    description_bn TEXT NOT NULL,
    description_en TEXT,
    chemical_name VARCHAR(150),
    dosage_bn TEXT,
    safety_instructions_bn TEXT,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);