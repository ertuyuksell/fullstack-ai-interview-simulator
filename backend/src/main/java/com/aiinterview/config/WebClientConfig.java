package com.aiinterview.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.reactive.ReactorClientHttpConnector;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.netty.http.client.HttpClient;

import java.time.Duration;

@Configuration
public class WebClientConfig {

    @Value("${app.ai.base-url}")
    private String aiBaseUrl;

    @Bean
    public WebClient aiServiceClient() {
        HttpClient http = HttpClient.create().responseTimeout(Duration.ofSeconds(180));
        return WebClient.builder()
                .baseUrl(aiBaseUrl)
                .clientConnector(new ReactorClientHttpConnector(http))
                .codecs(c -> c.defaultCodecs().maxInMemorySize(50 * 1024 * 1024))
                .build();
    }
}
