package com.aiinterview.service;

import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.util.Map;

@Service
public class AiClient {

    private final WebClient client;

    public AiClient(WebClient aiServiceClient) {
        this.client = aiServiceClient;
    }

    @SuppressWarnings("unchecked")
    public Mono<Map<String, Object>> analyze(Map<String, Object> payload) {
        return client.post()
                .uri("/analyze")
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(payload)
                .retrieve()
                .bodyToMono(Map.class)
                .map(m -> (Map<String, Object>) m);
    }

    @SuppressWarnings("unchecked")
    public Mono<Map<String, Object>> generateQuestions(Map<String, Object> payload) {
        return client.post()
                .uri("/questions")
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(payload)
                .retrieve()
                .bodyToMono(Map.class)
                .map(m -> (Map<String, Object>) m);
    }

    @SuppressWarnings("unchecked")
    public Mono<Map<String, Object>> trainModel(Map<String, Object> payload) {
        return client.post()
                .uri("/train")
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(payload)
                .retrieve()
                .bodyToMono(Map.class)
                .map(m -> (Map<String, Object>) m);
    }
}
