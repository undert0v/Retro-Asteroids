"""
bullet.py — Mermi (Bullet)
===========================
Oyuncunun ateş ettiği projektil.

Genişletilebilirlik notu (Bakım Ödevi için):
  Bu sınıf ileride bir BaseProjectile temel sınıfı haline getirilebilir.
  Farklı silah türleri (SpreadShot, LaserBeam, HomingMissile) bu temel sınıftan
  türetilebilir; game.py'deki çarpışma mantığı değişmez.
"""

import pygame
import math

from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    BULLET_SPEED, BULLET_LIFETIME_FRAMES, BULLET_RADIUS,
    ORANGE, WHITE,
)


class Bullet:
    """
    Geminin burnundan fırlatılan ve belirli bir süre sonra kaybolan mermi.

    Fizik: Sabit hız, ekran sarma, ömür sayacı.
    Çarpışma: Daire-tabanlı mesafe kontrolü (collides_with_asteroid).
    """

    def __init__(self, x: float, y: float, angle_deg: float) -> None:
        """
        Args:
            x, y      : Başlangıç koordinatları (genellikle geminin burnu)
            angle_deg : Geminin baktığı açı (derece); mermi bu yönde hareket eder
        """
        self.x = x
        self.y = y

        angle_rad  = math.radians(angle_deg)
        self.vel_x =  math.cos(angle_rad) * BULLET_SPEED
        self.vel_y = -math.sin(angle_rad) * BULLET_SPEED   # pygame y ekseni ters

        self.lifetime     = BULLET_LIFETIME_FRAMES
        self.max_lifetime = BULLET_LIFETIME_FRAMES

    # ── Güncelleme ────────────────────────────────────────────────────────────

    def update(self) -> None:
        """Konumu günceller, ömrü azaltır, ekran sarma uygular."""
        self.x        += self.vel_x
        self.y        += self.vel_y
        self.lifetime -= 1
        self.x        %= SCREEN_WIDTH
        self.y        %= SCREEN_HEIGHT

    def is_alive(self) -> bool:
        """Mermi hâlâ aktif mi?"""
        return self.lifetime > 0

    # ── Çarpışma ─────────────────────────────────────────────────────────────

    def collides_with_asteroid(self, asteroid) -> bool:
        """
        Daire-daire çarpışma tespiti.
        Dikdörtgen (Rect) yerine mesafe hesabı kullanılır; daha gerçekçi sonuç verir.

        Args:
            asteroid: Asteroid nesnesi (x, y, radius öznitelikleri olmalı)

        Returns:
            True → çarpışma var; False → yok
        """
        distance = math.hypot(self.x - asteroid.x, self.y - asteroid.y)
        return distance < (BULLET_RADIUS + asteroid.radius)

    # ── Çizim ─────────────────────────────────────────────────────────────────

    def draw(self, screen: pygame.Surface) -> None:
        """
        Mermiyi ekrana çizer.
        Dış turuncu daire + iç beyaz parlama noktası.
        """
        pygame.draw.circle(screen, ORANGE,
                           (int(self.x), int(self.y)), BULLET_RADIUS)
        pygame.draw.circle(screen, WHITE,
                           (int(self.x), int(self.y)), 1)
