-- ============================================================================
-- Seed File: seed_issues.sql
-- Target Schema: catalog.issues, catalog.remedies
-- Description: Major pilot pests, diseases, and recommended remedy guidelines
-- ============================================================================

-- 1. Seed Crop Issues
INSERT INTO catalog.issues (id, crop_id, code, name_en, name_bn, category, scientific_name, symptoms_bn, symptoms_en, severity_level)
VALUES 
    -- Potato Late Blight
    (
        '70000000-0000-0000-0000-000000000001',
        '50000000-0000-0000-0000-000000000001',
        'potato_late_blight',
        'Potato Late Blight',
        'আলুর লেট ব্লাইট (নাবি ধসা)',
        'disease',
        'Phytophthora infestans',
        'পাতায় পানি ভেজা ভেজা দাগ দেখা যায় যা দ্রুত কালো ও পচে যায়। আর্দ্র আবহাওয়ায় পাতার নিচে সাদা পাউডারের মতো ছত্রাক দেখা যায়।',
        'Water-soaked lesions on leaves turning brown-black rapidly with white fungal growth on undersides in humid conditions.',
        'critical'
    ),
    -- Potato Early Blight
    (
        '70000000-0000-0000-0000-000000000002',
        '50000000-0000-0000-0000-000000000002',
        'potato_early_blight',
        'Potato Early Blight',
        'আলুর আর্লি ব্লাইট (আগেধসা)',
        'disease',
        'Alternaria solani',
        'পুরানো পাতায় গাঢ় বাদামী থেকে কালো রঙের গোলাকার দাগ দেখা যায় যাতে রিং-এর মতো বৃত্তাকার দাগ থাকে।',
        'Concentric dark ring spots on mature lower leaves.',
        'medium'
    ),
    -- Tomato Leaf Curl
    (
        '70000000-0000-0000-0000-000000000003',
        '50000000-0000-0000-0000-000000000002',
        'tomato_leaf_curl',
        'Tomato Leaf Curl Virus',
        'টমেটোর পাতা কোঁকড়ানো রোগ',
        'disease',
        'Begomovirus',
        'পাতা উপরের দিকে কোঁকড়ে ছোট হয়ে যায়, গাছ খর্বাকৃতির হয় এবং ফুল-ফল ধরা কমে যায়।',
        'Upward curling and yellowing of leaves with stunted plant growth.',
        'high'
    ),
    -- Chili Leaf Curl Virus
    (
        '70000000-0000-0000-0000-000000000004',
        '50000000-0000-0000-0000-000000000003',
        'chili_leaf_curl',
        'Chili Leaf Curl Virus',
        'মরিচের পাতা কোঁকড়ানো রোগ',
        'disease',
        'Begomovirus',
        'গাছের পাতা উপরের দিকে কোঁকড়ে নৌকা আকৃতির হয়ে যায় এবং নতুন পাতা আকারে ছোট হয়ে যায়। সাদা মাছি দ্বারা এ রোগ ছড়ায়।',
        'Curling of leaves into boat shape with reduced leaf size transmitted by whitefly.',
        'high'
    )
ON CONFLICT (code) DO UPDATE SET 
    name_en = EXCLUDED.name_en,
    name_bn = EXCLUDED.name_bn,
    symptoms_bn = EXCLUDED.symptoms_bn,
    severity_level = EXCLUDED.severity_level;

-- 2. Seed Remedies
INSERT INTO catalog.remedies (id, issue_id, type, title_bn, title_en, description_bn, description_en, chemical_name, dosage_bn, safety_instructions_bn)
VALUES 
    -- Potato Late Blight Remedies
    (
        '71000000-0000-0000-0000-000000000001',
        '70000000-0000-0000-0000-000000000001',
        'chemical',
        'সিকিউর বা ম্যানকোজেব ছত্রাকনাশক স্প্রে',
        'Secure or Mancozeb Fungicide Spray',
        'রোগের প্রাথমিক লক্ষণ দেখা মাত্রই অনুমোদিত ছত্রাকনাশক সঠিক মাত্রায় ভালোভাব স্প্রে করুন। কুয়াশাচ্ছন্ন আবহাওয়ায় প্রতি ৫-৭ দিন পর পর স্প্রে অব্যাহত রাখুন।',
        'Spray approved fungicides upon initial symptoms. Re-apply every 5-7 days during foggy conditions.',
        'Mancozeb 75% WP / Fenamidone + Mancozeb',
        'প্রতি লিটার পানিতে ২ গ্রাম ম্যানকোজেব অথবা ১ গ্রাম সিকিউর মিশিয়ে গাছের পাতার উপরে ও নিচে ভালোভাবে ভিজিয়ে স্প্রে করুন।',
        'স্প্রে করার সময় মুখে মাস্ক ও হাতে গ্লাভস ব্যবহার করুন। স্প্রে করার পর ৭ দিন আলু তুলবেন না।'
    ),
    (
        '71000000-0000-0000-0000-000000000002',
        '70000000-0000-0000-0000-000000000001',
        'cultural',
        'ক্ষেত পরিচ্ছন্নতা ও সেচ নিয়ন্ত্রণ',
        'Field Hygiene & Irrigation Control',
        'রোগাক্রান্ত গাছ টেনে তুলে নষ্ট করে ফেলুন। কুয়াশাচ্ছন্ন আবহাওয়ায় জমিতে সেচ দেওয়া থেকে বিরত থাকুন।',
        'Remove and destroy infected plants. Avoid flooding irrigation during foggy weather.',
        NULL,
        'প্রয়োজন অনুযায়ী প্রয়োগ করুন।',
        'আক্রান্ত কান্ড ও পাতা খোলা জমিতে ফেলে রাখবেন না।'
    ),
    -- Chili Leaf Curl Remedies
    (
        '71000000-0000-0000-0000-000000000003',
        '70000000-0000-0000-0000-000000000004',
        'chemical',
        'সাদা মাছি দমনে ইমিডাক্লোপ্রিড স্প্রে',
        'Imidacloprid Spray for Whitefly Vector',
        'রোগ ছড়ানো সাদা মাছি দমনের জন্য ইমিডাক্লোপ্রিড বা এসিটামিপ্রিড জাতীয় কীটনাশক ব্যবহার করুন।',
        'Control whitefly vectors using systemic insecticides like Imidacloprid.',
        'Imidacloprid 200 SL',
        'প্রতি লিটার পানিতে ০.৫ মিলি ইমিডাক্লোপ্রিড মিশিয়ে ১০-১২ দিন পর পর ২ বার স্প্রে করুন।',
        'কীটনাশক প্রয়োগের পর ৫ দিনের মধ্যে মরিচ তুলবেন না।'
    )
ON CONFLICT (id) DO NOTHING;