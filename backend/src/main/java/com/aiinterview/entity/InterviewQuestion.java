package com.aiinterview.entity;

import jakarta.persistence.*;
import lombok.*;

import java.util.UUID;

@Entity
@Table(name = "interview_questions")
@Getter @Setter @NoArgsConstructor @AllArgsConstructor @Builder
public class InterviewQuestion {
    @Id @GeneratedValue
    private UUID id;

    @Column(name = "session_id", nullable = false)
    private UUID sessionId;

    @Column(name = "ordinal", nullable = false)
    private int ordinal;

    @Column(nullable = false, length = 1000)
    private String prompt;

    @Column(name = "reference_answer", length = 4000)
    private String referenceAnswer;

    @Column(nullable = false, length = 40)
    private String category;

    @Column(nullable = false)
    private Double difficulty;

    @Column(nullable = false, length = 20)
    private String source;

    @Column(name = "content_hash", nullable = false, length = 64)
    private String contentHash;

    @PrePersist
    void onCreate() {
        if (category == null) category = "general";
        if (difficulty == null) difficulty = 0.5;
        if (source == null) source = "template";
        if (contentHash == null) contentHash = "";
    }
}
