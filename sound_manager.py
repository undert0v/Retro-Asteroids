"""
sound_manager.py — Ses Yöneticisi (SoundManager)
=================================================
Oyunun tüm ses efektlerini merkezi olarak yöneten sınıf.

Tasarım kararı (Vibe Coding süreci):
  Aşama 1 ve 2'de sesler tamamen yoktu; TODO yorumları bırakıldı.
  Aşama 3'te "gerçek ses entegrasyonu" yerine önce bir yönetici
  sınıf yazıldı; bu sayede ses dosyaları olmadan oyun çökmüyor
  (graceful degradation). Dosyalar eklendikçe sistem otomatik etkinleşir.

Genişletilebilirlik (Bakım Ödevi için):
  - Müzik kanalı (background music loop) eklemek için
    play_music() / stop_music() metotları buraya eklenir.
  - Ses seviyesi kontrolü için set_volume(channel, level) eklenebilir.
  - Birden fazla aynı anda çalan ses için pygame.mixer.Channel kullanılabilir.
"""

import pygame
import os
from settings import SOUND_ENABLED, SOUND_PATHS


class SoundManager:
    """
    Oyun ses efektlerini yükler ve çalar.

    SOUND_ENABLED = False ise hiçbir ses dosyası yüklenmez;
    play() çağrıları sessizce yok sayılır. Bu sayede ses dosyaları
    olmadan geliştirme ortamında çalışmak mümkündür.

    Kullanım örneği:
        sound_mgr = SoundManager()
        sound_mgr.play("shoot")
        sound_mgr.play("explode")
    """

    def __init__(self) -> None:
        """
        Ses mikseri başlatılır ve konfigürasyondaki tüm ses dosyaları
        yüklenir. Eksik dosyalar sessizce atlanır.
        """
        self._sounds: dict[str, pygame.mixer.Sound] = {}
        self._enabled: bool = SOUND_ENABLED

        if not self._enabled:
            return

        # pygame.mixer zaten pygame.init() ile başlatılmış olabilir;
        # tekrar başlatmak zararsızdır.
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

        for sound_name, file_path in SOUND_PATHS.items():
            self._load_sound(sound_name, file_path)

    def _load_sound(self, name: str, path: str) -> None:
        """
        Tek bir ses dosyasını yükler.
        Dosya bulunamazsa uyarı yazdırır ama program çalışmaya devam eder.
        """
        if not os.path.exists(path):
            print(f"[SoundManager] Uyarı: Ses dosyası bulunamadı → {path}")
            return
        try:
            self._sounds[name] = pygame.mixer.Sound(path)
        except pygame.error as error:
            print(f"[SoundManager] Yükleme hatası ({path}): {error}")

    def play(self, sound_name: str) -> None:
        """
        Belirtilen ses efektini çalar.
        Ses devre dışıysa veya dosya yüklenemediyse hiçbir şey yapmaz.

        Args:
            sound_name: SOUND_PATHS sözlüğündeki anahtar
                        ("shoot", "explode", "game_over", "wave_up")
        """
        if not self._enabled:
            return
        sound = self._sounds.get(sound_name)
        if sound:
            sound.play()

    def set_volume(self, sound_name: str, volume: float) -> None:
        """
        Belirli bir ses efektinin ses düzeyini ayarlar.

        Args:
            sound_name: Ses anahtarı
            volume: 0.0 (sessiz) ile 1.0 (tam ses) arası değer
        """
        sound = self._sounds.get(sound_name)
        if sound:
            sound.set_volume(max(0.0, min(1.0, volume)))

    @property
    def is_enabled(self) -> bool:
        """Ses sisteminin aktif olup olmadığını döndürür."""
        return self._enabled
