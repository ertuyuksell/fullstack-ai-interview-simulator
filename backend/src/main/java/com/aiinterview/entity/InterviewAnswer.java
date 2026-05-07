package com.aiinterview.entity;

import jakarta.persistence.*;
import lombok.*;

import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "interview_answers")
@Getter @Setter @NoArgsConstructor @AllArgsConstructor @Builder
public class InterviewAnswer {
    @Id @GeneratedValue
    private UUID id;

    @Column(name = "question_id", nullable = false)
    private UUID questionId;

    @Column(name = "session_id", nullable = false)
    private UUID sessionId;

    @Column(columnDefinition = "TEXT")
    private String transcript;

    @Column(name = "confidence_score")
    private Double confidenceScore;

    @Column(name = "answer_quality_score")
    private Double answerQualityScore;

    @Column(name = "facial_emotion")
    private String facialEmotion;

    @Column(name = "speech_emotion")
    private String speechEmotion;

    @Column(name = "raw_analysis", columnDefinition = "TEXT")
    private String rawAnalysisJson;

    @Column(name = "response_time_ms")
    private Long responseTimeMs;

    @Column(name = "word_count")
    private Integer wordCount;

    @Column(name = "sentiment_score")
    private Double sentimentScore;

    @Column(name = "hesitation_score")
    private Double hesitationScore;

    @Column(name = "coherence_score")
    private Double coherenceScore;

    @Column(name = "difficulty_at_answer")
    private Double difficultyAtAnswer;

    @Column(name = "category", length = 40)
    private String category;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @PrePersist
    void onCreate() { if (createdAt == null) createdAt = Instant.now(); }
}
