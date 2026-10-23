-- ============================================================================
-- Test File: test_queries.sql
-- Description: Performance testing common operational queries (PostGIS spatial lookup,
--              farmer case dashboard query, and expert queue aggregation).
-- ============================================================================

-- Query 1: ChashiGuard Farmer Diagnosis History Dashboard Query
SELECT 
    c.id AS case_id,
    c.case_number,
    c.status,
    c.urgency_level,
    c.created_at,
    cr.name_bn AS crop_name_bn,
    iss.name_bn AS diagnosed_issue_bn,
    p.confidence_score,
    adv.summary_bn AS advisory_summary,
    f.public_url AS image_url
FROM case_mgmt.diagnosis_cases c
JOIN catalog.crops cr ON c.crop_id = cr.id
LEFT JOIN ai.predictions p ON p.case_id = c.id
LEFT JOIN catalog.issues iss ON p.primary_issue_id = iss.id
LEFT JOIN advisory.advisories adv ON adv.case_id = c.id
LEFT JOIN system.files f ON c.primary_image_id = f.id
WHERE c.farmer_id = 'a0000000-0000-0000-0000-000000000001'
  AND c.is_deleted = FALSE
ORDER BY c.created_at DESC;

-- Query 2: PostGIS Spatial Query — Find all Farm Plots within a 10km Radius of Shibganj, Bogura
-- Coordinates: Longitude 89.3512, Latitude 24.9215
SELECT 
    p.id AS plot_id,
    p.name AS plot_name,
    u.full_name AS farmer_name,
    u.phone_number,
    ST_Distance(
        p.location::geography,
        ST_SetSRID(ST_MakePoint(89.3512, 24.9215), 4326)::geography
    ) / 1000.0 AS distance_km
FROM farm.plots p
JOIN auth.users u ON p.user_id = u.id
WHERE ST_DWithin(
    p.location::geography,
    ST_SetSRID(ST_MakePoint(89.3512, 24.9215), 4326)::geography,
    10000 -- 10,000 meters = 10km
)
ORDER BY distance_km ASC;

-- Query 3: Expert Review Escalation Queue Summary (Aggregated by Crop)
SELECT 
    cr.name_bn AS crop_name,
    c.urgency_level,
    COUNT(c.id) AS pending_cases_count,
    MIN(c.created_at) AS oldest_unassigned_case
FROM case_mgmt.diagnosis_cases c
JOIN catalog.crops cr ON c.crop_id = cr.id
WHERE c.status IN ('submitted', 'escalated')
  AND c.assigned_expert_id IS NULL
  AND c.is_deleted = FALSE
GROUP BY cr.name_bn, c.urgency_level
ORDER BY 
    CASE c.urgency_level 
        WHEN 'critical' THEN 1 
        WHEN 'high' THEN 2 
        WHEN 'medium' THEN 3 
        ELSE 4 
    END;