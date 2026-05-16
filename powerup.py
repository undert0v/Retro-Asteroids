"""
powerup.py — Güçlendirme (Power-Up) Sistemi
============================================
Oyuncunun toplayabileceği geçici güçlendirme nesneleri.

Üç tür power-up desteklenir:

  1. SHIELD      — Gemiyi geçici olarak hasar almaz yapar (invincibility).
  2. DOUBLE_SHOT — Aynı anda iki mermi ateşlenmesini sağlar.
  3. SLOW_MO     — Ekrandaki tüm asteroidlerin hızını geçici olarak düşürür.

Tasarım kararı:
  PowerUp sınıfı yalnızca konumunu, türünü, ömrünü ve çizimini yönetir.
  Efektin uygulanması (oyuncu durumu, asteroid hızı) game.py ve player.py
  sorumluluğundadır. Bu, "Separation of Concerns" prensibine uygun bir
  ayrım sağlar.

Genişletilebilirlik:
  Yeni bir power-up eklemek için:
    1. settings.py'de POWERUP_KINDS listesine yeni sabiti ekle.
    2. Bu dosyada POWERUP_COLOR_MAP sözlüğüne rengi ekle.
    3. player.py'de ilgili durumu yönet; game.py'de efekti uygula.
"""

import pygame
import math
import random

from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    POWERUP_RADIUS, POWERUP_LIFETIME_FRAMES,
    POWERUP_KIND_SHIELD, POWERUP_KIND_DOUBLESHOT, POWERUP_KIND_SLOWMO,
    POWERUP_SHIELD_COLOR, POWERUP_DOUBLESHOT_COLOR, POWERUP_SLOWMO_COLOR,
    WHITE, DARK_GRAY,
)

# Tür → renk eşlemesi; yeni tür eklemek için yalnızca bu sözlüğü güncelle
POWERUP_COLOR_MAP: dict[str, tuple[int, int, int]] = {
    POWERUP_KIND_SHIELD:     POWERUP_SHIELD_COLOR,
    POWERUP_KIND_DOUBLESHOT: POWERUP_DOUBLESHOT_COLOR,
    POWERUP_KIND_SLOWMO:     POWERUP_SLOWMO_COLOR,
}

# Tür → HUD etiketi (kısa gösterim)
POWERUP_LABEL_MAP: dict[str, str] = {
    POWERUP_KIND_SHIELD:     "KALKAN",
    POWERUP_KIND_DOUBLESHOT: "2X ATES",
    POWERUP_KIND_SLOWMO:     "YAVAS",
}


class PowerUp:
    """
    Ekranda süzülen, oyuncu tarafından toplanabilen güçlendirme nesnesi.

    Attributes:
        x, y     : Merkez koordinatları
        kind     : Power-up türü (settings.POWERUP_KIND_* sabitlerinden biri)
        lifetime : Kalan ekranda kalma süresi (frame cinsinden; 0'a ulaşınca kaybolur)
        color    : Görsel renk (kind'a göre otomatik atanır)
        radius   : Çarpışma ve çizim yarıçapı (piksel)
    """

    def __init__(self, x: float, y: float, kind: str) -> None:
        """
        Args:
            x, y : Başlangıç koordinatları (genellikle ekranın rastgele bir noktası)
            kind : Power-up türü — POWERUP_KIND_SHIELD / DOUBLESHOT / SLOWMO
        """
        self.x        = float(x)
        self.y        = float(y)
        self.kind     = kind
        self.lifetime = POWERUP_LIFETIME_FRAMES
        self.radius   = POWERUP_RADIUS
        self.color    = POWERUP_COLOR_MAP.get(kind, WHITE)
        self._label   = POWERUP_LABEL_MAP.get(kind, kind.upper())

        # Hafif yüzme (drift) hareketi — tamamen sabit durmaması için
        angle = random.uniform(0, math.pi * 2)
        drift_speed = random.uniform(0.3, 0.8)
        self._vel_x = math.cos(angle) * drift_speed
        self._vel_y = math.sin(angle) * drift_speed

        # Titreşim (pulse) animasyonu için iç sayaç
        self._pulse_counter = 0

    # ── Durum Sorgusu ─────────────────────────────────────────────────────────

    def is_alive(self) -> bool:
        """Power-up hâlâ ekrandaysa True döner."""
        return self.lifetime > 0

    @property
    def label(self) -> str:
        """HUD'da gösterilecek kısa metin etiketi."""
        return self._label

    # ── Güncelleme ────────────────────────────────────────────────────────────

    def update(self) -> None:
        """
        Her frame'de konumu ve ömrü günceller.
        Ekran sarma (wrapping) uygulanır — mermi ve asteroid davranışıyla tutarlı.
        """
        self.x += self._vel_x
        self.y += self._vel_y
        self.x %= SCREEN_WIDTH
        self.y %= SCREEN_HEIGHT

        self.lifetime      -= 1
        self._pulse_counter = (self._pulse_counter + 1) % 60

    # ── Çarpışma ─────────────────────────────────────────────────────────────

    def collides_with_player(self, player) -> bool:
        """
        Daire-tabanlı çarpışma tespiti (oyuncu ↔ power-up).

        Args:
            player: Player nesnesi (x, y, radius öznitelikleri olmalı)

        Returns:
            True → oyuncu power-up'ı topladı; False → henüz değil
        """
        from settings import PLAYER_COLLISION_RADIUS
        distance = math.hypot(self.x - player.x, self.y - player.y)
        return distance < (self.radius + PLAYER_COLLISION_RADIUS)

    # ── Çizim ─────────────────────────────────────────────────────────────────

    def draw(self, screen: pygame.Surface) -> None:
        """
        Power-up'ı ekrana çizer.

        Görsel tasarım:
          - Dış halka (tür renginde outline)
          - Nabız (pulse) efekti: sinüs dalgasıyla iç dairenin yarıçapı değişir
          - Ömür azaldıkça renk solar (son 60 frame'de yanıp söner)
          - Tür sembolü: merkezdeki küçük iç çember
        """
        cx = int(self.x)
        cy = int(self.y)

        # Ömrün son 60 frame'inde blink efekti
        if self.lifetime < 60 and (self.lifetime // 8) % 2 == 0:
            return

        # Nabız efekti için yarıçap değişimi
        pulse = math.sin(self._pulse_counter * 0.2) * 2
        visual_r = int(self.radius + pulse)

        # Yarı saydam glow halkası (büyük, soluk)
        glow_surface = pygame.Surface((visual_r * 4, visual_r * 4), pygame.SRCALPHA)
        glow_color   = (*self.color, 50)
        pygame.draw.circle(glow_surface, glow_color,
                           (visual_r * 2, visual_r * 2), visual_r * 2)
        screen.blit(glow_surface,
                    (cx - visual_r * 2, cy - visual_r * 2))

        # Dış outline
        pygame.draw.circle(screen, self.color, (cx, cy), visual_r, 2)

        # İç küçük daire (tür belirteci)
        pygame.draw.circle(screen, self.color, (cx, cy), max(3, visual_r // 3))
