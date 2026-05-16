"""
renderer.py — Ekran Çizim (Renderer) Modülü
============================================
Tüm ekran durumlarına ait çizim fonksiyonlarını barındırır.
game.py ana döngüsünü sade tutmak için çizim kodu buraya taşındı.

State machine mimarisine uygun:
  render_menu()      → GameState.MENU
  render_playing()   → GameState.PLAYING (HUD + wave banner)
  render_game_over() → GameState.GAME_OVER

Bakım Güncellemesi (CSE444):
  render_powerup_hud() eklendi — aktif power-up'ları ve kalan sürelerini gösterir.

Genişletilebilirlik:
  Yeni bir GameState eklendığinde buraya yeni bir render_*() fonksiyonu
  eklemek yeterlidir.
"""

import pygame
import math

from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, STAR_POSITIONS,
    BLACK, WHITE, GRAY, DARK_GRAY, CYAN, LIGHT_CYAN,
    ORANGE, RED, GREEN, YELLOW, STAR_COLOR,
    POWERUP_SHIELD_COLOR, POWERUP_DOUBLESHOT_COLOR, POWERUP_SLOWMO_COLOR,
    POWERUP_KIND_SHIELD, POWERUP_KIND_DOUBLESHOT, POWERUP_KIND_SLOWMO,
    POWERUP_MAX_DURATION_FRAMES, FPS,
)


# ══════════════════════════════════════════════════════════════════════════════
# YARDIMCI: MERKEZLİ METİN ÇİZİMİ
# ══════════════════════════════════════════════════════════════════════════════

