package com.aiinterview.entity;

import jakarta.persistence.*;
import lombok.*;

import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "user_skill_profile",
       uniqueConstraints = @UniqueConstraint(columnNames = {"user_id", "category"}))
@Getter @Setter @NoArgsConstructor @AllArgsConstructor @Builder
public class UserSkillProfile {
    @Id @GeneratedValue
    private UUID id;

    @Column(name = "user_id", nullable = false)
    private UUID userId;

    @Column(nullable = false, length = 40)
    private String category;

    @Column(name = "skill_level", nullable = false)
    private Double skillLevel;

    @Column(nullable = false)
    private Double confidence;

    @Column(name = "sample_count", nullable = false)
    private Integer sampleCount;

    @Column(name = "last_updated", nullable = false)
    private Instant lastUpdated;

    @PrePersist @PreUpdate
    void touch() {
        lastUpdated = Instant.now();
        if (skillLevel == null) skillLevel = 0.5;
        if (confidence == null) confidence = 0.0;
        if (sampleCount == null) sampleCount = 0;
    }
}
