package com.aiinterview.entity;

import jakarta.persistence.*;
import lombok.*;

import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "question_history",
       uniqueConstraints = @UniqueConstraint(columnNames = {"user_id", "content_hash"}))
@Getter @Setter @NoArgsConstructor @AllArgsConstructor @Builder
public class QuestionHistory {
    @Id @GeneratedValue
    private UUID id;

    @Column(name = "user_id", nullable = false)
    private UUID userId;

    @Column(name = "question_id")
    private UUID questionId;

    @Column(name = "content_hash", nullable = false, length = 64)
    private String contentHash;

    @Column(name = "asked_at", nullable = false)
    private Instant askedAt;

    @PrePersist
    void onCreate() { if (askedAt == null) askedAt = Instant.now(); }
}
