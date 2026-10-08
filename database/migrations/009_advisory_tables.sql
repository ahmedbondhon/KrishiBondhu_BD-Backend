-- ============================================================================
-- Migration: 009_advisory_tables.sql
-- Project: KrishiBondhu Bangladesh
-- Description: Advisory engines and content generation tables in the 'advisory'
--              schema, including advisory templates, personalized farmer advisories,
--              audio voice advisory mappings, and farmer outcome feedback.
-- ============================================================================

-- 1. Advisory Templates Master Table
CREATE TABLE IF NOT EXISTS advisory.templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    issue_id UUID NOT NULL REFERENCES catalog.issues(id) ON DELETE CASCADE,
    growth_stage_id UUID REFERENCES catalog.growth_stages(id) ON DELETE SET NULL,
    severity_level VARCHAR(20) DEFAULT 'medium' NOT NULL, -- 'low', 'medium', 'high', 'critical'
    title_bn VARCHAR(255) NOT NULL,
    title_en VARCHAR(255),
    content_bn TEXT NOT NULL,
    content_en TEXT,
    preventive_measures_bn TEXT,
    safety_precautions_bn TEXT,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 2. Generated Farmer Advisories Table
CREATE TABLE IF NOT EXISTS advisory.advisories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID UNIQUE NOT NULL REFERENCES case_mgmt.diagnosis_cases(id) ON DELETE CASCADE,
    prediction_id UUID REFERENCES ai.predictions(id) ON DELETE SET NULL,
    template_id UUID REFERENCES advisory.templates(id) ON DELETE SET NULL,
    title_bn VARCHAR(255) NOT NULL,
    summary_bn TEXT NOT NULL,
    detailed_treatment_bn TEXT NOT NULL,
    preventive_measures_bn TEXT,
    chemical_recommendations_bn TEXT,
    organic_recommendations_bn TEXT,
    audio_advisory_id UUID REFERENCES system.files(id) ON DELETE SET NULL,
    source VARCHAR(50) DEFAULT 'ai_generated' NOT NULL, -- 'ai_generated', 'expert_approved', 'expert_overridden'
    created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    is_published BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 3. Advisory Outcome & Farmer Feedback Table
CREATE TABLE IF NOT EXISTS advisory.feedbacks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    advisory_id UUID NOT NULL REFERENCES advisory.advisories(id) ON DELETE CASCADE,
    farmer_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    rating INT CHECK (rating >= 1 AND rating <= 5),
    is_helpful BOOLEAN,
    feedback_text TEXT,
    audio_feedback_id UUID REFERENCES system.files(id) ON DELETE SET NULL,
    outcome_status VARCHAR(50), -- e.g., 'resolved', 'partially_resolved', 'ineffective'
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);