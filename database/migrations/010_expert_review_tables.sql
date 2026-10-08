-- ============================================================================
-- Migration: 010_expert_review_tables.sql
-- Project: KrishiBondhu Bangladesh
-- Description: Agricultural expert escalation and review management tables in
--              the 'case_mgmt' schema for ChashiGuard expert workflows.
-- ============================================================================

-- 1. Expert Profiles Table
CREATE TABLE IF NOT EXISTS case_mgmt.expert_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    designation VARCHAR(150) NOT NULL,
    organization VARCHAR(200) NOT NULL, -- e.g., 'Department of Agricultural Extension (DAE)', 'BARI'
    specialization_notes TEXT,
    is_available BOOLEAN DEFAULT TRUE NOT NULL,
    max_active_cases INT DEFAULT 10 NOT NULL,
    rating NUMERIC(3, 2) DEFAULT 5.00,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 2. Expert Specialization Mapping Table (Crop Expertise)
CREATE TABLE IF NOT EXISTS case_mgmt.expert_crop_specializations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    expert_id UUID NOT NULL REFERENCES case_mgmt.expert_profiles(id) ON DELETE CASCADE,
    crop_id UUID NOT NULL REFERENCES catalog.crops(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT uq_expert_crop UNIQUE (expert_id, crop_id)
);

-- 3. Case Escalation & Assignment Queue Table
CREATE TABLE IF NOT EXISTS case_mgmt.case_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES case_mgmt.diagnosis_cases(id) ON DELETE CASCADE,
    expert_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE RESTRICT,
    assigned_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    status VARCHAR(50) DEFAULT 'assigned' NOT NULL, -- 'assigned', 'accepted', 'reassigned', 'completed', 'declined'
    assigned_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    responded_at TIMESTAMPTZ,
    decline_reason TEXT
);

-- 4. Expert Case Reviews Table
CREATE TABLE IF NOT EXISTS case_mgmt.expert_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES case_mgmt.diagnosis_cases(id) ON DELETE CASCADE,
    expert_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE RESTRICT,
    agreed_with_ai BOOLEAN NOT NULL,
    verified_issue_id UUID REFERENCES catalog.issues(id) ON DELETE RESTRICT,
    diagnosis_notes_bn TEXT NOT NULL,
    diagnosis_notes_en TEXT,
    prescribed_treatment_bn TEXT,
    voice_note_id UUID REFERENCES system.files(id) ON DELETE SET NULL,
    review_status VARCHAR(50) DEFAULT 'completed' NOT NULL, -- 'draft', 'completed'
    reviewed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 5. Expert Review Internal Comments Table
CREATE TABLE IF NOT EXISTS case_mgmt.expert_comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES case_mgmt.diagnosis_cases(id) ON DELETE CASCADE,
    author_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE RESTRICT,
    comment_text TEXT NOT NULL,
    voice_note_id UUID REFERENCES system.files(id) ON DELETE SET NULL,
    is_internal_only BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);