-- ============================================================================
-- Seed File: seed_roles.sql
-- Target Schema: auth.roles
-- Description: System user roles for KrishiBondhu platform
-- ============================================================================

INSERT INTO auth.roles (id, code, name, description)
VALUES 
    ('11000000-0000-0000-0000-000000000001', 'farmer', 'Farmer', 'Smallholder farmer accessing ChashiGuard diagnosis and advisories'),
    ('11000000-0000-0000-0000-000000000002', 'expert', 'Agricultural Expert', 'DAE/BARI agricultural extension specialist providing expert reviews'),
    ('11000000-0000-0000-0000-000000000003', 'agent', 'Call Center Agent', 'Assisted channel call center operator registering cases for farmers'),
    ('11000000-0000-0000-0000-000000000004', 'admin', 'System Administrator', 'Platform administrator managing users, catalogs, and system settings')
ON CONFLICT (code) DO UPDATE SET 
    name = EXCLUDED.name,
    description = EXCLUDED.description;