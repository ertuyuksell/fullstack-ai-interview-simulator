package com.aiinterview.repository;

import com.aiinterview.entity.InterviewQuestion;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.UUID;

public interface InterviewQuestionRepository extends JpaRepository<InterviewQuestion, UUID> {
    List<InterviewQuestion> findBySessionIdOrderByOrdinalAsc(UUID sessionId);
}
