-- ============================================================
-- Supabase SQL: 创建 quiz_submissions 表
-- 在 Supabase Dashboard → SQL Editor 中执行此脚本
-- ============================================================

CREATE TABLE IF NOT EXISTS quiz_submissions (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  destination TEXT NOT NULL,
  duration_days INTEGER NOT NULL DEFAULT 7,
  party_type TEXT NOT NULL,
  japan_experience TEXT,
  play_mode TEXT,
  styles TEXT[] DEFAULT '{}',
  wechat_id TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'new',
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 自动更新 updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER quiz_submissions_updated_at
  BEFORE UPDATE ON quiz_submissions
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at();

-- 开启 RLS 但允许 anon insert + service 读取
ALTER TABLE quiz_submissions ENABLE ROW LEVEL SECURITY;

-- 允许匿名用户提交（insert only）
CREATE POLICY "Anyone can submit quiz"
  ON quiz_submissions
  FOR INSERT
  TO anon
  WITH CHECK (true);

-- 允许匿名用户读取（admin 页面用，生产环境应改为 service_role）
CREATE POLICY "Anyone can read quiz submissions"
  ON quiz_submissions
  FOR SELECT
  TO anon
  USING (true);

-- 允许匿名用户更新状态（admin 用）
CREATE POLICY "Anyone can update quiz submissions"
  ON quiz_submissions
  FOR UPDATE
  TO anon
  USING (true);
