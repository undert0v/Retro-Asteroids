# CSE444 — Retro Asteroids: Bakım Raporu
## Software Maintenance and Evolution — Maintenance Phase Report

---

# BÖLÜM 1: GİRİŞ

## 1.1 Orijinal Proje Tanımı

Bu rapor, daha önce "Vibe Coding" yaklaşımıyla geliştirilen Retro Asteroids oyununun
**CSE444 Software Maintenance and Evolution** dersi kapsamında gerçekleştirilen
bakım ve geliştirme sürecini belgelemektedir.

Orijinal sistem, klasik Atari Asteroids (1979) oyununun modern Python/PyGame yorumudur.
Modüler bir mimariye sahiptir: `game.py` durum makinesini yönetirken `player.py`,
`asteroid.py`, `bullet.py`, `particle.py`, `renderer.py`, `sound_manager.py`
ve `highscore.py` ayrı sorumlulukları üstlenir. Orijinal geliştirme "Önce Çalışır,
Sonra Düzelt" ilkesiyle üç aşamada tamamlanmıştır.

## 1.2 Bakım Aşamasının Hedefleri

Bu bakım aşamasında iki temel hedef belirlenmiştir:

1. **Sınır Davranışı Güncellemesi:** Asteroidlerin ekran kenarında sekme
   (bounce/reflection) davranışını kaldırarak toroidal ekran sarma (screen wrapping)
   ile değiştirmek. Bu değişiklik mevcut mermi davranışıyla tutarlılık sağlar ve
   orijinal Atari Asteroids mekaniğine daha sadık bir oynanış sunar.

2. **Power-Up Sistemi Eklenmesi:** Üç farklı güçlendirme türü (Kalkan, Çift Atış,
   Yavaşlatma) içeren toplanabilir nesne sistemi oluşturmak. Her power-up en fazla
   30 saniye aktif kalır.

Tüm değişiklikler mevcut modüler mimariyi koruyarak, yeni `powerup.py` modülü
eklenerek ve orijinal `game.py`'nin "Separation of Concerns" ilkesine bağlı yapısı
bozulmadan gerçekleştirilmiştir.

---

# BÖLÜM 2: FONKSİYONEL GEREKSİNİMLER

Aşağıdaki gereksinimler mevcut orijinal sistemin gereksinimlerini (FR-01 – FR-35)
**genişletir**. Yeni gereksinimler FR-36'dan başlar; değiştirilen gereksinimler
"Güncellendi" olarak işaretlenmiştir.

## 2.1 Screen Wrapping (Sınır Davranışı) — Güncelleme

**FR-16 (Güncellendi)** Asteroidler ekran sınırlarına çarptığında **yansıma
yapmayacak**; ekranın bir kenarından çıkıp **karşı kenardan (opposite side)
geri girecektir** (toroidal ekran sarma — screen wrapping).

**FR-37** Bullet sınıfı zaten screen wrapping uyguladığından ek değişiklik
gerekmez; mevcut `self.x %= SCREEN_WIDTH` mantığı korunur.

**FR-38** Power-up nesneleri de screen wrapping davranışı göstermelidir.

## 2.2 Power-Up Sistemi — Yeni

**FR-39** Oyun, `PLAYING` durumunda belirli aralıklarla ekranın rastgele bir
noktasında power-up nesnesi üretmelidir (`POWERUP_SPAWN_INTERVAL_FRAMES`).

**FR-40** Her spawn döneminde power-up türü üç seçenekten rastgele belirlenmelidir:
Kalkan (`shield`), Çift Atış (`double_shot`), Yavaşlatma (`slow_mo`).

**FR-41** Power-up nesneleri ekranda en fazla `POWERUP_LIFETIME_FRAMES` (10 saniye)
kalmalı; toplanmazsa kendiliğinden kaybolmalıdır.

**FR-42** Oyuncu bir power-up nesnesinin üzerine girdiğinde (daire-tabanlı
çarpışma tespiti) nesne otomatik olarak toplanmalı ve efekt aktive edilmelidir.

