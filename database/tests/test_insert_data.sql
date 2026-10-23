-- ============================================================================
-- Test File: test_insert_data.sql
-- Description: End-to-end integration test validating record insertion across
--              users, farm plots, files, diagnosis cases, AI predictions, and advisories.
-- ============================================================================

BEGIN;

-- 1. Insert Test Farmer User
INSERT INTO auth.users (id, role_id, phone_number, full_name, division_id, district_id, upazila_id, union_id, preferred_language)
VALUES (
    'a0000000-0000-0000-0000-000000000001',
    (SELECT id FROM auth.roles WHERE code = 'farmer'),
    '+8801700000001',
    'মোঃ রফিকুল ইসলাম',
    '10000000-0000-0000-0000-000000000001', -- Rajshahi
    '20000000-0000-0000-0000-000000000001', -- Bogura
    '30000000-0000-0000-0000-000000000002', -- Shibganj
    '40000000-0000-0000-0000-000000000001', -- Gokul
    'bn'
);

-- 2. Insert Test Farm Plot & Plot Crop
INSERT INTO farm.plots (id, user_id, name, area_bigha, soil_type, division_id, district_id, upazila_id, union_id, location)
VALUES (
    'b0000000-0000-0000-0000-000000000001',
    'a0000000-0000-0000-0000-000000000001',
    'উত্তর মাঠ আলু ক্ষেত',
    2.50,
    'clay_loam',
    '10000000-0000-0000-0000-000000000001',
    '20000000-0000-0000-0000-000000000001',
    '30000000-0000-0000-0000-000000000002',
    '40000000-0000-0000-0000-000000000001',
    ST_SetSRID(ST_MakePoint(89.3512, 24.9215), 4326)
);

INSERT INTO farm.plot_crops (id, plot_id, crop_id, current_stage_id, sowing_date, status)
VALUES (
    'b1000000-0000-0000-0000-000000000001',
    'b0000000-0000-0000-0000-000000000001',
    '50000000-0000-0000-0000-000000000001', -- Potato
    '60000000-0000-0000-0000-000000000003', -- Tuber Bulking
    '2026-11-15',
    'active'
);

-- 3. Insert System Leaf Image File Metadata
INSERT INTO system.files (id, uploaded_by, original_name, storage_path, bucket_name, provider, mime_type, file_size_bytes, entity_type)
VALUES (
    'c0000000-0000-0000-0000-000000000001',
    'a0000000-0000-0000-0000-000000000001',
    'potato_leaf_blight_sample.jpg',
    'cases/2026/10/potato_leaf_blight_sample.jpg',
    'chashiguard-images',
    'supabase',
    'image/jpeg',
    1024500,
    'diagnosis_case'
);

-- 4. Insert Diagnosis Case
INSERT INTO case_mgmt.diagnosis_cases (id, case_number, farmer_id, plot_id, plot_crop_id, crop_id, growth_stage_id, primary_image_id, farmer_notes, location, status, urgency_level)
VALUES (
    'd0000000-0000-0000-0000-000000000001',
    'CASE-20261008-0001',
    'a0000000-0000-0000-0000-000000000001',
    'b0000000-0000-0000-0000-000000000001',
    'b1000000-0000-0000-0000-000000000001',
    '50000000-0000-0000-0000-000000000001',
    '60000000-0000-0000-0000-000000000003',
    'c0000000-0000-0000-0000-000000000001',
    'পাতায় কালো কালো ভেজা দাগ দেখা যাচ্ছে, ২ দিনে অনেক বেড়েছে।',
    ST_SetSRID(ST_MakePoint(89.3512, 24.9215), 4326),
    'ai_analyzed',
    'high'
);

-- 5. Insert AI Prediction & Breakdown Details
INSERT INTO ai.predictions (id, case_id, model_id, file_id, primary_issue_id, confidence_score, is_confident, status)
VALUES (
    'e0000000-0000-0000-0000-000000000001',
    'd0000000-0000-0000-0000-000000000001',
    (SELECT id FROM ai.models WHERE model_code = 'chashiguard-cv-v1'),
    'c0000000-0000-0000-0000-000000000001',
    '70000000-0000-0000-0000-000000000001', -- Potato Late Blight
    0.9425,
    TRUE,
    'completed'
);

INSERT INTO ai.prediction_details (prediction_id, issue_id, class_label, rank_order, confidence_score)
VALUES 
    ('e0000000-0000-0000-0000-000000000001', '70000000-0000-0000-0000-000000000001', 'potato_late_blight', 1, 0.9425),
    ('e0000000-0000-0000-0000-000000000001', '70000000-0000-0000-0000-000000000002', 'potato_early_blight', 2, 0.0410);

-- 6. Insert Generated Bangla Advisory
INSERT INTO advisory.advisories (case_id, prediction_id, template_id, title_bn, summary_bn, detailed_treatment_bn, chemical_recommendations_bn, source, is_published)
VALUES (
    'd0000000-0000-0000-0000-000000000001',
    'e0000000-0000-0000-0000-000000000001',
    '80000000-0000-0000-0000-000000000001',
    'আলুর লেট ব্লাইট (নাবি ধসা) রোগের জরুরি পরামর্শ',
    'আপনার আলুর ক্ষেতে লেট ব্লাইট রোগের লক্ষণ সনাক্ত করা হয়েছে। অবিলম্বে ছত্রাকনাশক প্রয়োগ জরুরি।',
    'আক্রান্ত গাছ তুলে ধ্বংস করুন এবং আবহাওয়া শুষ্ক হওয়া পর্যন্ত জমিতে অতিরিক্ত সেচ দেওয়া বন্ধ রাখুন।',
    'প্রতি লিটার পানিতে ২ গ্রাম ম্যানকোজেব অথবা ১ গ্রাম সিকিউর মিশিয়ে গাছের পাতায় ভালোভাবে স্প্রে করুন।',
    'ai_generated',
    TRUE
);

-- Validate Insertion Count
DO $$
DECLARE
    case_count INT;
BEGIN
    SELECT COUNT(*) INTO case_count FROM case_mgmt.diagnosis_cases WHERE id = 'd0000000-0000-0000-0000-000000000001';
    IF case_count = 1 THEN
        RAISE NOTICE 'SUCCESS: test_insert_data completed successfully.';
    ELSE
        RAISE EXCEPTION 'FAIL: Insertion test failed.';
    END IF;
END $$;

COMMIT;