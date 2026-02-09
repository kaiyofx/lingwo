-- Добавление полей для оценки сочинения (max_score, common_mistakes, total_score_per).
-- Выполнить один раз при обновлении с предыдущей версии БД.

ALTER TABLE essays ADD COLUMN IF NOT EXISTS max_score DOUBLE PRECISION;
ALTER TABLE essays ADD COLUMN IF NOT EXISTS common_mistakes JSONB DEFAULT '[]'::jsonb;
ALTER TABLE essays ADD COLUMN IF NOT EXISTS total_score_per DOUBLE PRECISION;
