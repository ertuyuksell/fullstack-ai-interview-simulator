package com.aiinterview.entity;

import jakarta.persistence.*;
import lombok.*;

import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "feature_vectors")
@Getter @Setter @NoArgsConstructor @AllArgsConstructor @Builder
public class FeatureVector {
    @Id @GeneratedValue
    private UUID id;

    @Column(name = "answer_id", nullable = false)
    private UUID answerId;

    @Column(name = "user_id", nullable = false)
    private UUID userId;

    // jsonb -> JdbcTypeCode ile native postgres jsonb mapping
    @Column(name = "features_json", nullable = false, columnDefinition = "jsonb")
    @org.hibernate.annotations.JdbcTypeCode(org.hibernate.type.SqlTypes.JSON)
    private String featuresJson;

    @Column(name = "target_quality")
    private Double targetQuality;

    @Column(name = "target_confidence")
    private Double targetConfidence;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @PrePersist
    void onCreate() { if (createdAt == null) createdAt = Instant.now(); }
}
