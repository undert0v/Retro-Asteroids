"""
settings.py — Retro Asteroids: Merkezi Konfigürasyon Modülü
============================================================
Tüm oyun sabitleri ve ayarlanabilir parametreler bu dosyada toplanmıştır.
Herhangi bir değeri değiştirmek için yalnızca bu dosyayı düzenlemek yeterlidir;
bu tasarım kararı "Open/Closed Principle"e uygun bakım kolaylığı sağlar.

Bakım Güncellemeleri (CSE444 Maintenance Phase):
  - Screen wrapping: Asteroid boundary behavior değiştirildi
  - PowerUp sistemi için sabitler eklendi
  - Ses sistemi için "powerup_collect" anahtarı eklendi
"""

import random
from enum import Enum, auto

# ══════════════════════════════════════════════════════════════════════════════
# OYUN DURUMU (GAME STATE)
# ══════════════════════════════════════════════════════════════════════════════

class GameState(Enum):
    """
    Oyunun olası durumlarını temsil eden enum.
    State machine mimarisi: her durum kendi render ve input mantığına sahiptir.

    Genişletilebilirlik notu:
      Yeni bir durum eklemek (örn. PAUSED, HIGH_SCORES, SETTINGS) yalnızca
      buraya yeni bir değer ekleyip game.py'de ilgili handle/render
      fonksiyonlarını yazmayı gerektirir — mevcut kodda değişiklik olmaz.
    """
    MENU      = auto()   # Başlangıç / Ana menü ekranı
    PLAYING   = auto()   # Aktif oyun
    GAME_OVER = auto()   # Oyun bitti ekranı

# ══════════════════════════════════════════════════════════════════════════════
# EKRAN & ÇERÇEVE HIZI
# ══════════════════════════════════════════════════════════════════════════════

SCREEN_WIDTH  = 800
SCREEN_HEIGHT = 600
FPS           = 60

# ══════════════════════════════════════════════════════════════════════════════
# RENK PALETİ
# ══════════════════════════════════════════════════════════════════════════════

BLACK       = (0,   0,   0)
WHITE       = (255, 255, 255)
GRAY        = (160, 160, 160)
DARK_GRAY   = (60,  60,  60)
CYAN        = (0,   220, 220)
LIGHT_CYAN  = (180, 255, 255)
ORANGE      = (255, 160,  40)
ORANGE_DIM  = (180, 100,  20)
RED         = (220,  50,  50)
GREEN       = (80,  220,  80)
YELLOW      = (255, 220,  40)
STAR_COLOR  = (180, 180, 200)
EXHAUST_COL = (255, 120,  30)   # Egzoz parçacığı rengi

# ── Power-Up Renkleri ─────────────────────────────────────────────────────────
POWERUP_SHIELD_COLOR     = (100, 180, 255)   # Mavi — Kalkan
POWERUP_DOUBLESHOT_COLOR = (255, 80,  200)   # Pembe/Mor — Çift Atış
POWERUP_SLOWMO_COLOR     = (80,  255, 120)   # Yeşil — Yavaşlatma

# ══════════════════════════════════════════════════════════════════════════════
# OYUNCU (PLAYER)
# ══════════════════════════════════════════════════════════════════════════════

PLAYER_ROTATION_SPEED       = 4      # Derece/frame
PLAYER_THRUST_ACCELERATION  = 0.25   # Piksel/frame² — ivme büyüklüğü
PLAYER_MAX_SPEED            = 7      # Piksel/frame — hız tavanı
PLAYER_FRICTION_COEFFICIENT = 0.98   # [0,1] — 1 = sürtünme yok
PLAYER_COLLISION_RADIUS     = 18     # Piksel — üçgen dış çemberi yarıçapı

# Spawn koruması (invincibility): oyun başında ve ileride can sistemi eklendığında
# yeniden doğuşta oyuncu bu süre boyunca çarpışmadan bağışık olur.
PLAYER_INVINCIBILITY_FRAMES = 180    # 3 saniye @ 60 FPS
PLAYER_BLINK_INTERVAL       = 8     # Her N frame'de bir görünmez (blink)

# ══════════════════════════════════════════════════════════════════════════════
# MERMİ (BULLET)
# ══════════════════════════════════════════════════════════════════════════════

BULLET_SPEED          = 10    # Piksel/frame
BULLET_LIFETIME_FRAMES= 55    # ~0.9 saniye @ 60 FPS
BULLET_RADIUS         = 3     # Piksel — çizim ve çarpışma yarıçapı
SHOOT_COOLDOWN_FRAMES = 15    # Frame — ardışık atışlar arası minimum bekleme

# Double-shot açısal sapma (derece): iki mermi arasındaki açı farkının yarısı
DOUBLE_SHOT_SPREAD_DEG = 8

# ══════════════════════════════════════════════════════════════════════════════
# ASTEROİD
# ══════════════════════════════════════════════════════════════════════════════

INITIAL_ASTEROID_COUNT = 6