**FR-43** Her power-up efekti en fazla 30 saniye (`POWERUP_MAX_DURATION_FRAMES`)
aktif kalmalı; süre dolunca efekt sona ermelidir.

**FR-44** Aynı tür power-up tekrar toplanırsa mevcut süre yeniden başlatılmalıdır
(yani süre uzar veya en uzun değer korunur).

**FR-45** Kalkan (Shield) power-up'ı aktifken oyuncu asteroid çarpışmalarından
hasar almamalıdır. Mevcut `invincibility_timer` mantığı bu efekti desteklemek
üzere genişletilmelidir.

**FR-46** Çift Atış (Double Shot) power-up'ı aktifken oyuncu her `SPACE` tuşuna
basışında iki mermi birden ateşlemelidir. Mermi çiftleri hafif açısal saçılma
(`DOUBLE_SHOT_SPREAD_DEG`) ile fırlatılmalıdır.

**FR-47** Yavaşlatma (Slow-Mo) power-up'ı aktive edildiğinde ekrandaki tüm
asteroidlerin hızı `SLOWMO_ASTEROID_FACTOR` katsayısıyla anlık azaltılmalıdır.
Süre dolduğunda orijinal hızlar geri yüklenmelidir.

**FR-48** Aktif power-up'lar ve kalan süreleri oyun sırasında HUD'da görünür
ilerleme çubukları şeklinde gösterilmelidir.

**FR-49** Power-up toplama anında ses efekti çalınmalıdır ("powerup_collect");
dosya mevcut değilse `SoundManager` graceful degradation yaparak sessizce
devam etmelidir.

**FR-50** Power-up görsel efekti son 60 frame içinde yanıp sönerek oyuncuyu
yakında kaybolacağı konusunda uyarmalıdır.

---

# BÖLÜM 3: YAKLAŞIM (VİBE CODİNG & BAKIM SÜRECİ)

## 3.1 Kod Tabanının Analizi

Bakım aşamasına başlamadan önce mevcut kod tabanı analiz edildi. Aşağıdaki
tespitler yapıldı:

**Güçlü Yönler:**
- `GameState` enum yapısı yeni durumlar için kolayca genişletilebilir.
- `BaseParticle` hiyerarşisi yeni görsel nesneler için model olabilir.
- `SoundManager`'ın graceful degradation yapısı kolayca genişletilebilir.
- `settings.py`'nin merkezi sabit yönetimi yeni parametreler için hazır.

**Bakım Fırsatları:**
- `Asteroid._apply_boundary_reflection()` metodu tamamen değiştirilebilir
  düzeyde izole edilmiş; yansıma → sarma geçişi minimal etkiyle yapılabilir.
- `player.shoot()` metodunun tek `Bullet` döndürmesi, çift atış özelliği
  için bir refactoring fırsatı sunuyor.
- `game.py`'nin durum sözlüğü yapısı (`initialise_game_state()`) yeni
  zamanlayıcı anahtarları eklemeye uygun.

## 3.2 Screen Wrapping Geçişi

Screen wrapping değişikliği gerçek anlamda minimal bir bakım müdahalesidir.
`Asteroid.update()` metodundaki tek `_apply_boundary_reflection()` çağrısı
`self.x %= SCREEN_WIDTH` ve `self.y %= SCREEN_HEIGHT` satırlarıyla değiştirildi;
`_apply_boundary_reflection()` metodu tamamen kaldırıldı.

Bu değişiklik oyun hissini anında dönüştürdü: asteroidler artık köşelere
sıkışmak yerine ekranı özgürce kat ediyor. Vibe coding perspektifinden
bu, "yanlış hissettiren" bir mekaniğin "doğru hissettiren" bir mekaniğe
dönüştürülmesidir; kod satırı sayısı azaldı, oynanış kalitesi arttı.

## 3.3 Power-Up Sistemi: Aşamalı Geliştirme

