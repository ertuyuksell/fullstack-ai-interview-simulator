package com.aiinterview.service;

import com.aiinterview.dto.InterviewDtos.*;
import com.aiinterview.entity.*;
import com.aiinterview.entity.InterviewSession.Status;
import com.aiinterview.repository.*;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import java.time.Instant;
import java.util.*;

@Service
public class InterviewService {

    private final InterviewSessionRepository sessions;
    private final InterviewQuestionRepository questions;
    private final InterviewAnswerRepository answers;
    private final FeatureVectorRepository featureVectors;
    private final AdaptiveQuestionService adaptive;
    private final SkillProfileService skills;
    private final AiClient ai;
    private final ObjectMapper mapper = new ObjectMapper();

    public InterviewService(InterviewSessionRepository sessions,
                            InterviewQuestionRepository questions,
                            InterviewAnswerRepository answers,
                            FeatureVectorRepository featureVectors,
                            AdaptiveQuestionService adaptive,
                            SkillProfileService skills,
                            AiClient ai) {
        this.sessions = sessions;
        this.questions = questions;
        this.answers = answers;
        this.featureVectors = featureVectors;
        this.adaptive = adaptive;
        this.skills = skills;
        this.ai = ai;
    }

    @Transactional
    public SessionDto createSession(UUID userId, CreateSessionRequest req) {
        double targetDifficulty = skills.recommendDifficulty(userId);

        InterviewSession s = InterviewSession.builder()
                .userId(userId).role(req.role()).level(req.level())
                .status(Status.CREATED)
                .difficultyTarget(targetDifficulty)
                .startedAt(Instant.now()).build();
        s = sessions.save(s);

        List<AdaptiveQuestionService.GeneratedQuestion> generated =
                adaptive.generate(userId, req.role(), req.level(), 5);

        List<InterviewQuestion> qs = new ArrayList<>();
        int ord = 1;
        for (AdaptiveQuestionService.GeneratedQuestion g : generated) {
            InterviewQuestion q = questions.save(InterviewQuestion.builder()
                    .sessionId(s.getId())
                    .ordinal(ord++)
                    .prompt(g.prompt())
                    .category(g.category())
                    .difficulty(g.difficulty())
                    .source(g.source())
                    .contentHash(g.contentHash())
                    .build());
            adaptive.recordAsked(userId, q.getId(), g.contentHash());
            qs.add(q);
        }
        return toDto(s, qs);
    }

    @Transactional(readOnly = true)
    public SessionDto getSession(UUID userId, UUID sessionId) {
        InterviewSession s = loadOwned(userId, sessionId);
        return toDto(s, questions.findBySessionIdOrderByOrdinalAsc(sessionId));
    }

    @Transactional(readOnly = true)
    public List<SessionSummaryDto> listSessions(UUID userId) {
        return sessions.findByUserIdOrderByCreatedAtDesc(userId).stream()
                .map(s -> new SessionSummaryDto(s.getId(), s.getRole(), s.getLevel(),
                        s.getOverallScore(), s.getCreatedAt(), s.getEndedAt()))
                .toList();
    }

