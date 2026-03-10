-- Crestal Database Schema
-- PostgreSQL 15+

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. USERS & AUTHENTICATION
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    avatar_url VARCHAR(500),
    country VARCHAR(100) NOT NULL DEFAULT 'Nigeria',
    state VARCHAR(100),
    city VARCHAR(100),
    role VARCHAR(20) NOT NULL DEFAULT 'worker' 
        CHECK (role IN ('worker', 'client', 'creator', 'sponsor', 'admin')),
    is_phone_verified BOOLEAN DEFAULT FALSE,
    is_id_verified BOOLEAN DEFAULT FALSE,
    id_verified_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP,
    device_fingerprint VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_phone ON users(phone);
CREATE INDEX idx_users_role ON users(role);

-- 2. JOB HEADERS (15 categories)
CREATE TABLE skill_headers (
    header_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT NOT NULL,
    question_depth VARCHAR(20) NOT NULL 
        CHECK (question_depth IN ('light', 'medium', 'heavy', 'extreme')),
    icon_url VARCHAR(500),
    display_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. JOB TYPES (sub-headings)
CREATE TABLE job_types (
    job_type_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    header_id UUID NOT NULL REFERENCES skill_headers(header_id),
    name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    submission_type VARCHAR(50) NOT NULL 
        CHECK (submission_type IN ('form', 'file_upload', 'text_editor', 'interactive_form', 'rich_text')),
    avg_simulation_minutes INTEGER NOT NULL,
    mini_task_rubric JSONB NOT NULL DEFAULT '{}',
    question_count_beginner INTEGER DEFAULT 20,
    question_count_intermediate INTEGER DEFAULT 30,
    question_count_advanced INTEGER DEFAULT 40,
    question_count_expert INTEGER DEFAULT 50,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(header_id, name)
);

CREATE INDEX idx_job_types_header ON job_types(header_id);

-- 4. USER SKILLS (what each user has selected)
CREATE TABLE user_skills (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id),
    job_type_id UUID NOT NULL REFERENCES job_types(job_type_id),
    current_rank VARCHAR(20) NOT NULL DEFAULT 'beginner'
        CHECK (current_rank IN ('beginner', 'intermediate', 'advanced', 'expert')),
    rank_score DECIMAL(5,2) DEFAULT 0.00,
    status VARCHAR(20) NOT NULL DEFAULT 'pending_simulation'
        CHECK (status IN ('pending_simulation', 'active', 'suspended')),
    last_simulation_at TIMESTAMP,
    next_retake_available_at TIMESTAMP,
    total_attempts INTEGER DEFAULT 0,
    passed_attempts INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, job_type_id)
);

CREATE INDEX idx_user_skills_user ON user_skills(user_id);
CREATE INDEX idx_user_skills_job_type ON user_skills(job_type_id);
CREATE INDEX idx_user_skills_rank ON user_skills(current_rank);

-- 5. SIMULATION SESSIONS
CREATE TABLE simulation_sessions (
    session_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id),
    job_type_id UUID NOT NULL REFERENCES job_types(job_type_id),
    level VARCHAR(20) NOT NULL
        CHECK (level IN ('beginner', 'intermediate', 'advanced', 'expert')),
    status VARCHAR(20) NOT NULL DEFAULT 'in_progress'
        CHECK (status IN ('in_progress', 'paused', 'completed', 'abandoned')),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    last_active_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    knowledge_score DECIMAL(5,2),
    mini_task_score DECIMAL(5,2),
    mini_task_passed BOOLEAN,
    overall_passed BOOLEAN,
    skill_dna_snapshot JSONB,
    attempt_number INTEGER NOT NULL DEFAULT 1,
    ip_address INET,
    user_agent TEXT,
    session_token_hash VARCHAR(255)
);

CREATE INDEX idx_sessions_user ON simulation_sessions(user_id);
CREATE INDEX idx_sessions_job_type ON simulation_sessions(job_type_id);
CREATE INDEX idx_sessions_status ON simulation_sessions(status);
CREATE INDEX idx_sessions_active ON simulation_sessions(user_id, status) 
    WHERE status IN ('in_progress', 'paused');

-- 6. SIMULATION QUESTIONS
CREATE TABLE simulation_questions (
    question_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES simulation_sessions(session_id),
    concept_area VARCHAR(100) NOT NULL,
    question_type VARCHAR(20) NOT NULL
        CHECK (question_type IN ('core', 'specific')),
    question_text TEXT NOT NULL,
    answer_options JSONB NOT NULL,
    correct_answer VARCHAR(500) NOT NULL,
    worker_answer VARCHAR(500),
    is_correct BOOLEAN,
    order_index INTEGER NOT NULL,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    answered_at TIMESTAMP,
    time_spent_seconds INTEGER
);