Power-up sistemini doğrudan `game.py`'ye gömmek yerine aşamalı yaklaşım
benimsendi:

**Aşama A — Veri Modeli (powerup.py):**
İlk olarak `PowerUp` sınıfı oluşturuldu: konum, tür, ömür, çizim.
Bu aşamada hiçbir efekt kodlanmadı; sadece "ekranda görünen bir şey" vardı.
Görsel doğrulama sonrası sonraki adıma geçildi.

**Aşama B — Spawn ve Collect (game.py):**
`spawn_random_powerup()` ve `handle_powerup_collisions()` fonksiyonları eklendi.
Efekt kodu henüz stubdu: `print(f"Collected: {pu.kind}")`. Toplama mantığının
çalıştığı görsel olarak doğrulandı.

**Aşama C — Efekt Entegrasyonu:**
Her efekt sırayla eklendi:
1. Double Shot → `player.shoot()` refactor
2. Shield → `player.apply_shield()` + `is_invincible()` genişletme
3. Slow-Mo → hız vektörü ölçekleme + geri yükleme

**Aşama D — HUD:**
`renderer.py`'ye `render_powerup_hud()` eklendi.

Bu aşamalı yaklaşım, her adımda çalışır durumda bir oyun sağladı.

## 3.4 Karşılaşılan 3 Ana Zorluk ve Çözümleri

### Zorluk 1: `player.shoot()` İmza Değişikliği

**Problem:** Orijinal `shoot()` metodu tek `Bullet` döndürüyordu.
`game.py`'de `bullets.append(player.shoot())` şeklinde kullanılıyordu.
Çift atış için `list[Bullet]` döndürülmesi gerekince bu çağrı kırıldı.

**Çözüm:** `shoot()` refactor edilerek `list[Bullet]` döndürmesi sağlandı.
`game.py`'deki `append()` çağrısı `extend()` ile değiştirildi. Bu tek satırlık
değişiklik hem geriye dönük uyumluluğu korudu (tek mermi hâlâ bir elemanlı
liste) hem de çift atışı destekledi.

**Vibe Coding Refleksiyonu:** "Büyük refactoring değil, minimal değişiklik"
ilkesi burada tam anlamıyla uygulandı.

### Zorluk 2: Slow-Motion Hız Geri Yükleme

**Problem:** Slow-mo efekti asteroid hız vektörlerini anlık ölçekledi.
Ancak wave geçişinde yeni asteroidler spawn olduğunda orijinal hızların
ne olduğu bilgisi kayboluyordu. Dahası, slow-mo aktifken ikinci kez
toplanırsa asteroidler iki kez yavaşlıyor ve neredeyse duruyordu.

**Çözüm:** Her asteroid nesnesine `_orig_vel_x` ve `_orig_vel_y` öznitelikleri
eklendi. Slow-mo tekrar toplanırsa önce geri yükleme, sonra yeniden ölçekleme
yapıldı. Wave geçişinde yeni asteroidler orijinal hızda doğduğundan sorun
kendiliğinden ortadan kalktı.

**Vibe Coding Refleksiyonu:** İki iterasyon gerekti. İlk denemede timer
doğruydu ama hızlar çift yavaşlıyordu; "iyi oynamayan" bir his
refactoring kararını tetikledi.

### Zorluk 3: Power-Up HUD ile Player Bağlantısı

**Problem:** Slow-mo zamanlayıcısı `game.py`'de yönetilirken kalkan ve çift
atış zamanlayıcıları `player.py`'de. `render_powerup_hud()` fonksiyonu
her ikisine de erişmek için iki farklı kaynağa bağımlı olmak durumundaydı.

**Çözüm:** Slow-mo zamanlayıcısı `game.py`'deki `game["slow_mo_timer"]`
değişkeninin yanı sıra `player.slow_mo_timer` özniteliğine de yansıtıldı.
Bu sayede `render_powerup_hud()` yalnızca `player` nesnesine ihtiyaç duydu
ve `game` sözlüğüne bağımlılık oluşmadı. `getattr(player, "slow_mo_timer", 0)`
ile graceful erişim sağlandı.

