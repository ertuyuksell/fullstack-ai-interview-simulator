# Full Stack AI Mülakat Simülatörü — Web Platformu

Adaptif, öğrenebilen bir mülakat pratik platformu. Kullanıcı her cevap
verdikçe sistem onu daha iyi tanır; soruların kategorisi, zorluğu ve içeriği
kullanıcının önceki performansına göre şekillenir. Cevaplar yazılı içerik,
yanıt süresi, ses tonu, mimik ve dil özellikleri gibi 20'den fazla sinyal
üzerinden değerlendirilir.

## Genel Bakış

Sistem üç servisten oluşur ve hepsi tek bir `docker compose` komutu ile
ayağa kalkar:

- **Frontend** — React 18, Vite, TailwindCSS, Framer Motion. Webcam ve
  mikrofon erişimi ile mülakat odası, kategori bazlı yetenek paneli ve
  performans grafikleri içerir.
- **Backend** — Spring Boot 3, Java 21, PostgreSQL, JWT auth. Kullanıcı
  hesapları, oturum yönetimi, adaptif soru üretim orkestrasyonu, yetenek
  profili güncellemesi (EWMA) ve feature vektör loglaması yapar.
- **AI Servisi** — Python FastAPI. Yerel LLM (Ollama, qwen2.5:3b) ile soru
  üretir, çok-kipli (multimodal) analiz yapar: yüz duygusu, ses duygusu,
  semantik benzerlik, kararsızlık tespiti, tutarlılık ölçümü. SGDRegressor
  tabanlı online learning skor motoruna sahiptir.

Yardımcı bileşenler: PostgreSQL (kalıcı veri), Redis (oturum cache), Ollama
(yerel LLM çalışma zamanı).

## Mimari

```
┌──────────────┐    REST / JWT    ┌────────────────┐
│   Frontend   │ ───────────────► │  Spring Boot   │
│   (nginx)    │                  │   Backend API  │
└──────────────┘                  └───────┬────────┘
                                          │
                       ┌──────────────────┼──────────────────┐
                       │                  │                  │
                  ┌────▼────┐      ┌──────▼─────┐     ┌──────▼──────┐
                  │Postgres │      │   Redis    │     │  AI Service │
                  │  (V2)   │      │ (sessions) │     │  (FastAPI)  │
                  └─────────┘      └────────────┘     └──────┬──────┘
                                                             │
                                              ┌──────────────┼──────────────┐
                                              │                             │
                                         ┌────▼────┐               ┌────────▼────────┐
                                         │ Ollama  │               │ HuggingFace     │
                                         │qwen2.5  │               │ • multilingual  │
                                         │  :3b    │               │   MiniLM        │
                                         └─────────┘               │ • wav2vec2 ER   │
                                                                   │ • XLM-RoBERTa   │
                                                                   │   sentiment     │
                                                                   │ • FER (yüz)     │
                                                                   └─────────────────┘
```

## Adaptif Döngü

1. Kullanıcı yeni bir mülakat başlatır.
2. Backend, kullanıcının `user_skill_profile` tablosundaki kategori bazlı
   yetenek seviyelerine bakar. Buna göre bir hedef zorluk hesaplar.
3. Daha önce sorulmuş soruların hash'lerini AI servisine gönderir.
4. AI servisi Ollama'ya prompt atar. Prompt'a kullanıcının zayıf
   alanları, yakın zamanda görmüş olduğu konular ve hedef zorluk
   enjekte edilir. Çıktı temizleme filtresinden geçer; bozuk üretimde
   şablon havuzuna fallback yapılır.
4. Cevap geldiğinde feature extractor 20 sayısal sinyal çıkarır:
   yanıt süresi, kelime sayısı, kararsızlık yoğunluğu, tekrar oranı,
   yüz/ses duygusu, semantik benzerlik, tutarlılık, sentiment vb.
