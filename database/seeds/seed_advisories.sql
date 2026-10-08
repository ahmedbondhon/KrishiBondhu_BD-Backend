-- ============================================================================
-- Seed File: seed_advisories.sql
-- Target Schema: advisory.templates
-- Description: Core advisory templates for automated ChashiGuard responses
-- ============================================================================

INSERT INTO advisory.templates (id, issue_id, growth_stage_id, severity_level, title_bn, title_en, content_bn, content_en, preventive_measures_bn, safety_precautions_bn)
VALUES 
    -- Late Blight Emergency Advisory
    (
        '80000000-0000-0000-0000-000000000001',
        '70000000-0000-0000-0000-000000000001',
        '60000000-0000-0000-0000-000000000003',
        'critical',
        'আলুর লেট ব্লাইট (নাবি ধসা) রোগের জরুরি পরামর্শ',
        'Emergency Advisory for Potato Late Blight',
        'আপনার আলুর ক্ষেতে লেট ব্লাইট (নাবি ধসা) রোগের লক্ষণ পরিলক্ষিত হয়েছে। আর্দ্র ও কুয়াশাচ্ছন্ন আবহাওয়ায় এই রোগ দ্রুত ছড়িয়ে পড়ে। অনতিবিলম্বে অনুমোদিত ছত্রাকনাশক ব্যবহার করুন।',
        'Late blight symptoms detected in your potato field. Foggy weather spreads this disease rapidly. Apply recommended fungicides immediately.',
        '১. আক্রান্ত গাছের পাতা বা সম্পূর্ণ গাছ তুলে মাটিতে পুঁতে ফেলুন।\n২. কুয়াশা থাকলে সেচ দেওয়া বন্ধ রাখুন।\n৩. গাছ শুকানো অবস্থায় স্প্রে করুন।',
        'কীটনাশক/ছত্রাকনাশক স্প্রে করার সময় মাস্ক এবং গ্লাভস ব্যবহার করুন। বাতাসের বিপরীতে স্প্রে করবেন না।'
    ),
    -- Chili Leaf Curl Advisory
    (
        '80000000-0000-0000-0000-000000000002',
        '70000000-0000-0000-0000-000000000004',
        '60000000-0000-0000-0000-000000000008',
        'high',
        'মরিচের পাতা কোঁকড়ানো রোগের প্রতিকার পরামর্শ',
        'Advisory for Chili Leaf Curl Virus',
        'আপনার মরিচ গাছে পাতা কোঁকড়ানো রোগ দেখা গেছে। এটি মূলত সাদা মাছি বা থ্রিপস পোকার মাধ্যমে ছড়ায়। প্রাথমিক অবস্থায় বাহক পোকা দমন করা জরুরি।',
        'Chili leaf curl symptoms detected. Transmitted primarily by whiteflies. Vector control is essential.',
        '১. হলদে আঠালো ফাঁদ (Yellow Sticky Trap) জমিতে স্থাপন করুন।\n২. আক্রান্ত গাছ খুব বেশি ক্ষতিগ্রস্ত হলে তুলে ফেলুন।',
        'কীটনাশক স্প্রে করার পর নূন্যতম ৫ দিন ফসল তুলবেন না এবং স্প্রে করার সময় মুখ ঢেকে রাখুন।'
    )
ON CONFLICT (id) DO NOTHING;