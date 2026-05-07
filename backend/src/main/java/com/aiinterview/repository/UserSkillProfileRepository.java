package com.aiinterview.repository;

import com.aiinterview.entity.UserSkillProfile;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface UserSkillProfileRepository extends JpaRepository<UserSkillProfile, UUID> {
    List<UserSkillProfile> findByUserId(UUID userId);
    Optional<UserSkillProfile> findByUserIdAndCategory(UUID userId, String category);
}