---

# BÖLÜM 4: UYGULAMA GENEL BAKIŞI

## 4.1 Değiştirilen / Eklenen Modüller

```
powerup.py    (YENİ)   PowerUp sınıfı; spawn, draw, collision, wrapping
settings.py   (GELİŞT) Power-up sabitleri, renkler, DOUBLE_SHOT_SPREAD_DEG
asteroid.py   (GELİŞT) _apply_boundary_reflection kaldırıldı → screen wrapping
player.py     (GELİŞT) shield/double_shot/slow_mo timer; shoot() refactor
game.py       (GELİŞT) spawn/collect/timer mantığı; slow-mo hız yönetimi
renderer.py   (GELİŞT) render_powerup_hud() eklendi
sound_manager (MIN)    powerup_collect anahtarı SOUND_PATHS'a eklendi
```

## 4.2 powerup.py Mimarisi

`PowerUp` sınıfı `BaseParticle` hiyerarşisinden **türetilmedi** — kasıtlı
bir tasarım kararı. Power-up'lar parçacıktan çok "oyun nesnesi" (game entity)
niteliğindedir: uzun ömürlüdür, çarpışma mantığı taşır ve toplanabilir.
`BaseParticle` kısa ömürlü görsel efektler için tasarlanmıştı; bu iki sorumluluk
birbirinden ayrı tutularak "Single Responsibility Principle" korundu.

## 4.3 Screen Wrapping Değişikliğinin Kapsamı

| Bileşen     | Orijinal Davranış   | Yeni Davranış        | Değişen Satır Sayısı |
|-------------|---------------------|----------------------|---------------------|
| Asteroid    | Sınırda yansıma     | `x %= SCREEN_WIDTH`  | ~15 silindi, 2 eklendi |
| Bullet      | Screen wrapping (✓) | Değişmedi            | 0                   |
| PowerUp     | Yok (yeni modül)    | Screen wrapping      | —                   |
| Player      | Screen wrapping (✓) | Değişmedi            | 0                   |

## 4.4 Ses Sistemi Genişletmesi

`SOUND_PATHS` sözlüğüne `"powerup_collect": "assets/powerup_collect.wav"` eklendi.
`SoundManager` değişmedi — graceful degradation otomatik olarak yeni anahtarı
kapsar. Dosya yoksa oyun çökmez, sessizce devam eder.

---

# BÖLÜM 5: TARTIŞMA VE YANSIMALAR

## 5.1 Teknik Değişikliklerin Özeti

**Screen Wrapping:** Yansıma fiziği yerine modüler aritmetik kullanmak hem kodu
kısalttı hem de orijinal Asteroids mekaniğine daha sadık bir sonuç verdi.
Asteroidler artık ekranın herhangi bir noktasında bulunabilir; oyuncu tüm ekranı
kontrol etmek zorunda.

**shoot() Refactoring:** Dönüş tipini `Bullet → list[Bullet]` değiştirmek kırıcı
bir değişiklik (breaking change) olabilirdi. `extend()` geçişi bu riski sıfırladı.
Eski davranış hâlâ mevcut: tek mermi durumunda bir elemanlı liste döner.

**Slow-Mo Hız Yönetimi:** Hız vektörlerini doğrudan ölçeklemek yerine ayrı bir
"yavaş hız" değişkeni tutmak da bir seçenekti. Doğrudan ölçekleme tercih edildi;
çünkü asteroid nesnelerinin hâlihazırda `vel_x/vel_y` taşıması ve dışarıdan
okuma yapılmaması bu yaklaşımı güvenli kıldı.

## 5.2 Orijinal Sistemle Uyumluluk

Yapılan değişiklikler orijinal API'yi büyük ölçüde korudu:

- `Asteroid` sınıfı aynı `__init__` imzasına sahip.
- `Player` sınıfı `shoot()` dışında aynı arayüzü sunar.
- `renderer.py` fonksiyonlarının imzaları değişmedi; `render_powerup_hud()`
  yalnızca eklendi.
