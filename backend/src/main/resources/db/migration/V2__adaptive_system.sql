-- Adaptive system: kullanıcı yetenek profili, soru geçmişi, feature vektörleri,
-- üretilmiş sorular ve model tahminleri.

-- Mülakat oturumlarına zorluk seviyesi (skaler) ve kategori dağılımı ekle
ALTER TABLE interview_sessions
    ADD COLUMN difficulty_target DOUBLE PRECISION NOT NULL DEFAULT 0.5,
    ADD COLUMN category_focus VARCHAR(100);

-- Sorulara kategori, zorluk ve üretim kaynağı
ALTER TABLE interview_questions
    ADD COLUMN category VARCHAR(40) NOT NULL DEFAULT 'general',
    ADD COLUMN difficulty DOUBLE PRECISION NOT NULL DEFAULT 0.5,
    ADD COLUMN source VARCHAR(20) NOT NULL DEFAULT 'template',  -- llm | template | seed
    ADD COLUMN content_hash VARCHAR(64) NOT NULL DEFAULT '';

CREATE INDEX idx_questions_category_difficulty ON interview_questions(category, difficulty);

-- Cevaplara zengin metrikler
ALTER TABLE interview_answers
    ADD COLUMN response_time_ms BIGINT,        -- soru gösterilmesi → cevap gönderilmesi
    ADD COLUMN word_count INT,
    ADD COLUMN sentiment_score DOUBLE PRECISION,
    ADD COLUMN hesitation_score DOUBLE PRECISION,
    ADD COLUMN coherence_score DOUBLE PRECISION,
    ADD COLUMN difficulty_at_answer DOUBLE PRECISION,
    ADD COLUMN category VARCHAR(40);

-- Kullanıcı başına kategori-bazlı yetenek profili
-- (online güncellenir; periyodik retrain için tarihçe ayrı tabloda tutulur)
CREATE TABLE user_skill_profile (
    id           UUID PRIMARY KEY,
    user_id      UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category     VARCHAR(40) NOT NULL,
    skill_level  DOUBLE PRECISION NOT NULL DEFAULT 0.5,   -- 0..1
    confidence   DOUBLE PRECISION NOT NULL DEFAULT 0.0,   -- güven aralığı
    sample_count INT NOT NULL DEFAULT 0,
    last_updated TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, category)
);
CREATE INDEX idx_skill_user ON user_skill_profile(user_id);

-- Bir kullanıcıya gelmiş soruların hash'i — tekrar engelleme
CREATE TABLE question_history (
    id              UUID PRIMARY KEY,
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    question_id     UUID REFERENCES interview_questions(id) ON DELETE SET NULL,
    content_hash    VARCHAR(64) NOT NULL,
    asked_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, content_hash)
);
CREATE INDEX idx_qhistory_user ON question_history(user_id);

-- Üretilmiş soruları cache'leyip tekrar üretim maliyetini düşür
CREATE TABLE generated_questions (
    id            UUID PRIMARY KEY,
    role          VARCHAR(120) NOT NULL,
    level         VARCHAR(40) NOT NULL,
    category      VARCHAR(40) NOT NULL,
    difficulty    DOUBLE PRECISION NOT NULL,
    prompt        VARCHAR(1000) NOT NULL,
    content_hash  VARCHAR(64) NOT NULL UNIQUE,
    source        VARCHAR(20) NOT NULL,   -- llm | template
    use_count     INT NOT NULL DEFAULT 0,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_genq_lookup ON generated_questions(role, level, category, difficulty);

-- Model girdisi olarak kaydedilen feature vektörleri (offline retraining için)
CREATE TABLE feature_vectors (
    id              UUID PRIMARY KEY,
    answer_id       UUID NOT NULL REFERENCES interview_answers(id) ON DELETE CASCADE,
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    features_json   JSONB NOT NULL,
    target_quality  DOUBLE PRECISION,        -- modelin tahmini
    target_confidence DOUBLE PRECISION,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_fv_user ON feature_vectors(user_id);
CREATE INDEX idx_fv_answer ON feature_vectors(answer_id);

-- Model versiyon kayıtları — abstraction layer için
CREATE TABLE model_registry (
    id           UUID PRIMARY KEY,
    name         VARCHAR(80) NOT NULL,
    version      VARCHAR(40) NOT NULL,
    artifact_path VARCHAR(500),
    metrics_json JSONB,
    is_active    BOOLEAN NOT NULL DEFAULT FALSE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (name, version)
);
