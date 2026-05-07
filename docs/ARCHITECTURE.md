# Architecture

## Service topology

```
Browser ──► Frontend (nginx, static React)
   │
   ├── REST   ──► Backend (Spring Boot 3, Java 21)
   │              │
   │              ├── Postgres (Flyway-managed schema)
   │              ├── Redis    (sessions, rate limiting)
   │              └── WebClient ──► AI Service (FastAPI)
   │
   └── WS     ──► Backend WebSocket handler
                   └── Async fan-out to AI Service
```

## Why this split

- **Backend (Java)** owns identity, persistence, and orchestration. JVM is the
  right home for the parts that need long-lived connections, transactional
  integrity, and a mature security stack.
- **AI service (Python)** owns model inference. PyTorch + HuggingFace are
  first-class in Python; isolating them keeps the JVM image small and lets the
  ML stack scale and version independently.
- **Frontend** is a pure SPA. Build-time env baked in via `VITE_*`; static
  artefacts served by nginx in production.

## Data model

```
users (id, email, password_hash, full_name, created_at)
interview_sessions (id, user_id → users, role, level, status,
                    overall_score, started_at, ended_at, created_at)
interview_questions (id, session_id → sessions, ordinal, prompt,
                     reference_answer)
interview_answers (id, question_id → questions, session_id → sessions,
                   transcript, confidence_score, answer_quality_score,
                   facial_emotion, speech_emotion, raw_analysis, created_at)
```

## Inference pipeline

For each submitted answer:

```
                    ┌─► facial_emotion (FER / mini-Xception)
frame_base64 ──────►┤
                    └─► face_confidence

audio_base64 ──────► speech_emotion (wav2vec2, superb/ER head)

transcript + reference ─► answer_quality
                            • cosine sim of MiniLM embeddings (70%)
                            • length saturation (30%)

(transcript, voice, face) ─► confidence
                            • voice prior  (+/- 0.15)
                            • face prior   (+/- 0.10/0.15)
                            • filler-word density penalty (≤ 0.25)
```

All scores normalised to `[0, 1]`. Overall score = mean(0.5·quality + 0.5·confidence).

## Auth

- Stateless JWT (HS256, 24h default).
- Filter parses bearer token, loads `User`, populates `SecurityContext`.
- WebSocket auth via `?token=` query param at handshake (closed if missing/bad).

## Failure modes

- **AI service unreachable:** backend returns mid-confidence neutral fallback so
  the session can continue; the answer is persisted with the fallback values.
- **Webcam denied:** interview room shows the prompt textarea only; transcript-only
  scoring still works.
- **Postgres down:** backend fails fast at startup (Flyway dependency).
