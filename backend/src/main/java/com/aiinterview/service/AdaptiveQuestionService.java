package com.aiinterview.service;

import com.aiinterview.entity.QuestionHistory;
import com.aiinterview.repository.QuestionHistoryRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.*;

/**
 * Adaptif soru üretim katmanı.
 *
 * Akış:
 *  1. Kullanıcının bu kategoride görmüş olduğu hash'leri AI servisine gönderir.
 *  2. AI servisi LLM (Ollama) ile dinamik üretir; Ollama yoksa şablona düşer.
 *  3. Dönen sorular DB'ye yazılır ve history'ye işlenir.
 */
@Service
public class AdaptiveQuestionService {

    private static final Logger log = LoggerFactory.getLogger(AdaptiveQuestionService.class);

    private final AiClient ai;
    private final SkillProfileService skills;
    private final QuestionHistoryRepository history;

    public AdaptiveQuestionService(AiClient ai, SkillProfileService skills,
                                   QuestionHistoryRepository history) {
        this.ai = ai;
        this.skills = skills;
        this.history = history;
    }

    public List<GeneratedQuestion> generate(UUID userId, String role, String level, int count) {
        Set<String> seen = new HashSet<>();
        for (QuestionHistory h : history.findByUserId(userId)) seen.add(h.getContentHash());

        double targetDifficulty = skills.recommendDifficulty(userId);
        List<String> weakAreas = skills.weakAreas(userId, 3);

        Map<String, Object> payload = new HashMap<>();
        payload.put("role", role);
        payload.put("level", level);
        payload.put("count", count);
        payload.put("difficulty", targetDifficulty);
        payload.put("user_id", userId.toString());
        payload.put("seen_hashes", new ArrayList<>(seen));
        payload.put("weak_areas", weakAreas);
        payload.put("skill_level", averageSkill(userId));

        Map<String, Object> resp;
        try {
            resp = ai.generateQuestions(payload).block();
        } catch (Exception e) {
            log.warn("AI question generation failed: {}", e.getMessage());
            resp = null;
        }

        List<GeneratedQuestion> out = new ArrayList<>();
        if (resp != null && resp.get("questions") instanceof List<?> list) {
            for (Object o : list) {
                if (o instanceof Map<?, ?> m) {
                    out.add(new GeneratedQuestion(
                            String.valueOf(m.get("prompt")),
                            asString(m.get("category"), "general"),
                            asDouble(m.get("difficulty"), targetDifficulty),
                            asString(m.get("source"), "template"),
                            asString(m.get("content_hash"), "")
                    ));
                }
            }
        }
        if (out.isEmpty()) {
            // En son güvenlik ağı — AI tamamen erişilemezse
            out.add(new GeneratedQuestion(
                    "Kendinden ve seni bu role getiren süreçten bahseder misin?",
                    "behavioral", 0.4, "template", "fallback-1"));
        }
        return out;
    }

    private double averageSkill(UUID userId) {
        return skills.profileMap(userId).values().stream()
                .mapToDouble(p -> p.getSkillLevel())
                .average().orElse(0.5);
    }

    @Transactional
    public void recordAsked(UUID userId, UUID questionId, String contentHash) {
        if (contentHash == null || contentHash.isBlank()) return;
        if (history.existsByUserIdAndContentHash(userId, contentHash)) return;
        history.save(QuestionHistory.builder()
                .userId(userId).questionId(questionId).contentHash(contentHash).build());
    }

    private static double asDouble(Object o, double dflt) {
        if (o instanceof Number n) return n.doubleValue();
        return dflt;
    }

    private static String asString(Object o, String dflt) {
        return (o == null) ? dflt : String.valueOf(o);
    }

    public record GeneratedQuestion(
            String prompt, String category, double difficulty,
            String source, String contentHash
    ) {}
}
