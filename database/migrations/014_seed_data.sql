-- ============================================================================
-- Migration: 014_seed_data.sql
-- Project: KrishiBondhu Bangladesh
-- Description: Essential seed data for roles, consent types, pilot geographic
--              regions (Bogura, Satkhira), MVP target crops (Potato, Tomato, Chili),
--              growth stages, crop issues, remedies, AI models, and advisory templates.
-- ============================================================================

-- 1. Seed Roles (auth.roles)
INSERT INTO auth.roles (code, name, description)
VALUES 
    ('farmer', 'Farmer', 'Smallholder farmer accessing ChashiGuard diagnosis and advisories'),
    ('expert', 'Agricultural Expert', 'DAE/BARI agricultural extension officer providing expert reviews'),
    ('agent', 'Call Center Agent', 'Assisted channel call center operator'),
    ('admin', 'System Administrator', 'Platform and system administrator')
ON CONFLICT (code) DO UPDATE SET 
    name = EXCLUDED.name,
    description = EXCLUDED.description;

-- 2. Seed Consent Types (auth.consent_types)
INSERT INTO auth.consent_types (code, title, description, is_mandatory)
VALUES 
    ('terms_of_service', 'Terms of Service', 'Consent to platform terms of service and usage conditions', TRUE),
    ('privacy_policy', 'Privacy Policy', 'Consent to personal data processing for advisory delivery', TRUE),
    ('voice_recording', 'Voice Recording Consent', 'Consent to record audio queries for advisory generation', FALSE),
    ('location_data', 'Location Data Access', 'Consent to capture GPS coordinates for regional weather and pest tracking', TRUE)
ON CONFLICT (code) DO UPDATE SET 
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    is_mandatory = EXCLUDED.is_mandatory;

-- 3. Seed Geographic Divisions & Pilot Districts (geo.divisions & geo.districts)
INSERT INTO geo.divisions (id, bbs_code, name_en, name_bn)
VALUES 
    ('10000000-0000-0000-0000-000000000001', '50', 'Rajshahi', 'রাজশাহী'),
    ('10000000-0000-0000-0000-000000000002', '40', 'Khulna', 'খুলনা')
ON CONFLICT (bbs_code) DO NOTHING;

INSERT INTO geo.districts (id, division_id, bbs_code, name_en, name_bn)
VALUES 
    ('20000000-0000-0000-0000-000000000001', '10000000-0000-0000-0000-000000000001', '5010', 'Bogura', 'বগুড়া'),
    ('20000000-0000-0000-0000-000000000002', '10000000-0000-0000-0000-000000000002', '4087', 'Satkhira', 'সাতক্ষীরা')
ON CONFLICT (bbs_code) DO NOTHING;

INSERT INTO geo.upazilas (id, district_id, bbs_code, name_en, name_bn)
VALUES 
    ('30000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-000000000001', '501020', 'Bogura Sadar', 'বগুড়া সদর'),
    ('30000000-0000-0000-0000-000000000002', '20000000-0000-0000-0000-000000000001', '501088', 'Shibganj', 'শিবগঞ্জ'),
    ('30000000-0000-0000-0000-000000000003', '20000000-0000-0000-0000-000000000002', '408782', 'Sadar Satkhira', 'সাতক্ষীরা সদর')
ON CONFLICT (bbs_code) DO NOTHING;

INSERT INTO geo.unions (id, upazila_id, bbs_code, name_en, name_bn)
VALUES 
    ('40000000-0000-0000-0000-000000000001', '30000000-0000-0000-0000-000000000002', '15', 'Gokul', 'গোকুল'),
    ('40000000-0000-0000-0000-000000000002', '30000000-0000-0000-0000-000000000002', '25', 'Mokamtala', 'মোকামতলা')
ON CONFLICT (upazila_id, bbs_code) DO NOTHING;

