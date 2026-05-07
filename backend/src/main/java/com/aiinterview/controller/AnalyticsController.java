package com.aiinterview.controller;

import com.aiinterview.entity.User;
import com.aiinterview.service.AnalyticsService;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
@RequestMapping("/api/analytics")
public class AnalyticsController {

    private final AnalyticsService analytics;

    public AnalyticsController(AnalyticsService analytics) { this.analytics = analytics; }

    @GetMapping("/dashboard")
    public Map<String, Object> dashboard(@AuthenticationPrincipal User user) {
        return analytics.dashboard(user.getId());
    }
}
