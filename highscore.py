"""
highscore.py — Yüksek Skor Kalıcılığı (High Score Persistence)
===============================================================
Yüksek skoru bir metin dosyasına okuyup yazan yardımcı modül.

Tasarım kararı:
  Basit düz metin dosyası yeterlidir; veritabanı veya JSON gereksiz yük.
  Dosya bozulursa veya yoksa varsayılan değer (0) döner — hata toleranslı.
"""

import os
from settings import HIGH_SCORE_FILE


def load_high_score() -> int:
    """
    Yüksek skoru dosyadan okur.
    Dosya yoksa veya bozuksa 0 döner.

    Returns:
        Kaydedilmiş yüksek skor (tamsayı)
    """
    if not os.path.exists(HIGH_SCORE_FILE):
        return 0
    try:
        with open(HIGH_SCORE_FILE, "r", encoding="utf-8") as file_handle:
            content = file_handle.read().strip()
            return int(content)
    except (ValueError, IOError):
        return 0


def save_high_score(score: int) -> None:
    """
    Yüksek skoru dosyaya kaydeder.
    Yazma hatası olursa sessizce devam eder (oyun çökmez).

    Args:
        score: Kaydedilecek skor değeri
    """
    try:
        with open(HIGH_SCORE_FILE, "w", encoding="utf-8") as file_handle:
            file_handle.write(str(score))
    except IOError as error:
        print(f"[HighScore] Kayıt hatası: {error}")