# Her boyut için: görsel yarıçap, hız aralığı, renk, puan değeri, kaç çocuk
ASTEROID_SIZES: dict[str, dict] = {
    "large":  {
        "radius":      45,
        "speed_range": (1.0, 2.0),
        "color":       (200, 200, 200),
        "score":       20,
        "children":    2,
    },
    "medium": {
        "radius":      25,
        "speed_range": (1.5, 3.0),
        "color":       (160, 160, 160),
        "score":       50,
        "children":    2,
    },
    "small":  {
        "radius":      12,
        "speed_range": (2.5, 4.5),
        "color":       (120, 120, 120),
        "score":       100,
        "children":    0,    # Küçük asteroid parçalanmaz; tamamen silinir
    },
}

MAX_ASTEROIDS_ON_SCREEN      = 20
WAVE_BASE_SPAWN_COUNT        = INITIAL_ASTEROID_COUNT
DIFFICULTY_SPEED_MULTIPLIER  = 1.12   # Her wave'de hız bu katsayıyla artar

# Slow-motion power-up asteroid hız çarpanı (0 < x < 1)
SLOWMO_ASTEROID_FACTOR = 0.35   # Asteroidlerin hızını %35'e indirir

# ══════════════════════════════════════════════════════════════════════════════
# PATLAMA PARÇACIKLARİ (EXPLOSION PARTICLES)
# ══════════════════════════════════════════════════════════════════════════════

EXPLOSION_PARTICLE_COUNT      = 12
EXPLOSION_PARTICLE_LIFETIME   = 40    # Frame
EXPLOSION_PARTICLE_SPEED_MIN  = 1.5
EXPLOSION_PARTICLE_SPEED_MAX  = 4.5

# ══════════════════════════════════════════════════════════════════════════════
# EGZOZ PARÇACIKLARİ (EXHAUST / THRUSTER PARTICLES)
# ══════════════════════════════════════════════════════════════════════════════

EXHAUST_PARTICLE_COUNT    = 2     # Her thrust frame'inde kaç parçacık
EXHAUST_PARTICLE_LIFETIME = 18    # Frame — kısa ömürlü, sadece görsel
EXHAUST_PARTICLE_SPEED    = 2.5   # Piksel/frame — geminin tersine fırlar
EXHAUST_SPREAD_ANGLE_DEG  = 25    # Saçılma açısı (derece)

# ══════════════════════════════════════════════════════════════════════════════
# POWER-UP SİSTEMİ
# ══════════════════════════════════════════════════════════════════════════════

# Spawn sıklığı: her POWERUP_SPAWN_INTERVAL_FRAMES frame'de bir spawn denemesi
# (rastgele eşik kontrolüyle birlikte kullanılır)
POWERUP_SPAWN_INTERVAL_FRAMES = 360     # 6 saniye @ 60 FPS
POWERUP_SPAWN_CHANCE          = 0.55    # Her interval'da spawn olma olasılığı

# Power-up maksimum süre (saniye → frame)
POWERUP_MAX_DURATION_FRAMES   = 30 * FPS    # 30 saniye × 60 FPS = 1800 frame

# Power-up görsel boyutu
POWERUP_RADIUS                = 12     # Piksel — çizim ve çarpışma yarıçapı

# Power-up ekranda kalma süresi (toplanmazsa kaybolur)
POWERUP_LIFETIME_FRAMES       = 10 * FPS    # 10 saniye

# Power-up türleri (string sabitleri — PowerUp.kind özniteliği)
POWERUP_KIND_SHIELD      = "shield"
POWERUP_KIND_DOUBLESHOT  = "double_shot"
POWERUP_KIND_SLOWMO      = "slow_mo"

# Olası power-up türleri listesi (rastgele seçim için)
POWERUP_KINDS = [
    POWERUP_KIND_SHIELD,
    POWERUP_KIND_DOUBLESHOT,
    POWERUP_KIND_SLOWMO,
]

# ══════════════════════════════════════════════════════════════════════════════
# SES YÖNETİMİ (SOUND MANAGER — PLACEHOLDER ALTYAPISI)
# ══════════════════════════════════════════════════════════════════════════════

SOUND_ENABLED = False   # True yapıldığında SoundManager dosyaları yüklemeye çalışır

SOUND_PATHS: dict[str, str] = {
    "shoot":           "assets/shoot.wav",
    "explode":         "assets/explode.wav",
    "game_over":       "assets/game_over.wav",
    "wave_up":         "assets/wave_up.wav",
    "powerup_collect": "assets/powerup_collect.wav",   # Yeni: power-up toplama sesi
}

# ══════════════════════════════════════════════════════════════════════════════
# HIGH SCORE KALICILIĞI
# ══════════════════════════════════════════════════════════════════════════════

HIGH_SCORE_FILE = "highscore.txt"   # Çalışma dizinine kaydedilir

# ══════════════════════════════════════════════════════════════════════════════
# ARKA PLAN YILDIZLARI
# ══════════════════════════════════════════════════════════════════════════════

random.seed(42)   # Tutarlı yıldız haritası; seed değiştirilirse harita da değişir
STAR_POSITIONS: list[tuple[int, int]] = [
    (random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT))
    for _ in range(120)
]
