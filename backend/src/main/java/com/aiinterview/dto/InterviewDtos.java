package com.aiinterview.dto;

import jakarta.validation.constraints.NotBlank;

import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.UUID;

public class InterviewDtos {

    public record CreateSessionRequest(@NotBlank String role, @NotBlank String level) {}

    public record QuestionDto(UUID id, int ordinal, String prompt,
                              String category, Double difficulty, String source) {}

    public record SessionDto(
            UUID id, String role, String level, String status,
            Double overallScore, Double difficultyTarget,
            Instant createdAt, Instant endedAt,
            List<QuestionDto> questions) {}

    public record SubmitAnswerRequest(
            UUID questionId,
            String transcript,
            String audioBase64,
            String frameBase64,
            Long responseTimeMs
    ) {}

    public record AnswerScoreDto(
            UUID answerId,
            Double confidenceScore,
            Double answerQualityScore,
            String facialEmotion,
            String speechEmotion,
            Map<String, Object> features) {}

    public record SessionSummaryDto(
            UUID id, String role, String level, Double overallScore,
            Instant createdAt, Instant endedAt) {}

    public record SkillSnapshot(String category, Double level,
                                Double confidence, Integer samples) {}
}
