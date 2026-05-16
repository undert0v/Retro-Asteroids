"""
particle.py — Parçacık Sistemi (Particle System)
=================================================
İki tür parçacık barındırır:

  1. ExplosionParticle  — Asteroid vurulduğunda oluşan patlama efekti
  2. ExhaustParticle    — Oyuncu itme (thrust) yaparken oluşan egzoz efekti

Tasarım kararı:
  Her iki tür de ortak bir BaseParticle sınıfından türetilmiştir;
  bu yapı ilerleyen aşamalarda yeni parçacık türleri eklemeyi kolaylaştırır
  (örn. mermi izi, kalkan parlaması).

Vibe Coding notu:
  Aşama 2'de tek tip Particle sınıfı vardı. Aşama 3'te egzoz parçacığı
  ihtiyacı doğunca hiyerarşik yapıya geçildi — mevcut testleri bozmadan
  yeni özellik eklemenin somut örneği.
"""

import pygame
import math
import random

from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    EXPLOSION_PARTICLE_COUNT, EXPLOSION_PARTICLE_LIFETIME,
    EXPLOSION_PARTICLE_SPEED_MIN, EXPLOSION_PARTICLE_SPEED_MAX,
    EXHAUST_PARTICLE_LIFETIME, EXHAUST_PARTICLE_SPEED,
    EXHAUST_SPREAD_ANGLE_DEG, EXHAUST_COL,
)


# ══════════════════════════════════════════════════════════════════════════════
# TEMEL PARÇACİK (BASE)
# ══════════════════════════════════════════════════════════════════════════════

class BaseParticle:
    """
    Tüm parçacık türleri için ortak arayüz.

    Alt sınıflar draw() metodunu override etmelidir;
    update() ve is_alive() tüm türler için aynı kalır.
    """

    def __init__(self, x: float, y: float,
                 vel_x: float, vel_y: float,
                 lifetime: int,
                 color: tuple[int, int, int],
                 radius: int = 2) -> None:
        self.x        = x
        self.y        = y
        self.vel_x    = vel_x
        self.vel_y    = vel_y
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.color    = color
        self.radius   = radius

    def update(self) -> None:
        """Konumu günceller, ömrü azaltır, yavaşlama uygular."""
        self.x        += self.vel_x
        self.y        += self.vel_y
        self.lifetime -= 1
        self.vel_x    *= 0.92   # Hafif yavaşlama (sürtünme simülasyonu)
        self.vel_y    *= 0.92

    def is_alive(self) -> bool:
        """Parçacığın hâlâ aktif olup olmadığını döndürür."""
        return self.lifetime > 0

    def _calculate_fade_color(self) -> tuple[int, int, int]:
        """
        Ömürle orantılı renk soldurması hesaplar.
        Tam ömürde orijinal renk; sona doğru siyaha yaklaşır.
        """
        ratio = max(0.0, self.lifetime / self.max_lifetime)
        return tuple(int(channel * ratio) for channel in self.color)

    def draw(self, screen: pygame.Surface) -> None:
        """Alt sınıflar bu metodu override etmelidir."""
        raise NotImplementedError


# ══════════════════════════════════════════════════════════════════════════════
# PATLAMA PARÇACİĞI
# ══════════════════════════════════════════════════════════════════════════════

class ExplosionParticle(BaseParticle):
    """
    Asteroid vurulduğunda üretilen kısa ömürlü parlama parçacığı.
    Ömrü azaldıkça rengi solar (fade-out).
    """

    def __init__(self, x: float, y: float,
                 color: tuple[int, int, int]) -> None:
        speed = random.uniform(EXPLOSION_PARTICLE_SPEED_MIN,
                               EXPLOSION_PARTICLE_SPEED_MAX)
        angle = random.uniform(0, math.pi * 2)
        super().__init__(
            x=x, y=y,
            vel_x=math.cos(angle) * speed,
            vel_y=math.sin(angle) * speed,
            lifetime=EXPLOSION_PARTICLE_LIFETIME,
            color=color,
            radius=random.randint(1, 3),
        )

    def draw(self, screen: pygame.Surface) -> None:
        faded_color = self._calculate_fade_color()
        pygame.draw.circle(screen, faded_color,
                           (int(self.x), int(self.y)), self.radius)


# ══════════════════════════════════════════════════════════════════════════════
# EGZOZ PARÇACİĞI (THRUSTER EXHAUST)
# ══════════════════════════════════════════════════════════════════════════════

class ExhaustParticle(BaseParticle):
    """
    Oyuncu itme (thrust) tuşuna bastığında geminin arkasından çıkan
    egzoz efekti parçacığı.

    Gemi yönünün tersine saçılır; küçük açısal rastgele sapma ile
    doğal görünüm sağlanır.

    Args:
        x, y          : Geminin kuyruğunun koordinatları
        ship_angle_deg: Geminin baktığı yön (derece); parçacık bunun tersine gider
    """

    def __init__(self, x: float, y: float, ship_angle_deg: float) -> None:
        # Gemi yönünün tam tersi + küçük rastgele sapma
        spread = random.uniform(-EXHAUST_SPREAD_ANGLE_DEG,
                                EXHAUST_SPREAD_ANGLE_DEG)
        exhaust_angle_rad = math.radians(ship_angle_deg + 180 + spread)

        super().__init__(
            x=x, y=y,
            vel_x=math.cos(exhaust_angle_rad) * EXHAUST_PARTICLE_SPEED,
            vel_y=-math.sin(exhaust_angle_rad) * EXHAUST_PARTICLE_SPEED,
            lifetime=EXHAUST_PARTICLE_LIFETIME,
            color=EXHAUST_COL,
            radius=2,
        )

    def draw(self, screen: pygame.Surface) -> None:
        faded_color = self._calculate_fade_color()
        pygame.draw.circle(screen, faded_color,
                           (int(self.x), int(self.y)), self.radius)


# ══════════════════════════════════════════════════════════════════════════════
# FABRIKA FONKSİYONLARI
# ══════════════════════════════════════════════════════════════════════════════

def create_explosion(x: float, y: float,
                     color: tuple[int, int, int]) -> list[ExplosionParticle]:
    """
    Verilen konumda patlama parçacıkları üretir.

    Args:
        x, y : Patlama merkezi
        color: Asteroid rengi — parçacıklar ebeveynin rengini miras alır

    Returns:
        ExplosionParticle listesi
    """
    return [ExplosionParticle(x, y, color)
            for _ in range(EXPLOSION_PARTICLE_COUNT)]


def create_exhaust(x: float, y: float,
                   ship_angle_deg: float) -> list[ExhaustParticle]:
    """
    Geminin kuyruğunda egzoz parçacıkları üretir.

    Args:
        x, y           : Gemi kuyruk koordinatları
        ship_angle_deg : Geminin baktığı açı (settings.EXHAUST_PARTICLE_COUNT kadar üretir)

    Returns:
        ExhaustParticle listesi
    """
    from settings import EXHAUST_PARTICLE_COUNT
    return [ExhaustParticle(x, y, ship_angle_deg)
            for _ in range(EXHAUST_PARTICLE_COUNT)]