CREATE INDEX idx_questions_session ON simulation_questions(session_id);
CREATE INDEX idx_questions_concept ON simulation_questions(concept_area);
CREATE INDEX idx_questions_answered ON simulation_questions(session_id, answered_at) 
    WHERE answered_at IS NULL;

-- 7. TASK SUBMISSIONS (mini-tasks)
CREATE TABLE task_submissions (
    submission_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES simulation_sessions(session_id),
    user_id UUID NOT NULL REFERENCES users(user_id),
    job_type_id UUID NOT NULL REFERENCES job_types(job_type_id),
    task_description TEXT NOT NULL,
    submission_content TEXT,
    file_url VARCHAR(500),
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    auto_score DECIMAL(5,2),
    ai_evaluation JSONB,
    peer_review_score DECIMAL(5,2),
    peer_reviewer_id UUID REFERENCES users(user_id),
    passed BOOLEAN,
    feedback_notes TEXT,
    evaluation_status VARCHAR(20) DEFAULT 'pending'
        CHECK (evaluation_status IN ('pending', 'ai_completed', 'peer_reviewed', 'finalized'))
);

CREATE INDEX idx_submissions_session ON task_submissions(session_id);
CREATE INDEX idx_submissions_user ON task_submissions(user_id);
CREATE INDEX idx_submissions_status ON task_submissions(evaluation_status);

-- 8. SKILL DNA (weakness tracking)
CREATE TABLE user_skill_dna (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id),
    job_type_id UUID NOT NULL REFERENCES job_types(job_type_id),
    concept_area VARCHAR(100) NOT NULL,
    fail_count INTEGER DEFAULT 0,
    pass_count INTEGER DEFAULT 0,
    weakness_score DECIMAL(4,3) GENERATED ALWAYS AS (
        CASE 
            WHEN (fail_count + pass_count) = 0 THEN 0.000
            ELSE fail_count::DECIMAL / (fail_count + pass_count)
        END
    ) STORED,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, job_type_id, concept_area)
);

CREATE INDEX idx_skill_dna_user ON user_skill_dna(user_id);
CREATE INDEX idx_skill_dna_job_type ON user_skill_dna(job_type_id);
CREATE INDEX idx_skill_dna_weakness ON user_skill_dna(weakness_score) 
    WHERE weakness_score > 0.3;

-- 9. COOLDOWN TRACKING
CREATE TABLE cooldown_tracking (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id),
    job_type_id UUID NOT NULL REFERENCES job_types(job_type_id),
    level VARCHAR(20) NOT NULL,
    attempt_number INTEGER NOT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    next_available_at TIMESTAMP NOT NULL,
    passed BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, job_type_id, level, attempt_number)
);

CREATE INDEX idx_cooldown_user ON cooldown_tracking(user_id);
CREATE INDEX idx_cooldown_next ON cooldown_tracking(next_available_at);
CREATE INDEX idx_cooldown_active ON cooldown_tracking(user_id, job_type_id, level)
    WHERE completed_at IS NOT NULL AND passed = FALSE;

-- 10. CONCEPT POOLS (for AI generation)
CREATE TABLE concept_pools (
    concept_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_type_id UUID NOT NULL REFERENCES job_types(job_type_id),
    concept_key VARCHAR(100) NOT NULL,
    concept_name VARCHAR(255) NOT NULL,
    definition TEXT NOT NULL,
    difficulty VARCHAR(20) NOT NULL
        CHECK (difficulty IN ('beginner', 'intermediate', 'advanced', 'expert')),
    question_templates JSONB NOT NULL DEFAULT '[]',
    nigerian_contexts JSONB NOT NULL DEFAULT '[]',
    common_mistakes JSONB NOT NULL DEFAULT '[]',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(job_type_id, concept_key)
);

CREATE INDEX idx_concepts_job_type ON concept_pools(job_type_id);
CREATE INDEX idx_concepts_difficulty ON concept_pools(difficulty);

-- 11. OTP VERIFICATION
CREATE TABLE otp_verifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phone VARCHAR(20) NOT NULL,
    otp_code VARCHAR(6) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    verified_at TIMESTAMP,
    attempt_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_otp_phone ON otp_verifications(phone);
CREATE INDEX idx_otp_expires ON otp_verifications(expires_at);