-- 4. Seed Target MVP Pilot Crops (catalog.crops)
INSERT INTO catalog.crops (id, code, name_en, name_bn, scientific_name, description)
VALUES 
    ('50000000-0000-0000-0000-000000000001', 'potato', 'Potato', 'আলু', 'Solanum tuberosum', 'Major tuber crop widely cultivated in Bogura region.'),
    ('50000000-0000-0000-0000-000000000002', 'tomato', 'Tomato', 'টমেটো', 'Solanum lycopersicum', 'High-value winter cash vegetable crop.'),
    ('50000000-0000-0000-0000-000000000003', 'chili', 'Chili', 'মরিচ', 'Capsicum annuum', 'Major spice crop susceptible to leaf curl virus.')
ON CONFLICT (code) DO UPDATE SET 
    name_en = EXCLUDED.name_en,
    name_bn = EXCLUDED.name_bn,
    scientific_name = EXCLUDED.scientific_name;

-- 5. Seed Crop Varieties (catalog.crop_varieties)
INSERT INTO catalog.crop_varieties (crop_id, code, name_en, name_bn)
VALUES 
    ('50000000-0000-0000-0000-000000000001', 'granola', 'Granola', 'গ্রানোলা'),
    ('50000000-0000-0000-0000-000000000001', 'asterix', 'Asterix', 'অ্যাস্টারিক্স'),
    ('50000000-0000-0000-0000-000000000002', 'bari_tomato_14', 'BARI Tomato 14', 'বারি টমেটো ১৪'),
    ('50000000-0000-0000-0000-000000000003', 'bari_jhalka', 'BARI Jhalka', 'বারি ঝালকা')
ON CONFLICT (crop_id, code) DO NOTHING;

-- 6. Seed Growth Stages (catalog.growth_stages)
INSERT INTO catalog.growth_stages (id, crop_id, stage_code, name_en, name_bn, sequence_order)
VALUES 
    ('60000000-0000-0000-0000-000000000001', '50000000-0000-0000-0000-000000000001', 'sprouting', 'Sprouting / Vegetative', 'অঙ্কুরোদগম ও অঙ্গজ বৃদ্ধি', 1),
    ('60000000-0000-0000-0000-000000000002', '50000000-0000-0000-0000-000000000001', 'tuber_initiation', 'Tuber Initiation', 'টিউবার গঠন সূচনা', 2),
    ('60000000-0000-0000-0000-000000000003', '50000000-0000-0000-0000-000000000001', 'tuber_bulking', 'Tuber Bulking', 'আলু বৃদ্ধি পর্যায়', 3),
    ('60000000-0000-0000-0000-000000000004', '50000000-0000-0000-0000-000000000001', 'maturation', 'Maturation & Harvesting', 'পরিপক্কতা ও সংগ্রহ', 4)
ON CONFLICT (crop_id, sequence_order) DO NOTHING;

-- 7. Seed Common Crop Issues (catalog.issues)
INSERT INTO catalog.issues (id, crop_id, code, name_en, name_bn, category, scientific_name, symptoms_bn, severity_level)
VALUES 
    (
        '70000000-0000-0000-0000-000000000001',
        '50000000-0000-0000-0000-000000000001',
        'potato_late_blight',
        'Potato Late Blight',
        'আলুর লেট ব্লাইট (নাবি ধসা)',
        'disease',
        'Phytophthora infestans',
        'পাতায় পানি ভেজা ভেজা দাগ দেখা যায় যা দ্রুত কালো ও পচে যায়। আর্দ্র আবহাওয়ায় পাতার নিচে সাদা পাউডারের মতো ছত্রাক দেখা যায়।',
        'critical'
    ),
    (
        '70000000-0000-0000-0000-000000000002',
        '50000000-0000-0000-0000-000000000001',
        'potato_early_blight',
        'Potato Early Blight',
        'আলুর আর্লি ব্লাইট (আগেধসা)',
        'disease',
        'Alternaria solani',
        'পুরানো পাতায় গাঢ় বাদামী থেকে কালো রঙের গোলাকার দাগ দেখা যায় যাতে রিং-এর মতো বৃত্তাকার দাগ থাকে।',
        'medium'
    ),
    (
        '70000000-0000-0000-0000-000000000003',
        '50000000-0000-0000-0000-000000000003',
        'chili_leaf_curl',
        'Chili Leaf Curl Virus',
        'মরিচের পাতা কোঁকড়ানো রোগ',
        'disease',
        'Begomovirus',
        'গাছের পাতা উপরের দিকে কোঁকড়ে নৌকা আকৃতির হয়ে যায় এবং নতুন পাতা আকারে ছোট হয়ে যায়।',
        'high'
    )