- `GameState` enum değerleri korundu.
- `highscore.py` ve `sound_manager.py` değişmedi.

Geriye dönük uyumsuzluk yalnızca `player.shoot()` dönüş tipindedir:
`Bullet` yerine `list[Bullet]`. Bu değişiklik `game.py` dışında herhangi
bir modülü etkilemez çünkü `shoot()` yalnızca `game.py` içinde çağrılıyordu.

## 5.3 Yazılım Bakımı Üzerine Öğrenilen Dersler

**"Separation of Concerns" Bileşik Etki (Compound Effect):**
Orijinal modüler yapı, bakım maliyetini önemli ölçüde düşürdü. `asteroid.py`'deki
tek metod değişikliği (`_apply_boundary_reflection` kaldırma) diğer hiçbir modülü
etkilemedi. `powerup.py`'nin bağımsız bir modül olarak eklenmesi `game.py`'yi
yalnızca 3 yeni fonksiyon çağrısıyla genişletti.

Bakım aşamasında açıkça gözlemlendi: iyi izole edilmiş modüller, yeni özellik
eklemeyi "hepsini baştan yazma" gerektirmeyen küçük, güvenli adımlara dönüştürür.

**Zamanlayıcı Yönetiminin Merkezileştirilmesi:**
Power-up zamanlayıcılarının bir kısmı `player.py`'de, bir kısmı `game.py`'de
tutuldu. Bu hafif bir tutarsızlık yarattı (Zorluk 3). İleride tüm oyun durumu
zamanlayıcılarını tek bir yerde (örn. `game["timers"]` sözlüğünde) toplamak
bakım kolaylığı sağlayabilir.

## 5.4 Sürdürülebilirlik ve Genişletilebilirlik

**Yeni Power-Up Eklemek:** Yalnızca şu adımlar yeterli:
1. `settings.py`'de `POWERUP_KINDS` listesine yeni sabit ekle.
2. `powerup.py`'de `POWERUP_COLOR_MAP` ve `POWERUP_LABEL_MAP`'e değer ekle.
3. `game.py`'deki `handle_powerup_collisions()` içine `elif pu.kind == ...` bloğu ekle.

**Yeni Sınır Davranışı:** Screen wrapping → yansıma geri dönüşü gerekirse
`asteroid.py`'de yalnızca `update()` metodu değiştirilir; başka modül etkilenmez.

**Dinamik Zorluk:** `SLOWMO_ASTEROID_FACTOR`, `POWERUP_SPAWN_CHANCE` gibi tüm
eşik değerleri `settings.py`'de merkezi konumda; oyun dengesi (game balance)
ayarlaması için tek dosyayı düzenlemek yeterli.

## 5.5 Olası Gelecekteki İyileştirmeler

- **Can Sistemi (Lives):** Kalkan power-up'ı tek seferlik hasar korumasına
  dönüştürülerek `lives` sayacıyla ilişkilendirilebilir.
- **Power-Up Birleşimi:** Aynı anda birden fazla power-up aktif olduğunda
  görsel öncelik sırası (`shield > double_shot > normal`) genişletilebilir.
- **Mıknatıs Efekti:** Oyuncuya yaklaşan power-up'lar için hafif çekim
  (attraction) kuvveti eklenebilir; `PowerUp.update()` metodunda
  player koordinatlarına göre yön vektörü hesaplanır.
- **Power-Up Puanı:** Bazı power-up'lar toplanınca bonus puan verebilir;
  `handle_powerup_collisions()` score_gained döndürecek şekilde genişletilebilir.
- **Animasyonlu Power-Up İkonu:** `powerup.py` içine SVG benzeri basit
  şekil çizimi (kare, üçgen, yıldız) tür ayrımını renkten daha belirgin kılar.

---

*Rapor Sonu — CSE444 Software Maintenance and Evolution, Mayıs 2026*
