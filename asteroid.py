"""
asteroid.py — Asteroid
=======================
Oyunun temel engeli. Üç boyut (large / medium / small) destekler;
vurulduğunda split() ile daha küçük asteroidlere dönüşür.

Fizik (Bakım Güncellemesi — CSE444):
  - Eskiden: Ekran sınırlarında yansıma (gelen açı = giden açı)
  - Şimdi:   Toroidal (screen wrapping) davranış — bir kenardan çıkıp
             karşı kenardan girer. Mermi davranışıyla tutarlı hale getirildi.

Çarpışma:
  - Mermi ile: bullet.collides_with_asteroid() tarafından kontrol edilir
  - Oyuncu ile: collides_with_player() bu sınıf içinde tanımlıdır
"""

import pygame
import math
import random

from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    ASTEROID_SIZES, PLAYER_COLLISION_RADIUS,
    DARK_GRAY,
)


class Asteroid:
    """
    Ekranda hareket eden, ekran sarma (wrapping) uygulayan ve parçalanan engel.

    Attributes:
        x, y          : Merkez koordinatları
        size          : "large" | "medium" | "small"
        radius        : Çizim ve çarpışma yarıçapı (piksel)
        score_value   : Bu asteroid vurulunca eklenen puan
        vel_x, vel_y  : Hız vektörü bileşenleri (piksel/frame)
    """

    def __init__(self, x: float, y: float,
                 size: str = "large",
                 speed_multiplier: float = 1.0) -> None:
        """
        Args:
            x, y             : Başlangıç koordinatları
            size             : Asteroid boyutu — "large", "medium" veya "small"
            speed_multiplier : Zorluk katsayısı; wave ilerledikçe artar
        """
        self.x    = float(x)
        self.y    = float(y)
        self.size = size

        config           = ASTEROID_SIZES[size]
        self.radius      = config["radius"]
        self.color       = config["color"]
        self.score_value = config["score"]

        # Rastgele hız & yön; zorluk katsayısı uygulanır
        base_speed    = random.uniform(*config["speed_range"])
        speed         = base_speed * speed_multiplier
        direction_rad = random.uniform(0, math.pi * 2)
        self.vel_x    = math.cos(direction_rad) * speed
        self.vel_y    = math.sin(direction_rad) * speed

        # Görsel çeşitlilik: hafif yarıçap varyasyonu
        self._radius_offset = random.randint(-4, 4)

    # ── Güncelleme ────────────────────────────────────────────────────────────

    def update(self) -> None:
        """
        Konumu günceller ve ekran sarma (toroidal wrapping) uygular.

        Bakım notu: Orijinal _apply_boundary_reflection() kaldırıldı.
        Ekranın bir kenarından çıkan asteroid karşı kenardan girer;
        bu davranış mermi fiziğiyle tutarlıdır ve klasik Asteroids
        arcade oyununun orijinal davranışını yansıtır.
        """
        self.x += self.vel_x
        self.y += self.vel_y

        # Toroidal (ekran sarma) sınır davranışı
        self.x %= SCREEN_WIDTH
        self.y %= SCREEN_HEIGHT

    # ── Çarpışma ─────────────────────────────────────────────────────────────

    def collides_with_player(self, player) -> bool:
        """
        Oyuncu ile daire-tabanlı çarpışma kontrolü.
        Oyuncu dokunulmazsa (invincible) otomatik olarak False döner.

        Args:
            player: Player nesnesi (x, y, is_invincible() olmalı)

        Returns:
            True → çarpışma var ve geçerli; False → yok veya dokunulmaz
        """
        if player.is_invincible():
            return False
        distance = math.hypot(self.x - player.x, self.y - player.y)
        # Oyuncunun tam yarıçapı yerine %75'i kullanılır: biraz affedici his
        effective_player_radius = PLAYER_COLLISION_RADIUS * 0.75
        return distance < (self.radius + effective_player_radius)

    # ── Parçalanma ────────────────────────────────────────────────────────────

    def split(self, speed_multiplier: float = 1.0) -> list["Asteroid"]:
        """
        Asteroidi boyutuna göre daha küçük parçalara böler.

        Davranış:
          - large  → 2 adet medium asteroid
          - medium → 2 adet small asteroid
          - small  → boş liste (tamamen yok olur)

        Çocuk asteroidler ebeveynin konumundan küçük bir ofsetle doğar;
        bu üst üste binme (overlap) görünümünü önler.

        Args:
            speed_multiplier: Mevcut wave'in zorluk katsayısı

        Returns:
            Yeni Asteroid nesneleri listesi (boş olabilir)
        """
        config         = ASTEROID_SIZES[self.size]
        children_count = config["children"]

        if children_count == 0:
            return []

        size_progression = {"large": "medium", "medium": "small"}
        next_size        = size_progression[self.size]
        child_radius     = ASTEROID_SIZES[next_size]["radius"]

        children = []
        for _ in range(children_count):
            offset_x = random.uniform(-child_radius, child_radius)
            offset_y = random.uniform(-child_radius, child_radius)
            child    = Asteroid(
                x=self.x + offset_x,
                y=self.y + offset_y,
                size=next_size,
                speed_multiplier=speed_multiplier,
            )
            children.append(child)
        return children

    # ── Çizim ─────────────────────────────────────────────────────────────────

    def draw(self, screen: pygame.Surface) -> None:
        """
        Asteroidi ekrana çizer: dış halka + iç detay çemberi.

        Görsel tasarım notu:
          Daireler kasıtlı olarak dolu (filled) değil, çizgi (outline) olarak
          çizilmiştir; bu retro vektör oyun estetiğini yansıtır.
        """
        center_x = int(self.x)
        center_y = int(self.y)
        visual_r = self.radius + self._radius_offset

        # Dış halka (outline)
        pygame.draw.circle(screen, self.color,
                           (center_x, center_y), visual_r, 2)

        # İç detay çemberi (boyutu yeterince büyükse)
        if visual_r > 15:
            inner_radius = visual_r // 3
            pygame.draw.circle(screen, DARK_GRAY,
                               (center_x, center_y), inner_radius, 1)