-- Seed data: Job Headers (7 from master prompt)
INSERT INTO skill_headers (header_id, name, description, question_depth, display_order) VALUES
(uuid_generate_v4(), 'Data & Operations', 'Transform raw data into clean, actionable information. The foundation of modern business operations.', 'medium', 1),
(uuid_generate_v4(), 'Business & Finance', 'Research, analyze, and communicate business information to drive decisions.', 'medium', 2),
(uuid_generate_v4(), 'Software Development', 'Build applications, websites, and software solutions.', 'heavy', 3),
(uuid_generate_v4(), 'Design & Creative', 'Create visual content, user interfaces, and media.', 'medium', 4),
(uuid_generate_v4(), 'Writing & Content', 'Produce written content for various audiences and purposes.', 'light', 5),
(uuid_generate_v4(), 'Customer Support', 'Help customers solve problems and answer questions.', 'light', 6),
(uuid_generate_v4(), 'Marketing & Sales', 'Promote products and drive revenue growth.', 'medium', 7);

-- Seed data: Job Types for Data & Operations
INSERT INTO job_types (job_type_id, header_id, name, description, submission_type, avg_simulation_minutes, question_count_beginner, question_count_intermediate, question_count_advanced, question_count_expert, mini_task_rubric)
SELECT 
    uuid_generate_v4(),
    h.header_id,
    'Data Entry',
    'Accurate, fast data input into structured systems',
    'form',
    30,
    20, 25, 30, 35,
    '{"accuracy_threshold": 95, "speed_weight": 0.3, "accuracy_weight": 0.7}'::jsonb
FROM skill_headers h WHERE h.name = 'Data & Operations'
UNION ALL
SELECT 
    uuid_generate_v4(),
    h.header_id,
    'Data Cleaning',
    'Identify, correct, and standardize errors in datasets',
    'file_upload',
    45,
    25, 30, 35, 40,
    '{"completeness": 0.25, "accuracy": 0.35, "consistency": 0.25, "documentation": 0.15}'::jsonb
FROM skill_headers h WHERE h.name = 'Data & Operations'
UNION ALL
SELECT 
    uuid_generate_v4(),
    h.header_id,
    'Data Analysis',
    'Interpret data, answer business questions, create visualizations',
    'interactive_form',
    60,
    25, 35, 40, 45,
    '{"calculations": 0.30, "visualization": 0.30, "interpretation": 0.25, "recommendations": 0.15}'::jsonb
FROM skill_headers h WHERE h.name = 'Data & Operations';

-- Seed data: Job Types for Business & Finance
INSERT INTO job_types (job_type_id, header_id, name, description, submission_type, avg_simulation_minutes, question_count_beginner, question_count_intermediate, question_count_advanced, question_count_expert, mini_task_rubric)
SELECT 
    uuid_generate_v4(),
    h.header_id,
    'Market Research',
    'Research markets, competitors, and trends; compile findings',
    'text_editor',
    45,
    20, 25, 30, 35,
    '{"structure": 0.20, "data_use": 0.25, "insight_depth": 0.25, "actionability": 0.15, "presentation": 0.15}'::jsonb
FROM skill_headers h WHERE h.name = 'Business & Finance'
UNION ALL
SELECT 
    uuid_generate_v4(),
    h.header_id,
    'Financial Analysis',
    'Read financial statements, calculate ratios, assess health',
    'interactive_form',
    50,
    25, 30, 35, 40,
    '{"ratio_calculations": 0.35, "trend_analysis": 0.20, "risk_assessment": 0.25, "recommendation": 0.20}'::jsonb
FROM skill_headers h WHERE h.name = 'Business & Finance'
UNION ALL
SELECT 
    uuid_generate_v4(),
    h.header_id,
    'Bookkeeping',
    'Categorize transactions, reconcile accounts, maintain records',
    'interactive_form',
    40,
    20, 25, 30, 35,
    '{"journal_entries": 0.40, "trial_balance": 0.30, "reconciliation": 0.20, "accuracy": 0.10}'::jsonb
FROM skill_headers h WHERE h.name = 'Business & Finance'
UNION ALL
SELECT 
    uuid_generate_v4(),
    h.header_id,
    'Business Writing',
    'Write professional proposals, emails, reports, and documents',
    'rich_text',
    45,
    20, 25, 30, 35,
    '{"professionalism": 0.20, "clarity": 0.25, "audience_awareness": 0.20, "structure": 0.20, "grammar": 0.15}'::jsonb
FROM skill_headers h WHERE h.name = 'Business & Finance';

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_skills_updated_at BEFORE UPDATE ON user_skills
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
