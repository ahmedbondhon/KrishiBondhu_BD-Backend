-- ============================================================================
-- Migration: 008_ai_tables.sql
-- Project: KrishiBondhu Bangladesh
-- Description: AI inference, computer vision model registry, prediction logs,
--              top-N class probabilities, and model performance feedback
--              in the 'ai' schema.
-- ============================================================================

-- 1. AI Models Registry Table
CREATE TABLE IF NOT EXISTS ai.models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    version VARCHAR(20) NOT NULL,
    framework VARCHAR(50) DEFAULT 'PyTorch' NOT NULL, -- e.g., 'PyTorch', 'TensorFlow', 'ONNX'
    task_type VARCHAR(50) DEFAULT 'image_classification' NOT NULL,
    accuracy_score NUMERIC(5, 4),
    f1_score NUMERIC(5, 4),
    artifact_path TEXT,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT uq_ai_model_version UNIQUE (model_code, version)
);

-- 2. AI Predictions Log Table
CREATE TABLE IF NOT EXISTS ai.predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES case_mgmt.diagnosis_cases(id) ON DELETE CASCADE,
    model_id UUID NOT NULL REFERENCES ai.models(id) ON DELETE RESTRICT,
    file_id UUID REFERENCES system.files(id) ON DELETE SET NULL,
    primary_issue_id UUID REFERENCES catalog.issues(id) ON DELETE SET NULL,
    confidence_score NUMERIC(5, 4) NOT NULL, -- e.g., 0.8525 representing 85.25%
    is_confident BOOLEAN DEFAULT TRUE NOT NULL, -- Indicates if score meets minimum threshold
    raw_response JSONB,
    processing_time_ms INT,
    status VARCHAR(50) DEFAULT 'completed' NOT NULL, -- 'pending', 'completed', 'failed'
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 3. Prediction Details Table (Top-N Class Probabilities Breakdown)
CREATE TABLE IF NOT EXISTS ai.prediction_details (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prediction_id UUID NOT NULL REFERENCES ai.predictions(id) ON DELETE CASCADE,
    issue_id UUID REFERENCES catalog.issues(id) ON DELETE SET NULL,
    class_label VARCHAR(150) NOT NULL,
    rank_order INT NOT NULL,
    confidence_score NUMERIC(5, 4) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT uq_prediction_rank UNIQUE (prediction_id, rank_order)
);

-- 4. AI Model Feedback & Expert Ground Truth Validation Table
CREATE TABLE IF NOT EXISTS ai.model_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prediction_id UUID NOT NULL REFERENCES ai.predictions(id) ON DELETE CASCADE,
    case_id UUID NOT NULL REFERENCES case_mgmt.diagnosis_cases(id) ON DELETE CASCADE,
    expert_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    actual_issue_id UUID REFERENCES catalog.issues(id) ON DELETE RESTRICT,
    is_ai_correct BOOLEAN NOT NULL,
    feedback_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);