ON CONFLICT (code) DO UPDATE SET 
    name_en = EXCLUDED.name_en,
    name_bn = EXCLUDED.name_bn,
    symptoms_bn = EXCLUDED.symptoms_bn,
    severity_level = EXCLUDED.severity_level;

-- 8. Seed Remedies (catalog.remedies)
INSERT INTO catalog.remedies (issue_id, type, title_bn, title_en, description_bn, chemical_name, dosage_bn, safety_instructions_bn)
VALUES 
    (
        '70000000-0000-0000-0000-000000000001',
        'chemical',
        'ম্যানকোজেব বা সিকিউর স্প্রে',
        'Mancozeb or Secure Spray',
        'রোগের লক্ষণ দেখা মাত্রই অনুমোদিত ছত্রাকনাশক স্প্রে করুন। প্রতি ৭-১০ দিন পর পর আবহাওয়া আর্দ্র থাকলে পুনরায় স্প্রে করুন।',
        'Mancozeb 75% WP / Fenamidone + Mancozeb',
        'প্রতি লিটার পানিতে ২ গ্রাম ম্যানকোজেব মিশিয়ে ভালোভাবে স্প্রে করতে হবে।',
        'স্প্রে করার সময় মাস্ক এবং গ্লাভস ব্যবহার করুন। স্প্রে করার পর ৭ দিন ফসল তুলবেন না।'
    ),
    (
        '70000000-0000-0000-0000-000000000001',
        'cultural',
        'জমি পরিষ্কারকরণ ও সুষম সেচ',
        'Field Sanitation & Balanced Irrigation',
        'আক্রান্ত গাছ বা পাতা তুলে ধ্বংস করুন। জমিতে অতিরিক্ত পানি জমা হতে দেবেন না।',
        NULL,
        'প্রয়োজন অনুযায়ী প্রয়োগ করুন।',
        'আক্রান্ত কান্ড বা পাতা খোলা স্থানে ফেলে রাখবেন না।'
    )
ON CONFLICT DO NOTHING;

-- 9. Seed AI Model Registry (ai.models)
INSERT INTO ai.models (model_code, name, version, framework, task_type, accuracy_score, f1_score, is_active)
VALUES 
    ('chashiguard-cv-v1', 'ChashiGuard Disease Vision Classifier', '1.0.0', 'PyTorch', 'image_classification', 0.9250, 0.9180, TRUE)
ON CONFLICT (model_code) DO UPDATE SET 
    name = EXCLUDED.name,
    version = EXCLUDED.version,
    accuracy_score = EXCLUDED.accuracy_score,
    is_active = EXCLUDED.is_active;

-- 10. Seed Advisory Templates (advisory.templates)
INSERT INTO advisory.templates (issue_id, severity_level, title_bn, title_en, content_bn, preventive_measures_bn, safety_precautions_bn)
VALUES 
    (
        '70000000-0000-0000-0000-000000000001',
        'critical',
        'আলুর লেট ব্লাইট রোগের জরুরি পরামর্শ',
        'Emergency Advisory for Potato Late Blight',
        'আপনার আলুর ক্ষেতে লেট ব্লাইট (নাবি ধসা) রোগের লক্ষণ দেখা গেছে। এটি দ্রুত ছড়ায় তাই অনতিবিলম্বে ব্যবস্থা গ্রহণ করা জরুরি।',
        '১. ক্ষেত নিয়মিত পরিদর্শন করুন।\n২. আক্রান্ত গাছ তুলে মাটির নিচে পুঁতে ফেলুন।\n৩. অতিরিক্ত সিক্ত আবহাওয়ায় সেচ বন্ধ রাখুন।',
        'কীটনাশক/ছত্রাকনাশক স্প্রে করার সময় মুখ ও হাত ঢেকে রাখুন এবং বাতাসের প্রতিকূলে স্প্রে করবেন না।'
    )
ON CONFLICT DO NOTHING;