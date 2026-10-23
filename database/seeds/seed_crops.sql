-- ============================================================================
-- Seed File: seed_crops.sql
-- Target Schema: catalog.crops, catalog.crop_varieties
-- Description: Pilot target crops (Potato, Tomato, Chili) and regional varieties
-- ============================================================================

-- Target Crops
INSERT INTO catalog.crops (id, code, name_en, name_bn, scientific_name, description)
VALUES 
    (
        '50000000-0000-0000-0000-000000000001',
        'potato',
        'Potato',
        'আলু',
        'Solanum tuberosum',
        'বগুড়া ও রংপুর অঞ্চলের প্রধান অর্থকরী কন্দ ফসল।'
    ),
    (
        '50000000-0000-0000-0000-000000000002',
        'tomato',
        'Tomato',
        'টমেটো',
        'Solanum lycopersicum',
        'শীতকালীন ও গ্রীষ্মকালীন উচ্চমূল্যের সবজি ফসল।'
    ),
    (
        '50000000-0000-0000-0000-000000000003',
        'chili',
        'Chili',
        'মরিচ',
        'Capsicum annuum',
        'সাতক্ষীরা ও বগুড়া অঞ্চলের অন্যতম প্রধান মশলা জাতীয় ফসল।'
    )
ON CONFLICT (code) DO UPDATE SET 
    name_en = EXCLUDED.name_en,
    name_bn = EXCLUDED.name_bn,
    scientific_name = EXCLUDED.scientific_name,
    description = EXCLUDED.description;

-- Target Crop Varieties
INSERT INTO catalog.crop_varieties (crop_id, code, name_en, name_bn, description)
VALUES 
    -- Potato Varieties
    ('50000000-0000-0000-0000-000000000001', 'granola', 'Granola', 'গ্রানোলা', 'বহুল প্রচলিত হলুদ জাতের আলু।'),
    ('50000000-0000-0000-0000-000000000001', 'asterix', 'Asterix', 'অ্যাস্টারিক্স', 'লাল রঙের উচ্চ ফলনশীল আলু।'),
    ('50000000-0000-0000-0000-000000000001', 'cardinal', 'Cardinal', 'কার্ডিনাল', 'রপ্তানিযোগ্য লাল জাতের আলু।'),
    
    -- Tomato Varieties
    ('50000000-0000-0000-0000-000000000002', 'bari_tomato_14', 'BARI Tomato 14', 'বারি টমেটো ১৪', 'উচ্চ ফলনশীল শীতকালীন জাত।'),
    ('50000000-0000-0000-0000-000000000002', 'bari_tomato_15', 'BARI Tomato 15', 'বারি টমেটো ১৫', 'ভাইরাস প্রতিরোধী উচ্চ ফলনশীল জাত।'),
    
    -- Chili Varieties
    ('50000000-0000-0000-0000-000000000003', 'bari_jhalka', 'BARI Jhalka', 'বারি ঝালকা', 'উচ্চ ফলনশীল মরিচের জাত।'),
    ('50000000-0000-0000-0000-000000000003', 'local_bogura', 'Local Bogura', 'বগুড়া স্থানীয় ঝাল', 'স্থানীয় জনপ্রিয় মরিচের জাত।')
ON CONFLICT (crop_id, code) DO UPDATE SET 
    name_en = EXCLUDED.name_en,
    name_bn = EXCLUDED.name_bn,
    description = EXCLUDED.description;