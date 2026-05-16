"""
game.py — Retro Asteroids: Ana Oyun Döngüsü
============================================
CSE444 Take-Home Exam — Vibe Coding Project
Bakım Aşaması: Screen Wrapping + Power-Up Sistemi

Mimari özet:
  Bu dosya yalnızca oyun döngüsünü (game loop) ve durum makinesini (state machine)
  yönetir. Çizim mantığı → renderer.py, ses → sound_manager.py,
  skor kalıcılığı → highscore.py, power-up nesneleri → powerup.py modüllerine taşındı.

Bakım Değişiklikleri (CSE444):
  - Asteroid boundary davranışı: yansıma → screen wrapping (asteroid.py'de)
  - Power-up spawn/collect/timer mantığı eklendi
  - Slow-motion efekti: asteroid hız vektörleri geçici olarak ölçeklenir
  - player.shoot() artık list[Bullet] döndürür → bullets.extend() kullanılır

Durum makinesi (State Machine):
  MENU ──[SPACE]──► PLAYING ──[çarpışma]──► GAME_OVER ──[R]──► PLAYING
    ▲                                                               │
    └──────────────────────[ESC]────────────────────────────────────┘
"""

import pygame
import sys
import random
import math

from settings      import (
    GameState, SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
    INITIAL_ASTEROID_COUNT, WAVE_BASE_SPAWN_COUNT,
    MAX_ASTEROIDS_ON_SCREEN, DIFFICULTY_SPEED_MULTIPLIER,
    SHOOT_COOLDOWN_FRAMES,
    POWERUP_SPAWN_INTERVAL_FRAMES, POWERUP_SPAWN_CHANCE,
    POWERUP_MAX_DURATION_FRAMES, POWERUP_KINDS,
    POWERUP_KIND_SHIELD, POWERUP_KIND_DOUBLESHOT, POWERUP_KIND_SLOWMO,
    SLOWMO_ASTEROID_FACTOR,
)
from player        import Player
from asteroid      import Asteroid
from bullet        import Bullet
from particle      import BaseParticle, create_explosion
from powerup       import PowerUp
from renderer      import (render_starfield, render_menu, render_hud,
                           render_wave_banner, render_game_over,
                           render_powerup_hud)
from sound_manager import SoundManager
from highscore     import load_high_score, save_high_score

# ══════════════════════════════════════════════════════════════════════════════
# YARDIMCI FONKSİYONLAR
# ══════════════════════════════════════════════════════════════════════════════

def spawn_asteroids_on_edge(count: int,
                             speed_multiplier: float = 1.0) -> list[Asteroid]:
    """
    Belirtilen sayıda büyük asteroidi ekranın kenarlarından başlatır.
    Merkezdeki oyuncu ile başlangıçta güvenli mesafe sağlanır.

    Args:
        count            : Oluşturulacak asteroid sayısı
        speed_multiplier : Mevcut wave'in zorluk katsayısı

    Returns:
        Asteroid nesneleri listesi
    """
    asteroids: list[Asteroid] = []
    edges = ["top", "bottom", "left", "right"]

    for _ in range(count):
        edge = random.choice(edges)
        if edge == "top":
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(0, 80)
        elif edge == "bottom":
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(SCREEN_HEIGHT - 80, SCREEN_HEIGHT)
        elif edge == "left":
            x = random.randint(0, 80)
            y = random.randint(0, SCREEN_HEIGHT)
        else:
            x = random.randint(SCREEN_WIDTH - 80, SCREEN_WIDTH)
            y = random.randint(0, SCREEN_HEIGHT)

        asteroids.append(Asteroid(x, y, size="large",
                                  speed_multiplier=speed_multiplier))
    return asteroids


def spawn_random_powerup() -> PowerUp:
    """
    Ekranın rastgele bir noktasında rastgele türde bir power-up oluşturur.
    Oyuncu alanından uzakta (kenarlara yakın) doğar.

    Returns:
        Yeni PowerUp nesnesi
    """
    kind = random.choice(POWERUP_KINDS)
    # Kenarlara yakın doğmasını tercih et — oyuncunun hemen yanına değil
    margin = 80
    x = random.choice([
        random.randint(margin, SCREEN_WIDTH - margin),
    ])
    y = random.choice([
        random.randint(margin, SCREEN_HEIGHT - margin),
    ])
    return PowerUp(x, y, kind)


