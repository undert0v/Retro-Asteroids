# 🚀 Retro Asteroids Game

**CSE444 Take-Home Exam — Vibe Coding Project (Bakım Aşaması)**
Python 3.10+ | PyGame 2.x

---

## Kurulum

### 1. Gereksinimler
- Python 3.10 veya üzeri
- pip (Python paket yöneticisi)

### 2. Bağımlılıkları Yükle
```bash
pip install pygame
```

### 3. Oyunu Çalıştır
```bash
python game.py
```

> **Not:** `highscore.txt` dosyası ilk çalıştırmada otomatik oluşturulur.  
> Ses efektleri için `assets/` klasörüne `.wav` dosyaları ekleyin (opsiyonel).

---

## Kontroller

| Tuş         | Eylem                          |
|-------------|--------------------------------|
| `←` `→`     | Gemiyi döndür                  |
| `↑`         | İtme (thrust / ivme uygula)    |
| `SPACE`     | Ateş et                        |
| `R`         | Yeniden başlat (Game Over'da)  |
| `ESC`       | Oyundan çık                    |

---

## Proje Yapısı

```
retro_asteroids/
├── game.py            # Ana döngü ve durum makinesi (State Machine)
├── settings.py        # Tüm sabitler ve GameState enum
├── player.py          # Oyuncu gemisi (hareket, ateş, egzoz, blink, power-up durumu)
├── asteroid.py        # Asteroid (screen wrapping, parçalanma, çarpışma)
├── bullet.py          # Mermi
├── particle.py        # Patlama ve egzoz parçacık sistemi
├── powerup.py         # Power-Up sistemi (Kalkan / Çift Atış / Yavaşlatma)
├── renderer.py        # Tüm ekran çizim fonksiyonları + Power-Up HUD
├── sound_manager.py   # Ses yöneticisi (graceful degradation)
├── highscore.py       # High score dosya okuma/yazma
├── README.md          # Bu dosya
└── assets/            # (Opsiyonel) Ses dosyaları klasörü
    ├── shoot.wav
    ├── explode.wav
    ├── game_over.wav
    ├── wave_up.wav
    └── powerup_collect.wav   # Yeni: power-up toplama sesi
```

---

## Oyun Özellikleri

| Özellik                        | Durum |
|-------------------------------|-------|
| Ana menü ekranı               | ✅    |
| Gemi: döndürme + ivme + sarma | ✅    |
| Ateş sistemi (cooldown)       | ✅    |
| Egzoz parçacığı efekti        | ✅    |
| Asteroidler: **screen wrapping** | ✅ |
| Asteroid parçalanması (3 boy) | ✅    |
| Daire tabanlı çarpışma tespiti| ✅    |
| Patlama parçacığı efekti      | ✅    |
| Puan sistemi (boyuta göre)    | ✅    |
| High score (dosyaya kayıt)    | ✅    |
| Wave/zorluk sistemi           | ✅    |
| Spawn koruması (blink efekti) | ✅    |
| Game Over ekranı              | ✅    |
| Ses yönetimi altyapısı        | ✅    |
| **Power-Up: Kalkan (Shield)**  | ✅   |
| **Power-Up: Çift Atış (Double Shot)** | ✅ |
| **Power-Up: Yavaşlatma (Slow-Mo)** | ✅ |
| **Power-Up HUD (kalan süre)**  | ✅   |

---

## Power-Up Sistemi

Ekranda belirli aralıklarla toplanabilir power-up nesneleri belirir. Toplama mesafesine girince otomatik aktif olur; maksimum 30 saniye sürer.

| Renk    | Tür           | Efekt                                            |
|---------|---------------|--------------------------------------------------|
| 🔵 Mavi  | Kalkan        | Gemi geçici olarak hasar almaz; mavi outline     |
| 🟣 Pembe | Çift Atış     | Her atışta iki mermi birden fırlatılır           |
| 🟢 Yeşil | Yavaşlatma    | Tüm asteroidlerin hızı %35'e düşer              |

---

## Bakım Güncellemeleri (CSE444)

1. **Screen Wrapping (Asteroid):** Asteroidler artık ekran kenarına çarptığında sekmiyor; toroidal sarma davranışıyla karşı kenardan geri giriyor.
2. **Power-Up Sistemi:** Yeni `powerup.py` modülü eklendi; üç tür güçlendirme destekleniyor.
3. **Çift Atış Refactoring:** `player.shoot()` artık `list[Bullet]` döndürüyor.
4. **Power-Up HUD:** `renderer.py`'e `render_powerup_hud()` fonksiyonu eklendi.

---

## Harici Kaynaklar

- [pygame Belgeleri](https://www.pygame.org/docs/)
- Classic Asteroids, Atari (1979) — oyun mekaniği referansı
