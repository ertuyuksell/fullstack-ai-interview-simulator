package com.aiinterview.service;

import com.aiinterview.entity.InterviewAnswer;
import com.aiinterview.entity.InterviewSession;
import com.aiinterview.entity.UserSkillProfile;
import com.aiinterview.repository.InterviewAnswerRepository;
import com.aiinterview.repository.InterviewSessionRepository;
import com.aiinterview.repository.UserSkillProfileRepository;
import org.springframework.stereotype.Service;

import java.util.*;
import java.util.stream.Collectors;

@Service
public class AnalyticsService {

    private final InterviewSessionRepository sessions;
    private final InterviewAnswerRepository answers;
    private final UserSkillProfileRepository skills;

    public AnalyticsService(InterviewSessionRepository sessions,
                            InterviewAnswerRepository answers,
                            UserSkillProfileRepository skills) {
        this.sessions = sessions;
        this.answers = answers;
        this.skills = skills;
    }

    public Map<String, Object> dashboard(UUID userId) {
        List<InterviewSession> mine = sessions.findByUserIdOrderByCreatedAtDesc(userId);
        long completed = mine.stream().filter(s -> s.getStatus() == InterviewSession.Status.COMPLETED).count();
        double avgScore = mine.stream()
                .map(InterviewSession::getOverallScore)
                .filter(Objects::nonNull)
                .mapToDouble(Double::doubleValue).average().orElse(0.0);

        List<Map<String, Object>> trend = mine.stream()
                .filter(s -> s.getOverallScore() != null)
                .sorted(Comparator.comparing(InterviewSession::getCreatedAt))
                .map(s -> Map.<String, Object>of(
                        "date", s.getCreatedAt().toString(),
                        "score", s.getOverallScore(),
                        "role", s.getRole()))
                .toList();

        Map<String, Long> emotionCounts = mine.stream()
                .flatMap(s -> answers.findBySessionId(s.getId()).stream())
                .map(InterviewAnswer::getFacialEmotion)
                .filter(Objects::nonNull)
                .collect(Collectors.groupingBy(e -> e, Collectors.counting()));

        List<Map<String, Object>> skillProfile = skills.findByUserId(userId).stream()
                .sorted(Comparator.comparing(UserSkillProfile::getCategory))
                .map(p -> Map.<String, Object>of(
                        "category", p.getCategory(),
                        "level", p.getSkillLevel(),
                        "confidence", p.getConfidence(),
                        "samples", p.getSampleCount()))
                .toList();

        Map<String, Object> out = new HashMap<>();
        out.put("totalSessions", mine.size());
        out.put("completedSessions", completed);
        out.put("averageScore", Math.round(avgScore * 1000.0) / 1000.0);
        out.put("trend", trend);
        out.put("emotionDistribution", emotionCounts);
        out.put("skillProfile", skillProfile);
        return out;
    }
}