def handle_bullet_asteroid_collisions(
    bullets: list[Bullet],
    asteroids: list[Asteroid],
    particles: list[BaseParticle],
    speed_multiplier: float,
    sound_manager: SoundManager,
) -> tuple[list[Bullet], list[Asteroid], int]:
    """
    Mermi ↔ Asteroid çarpışma tespiti ve sonuçlarını işler.

    Her çarpışmada:
      1. Mermi ve asteroid listeleri güncellenir.
      2. Asteroid split() ile daha küçük parçalara bölünür.
      3. Patlama parçacıkları oluşturulur.
      4. Ses efekti çalınır (ses sistemi aktifse).
      5. Puan hesaplanır.

    Args:
        bullets          : Mevcut mermi listesi
        asteroids        : Mevcut asteroid listesi
        particles        : Parçacık listesi (in-place güncellenir)
        speed_multiplier : Çocuk asteroidlerin hız katsayısı
        sound_manager    : Ses efekti yöneticisi

    Returns:
        (güncel_bullets, güncel_asteroids, bu_turda_kazanılan_puan)
    """
    bullets_to_remove:   set[int] = set()
    asteroids_to_remove: set[int] = set()
    asteroids_to_add:    list[Asteroid] = []
    score_gained = 0

    for bullet_idx, bullet in enumerate(bullets):
        if bullet_idx in bullets_to_remove:
            continue
        for asteroid_idx, asteroid in enumerate(asteroids):
            if asteroid_idx in asteroids_to_remove:
                continue
            if bullet.collides_with_asteroid(asteroid):
                bullets_to_remove.add(bullet_idx)
                asteroids_to_remove.add(asteroid_idx)
                score_gained += asteroid.score_value

                children = asteroid.split(speed_multiplier=speed_multiplier)
                asteroids_to_add.extend(children)

                explosion_particles = create_explosion(asteroid.x, asteroid.y,
                                                       asteroid.color)
                particles.extend(explosion_particles)

                sound_manager.play("explode")
                break

    updated_bullets   = [b for i, b in enumerate(bullets)
                         if i not in bullets_to_remove]
    updated_asteroids = [a for i, a in enumerate(asteroids)
                         if i not in asteroids_to_remove]
    updated_asteroids.extend(asteroids_to_add)

    return updated_bullets, updated_asteroids, score_gained


def handle_powerup_collisions(
    player: Player,
    powerups: list[PowerUp],
    asteroids: list[Asteroid],
    sound_manager: SoundManager,
    game: dict,
) -> list[PowerUp]:
    """
    Oyuncu ↔ Power-up çarpışma tespiti ve efekt uygulaması.

    Toplanan power-up listeden çıkarılır; efekti player ve/veya
    oyun durumu üzerine uygulanır.

    Slow-motion efekti:
      Aktif asteroid hız vektörleri SLOWMO_ASTEROID_FACTOR ile ölçeklenerek
      anlık yavaşlatma sağlanır. Zamanlayıcı bitmeden önce tekrar
      toplanırsa hız zaten düşük olduğundan görsel fark minimal kalır.

    Args:
        player       : Oyuncu nesnesi
        powerups     : Mevcut power-up listesi
        asteroids    : Mevcut asteroid listesi (slow-mo için)
        sound_manager: Ses yöneticisi
        game         : Oyun durumu sözlüğü (slow_mo_timer için)

    Returns:
        Güncellenen power-up listesi (toplananlar çıkarıldı)
    """
    remaining = []
    for pu in powerups:
        if pu.collides_with_player(player):
            sound_manager.play("powerup_collect")

            if pu.kind == POWERUP_KIND_SHIELD:
                player.apply_shield(POWERUP_MAX_DURATION_FRAMES)

            elif pu.kind == POWERUP_KIND_DOUBLESHOT:
                player.apply_double_shot(POWERUP_MAX_DURATION_FRAMES)

            elif pu.kind == POWERUP_KIND_SLOWMO:
                # Slow-mo: asteroid hızlarını anlık ölçekle, timer'ı kaydet
                _apply_slow_motion(asteroids, game)

        else:
            remaining.append(pu)
    return remaining


