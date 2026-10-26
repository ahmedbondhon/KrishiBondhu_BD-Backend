DO $$
DECLARE r record;
BEGIN
  FOR r IN SELECT table_schema FROM information_schema.tables WHERE table_name = 'expert_reviews' LOOP
    EXECUTE format('ALTER TABLE %I.expert_reviews ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now()', r.table_schema);
  END LOOP;
END $$;
