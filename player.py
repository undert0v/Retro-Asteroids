"""
player.py — Oyuncu (Player)
============================
Kullanıcının kontrol ettiği uzay gemisi.

Görsel: Üçgen outline (retro vektör stili).
Fizik : İvme (thrust) + sürtünme (friction) + ekran sarma (wrapping).
Özellikler:
  - Spawn koruması: başlangıçta PLAYER_INVINCIBILITY_FRAMES boyunca dokunulmaz
  - Blink efekti: dokunulmazken yanıp söner (sarı outline)
  - Egzoz parçacığı: itme sırasında geminin kuyruğundan üretilir

Bakım Güncellemesi (CSE444):
  - Power-up durumlarını takip eden timer öznitelikleri eklendi
  - Shield efekti invincibility_timer ile entegre edildi
  - Double-shot desteği için shoot() refactor edildi
  - is_invincible() hem spawn hem de kalkan durumunu kapsar
"""

import pygame
import math
from typing import TYPE_CHECKING

from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    PLAYER_ROTATION_SPEED, PLAYER_THRUST_ACCELERATION,
    PLAYER_MAX_SPEED, PLAYER_FRICTION_COEFFICIENT,
    PLAYER_COLLISION_RADIUS, PLAYER_INVINCIBILITY_FRAMES,
    PLAYER_BLINK_INTERVAL,
    DOUBLE_SHOT_SPREAD_DEG,
    CYAN, YELLOW, WHITE,
    POWERUP_SHIELD_COLOR,
)
from bullet   import Bullet
from particle import create_exhaust, ExhaustParticle

if TYPE_CHECKING:
    pass