5. Hibrit skor motoru çalışır: sezgisel formül + SGDRegressor tahmini.
   Model güveni (sample sayısına bağlı) arttıkça ML çıktısının ağırlığı
   artar. Bu sayede sistem soğuk başlangıçta da mantıklı skor verir,
   veri biriktikçe rafine olur.
6. EWMA ile kullanıcının ilgili kategorideki yetenek seviyesi güncellenir.
   Bir sonraki mülakatta zorluk hedefi otomatik adapte olur.

## Klasör Yapısı

```
ai-interview-simulator/
├── docker-compose.yml          # Tüm servislerin orkestrasyonu
├── .env.example                # Örnek env dosyası
├── README.md
├── docs/
│   ├── ARCHITECTURE.md
│   ├── API.md
│   └── DEPLOYMENT.md
├── backend/                    # Spring Boot
│   ├── pom.xml
│   ├── Dockerfile
│   └── src/main/
│       ├── java/com/aiinterview/
│       │   ├── config/         # CORS, WebClient, exception handler
│       │   ├── controller/     # REST endpoints
│       │   ├── dto/            # Request/response kayıtları
│       │   ├── entity/         # JPA entity'leri
│       │   ├── repository/     # Spring Data repos
│       │   ├── security/       # JWT filter, config
│       │   ├── service/        # AdaptiveQuestionService, SkillProfileService, ...
│       │   └── websocket/      # Canlı geri bildirim handler'ı
│       └── resources/
│           ├── application.yml
│           └── db/migration/   # Flyway: V1__init.sql, V2__adaptive_system.sql
├── ai-service/                 # FastAPI + PyTorch
│   ├── requirements.txt
│   ├── Dockerfile
│   └── app/
│       ├── main.py
│       ├── routers/            # /analyze, /questions, /train, /health
│       ├── schemas/            # Pydantic modelleri
│       ├── llm/                # Ollama provider, question generator
│       ├── features/           # 20 boyutlu feature extractor
│       ├── scoring/            # Online learning skor motoru
│       └── services/           # Yüz/ses duygu modelleri
└── frontend/                   # React + Vite
    ├── package.json
    ├── Dockerfile
    ├── nginx.conf
    └── src/
        ├── App.jsx
        ├── pages/              # Login, Register, Dashboard, ...
        ├── components/         # Layout, ScorePanel
        ├── hooks/              # useWebcam, useAudioRecorder, useSessionGuard
        ├── lib/api.js          # Backend HTTP istemcisi
        └── store/auth.js       # Zustand auth store
```

## Gereksinimler

- Docker Desktop (Windows/macOS) veya Docker Engine + Compose plugin (Linux)
- En az 8 GB boş RAM. Ollama'nın `qwen2.5:3b` modeli ~2 GB bellek tutar;
  Python servisi de wav2vec2 + sentence-transformers + sentiment modelleri
  için 1-2 GB RAM kullanır.
