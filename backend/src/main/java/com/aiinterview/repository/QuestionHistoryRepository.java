package com.aiinterview.repository;

import com.aiinterview.entity.QuestionHistory;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.UUID;

public interface QuestionHistoryRepository extends JpaRepository<QuestionHistory, UUID> {
    List<QuestionHistory> findByUserId(UUID userId);
    boolean existsByUserIdAndContentHash(UUID userId, String contentHash);
}
