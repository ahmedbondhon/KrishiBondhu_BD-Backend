-- ============================================================================
-- Seed File: seed_consent_types.sql
-- Target Schema: auth.consent_types
-- Description: User consent requirements and regulatory compliance types
-- ============================================================================

INSERT INTO auth.consent_types (id, code, title, description, is_mandatory)
VALUES 
    (
        '12000000-0000-0000-0000-000000000001',
        'terms_of_service',
        'শর্তাবলী ও সম্মতি (Terms of Service)',
        'কৃষিবন্ধু প্ল্যাটফর্ম ব্যবহারের সাধারণ শর্তাবলী ও সেবা ব্যবহারের সম্মতি।',
        TRUE
    ),
    (
        '12000000-0000-0000-0000-000000000002',
        'privacy_policy',
        'গোপনীয়তা নীতি (Privacy Policy)',
        'ব্যক্তিগত ও কৃষি সংক্রান্ত তথ্য সংরক্ষণ ও পরামর্শ প্রদানের লক্ষ্যে ব্যবহারের অনুমতি।',
        TRUE
    ),
    (
        '12000000-0000-0000-0000-000000000003',
        'voice_recording',
        'ভয়েস রেকর্ড ব্যবহারের অনুমতি (Voice Recording)',
        'কণ্ঠস্বরের মাধ্যমে প্রদত্ত প্রশ্ন এবং ভয়েস বার্তা বিশ্লেষণ করার অনুমতি।',
        FALSE
    ),
    (
        '12000000-0000-0000-0000-000000000004',
        'location_data',
        'অবস্থান সনাক্তকরণ সম্মতি (Location Access)',
        'সঠিক আবহাওয়া ও আঞ্চলিক বালাই পূর্বাভাস প্রদানের জন্য জিপিএস অবস্থান ব্যবহারের অনুমতি।',
        TRUE
    )
ON CONFLICT (code) DO UPDATE SET 
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    is_mandatory = EXCLUDED.is_mandatory;