# API Reference

All authenticated endpoints require `Authorization: Bearer <jwt>`.

## Auth

### POST `/api/auth/register`
```json
{ "email": "you@x.com", "password": "min8chars", "fullName": "Your Name" }
```
**200** `{ "token": "...", "email": "...", "fullName": "..." }`

### POST `/api/auth/login`
Same body and response shape as register.

## Interviews

### POST `/api/interviews`
```json
{ "role": "Backend Engineer", "level": "mid" }
```
**200** Returns full session including 5 generated questions.

### GET `/api/interviews`
List of session summaries, newest first.

### GET `/api/interviews/{id}`
Full session including question list.

### POST `/api/interviews/{id}/answers`
```json
{
  "questionId": "uuid",
  "transcript": "I would approach...",
  "audioBase64": "...",   // optional, raw webm/wav bytes b64
  "frameBase64": "..."    // optional, jpg keyframe b64
}
```
**200** `{ confidenceScore, answerQualityScore, facialEmotion, speechEmotion }`

### POST `/api/interviews/{id}/complete`
Finalises the session. Computes overall score.

## Analytics

### GET `/api/analytics/dashboard`
```json
{
  "totalSessions": 12,
  "completedSessions": 9,
  "averageScore": 0.71,
  "trend": [{ "date": "...", "score": 0.7, "role": "..." }],
  "emotionDistribution": { "happy": 14, "neutral": 22 }
}
```

## WebSocket

### `/ws/interview?token=<jwt>`

Inbound messages from client:
```json
{ "type": "frame",      "data": "<base64 jpg>" }
{ "type": "audio",      "data": "<base64 wav>" }
{ "type": "transcript", "text": "..." }
```

Outbound from server:
```json
{ "type": "ready" }
{ "type": "feedback", "confidence_score": 0.7, "answer_quality_score": 0.6,
  "facial_emotion": "neutral", "speech_emotion": "calm", "detail": { ... } }
```

## AI service (internal only)

| Method | Path        | Purpose                                |
| ------ | ----------- | -------------------------------------- |
| GET    | `/health`   | Liveness                               |
| POST   | `/analyze`  | Multi-modal scoring                    |
| POST   | `/questions`| Generate role/level-appropriate prompts|
