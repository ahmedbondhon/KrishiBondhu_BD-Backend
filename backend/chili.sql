INSERT INTO advisory.templates
  (id, issue_id, growth_stage_id, severity_level,
   title_bn, title_en, content_bn, content_en,
   preventive_measures_bn, safety_precautions_bn,
   is_active, created_at, updated_at)
SELECT gen_random_uuid(), id, NULL, 'high',
   'মরিচের পাতা কোঁকড়ানো রোগের পরামর্শ',
   'Chili Leaf Curl Virus Advisory',
   'আক্রান্ত গাছ দ্রুত তুলে মাটিতে পুঁতে দিন বা পুড়িয়ে ফেলুন। এই রোগ সাদা মাছি দ্বারা ছড়ায়, তাই সাদা মাছি দমন করুন। নিম তেলের স্প্রে বা হলুদ আঠালো ফাঁদ ব্যবহার করুন। প্রয়োজনে স্থানীয় কৃষি কর্মকর্তার পরামর্শ নিয়ে অনুমোদিত কীটনাশক ব্যবহার করুন।',
   'Remove infected plants quickly and control whiteflies, which spread the virus.',
   'রোগ প্রতিরোধী জাত লাগান। জমি ও আশপাশ আগাছামুক্ত রাখুন। চারা লাগানোর আগে চারা পরীক্ষা করুন।',
   'কীটনাশক ব্যবহারের সময় মাস্ক ও গ্লাভস পরুন। স্প্রের পর হাত-মুখ ভালো করে ধুয়ে নিন।',
   true, now(), now()
FROM catalog.issues WHERE code = 'chili_leaf_curl';
