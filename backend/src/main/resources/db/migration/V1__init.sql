CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE users (
    id            UUID PRIMARY KEY,
    email         VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name     VARCHAR(255),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE interview_sessions (
    id            UUID PRIMARY KEY,
    user_id       UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role          VARCHAR(120) NOT NULL,
    level         VARCHAR(40)  NOT NULL,
    status        VARCHAR(20)  NOT NULL,
    overall_score DOUBLE PRECISION,
    started_at    TIMESTAMPTZ,
    ended_at      TIMESTAMPTZ,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_sessions_user_created ON interview_sessions(user_id, created_at DESC);

CREATE TABLE interview_questions (
    id              UUID PRIMARY KEY,
    session_id      UUID NOT NULL REFERENCES interview_sessions(id) ON DELETE CASCADE,
    ordinal         INT NOT NULL,
    prompt          VARCHAR(1000) NOT NULL,
    reference_answer VARCHAR(4000)
);
CREATE INDEX idx_questions_session ON interview_questions(session_id, ordinal);

CREATE TABLE interview_answers (
    id                   UUID PRIMARY KEY,
    question_id          UUID NOT NULL REFERENCES interview_questions(id) ON DELETE CASCADE,
    session_id           UUID NOT NULL REFERENCES interview_sessions(id) ON DELETE CASCADE,
    transcript           TEXT,
    confidence_score     DOUBLE PRECISION,
    answer_quality_score DOUBLE PRECISION,
    facial_emotion       VARCHAR(40),
    speech_emotion       VARCHAR(40),
    raw_analysis         TEXT,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_answers_session ON interview_answers(session_id);
