package com.aiinterview.entity;

import jakarta.persistence.*;
import lombok.*;

import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "interview_sessions")
@Getter @Setter @NoArgsConstructor @AllArgsConstructor @Builder
public class InterviewSession {

    public enum Status { CREATED, IN_PROGRESS, COMPLETED, ABORTED }

    @Id @GeneratedValue
    private UUID id;

    @Column(name = "user_id", nullable = false)
    private UUID userId;

    @Column(nullable = false)
    private String role;

    @Column(nullable = false)
    private String level;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private Status status;

    @Column(name = "overall_score")
    private Double overallScore;

    @Column(name = "difficulty_target", nullable = false)
    private Double difficultyTarget;

    @Column(name = "category_focus")
    private String categoryFocus;

    @Column(name = "started_at")
    private Instant startedAt;

    @Column(name = "ended_at")
    private Instant endedAt;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @PrePersist
    void onCreate() {
        if (createdAt == null) createdAt = Instant.now();
        if (status == null) status = Status.CREATED;
        if (difficultyTarget == null) difficultyTarget = 0.5;
    }
}
