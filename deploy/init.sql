-- Travel AI 初始化 SQL
-- 仅用于 Docker 首次启动时建表，alembic 迁移会在 backend 启动后接管

CREATE TABLE IF NOT EXISTS quiz_submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT,
    destination TEXT NOT NULL,
    duration_days INTEGER NOT NULL DEFAULT 7,
    people_count INTEGER,
    party_type TEXT NOT NULL DEFAULT 'unknown',
    japan_experience TEXT,
    play_mode TEXT,
    budget_focus TEXT,
    styles TEXT[] DEFAULT '{}',
    wechat_id TEXT,
    status TEXT NOT NULL DEFAULT 'new',
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_quiz_submissions_status ON quiz_submissions(status);
CREATE INDEX IF NOT EXISTS idx_quiz_submissions_created ON quiz_submissions(created_at DESC);
