package com.aiinterview.websocket;

import org.springframework.context.annotation.Configuration;
import org.springframework.web.socket.config.annotation.EnableWebSocket;
import org.springframework.web.socket.config.annotation.WebSocketConfigurer;
import org.springframework.web.socket.config.annotation.WebSocketHandlerRegistry;

@Configuration
@EnableWebSocket
public class InterviewWebSocketConfig implements WebSocketConfigurer {

    private final InterviewWebSocketHandler handler;

    public InterviewWebSocketConfig(InterviewWebSocketHandler handler) {
        this.handler = handler;
    }

    @Override
    public void registerWebSocketHandlers(WebSocketHandlerRegistry registry) {
        registry.addHandler(handler, "/ws/interview").setAllowedOriginPatterns("*");
    }
}
