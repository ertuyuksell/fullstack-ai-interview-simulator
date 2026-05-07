package com.aiinterview.websocket;

import com.aiinterview.security.JwtService;
import com.aiinterview.service.AiClient;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.CloseStatus;
import org.springframework.web.socket.TextMessage;
import org.springframework.web.socket.WebSocketSession;
import org.springframework.web.socket.handler.TextWebSocketHandler;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Streams partial AI feedback during a live interview.
 * Client sends: {"type":"frame", "data":"<base64>"} or
 *               {"type":"audio", "data":"<base64>"} or
 *               {"type":"transcript", "text":"..."}
 *
 * Auth: pass ?token=<jwt> as a query param on the WS URL.
 */
@Component
public class InterviewWebSocketHandler extends TextWebSocketHandler {

    private final JwtService jwt;
    private final AiClient ai;
    private final ObjectMapper mapper = new ObjectMapper();
    private final Map<String, UUID> sessionUsers = new ConcurrentHashMap<>();

    public InterviewWebSocketHandler(JwtService jwt, AiClient ai) {
        this.jwt = jwt;
        this.ai = ai;
    }

    @Override
    public void afterConnectionEstablished(WebSocketSession session) throws Exception {
        String query = session.getUri() == null ? "" : session.getUri().getQuery();
        String token = null;
        if (query != null) {
            for (String p : query.split("&")) {
                if (p.startsWith("token=")) token = p.substring(6);
            }
        }
        try {
            if (token == null) throw new IllegalArgumentException("missing token");
            UUID userId = jwt.extractUserId(token);
            sessionUsers.put(session.getId(), userId);
            session.sendMessage(new TextMessage("{\"type\":\"ready\"}"));
        } catch (Exception e) {
            session.close(CloseStatus.NOT_ACCEPTABLE.withReason("auth"));
        }
    }

    @Override
    protected void handleTextMessage(WebSocketSession session, TextMessage message) throws Exception {
        if (!sessionUsers.containsKey(session.getId())) {
            session.close(CloseStatus.NOT_ACCEPTABLE);
            return;
        }
        JsonNode node = mapper.readTree(message.getPayload());
        String type = node.path("type").asText();

        Map<String, Object> payload = new HashMap<>();
        switch (type) {
            case "frame" -> payload.put("frame_base64", node.path("data").asText());
            case "audio" -> payload.put("audio_base64", node.path("data").asText());
            case "transcript" -> payload.put("transcript", node.path("text").asText());
            default -> { return; }
        }

        ai.analyze(payload).subscribe(result -> {
            try {
                Map<String, Object> out = new HashMap<>(result);
                out.put("type", "feedback");
                session.sendMessage(new TextMessage(mapper.writeValueAsString(out)));
            } catch (Exception ignored) {}
        }, err -> {});
    }

    @Override
    public void afterConnectionClosed(WebSocketSession session, CloseStatus status) {
        sessionUsers.remove(session.getId());
    }
}
