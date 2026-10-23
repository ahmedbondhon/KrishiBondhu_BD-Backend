-- ============================================================================
-- Test File: test_relationships.sql
-- Description: Verifies Foreign Key integrity, ON DELETE actions, and multi-schema
--              join consistency across geo, auth, catalog, farm, and case_mgmt.
-- ============================================================================

BEGIN;

-- 1. Test Foreign Key Cascades and Integrity Verification
DO $$
DECLARE
    v_user_id UUID := 'a0000000-0000-0000-0000-000000000099';
    v_plot_id UUID := 'b0000000-0000-0000-0000-000000000099';
    v_case_id UUID := 'd0000000-0000-0000-0000-000000000099';
    v_file_id UUID := 'c0000000-0000-0000-0000-000000000099';
    v_count INT;
BEGIN
    -- Temporary User
    INSERT INTO auth.users (id, role_id, phone_number, full_name)
    VALUES (v_user_id, (SELECT id FROM auth.roles WHERE code = 'farmer'), '+8801799999999', 'Test FK User');

    -- Temporary Plot linked to User
    INSERT INTO farm.plots (id, user_id, name) VALUES (v_plot_id, v_user_id, 'Temp Plot');

    -- Temporary File
    INSERT INTO system.files (id, uploaded_by, original_name, storage_path, mime_type, file_size_bytes)
    VALUES (v_file_id, v_user_id, 'test.jpg', 'temp/test.jpg', 'image/jpeg', 100);

    -- Temporary Diagnosis Case linked to User, Plot, and File
    INSERT INTO case_mgmt.diagnosis_cases (id, case_number, farmer_id, plot_id, primary_image_id, crop_id)
    VALUES (v_case_id, 'CASE-TEMP-999', v_user_id, v_plot_id, v_file_id, '50000000-0000-0000-0000-000000000001');

    -- Verify FK CASCADE: Deleting User should cascade and remove linked Plots and Cases
    DELETE FROM auth.users WHERE id = v_user_id;

    SELECT COUNT(*) INTO v_count FROM farm.plots WHERE id = v_plot_id;
    IF v_count <> 0 THEN
        RAISE EXCEPTION 'FK CASCADE FAIL: Plot not deleted when User was deleted.';
    END IF;

    SELECT COUNT(*) INTO v_count FROM case_mgmt.diagnosis_cases WHERE id = v_case_id;
    IF v_count <> 0 THEN
        RAISE EXCEPTION 'FK CASCADE FAIL: Case not deleted when User was deleted.';
    END IF;

    -- Clean up file entry if set null
    DELETE FROM system.files WHERE id = v_file_id;

    RAISE NOTICE 'SUCCESS: All Foreign Key relationships and CASCADE rules functioning correctly.';
END $$;

-- 2. Verify Schema Join Reachability Query
SELECT 
    c.case_number,
    u.full_name AS farmer_name,
    g_dist.name_bn AS district,
    cr.name_bn AS crop_name,
    iss.name_bn AS issue_name,
    adv.title_bn AS advisory_title
FROM case_mgmt.diagnosis_cases c
JOIN auth.users u ON c.farmer_id = u.id
LEFT JOIN geo.districts g_dist ON u.district_id = g_dist.id
JOIN catalog.crops cr ON c.crop_id = cr.id
LEFT JOIN ai.predictions p ON p.case_id = c.id
LEFT JOIN catalog.issues iss ON p.primary_issue_id = iss.id
LEFT JOIN advisory.advisories adv ON adv.case_id = c.id;

ROLLBACK;