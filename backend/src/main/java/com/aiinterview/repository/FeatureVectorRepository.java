package com.aiinterview.repository;

import com.aiinterview.entity.FeatureVector;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.UUID;

public interface FeatureVectorRepository extends JpaRepository<FeatureVector, UUID> {
    List<FeatureVector> findByUserId(UUID userId);
}