class Player:
    """
    Kullanıcının kontrol ettiği uzay gemisi.

    Attributes:
        x, y                  : Merkez koordinatları
        angle_deg             : Geminin baktığı yön (derece; 90 = yukarı)
        vel_x, vel_y          : Hız vektörü bileşenleri
        invincibility_timer   : Spawn koruması için kalan frame sayısı
        shield_timer          : Kalkan power-up için kalan frame sayısı
        double_shot_timer     : Çift atış power-up için kalan frame sayısı
        is_thrusting          : Bu frame'de itme tuşuna basılıyor mu (egzoz için)
    """

    def __init__(self, x: float, y: float) -> None:
        self.x         = float(x)
        self.y         = float(y)
        self.angle_deg = 90.0    # Başlangıçta yukarıya bakar
        self.vel_x     = 0.0
        self.vel_y     = 0.0

        # Spawn koruması sayacı
        self.invincibility_timer = PLAYER_INVINCIBILITY_FRAMES
        self.is_thrusting        = False

        # Power-up zamanlayıcıları (0 = aktif değil)
        self.shield_timer      = 0
        self.double_shot_timer = 0

    # ── Durum Sorguları ───────────────────────────────────────────────────────

    def is_invincible(self) -> bool:
        """
        Oyuncu hasar almaz mı?

        Hem spawn koruması (invincibility_timer) hem de kalkan power-up
        (shield_timer) bu durumu etkinleştirebilir.
        """
        return self.invincibility_timer > 0 or self.shield_timer > 0

    @property
    def has_shield(self) -> bool:
        """Kalkan power-up'ı aktif mi?"""
        return self.shield_timer > 0

    @property
    def has_double_shot(self) -> bool:
        """Çift atış power-up'ı aktif mi?"""
        return self.double_shot_timer > 0

    # ── Power-Up Uygulama ────────────────────────────────────────────────────

    def apply_shield(self, duration_frames: int) -> None:
        """
        Kalkan power-up'ı uygular veya süresini yeniler.

        Args:
            duration_frames: Kalkan süresi (frame cinsinden)
        """
        self.shield_timer = max(self.shield_timer, duration_frames)

    def apply_double_shot(self, duration_frames: int) -> None:
        """
        Çift atış power-up'ı uygular veya süresini yeniler.

        Args:
            duration_frames: Çift atış süresi (frame cinsinden)
        """
        self.double_shot_timer = max(self.double_shot_timer, duration_frames)

    # ── Kontroller ────────────────────────────────────────────────────────────

    def rotate(self, direction: int) -> None:
        """
        Gemiyi döndürür.

        Args:
            direction: -1 = sola, +1 = sağa
        """
        self.angle_deg += direction * PLAYER_ROTATION_SPEED

    def apply_thrust(self) -> None:
        """
        Geminin baktığı yönde ivme uygular.
        Hız, PLAYER_MAX_SPEED ile sınırlanır.
        Aynı zamanda egzoz bayrağını True olarak işaretler.
        """
        angle_rad   = math.radians(self.angle_deg)
        self.vel_x += math.cos(angle_rad) * PLAYER_THRUST_ACCELERATION
        self.vel_y -= math.sin(angle_rad) * PLAYER_THRUST_ACCELERATION

        current_speed = math.hypot(self.vel_x, self.vel_y)
        if current_speed > PLAYER_MAX_SPEED:
            scale       = PLAYER_MAX_SPEED / current_speed
            self.vel_x *= scale
            self.vel_y *= scale

        self.is_thrusting = True

    def shoot(self) -> list[Bullet]:
        """
        Geminin burnundan mermi(ler) oluşturur ve döndürür.

        Çift atış aktifse iki mermi, aksi hâlde tek mermi döner.
        Mermi listesini ana döngüye eklemek çağıranın sorumluluğundadır.

        Bakım notu: Orijinal imza `-> Bullet` iken `-> list[Bullet]` olarak
        güncellendi. game.py'de `bullets.extend(player.shoot())` kullanılmalıdır.

        Returns:
            Bullet nesnelerinin listesi (1 veya 2 eleman)
        """
        angle_rad = math.radians(self.angle_deg)
        nose_x    = self.x + math.cos(angle_rad) * PLAYER_COLLISION_RADIUS
        nose_y    = self.y - math.sin(angle_rad) * PLAYER_COLLISION_RADIUS

        if self.has_double_shot:
            spread = DOUBLE_SHOT_SPREAD_DEG
            bullet_left  = Bullet(nose_x, nose_y, self.angle_deg + spread)
            bullet_right = Bullet(nose_x, nose_y, self.angle_deg - spread)
            return [bullet_left, bullet_right]

        return [Bullet(nose_x, nose_y, self.angle_deg)]

    def get_exhaust_particles(self) -> list[ExhaustParticle]:
        """
        Egzoz parçacıklarını üretir ve döndürür.
        Yalnızca is_thrusting == True iken çağrılmalıdır.

        Returns:
            ExhaustParticle listesi (EXHAUST_PARTICLE_COUNT kadar)
        """
        angle_rad = math.radians(self.angle_deg)
        tail_x = self.x - math.cos(angle_rad) * PLAYER_COLLISION_RADIUS * 0.7
        tail_y = self.y + math.sin(angle_rad) * PLAYER_COLLISION_RADIUS * 0.7
        return create_exhaust(tail_x, tail_y, self.angle_deg)

    # ── Güncelleme ────────────────────────────────────────────────────────────

    def update(self) -> None:
        """
        Her frame'de fizik ve sayaçları günceller.
        is_thrusting bayrağı her frame başında sıfırlanır;
        apply_thrust() çağrılırsa yeniden True yapılır.
        """
        # Sürtünme
        self.vel_x *= PLAYER_FRICTION_COEFFICIENT
        self.vel_y *= PLAYER_FRICTION_COEFFICIENT

        # Konum güncelleme
        self.x += self.vel_x
        self.y += self.vel_y

        # Ekran sarma
        self.x %= SCREEN_WIDTH
        self.y %= SCREEN_HEIGHT

        # Spawn dokunulmazlık sayacı
        if self.invincibility_timer > 0:
            self.invincibility_timer -= 1

        # Power-up zamanlayıcıları
        if self.shield_timer > 0:
            self.shield_timer -= 1
        if self.double_shot_timer > 0:
            self.double_shot_timer -= 1

        # Egzoz bayrağını sıfırla (her frame)
        self.is_thrusting = False

    # ── Çizim ─────────────────────────────────────────────────────────────────

    def _calculate_vertices(self) -> list[tuple[float, float]]:
        """
        Üçgenin üç köşe noktasını hesaplar.

        Returns:
            [(nose_x, nose_y), (left_x, left_y), (right_x, right_y)]
        """
        angle_rad = math.radians(self.angle_deg)
        size      = PLAYER_COLLISION_RADIUS

        nose_x = self.x + math.cos(angle_rad) * size
        nose_y = self.y - math.sin(angle_rad) * size

        left_angle_rad  = angle_rad + math.radians(140)
        right_angle_rad = angle_rad - math.radians(140)

        left_x  = self.x + math.cos(left_angle_rad)  * size * 0.8
        left_y  = self.y - math.sin(left_angle_rad)  * size * 0.8
        right_x = self.x + math.cos(right_angle_rad) * size * 0.8
        right_y = self.y - math.sin(right_angle_rad) * size * 0.8

        return [(nose_x, nose_y), (left_x, left_y), (right_x, right_y)]

    def draw(self, screen: pygame.Surface, frame_count: int = 0) -> None:
        """
        Gemiyi ekrana çizer.

        Dokunulmazlık süresi boyunca (spawn koruması veya kalkan) blink efekti
        uygulanır. Outline rengi:
          - Spawn koruması aktifse: sarı
          - Kalkan aktifse        : mavi (POWERUP_SHIELD_COLOR)
          - Normal                : cyan

        Args:
            screen      : Çizim yapılacak pygame yüzeyi
            frame_count : Ana döngüdeki toplam frame sayısı (blink için)
        """
        if self.is_invincible():
            if (frame_count // PLAYER_BLINK_INTERVAL) % 2 == 0:
                return

        vertices = self._calculate_vertices()

        # İç glow
        inner_vertices = [
            (self.x + (vx - self.x) * 0.45,
             self.y + (vy - self.y) * 0.45)
            for vx, vy in vertices
        ]
        pygame.draw.polygon(screen, (0, 55, 75), inner_vertices)

        # Outline rengi: öncelik sırası spawn > kalkan > normal
        if self.invincibility_timer > 0:
            outline_color = YELLOW
        elif self.has_shield:
            outline_color = POWERUP_SHIELD_COLOR
        else:
            outline_color = CYAN

        pygame.draw.polygon(screen, outline_color, vertices, 2)