- ~10 GB boş disk alanı (model artifact'leri için).
- 5173, 8080, 8000, 5432, 6379, 11434 portları boş olmalı.
- Internet bağlantısı (yalnızca ilk kurulumda; image'leri ve modelleri
  indirmek için).

## Kurulum

Aşağıdaki komutları proje kök dizininde sırasıyla çalıştır.

### 1. Repoyu klonla

```bash
git clone https://github.com/<kullanici>/<repo>.git
cd ai-interview-simulator
```

### 2. Ortam dosyasını oluştur

`.env.example` dosyasını kopyala. İçinde JWT secret, veritabanı şifresi
ve Ollama model adı gibi ayarlar var. İlk denemede varsayılan değerlerle
çalışır; production için en azından `JWT_SECRET` ve `POSTGRES_PASSWORD`
değerlerini değiştir.

```bash
cp .env.example .env
```

### 3. Servisleri ayağa kaldır

```bash
docker compose up -d --build
```

İlk açılışta yapılanlar:

- Tüm imajlar build edilir (~5-10 dk).
- PostgreSQL ayağa kalkar, Flyway V1 ve V2 migration'larını uygular.
- AI servisi açılır ve ilk istekte HuggingFace modellerini indirir
  (`hf_cache` volume'una; ~1.5 GB, sonraki başlatmalarda hızlı).
- `ollama-init` adında geçici bir konteyner Ollama'ya bağlanıp `qwen2.5:3b`
  modelini çeker (~2 GB). Bu adım 5-15 dk sürebilir; bu süre boyunca AI
  servisi şablon havuzuna fallback yapar, sistem yine kullanılabilir.

### 4. Çalıştığını doğrula

Tüm konteynerlerin sağlıklı durumda olduğunu kontrol et:

```bash
docker compose ps
```

Çıktıda `postgres`, `redis`, `ollama`, `ai-service`, `backend`, `frontend`
servislerinin `Up` veya `Up (healthy)` durumunda olması gerekir.

Servis URL'leri:

| Servis      | URL                                    |
|-------------|----------------------------------------|
| Frontend    | http://localhost:5173                  |
| Backend API | http://localhost:8080/api              |
| AI Servisi  | http://localhost:8000/docs (Swagger)   |
| Ollama API  | http://localhost:11434                 |

### 5. Hesap oluştur ve mülakata başla

1. Tarayıcıda http://localhost:5173 adresini aç.
2. "Hesap oluştur" linkine tıkla. E-posta, şifre (en az 8 karakter) ve
   ad-soyad gir.
3. Sol menüden "Yeni Mülakat" → rol ve seviye seç → "Mülakatı başlat".
4. Tarayıcı kamera ve mikrofon izni ister, izin ver.
5. Soruları yazılı olarak cevapla. İstersen "Kaydı başlat" diyerek
   sesini de gönder. "Cevabı gönder" ile AI değerlendirmesi alırsın.

## Yapılandırma

`.env` dosyasındaki kritik değişkenler:

| Değişken              | Açıklama                                          | Varsayılan       |
|-----------------------|---------------------------------------------------|------------------|
| `JWT_SECRET`          | Token imzalama anahtarı (en az 32 byte)           | dev değer        |
| `JWT_EXPIRATION_MS`   | Token geçerlilik süresi (ms)                      | 3600000 (1 saat) |
| `POSTGRES_PASSWORD`   | Veritabanı şifresi                                | changeme         |
| `OLLAMA_MODEL`        | Soru üretiminde kullanılacak yerel LLM            | qwen2.5:3b       |
| `AI_SERVICE_URL`      | Backend'in AI servise erişeceği URL               | http://ai-service:8000 |
| `VITE_API_URL`        | Frontend'in build sırasında baktığı backend URL   | http://localhost:8080/api |

Frontend env değişkenleri build sırasında imaja gömüldüğü için, dış
ortama deploy ederken `frontend` imajını güncel `VITE_API_URL` ile
yeniden build etmek gerekir.

## Yaygın Komutlar

Logları izlemek:

```bash
docker compose logs -f                 # tüm servisler
docker compose logs -f backend         # sadece backend
docker compose logs -f ai-service      # sadece AI
```

Belirli bir servisi yeniden başlatmak (örn. kod değiştirdikten sonra):

```bash
docker compose up -d --build backend
docker compose up -d --build ai-service
docker compose up -d --build frontend
```

Tüm sistemi durdurmak (veriyi koruyarak):

```bash
docker compose down
```

Tüm sistemi durdurup veritabanını ve model cache'ini sıfırlamak (geri
alınamaz):

```bash
docker compose down -v
```

Ollama'da farklı bir model denemek:

```bash
docker exec ai-interview-simulator-ollama-1 ollama pull <model-adi>
# .env dosyasında OLLAMA_MODEL değerini güncelle, sonra:
docker compose up -d --force-recreate ai-service
```

## Veritabanı Şeması

V2 migration'ı sonrası tablolar:

- `users` — hesaplar
- `interview_sessions` — bir mülakat oturumu (rol, seviye, hedef zorluk,
  genel skor)
- `interview_questions` — oturuma ait sorular (kategori, zorluk, üretim
  kaynağı, content hash)
- `interview_answers` — cevaplar ve hesaplanmış skorlar (kalite,
  özgüven, yüz/ses duygusu, kararsızlık, tutarlılık, yanıt süresi)
- `user_skill_profile` — kullanıcının kategori bazlı yetenek seviyesi
  (EWMA ile online güncelleniyor)
- `question_history` — kullanıcıya sorulmuş tüm soruların hash kaydı
  (tekrar engelleme için)
- `feature_vectors` — her cevabın 20 boyutlu feature vektörü
  (offline retraining için)
- `generated_questions` — LLM tarafından üretilmiş soru cache'i
- `model_registry` — model versiyon kayıtları (abstraction katmanı)

## Modelleri Değiştirme

Skor motoru abstraction katmanı sayesinde model değiştirilebilir.
`ai-service/app/scoring/base.py` içindeki `ScoringModel` arayüzünü
implemente eden yeni bir sınıf yaz, `engine.py`'da yükleme yolunu
değiştir. Mevcut SGDRegressor tabanlı `OnlineScoringModel` örnek olarak
inceleyebilirsin.

LLM sağlayıcısını değiştirmek için `ai-service/app/llm/base.py`
arayüzünü kullan. Şu an `OllamaProvider` var; OpenAI veya Anthropic
sağlayıcısı eklemek için sadece bu arayüzü implemente etmen yeterli.

## Sorun Giderme

**Frontend açılıyor ama backend'e istek atınca CORS hatası alıyorum.**
Backend imajı `app.cors.allowed-origins` değişkeninden hangi origin'lere
izin vereceğini okur. Farklı bir host'tan eriştiğinizde
`backend/src/main/resources/application.yml` içinden bu değeri ya da
`SecurityConfig` içindeki CORS yapılandırmasını güncelleyin.

**"Bu e-posta zaten kayıtlı" hatası alıyorum ama hesabım yok.**
Veritabanı eski bir kayıt tutuyor olabilir. `docker compose down -v` ile
sıfırla ve tekrar başlat.

**Sorular bekleyince geliyor.** Ollama ilk istekte modeli RAM'e yükler,
soğuk başlangıç 30-60 saniye sürebilir. Sonraki istekler hızlanır.
Modelin hâlâ inmediğini düşünüyorsanız:

```bash
docker exec ai-interview-simulator-ollama-1 ollama list
```

ile mevcut modelleri görün. Liste boşsa indirme tamamlanmamış demektir.

**Webcam çalışmıyor.** Tarayıcı kamera/mikrofon iznini sıfırlayın ve
sayfayı yeniden yükleyin. http://localhost yerine 127.0.0.1 kullanmak
da bazen yardımcı olur (bazı tarayıcılar localhost'u farklı değerlendirir).

**Skorlar her zaman %50.** Backend AI servisine ulaşamıyor demek. AI
servisinin loglarını kontrol edin:

```bash
docker compose logs ai-service --tail 50
```

## Güvenlik Notu

Bu repo geliştirme amaçlıdır. Production'a almadan önce mutlaka:

- `JWT_SECRET` değerini güçlü bir rastgele string ile değiştirin.
- `POSTGRES_PASSWORD` değerini değiştirin.
- CORS allowed-origins listesini production frontend host'una daraltın.
- Postgres ve Redis port'larını dış dünyaya açmayın
  (`docker-compose.yml` içinde `ports` yerine sadece `expose` kullanın).
- Reverse proxy arkasına alıp HTTPS terminate edin.

Daha kapsamlı production kontrol listesi için `docs/DEPLOYMENT.md`
dosyasına bakın.

## Lisans

Henüz lisans belirtilmedi. Repo public ise dilediğiniz lisansı (MIT,
Apache-2.0, GPL-3.0 vb.) eklemeyi unutmayın.