    @Transactional
    public AnswerScoreDto submitAnswer(UUID userId, UUID sessionId, SubmitAnswerRequest req) {
        InterviewSession s = loadOwned(userId, sessionId);
        if (s.getStatus() == Status.COMPLETED || s.getStatus() == Status.ABORTED) {
            throw new ResponseStatusException(HttpStatus.CONFLICT, "Oturum kapalı");
        }
        InterviewQuestion q = questions.findById(req.questionId())
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Soru bulunamadı"));

        double skillLevel = skills.levelFor(userId, q.getCategory());

        Map<String, Object> payload = new HashMap<>();
        payload.put("transcript", req.transcript());
        payload.put("question", q.getPrompt());
        payload.put("difficulty", q.getDifficulty());
        payload.put("skill_level", skillLevel);
        payload.put("category", q.getCategory());
        payload.put("user_id", userId.toString());
        if (req.responseTimeMs() != null) payload.put("response_time_ms", req.responseTimeMs());
        if (q.getReferenceAnswer() != null) payload.put("reference_answer", q.getReferenceAnswer());
        if (req.audioBase64() != null) payload.put("audio_base64", req.audioBase64());
        if (req.frameBase64() != null) payload.put("frame_base64", req.frameBase64());

        Map<String, Object> result;
        try {
            result = ai.analyze(payload).block();
        } catch (Exception e) {
            result = Map.of(
                    "confidence_score", 0.5,
                    "answer_quality_score", 0.5,
                    "facial_emotion", "neutral",
                    "speech_emotion", "neutral",
                    "features", Map.of());
        }
        if (result == null) result = Map.of();

        @SuppressWarnings("unchecked")
        Map<String, Object> features = (Map<String, Object>)
                result.getOrDefault("features", Map.of());

        Double quality = asDouble(result.get("answer_quality_score"));
        Double confidence = asDouble(result.get("confidence_score"));

        InterviewAnswer a = InterviewAnswer.builder()
                .questionId(q.getId())
                .sessionId(s.getId())
                .transcript(req.transcript())
                .confidenceScore(confidence)
                .answerQualityScore(quality)
                .facialEmotion(asString(result.get("facial_emotion")))
                .speechEmotion(asString(result.get("speech_emotion")))
                .rawAnalysisJson(toJson(result))
                .responseTimeMs(req.responseTimeMs())
                .wordCount(asInt(features.get("word_count")))
                .sentimentScore(asDouble(features.get("sentiment_score")))
                .hesitationScore(asDouble(features.get("hesitation_density")))
                .coherenceScore(asDouble(features.get("coherence_score")))
                .difficultyAtAnswer(q.getDifficulty())
                .category(q.getCategory())
                .build();
        a = answers.save(a);

        // Feature vektörünü ileride retraining için kalıcı yaz
        try {
            featureVectors.save(FeatureVector.builder()
                    .answerId(a.getId())
                    .userId(userId)
                    .featuresJson(toJson(features))
                    .targetQuality(quality)
                    .targetConfidence(confidence)
                    .build());
        } catch (Exception ignored) { /* feature dump zorunlu değil */ }

        // Yetenek profilini güncelle
        if (quality != null) {
            skills.update(userId, q.getCategory(), quality, q.getDifficulty());
        }

        if (s.getStatus() == Status.CREATED) {
            s.setStatus(Status.IN_PROGRESS);
            sessions.save(s);
        }

        return new AnswerScoreDto(a.getId(), confidence, quality,
                a.getFacialEmotion(), a.getSpeechEmotion(), features);
    }

    @Transactional
    public SessionDto completeSession(UUID userId, UUID sessionId) {
        InterviewSession s = loadOwned(userId, sessionId);
        List<InterviewAnswer> as = answers.findBySessionId(sessionId);
        double overall = as.stream()
                .mapToDouble(a -> 0.5 * nz(a.getAnswerQualityScore()) + 0.5 * nz(a.getConfidenceScore()))
                .average().orElse(0.0);
        s.setStatus(Status.COMPLETED);
        s.setEndedAt(Instant.now());
        s.setOverallScore(Math.round(overall * 1000.0) / 1000.0);
        sessions.save(s);
        return toDto(s, questions.findBySessionIdOrderByOrdinalAsc(sessionId));
    }

    private InterviewSession loadOwned(UUID userId, UUID sessionId) {
        InterviewSession s = sessions.findById(sessionId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Oturum bulunamadı"));
        if (!s.getUserId().equals(userId)) {
            throw new ResponseStatusException(HttpStatus.FORBIDDEN);
        }
        return s;
    }

    private SessionDto toDto(InterviewSession s, List<InterviewQuestion> qs) {
        List<QuestionDto> qDtos = qs.stream()
                .map(q -> new QuestionDto(q.getId(), q.getOrdinal(), q.getPrompt(),
                        q.getCategory(), q.getDifficulty(), q.getSource())).toList();
        return new SessionDto(s.getId(), s.getRole(), s.getLevel(), s.getStatus().name(),
                s.getOverallScore(), s.getDifficultyTarget(),
                s.getCreatedAt(), s.getEndedAt(), qDtos);
    }

    private static double nz(Double d) { return d == null ? 0.0 : d; }
    private static Double asDouble(Object o) { return o instanceof Number n ? n.doubleValue() : null; }
    private static Integer asInt(Object o) { return o instanceof Number n ? n.intValue() : null; }
    private static String asString(Object o) { return o == null ? null : o.toString(); }
    private String toJson(Object o) {
        try { return mapper.writeValueAsString(o); }
        catch (JsonProcessingException e) { return "{}"; }
    }
}
