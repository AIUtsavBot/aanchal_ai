DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'postnatal_assessments' AND column_name = 'nutrition_advice') THEN
        ALTER TABLE postnatal_assessments ADD COLUMN nutrition_advice TEXT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'postnatal_assessments' AND column_name = 'medications') THEN
        ALTER TABLE postnatal_assessments ADD COLUMN medications TEXT;
    END IF;
END $$;
