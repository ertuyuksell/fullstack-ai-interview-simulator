package com.aiinterview.controller;

import com.aiinterview.dto.InterviewDtos.*;
import com.aiinterview.entity.User;
import com.aiinterview.service.InterviewService;
import jakarta.validation.Valid;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/interviews")
public class InterviewController {

    private final InterviewService service;

    public InterviewController(InterviewService service) { this.service = service; }

    @PostMapping
    public SessionDto create(@AuthenticationPrincipal User user,
                             @Valid @RequestBody CreateSessionRequest req) {
        return service.createSession(user.getId(), req);
    }

    @GetMapping
    public List<SessionSummaryDto> list(@AuthenticationPrincipal User user) {
        return service.listSessions(user.getId());
    }

    @GetMapping("/{id}")
    public SessionDto get(@AuthenticationPrincipal User user, @PathVariable UUID id) {
        return service.getSession(user.getId(), id);
    }

    @PostMapping("/{id}/answers")
    public AnswerScoreDto answer(@AuthenticationPrincipal User user,
                                 @PathVariable UUID id,
                                 @RequestBody SubmitAnswerRequest req) {
        return service.submitAnswer(user.getId(), id, req);
    }

    @PostMapping("/{id}/complete")
    public SessionDto complete(@AuthenticationPrincipal User user, @PathVariable UUID id) {
        return service.completeSession(user.getId(), id);
    }
}
