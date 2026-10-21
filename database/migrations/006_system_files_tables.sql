-- ============================================================================
-- Migration: 006_system_files_tables.sql
-- Project: KrishiBondhu Bangladesh
-- Description: Object storage file metadata tracking (Cloudinary/Supabase)
--              and system-wide audit logging in the 'system' schema.
-- ============================================================================

-- 1. Files Metadata Table
CREATE TABLE IF NOT EXISTS system.files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    uploaded_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    original_name VARCHAR(255) NOT NULL,
    storage_path TEXT NOT NULL,
    bucket_name VARCHAR(100) DEFAULT 'krishibondhu-uploads' NOT NULL,
    provider VARCHAR(50) DEFAULT 'supabase' NOT NULL, -- e.g., 'supabase', 'cloudinary', 's3'
    mime_type VARCHAR(100) NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    checksum VARCHAR(64),
    public_url TEXT,
    entity_type VARCHAR(50), -- e.g., 'diagnosis_case', 'user_avatar', 'crop'
    entity_id UUID,
    is_processed BOOLEAN DEFAULT FALSE NOT NULL,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    deleted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 2. Audit Logs Table
CREATE TABLE IF NOT EXISTS system.audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL, -- e.g., 'USER_LOGIN', 'DIAGNOSIS_SUBMITTED', 'EXPERT_REVIEW'
    entity_name VARCHAR(100) NOT NULL,
    entity_id UUID,
    old_data JSONB,
    new_data JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 3. Notifications Table
-- In-app notification messages delivered to users when case events occur.
-- Supports: expert_review_completed | case_status_changed | advisory_updated
CREATE TABLE IF NOT EXISTS system.notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    notification_type VARCHAR(100) NOT NULL, -- e.g., 'expert_review_completed'
    title_bn VARCHAR(255) NOT NULL,           -- Notification title in Bangla
    body_bn TEXT,                             -- Full notification body in Bangla
    entity_type VARCHAR(50),                  -- e.g., 'diagnosis_case'
    entity_id UUID,                           -- FK to the related entity
    is_read BOOLEAN DEFAULT FALSE NOT NULL,
    read_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);