def _apply_slow_motion(asteroids: list[Asteroid], game: dict) -> None:
    """
    Slow-motion power-up efektini uygular.

    Tüm aktif asteroidlerin hız vektörlerini SLOWMO_ASTEROID_FACTOR ile çarpar.
    Zamanlayıcı game["slow_mo_timer"]'a kaydedilir; süre dolunca orijinal
    hızlar geri yüklenir (orijinal hızlar _orig_vel özniteliklerinde saklanır).

    Args:
        asteroids: Mevcut asteroid listesi
        game     : Oyun durumu sözlüğü
    """
    # Eğer zaten aktifse, önce geri yükle (yenilenmiş süre için)
    if game.get("slow_mo_timer", 0) > 0:
        _restore_asteroid_speeds(asteroids)

    # Orijinal hızları sakla ve yavaşlat
    for asteroid in asteroids:
        asteroid._orig_vel_x = asteroid.vel_x
        asteroid._orig_vel_y = asteroid.vel_y
        asteroid.vel_x *= SLOWMO_ASTEROID_FACTOR
        asteroid.vel_y *= SLOWMO_ASTEROID_FACTOR

    game["slow_mo_timer"]  = POWERUP_MAX_DURATION_FRAMES
    # player nesnesine de slow_mo_timer yansıt (HUD için)
    game["player"].slow_mo_timer = POWERUP_MAX_DURATION_FRAMES


def _restore_asteroid_speeds(asteroids: list[Asteroid]) -> None:
    """
    Slow-motion power-up süresi dolduğunda asteroid hızlarını geri yükler.

    Args:
        asteroids: Mevcut asteroid listesi
    """
    for asteroid in asteroids:
        if hasattr(asteroid, "_orig_vel_x"):
            asteroid.vel_x = asteroid._orig_vel_x
            asteroid.vel_y = asteroid._orig_vel_y
            del asteroid._orig_vel_x
            del asteroid._orig_vel_y


def check_player_hit(player: Player,
                     asteroids: list[Asteroid]) -> bool:
    """
    Oyuncu ↔ Asteroid çarpışma kontrolü.
    Oyuncu dokunulmazsa (spawn veya kalkan) her zaman False döner.

    Args:
        player    : Oyuncu nesnesi
        asteroids : Mevcut asteroid listesi

    Returns:
        True → oyuncu vuruldu; False → güvende
    """
    return any(asteroid.collides_with_player(player)
               for asteroid in asteroids)


# ══════════════════════════════════════════════════════════════════════════════
# OYUN DURUM SIFIRLAMA
# ══════════════════════════════════════════════════════════════════════════════

def initialise_game_state() -> dict:
    """
    Yeni bir oyun oturumu için tüm durum değişkenlerini hazırlar.
    Hem ilk başlatmada hem de 'R' ile yeniden başlatmada çağrılır.

    Returns:
        Oyun durumu sözlüğü (game_state dict)
    """
    return {
        "player":              Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2),
        "asteroids":           spawn_asteroids_on_edge(INITIAL_ASTEROID_COUNT,
                                                       speed_multiplier=1.0),
        "bullets":             [],
        "particles":           [],
        "powerups":            [],
        "score":               0,
        "wave":                1,
        "speed_multiplier":    1.0,
        "wave_banner_timer":   90,
        "shoot_cooldown":      0,
        "frame_count":         0,
        "powerup_spawn_timer": POWERUP_SPAWN_INTERVAL_FRAMES,
        "slow_mo_timer":       0,
    }


# ══════════════════════════════════════════════════════════════════════════════
# DURUM: MENÜ
# ══════════════════════════════════════════════════════════════════════════════

def handle_menu_input(event: pygame.event.Event,
                      current_state: GameState) -> GameState:
    """
    Menü ekranında klavye olaylarını işler.

    Returns:
        Yeni GameState değeri
    """
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_SPACE:
            return GameState.PLAYING
        if event.key == pygame.K_ESCAPE:
            pygame.quit()
            sys.exit()
    return current_state


# ══════════════════════════════════════════════════════════════════════════════
# DURUM: OYUN (PLAYING)
# ══════════════════════════════════════════════════════════════════════════════

def handle_playing_input(event: pygame.event.Event,
                         current_state: GameState) -> GameState:
    """Oyun sırasında ESC olayını işler."""
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
            pygame.quit()
            sys.exit()
    return current_state