def draw_centered_text(screen: pygame.Surface,
                       text: str,
                       font: pygame.font.Font,
                       color: tuple[int, int, int],
                       center_y: int,
                       alpha: int = 255) -> None:
    """
    Metni yatayda ortalayarak ekrana çizer.

    Args:
        screen  : Çizim yüzeyi
        text    : Gösterilecek metin
        font    : pygame.font.Font nesnesi
        color   : (R, G, B) renk demeti
        center_y: Metnin dikey merkez koordinatı
        alpha   : Saydamlık (0-255); fade efektleri için
    """
    surface = font.render(text, True, color)
    if alpha < 255:
        surface.set_alpha(alpha)
    screen.blit(surface, (SCREEN_WIDTH // 2 - surface.get_width() // 2, center_y))


# ══════════════════════════════════════════════════════════════════════════════
# ARKA PLAN
# ══════════════════════════════════════════════════════════════════════════════

def render_starfield(screen: pygame.Surface) -> None:
    """Statik yıldız arka planını çizer."""
    screen.fill(BLACK)
    for star_x, star_y in STAR_POSITIONS:
        pygame.draw.circle(screen, STAR_COLOR, (star_x, star_y), 1)


# ══════════════════════════════════════════════════════════════════════════════
# ANA MENÜ (MENU STATE)
# ══════════════════════════════════════════════════════════════════════════════

def render_menu(screen: pygame.Surface,
                big_font: pygame.font.Font,
                font: pygame.font.Font,
                small_font: pygame.font.Font,
                frame_count: int,
                high_score: int) -> None:
    """
    Başlangıç / Ana menü ekranını çizer.

    Özellikler:
      - Pulsating (nefes alan) başlık efekti: sinüs dalgasıyla parlaklık değişir
      - "PRESS SPACE TO START" yanıp söner
      - Kontroller listesi
      - Yüksek skor gösterimi (kaydedilmiş ise)
    """
    render_starfield(screen)

    # ── Başlık: pulsating parlama efekti ─────────────────────────────────────
    pulse_ratio   = (math.sin(frame_count * 0.04) + 1) / 2
    title_alpha   = int(180 + 75 * pulse_ratio)
    draw_centered_text(screen, "RETRO ASTEROIDS",
                       big_font, CYAN, 130, alpha=title_alpha)

    draw_centered_text(screen, "CSE444 — Vibe Coding Project",
                       small_font, DARK_GRAY, 195)

    # ── "PRESS SPACE" yanıp sönen çağrı ──────────────────────────────────────
    blink_visible = (frame_count // 35) % 2 == 0
    if blink_visible:
        draw_centered_text(screen, "SPACE  ile  Başla",
                           font, GREEN, 280)

    # ── Kontroller ────────────────────────────────────────────────────────────
    controls = [
        ("← →", "Döndür"),
        ("↑",   "İtme (Thrust)"),
        ("SPC", "Ateş Et"),
        ("ESC", "Çıkış"),
    ]
    label_x   = SCREEN_WIDTH // 2 - 120
    value_x   = SCREEN_WIDTH // 2 + 10
    start_y   = 350

    for index, (key_label, action) in enumerate(controls):
        row_y = start_y + index * 28
        key_surf = small_font.render(key_label, True, YELLOW)
        act_surf = small_font.render(action,    True, GRAY)
        screen.blit(key_surf, (label_x, row_y))
        screen.blit(act_surf, (value_x, row_y))

    # ── Yüksek skor ──────────────────────────────────────────────────────────
    if high_score > 0:
        draw_centered_text(screen, f"EN YÜK. SKOR: {high_score}",
                           small_font, YELLOW, 510)


# ══════════════════════════════════════════════════════════════════════════════
# OYUN İÇİ HUD (PLAYING STATE)
# ══════════════════════════════════════════════════════════════════════════════

def render_hud(screen: pygame.Surface,
               score: int,
               high_score: int,
               wave: int,
               font: pygame.font.Font,
               small_font: pygame.font.Font) -> None:
    """
    Oyun içi Heads-Up Display (HUD).
    Sol üst: skor | Sağ üst: yüksek skor | Orta üst: wave
    Sol alt : kontrol ipuçları
    """
    screen.blit(font.render(f"SCORE: {score}", True, WHITE), (10, 10))

    high_score_surface = font.render(f"BEST: {high_score}", True, YELLOW)
    screen.blit(high_score_surface,
                (SCREEN_WIDTH - high_score_surface.get_width() - 10, 10))

    wave_surface = small_font.render(f"WAVE {wave}", True, GRAY)
    screen.blit(wave_surface,
                (SCREEN_WIDTH // 2 - wave_surface.get_width() // 2, 10))

    hints = ["← → : Döndür", "↑ : İtme", "SPACE : Ateş", "ESC : Çıkış"]
    for idx, hint_text in enumerate(hints):
        hint_surface = small_font.render(hint_text, True, DARK_GRAY)
        screen.blit(hint_surface, (10, SCREEN_HEIGHT - 90 + idx * 20))


def render_wave_banner(screen: pygame.Surface,
                       wave: int,
                       timer: int,
                       font: pygame.font.Font) -> None:
    """
    Yeni wave başladığında ekran ortasında geçici banner gösterir.
    timer azaldıkça fade-out uygulanır.

    Args:
        timer: Kalan görünürlük frame sayısı (0 ise çizilmez)
    """
    if timer <= 0:
        return
    alpha = min(255, timer * 8)
    draw_centered_text(screen, f"— WAVE {wave} —",
                       font, CYAN,
                       SCREEN_HEIGHT // 2 - 20,
                       alpha=alpha)


def render_powerup_hud(screen: pygame.Surface,
                       player,
                       small_font: pygame.font.Font) -> None:
    """
    Aktif power-up'ları ve kalan sürelerini sağ alt köşede gösterir.

    Her aktif power-up için:
      - Renkli ikon (küçük daire)
      - Kısa etiket
      - İlerleme çubuğu (kalan süre / maksimum süre)

    Args:
        screen     : Çizim yüzeyi
        player     : Player nesnesi (shield_timer, double_shot_timer)
        small_font : Küçük font nesnesi
    """
    active_powerups = []

    if player.shield_timer > 0:
        active_powerups.append({
            "label":   "KALKAN",
            "timer":   player.shield_timer,
            "color":   POWERUP_SHIELD_COLOR,
        })
    if player.double_shot_timer > 0:
        active_powerups.append({
            "label":   "2X ATES",
            "timer":   player.double_shot_timer,
            "color":   POWERUP_DOUBLESHOT_COLOR,
        })

    # Slow-mo bilgisi game.py'den ayrı tutulur;
    # burada player nesnesi üzerinden slow_mo_timer okunur (varsa).
    slow_timer = getattr(player, "slow_mo_timer", 0)
    if slow_timer > 0:
        active_powerups.append({
            "label":   "YAVAS",
            "timer":   slow_timer,
            "color":   POWERUP_SLOWMO_COLOR,
        })

    if not active_powerups:
        return

    bar_width  = 100
    bar_height = 6
    row_height = 24
    start_x    = SCREEN_WIDTH - bar_width - 60
    start_y    = SCREEN_HEIGHT - (len(active_powerups) * row_height) - 10

    for idx, pu in enumerate(active_powerups):
        row_y = start_y + idx * row_height

        # Renkli ikon
        pygame.draw.circle(screen, pu["color"], (start_x - 10, row_y + 8), 5)

        # Etiket
        label_surf = small_font.render(pu["label"], True, pu["color"])
        screen.blit(label_surf, (start_x, row_y))

        # İlerleme çubuğu (fill)
        ratio    = max(0.0, pu["timer"] / POWERUP_MAX_DURATION_FRAMES)
        fill_w   = int(bar_width * ratio)
        bar_rect = pygame.Rect(start_x, row_y + bar_height + 10,
                               bar_width, bar_height)
        fill_rect = pygame.Rect(start_x, row_y + bar_height + 10,
                                fill_w, bar_height)

        pygame.draw.rect(screen, DARK_GRAY, bar_rect)
        pygame.draw.rect(screen, pu["color"], fill_rect)
        pygame.draw.rect(screen, GRAY, bar_rect, 1)


# ══════════════════════════════════════════════════════════════════════════════
# OYUN BİTTİ EKRANI (GAME OVER STATE)
# ══════════════════════════════════════════════════════════════════════════════

def render_game_over(screen: pygame.Surface,
                     score: int,
                     high_score: int,
                     wave: int,
                     font: pygame.font.Font,
                     big_font: pygame.font.Font,
                     small_font: pygame.font.Font) -> None:
    """
    Game Over ekranını çizer.
    Yeni rekor kırıldıysa altın renkli "YENİ REKOR!" mesajı gösterir.

    Args:
        score     : Oyuncunun bu turda yaptığı toplam puan
        high_score: Güncellenmeden önceki en yüksek skor (karşılaştırma için)
        wave      : Ulaşılan wave numarası
    """
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 175))
    screen.blit(overlay, (0, 0))

    draw_centered_text(screen, "GAME OVER", big_font, RED, 100)

    draw_centered_text(screen, f"SKOR: {score}",       font, WHITE,  215)
    draw_centered_text(screen, f"WAVE: {wave}",        font, GRAY,   255)

    is_new_record   = score > 0 and score >= high_score
    record_text     = "★  YENİ REKOR!  ★" if is_new_record else f"EN İYİ: {high_score}"
    record_color    = YELLOW if is_new_record else GRAY
    draw_centered_text(screen, record_text, font, record_color, 305)

    draw_centered_text(screen, "R  —  Yeniden Başlat",    font, GREEN, 390)
    draw_centered_text(screen, "ESC  —  Çıkış",          small_font, DARK_GRAY, 430)
