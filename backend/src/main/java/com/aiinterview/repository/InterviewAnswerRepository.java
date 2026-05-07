package com.aiinterview.repository;

import com.aiinterview.entity.InterviewAnswer;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.UUID;

public interface InterviewAnswerRepository extends JpaRepository<InterviewAnswer, UUID> {
    List<InterviewAnswer> findBySessionId(UUID sessionId);
}