def update_playing(game: dict, sound_manager: SoundManager) -> GameState:
    """
    Oyun (PLAYING) durumunun mantığını her frame günceller.

    İşlemler (sırasıyla):
      1. Klavye okuma ve oyuncu kontrolü
      2. Tüm nesne güncellemeleri (player, asteroids, bullets, particles, powerups)
      3. Power-up spawn zamanlayıcısı
      4. Çarpışma tespiti (mermi↔asteroid, oyuncu↔asteroid, oyuncu↔powerup)
      5. Slow-motion zamanlayıcı kontrolü
      6. Wave/zorluk geçişi kontrolü

    Args:
        game          : initialise_game_state() tarafından döndürülen sözlük
        sound_manager : Ses yöneticisi

    Returns:
        Yeni GameState (PLAYING devam || GAME_OVER geçiş)
    """
    game["frame_count"] += 1
    player: Player = game["player"]
    asteroids: list = game["asteroids"]
    bullets: list   = game["bullets"]
    particles: list = game["particles"]
    powerups: list  = game["powerups"]

    # ── Klavye girdisi ────────────────────────────────────────────────────────
    keys = pygame.key.get_pressed()

    if keys[pygame.K_LEFT]:
        player.rotate(1)
    if keys[pygame.K_RIGHT]:
        player.rotate(-1)
    if keys[pygame.K_UP]:
        player.apply_thrust()

    if keys[pygame.K_SPACE] and game["shoot_cooldown"] <= 0:
        new_bullets = player.shoot()   # artık list döner
        bullets.extend(new_bullets)
        game["shoot_cooldown"] = SHOOT_COOLDOWN_FRAMES
        sound_manager.play("shoot")

    if game["shoot_cooldown"] > 0:
        game["shoot_cooldown"] -= 1

    # ── Nesneleri güncelle ────────────────────────────────────────────────────
    player.update()

    for asteroid in asteroids:
        asteroid.update()

    game["bullets"] = [b for b in bullets if b.is_alive()]
    for bullet in game["bullets"]:
        bullet.update()

    game["particles"] = [p for p in particles if p.is_alive()]
    for particle in game["particles"]:
        particle.update()

    # Power-up'ları güncelle
    game["powerups"] = [pu for pu in powerups if pu.is_alive()]
    for pu in game["powerups"]:
        pu.update()

    # Egzoz parçacıkları
    if player.is_thrusting:
        exhaust = player.get_exhaust_particles()
        game["particles"].extend(exhaust)

    if game["wave_banner_timer"] > 0:
        game["wave_banner_timer"] -= 1

    # ── Power-up spawn zamanlayıcısı ──────────────────────────────────────────
    game["powerup_spawn_timer"] -= 1
    if game["powerup_spawn_timer"] <= 0:
        game["powerup_spawn_timer"] = POWERUP_SPAWN_INTERVAL_FRAMES
        if random.random() < POWERUP_SPAWN_CHANCE:
            game["powerups"].append(spawn_random_powerup())

    # ── Slow-motion zamanlayıcı kontrolü ─────────────────────────────────────
    if game["slow_mo_timer"] > 0:
        game["slow_mo_timer"] -= 1
        # Player nesnesindeki HUD zamanlayıcısını da güncelle
        if hasattr(player, "slow_mo_timer"):
            player.slow_mo_timer = game["slow_mo_timer"]
        # Süre bitti: orijinal hızları geri yükle
        if game["slow_mo_timer"] == 0:
            _restore_asteroid_speeds(game["asteroids"])
            if hasattr(player, "slow_mo_timer"):
                player.slow_mo_timer = 0

    # ── Çarpışma tespiti ──────────────────────────────────────────────────────
    (game["bullets"],
     game["asteroids"],
     score_gained) = handle_bullet_asteroid_collisions(
        game["bullets"], game["asteroids"],
        game["particles"], game["speed_multiplier"],
        sound_manager,
    )
    game["score"] += score_gained

    # Oyuncu ↔ Power-up
    game["powerups"] = handle_powerup_collisions(
        player, game["powerups"], game["asteroids"],
        sound_manager, game,
    )

    # Oyuncu ↔ Asteroid
    if check_player_hit(player, game["asteroids"]):
        sound_manager.play("game_over")
        return GameState.GAME_OVER

    # ── Wave geçişi ───────────────────────────────────────────────────────────
    if len(game["asteroids"]) == 0:
        # Slow-mo aktifse yeni asteroidler normal hızda doğar
        if game["slow_mo_timer"] > 0:
            _restore_asteroid_speeds([])   # boş liste, sadece temizlik
            game["slow_mo_timer"] = 0
            if hasattr(player, "slow_mo_timer"):
                player.slow_mo_timer = 0

        game["wave"]             += 1
        game["speed_multiplier"] *= DIFFICULTY_SPEED_MULTIPLIER
        game["wave_banner_timer"] = 90

        new_count = min(
            WAVE_BASE_SPAWN_COUNT + game["wave"] - 1,
            MAX_ASTEROIDS_ON_SCREEN,
        )
        game["asteroids"] = spawn_asteroids_on_edge(
            new_count, game["speed_multiplier"]
        )
        sound_manager.play("wave_up")

    return GameState.PLAYING


