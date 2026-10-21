-- ============================================================================
-- Migration: 007_diagnosis_case_tables.sql
-- Project: KrishiBondhu Bangladesh
-- Description: Diagnosis case management tables for ChashiGuard in the
--              'case_mgmt' schema, capturing farmer crop disease requests,
--              attachments, and status lifecycle histories.
-- ============================================================================

-- 1. Diagnosis Cases Master Table
CREATE TABLE IF NOT EXISTS case_mgmt.diagnosis_cases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_number VARCHAR(50) UNIQUE NOT NULL,
    farmer_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    plot_id UUID REFERENCES farm.plots(id) ON DELETE SET NULL,
    plot_crop_id UUID REFERENCES farm.plot_crops(id) ON DELETE SET NULL,
    crop_id UUID REFERENCES catalog.crops(id) ON DELETE RESTRICT,
    growth_stage_id UUID REFERENCES catalog.growth_stages(id) ON DELETE SET NULL,
    primary_image_id UUID REFERENCES system.files(id) ON DELETE SET NULL,
    voice_note_id UUID REFERENCES system.files(id) ON DELETE SET NULL,
    farmer_notes TEXT,
    latitude NUMERIC(10, 8),
    longitude NUMERIC(11, 8),
    location GEOMETRY(Point, 4326),
    status VARCHAR(50) DEFAULT 'submitted' NOT NULL, -- 'submitted', 'processing', 'ai_analyzed', 'escalated', 'expert_reviewed', 'closed'
    urgency_level VARCHAR(20) DEFAULT 'medium' NOT NULL, -- 'low', 'medium', 'high', 'critical'
    assigned_expert_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    resolved_at TIMESTAMPTZ,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    deleted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 2. Case Multi-Image Attachments Table
CREATE TABLE IF NOT EXISTS case_mgmt.case_images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES case_mgmt.diagnosis_cases(id) ON DELETE CASCADE,
    file_id UUID NOT NULL REFERENCES system.files(id) ON DELETE CASCADE,
    image_type VARCHAR(50) DEFAULT 'leaf' NOT NULL, -- 'leaf', 'stem', 'fruit', 'root', 'whole_plant'
    is_primary BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 3. Case Status Lifecycle History Log Table
CREATE TABLE IF NOT EXISTS case_mgmt.case_status_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES case_mgmt.diagnosis_cases(id) ON DELETE CASCADE,
    previous_status VARCHAR(50),
    new_status VARCHAR(50) NOT NULL,
    changed_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);