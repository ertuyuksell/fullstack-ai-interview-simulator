package com.aiinterview.service;

import com.aiinterview.entity.UserSkillProfile;
import com.aiinterview.repository.UserSkillProfileRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.*;

/**
 * Kullanıcının kategori bazlı yetenek profilini online günceller.
 * EWMA (exponential weighted moving average) ile her cevap profile yansır.
 */
@Service
public class SkillProfileService {

    private static final double ALPHA = 0.25;   // yeni gözlem ağırlığı
    private static final double DEFAULT_LEVEL = 0.5;

    private final UserSkillProfileRepository repo;

    public SkillProfileService(UserSkillProfileRepository repo) {
        this.repo = repo;
    }

    @Transactional(readOnly = true)
    public Map<String, UserSkillProfile> profileMap(UUID userId) {
        Map<String, UserSkillProfile> out = new HashMap<>();
        for (UserSkillProfile p : repo.findByUserId(userId)) {
            out.put(p.getCategory(), p);
        }
        return out;
    }

    @Transactional(readOnly = true)
    public double levelFor(UUID userId, String category) {
        return repo.findByUserIdAndCategory(userId, category)
                .map(UserSkillProfile::getSkillLevel)
                .orElse(DEFAULT_LEVEL);
    }

    @Transactional(readOnly = true)
    public List<String> weakAreas(UUID userId, int max) {
        List<UserSkillProfile> all = repo.findByUserId(userId);
        all.sort(Comparator.comparingDouble(UserSkillProfile::getSkillLevel));
        return all.stream()
                .filter(p -> p.getSampleCount() >= 2)
                .limit(max)
                .map(UserSkillProfile::getCategory)
                .toList();
    }

    /**
     * EWMA: skill = (1-α)·skill + α·observed
     * observed: cevap kalitesi (0..1) — zorluğa göre hafif düzeltilmiş.
     */
    @Transactional
    public void update(UUID userId, String category, double qualityScore, double difficulty) {
        final String cat = (category == null) ? "general" : category;
        UserSkillProfile p = repo.findByUserIdAndCategory(userId, cat)
                .orElseGet(() -> UserSkillProfile.builder()
                        .userId(userId).category(cat)
                        .skillLevel(DEFAULT_LEVEL)
                        .confidence(0.0)
                        .sampleCount(0)
                        .build());

        // Zorluk düzeltmesi: zor soruda iyi performans skill'i daha çok yükseltir
        double observed = qualityScore + (difficulty - 0.5) * 0.2 * qualityScore;
        observed = Math.max(0.0, Math.min(1.0, observed));

        double newLevel = (1 - ALPHA) * p.getSkillLevel() + ALPHA * observed;
        int newCount = p.getSampleCount() + 1;
        double newConf = Math.min(1.0, Math.log1p(newCount) / Math.log(50));

        p.setSkillLevel(newLevel);
        p.setSampleCount(newCount);
        p.setConfidence(newConf);
        repo.save(p);
    }

    /** Zorluk hedefi — kullanıcı genel ortalamasına göre adapte olur. */
    @Transactional(readOnly = true)
    public double recommendDifficulty(UUID userId) {
        List<UserSkillProfile> all = repo.findByUserId(userId);
        if (all.isEmpty()) return 0.5;
        double avg = all.stream().mapToDouble(UserSkillProfile::getSkillLevel).average().orElse(0.5);
        // Skill yüksekse biraz daha zor, düşükse biraz daha kolay
        return Math.max(0.25, Math.min(0.85, avg + 0.10));
    }
}