# ══════════════════════════════════════════════════════════════════════════════
# DURUM: GAME OVER
# ══════════════════════════════════════════════════════════════════════════════

def handle_game_over_input(event: pygame.event.Event,
                           current_state: GameState,
                           game: dict,
                           high_score: int) -> tuple[GameState, dict, int]:
    """
    Game Over ekranında klavye olaylarını işler.

    Returns:
        (yeni_state, yeni_game_dict, güncel_high_score)
    """
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_r:
            updated_high = max(high_score, game["score"])
            save_high_score(updated_high)
            return GameState.PLAYING, initialise_game_state(), updated_high
        if event.key == pygame.K_ESCAPE:
            pygame.quit()
            sys.exit()
    return current_state, game, high_score


# ══════════════════════════════════════════════════════════════════════════════
# ANA FONKSİYON
# ══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    """
    Programın giriş noktası.

    Başlatma adımları:
      1. pygame başlatma ve pencere oluşturma
      2. Fontlar, ses yöneticisi, high score yükleme
      3. Ana oyun döngüsü (MENU → PLAYING → GAME_OVER döngüsü)
    """
    pygame.init()
    pygame.display.set_caption("Retro Asteroids")
    screen      = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock       = pygame.time.Clock()

    # ── Fontlar ───────────────────────────────────────────────────────────────
    big_font   = pygame.font.SysFont("monospace", 52, bold=True)
    font       = pygame.font.SysFont("monospace", 20, bold=True)
    small_font = pygame.font.SysFont("monospace", 14)

    # ── Ses yöneticisi ────────────────────────────────────────────────────────
    sound_manager = SoundManager()

    # ── Yüksek skor ───────────────────────────────────────────────────────────
    high_score = load_high_score()

    # ── Durum makinesi başlangıcı ─────────────────────────────────────────────
    current_state = GameState.MENU
    game          = initialise_game_state()
    menu_frame    = 0

    # ══════════════════════════════════════════════════════════════════════════
    # ANA DÖNGÜ
    # ══════════════════════════════════════════════════════════════════════════
    running = True
    while running:

        clock.tick(FPS)

        # ── Olay işleme ───────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif current_state == GameState.MENU:
                current_state = handle_menu_input(event, current_state)
                if current_state == GameState.PLAYING:
                    game = initialise_game_state()

            elif current_state == GameState.PLAYING:
                current_state = handle_playing_input(event, current_state)

            elif current_state == GameState.GAME_OVER:
                (current_state,
                 game,
                 high_score) = handle_game_over_input(
                    event, current_state, game, high_score
                )

        # ── Güncelleme & Çizim ────────────────────────────────────────────────
        if current_state == GameState.MENU:
            menu_frame += 1
            render_menu(screen, big_font, font, small_font,
                        menu_frame, high_score)

        elif current_state == GameState.PLAYING:
            next_state = update_playing(game, sound_manager)

            if next_state == GameState.GAME_OVER:
                high_score = max(high_score, game["score"])
                save_high_score(high_score)
            current_state = next_state

            # Çizim
            render_starfield(screen)
            for asteroid in game["asteroids"]:
                asteroid.draw(screen)
            for pu in game["powerups"]:
                pu.draw(screen)
            for particle in game["particles"]:
                particle.draw(screen)
            for bullet in game["bullets"]:
                bullet.draw(screen)
            game["player"].draw(screen, game["frame_count"])
            render_hud(screen, game["score"], high_score,
                       game["wave"], font, small_font)
            render_wave_banner(screen, game["wave"],
                               game["wave_banner_timer"], font)
            render_powerup_hud(screen, game["player"], small_font)

        elif current_state == GameState.GAME_OVER:
            render_starfield(screen)
            render_game_over(screen, game["score"], high_score,
                             game["wave"], font, big_font, small_font)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
