package com.aiinterview.service;

import com.aiinterview.dto.AuthDtos.*;
import com.aiinterview.entity.User;
import com.aiinterview.repository.UserRepository;
import com.aiinterview.security.JwtService;
import org.springframework.http.HttpStatus;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

@Service
public class AuthService {

    private final UserRepository users;
    private final PasswordEncoder encoder;
    private final JwtService jwt;

    public AuthService(UserRepository users, PasswordEncoder encoder, JwtService jwt) {
        this.users = users;
        this.encoder = encoder;
        this.jwt = jwt;
    }

    public AuthResponse register(RegisterRequest req) {
        if (users.existsByEmail(req.email())) {
            throw new ResponseStatusException(HttpStatus.CONFLICT, "Bu e-posta zaten kayıtlı");
        }
        User u = User.builder()
                .email(req.email())
                .passwordHash(encoder.encode(req.password()))
                .fullName(req.fullName())
                .build();
        u = users.save(u);
        return new AuthResponse(jwt.generate(u.getId(), u.getEmail()), u.getEmail(), u.getFullName());
    }

    public AuthResponse login(LoginRequest req) {
        User u = users.findByEmail(req.email())
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.UNAUTHORIZED, "Hatalı e-posta veya şifre"));
        if (!encoder.matches(req.password(), u.getPasswordHash())) {
            throw new ResponseStatusException(HttpStatus.UNAUTHORIZED, "Hatalı e-posta veya şifre");
        }
        return new AuthResponse(jwt.generate(u.getId(), u.getEmail()), u.getEmail(), u.getFullName());
    }
}
