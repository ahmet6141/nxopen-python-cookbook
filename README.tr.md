# NXOpen Python Cookbook

> 🌐 [English](README.md) · **Türkçe**

> NXOpen Python API ile **headless Siemens NX journaling** için doğrulanmış, kopyala-kullan reçeteler ve zorlu yoldan öğrenilmiş tuzaklar.

İnternetteki NXOpen içeriğinin çoğu interaktif GUI için yazılmıştır ve "bir journal kaydet, üstünde oyna" seviyesinde kalır. Bu cookbook farklı: hedefi **tamamen headless, parametrik, toplu (batch) geometri üretimi** — CAD'i koddan ürettiğinizde (parametre → blueprint → katı model) ve döngüde insan olmadığında ihtiyaç duyduğunuz iş akışı; `run_journal.exe` ile sürülür.

Buradaki her reçete, gerçek bir NX kurulumuna karşı (sürüm **NX 2506**, Continuous Release serisi) headless journal'lar çalıştırılıp ortaya çıkan `.prt` incelenerek **canlı doğrulandı** — sürümünüz için eski ya da yanlış olabilecek dokümanlardan kopyalanmadı. Yaygın kullanılan bir API imzasının yanlış çıktığı yerde, düzeltme ve kanıtı belgelendi.

## Neden var

NX'i Python'dan otomatikleştirmek güçlüdür ama API büyük, headless kullanım için az belgelenmiş ve yalnızca çalışma anında ortaya çıkan tuzaklarla dolu — sessizce kopuk gövde üreten bir builder, başarı raporlayıp asla birleşmeyen bir boolean, tüm oturumu zehirleyen bir export. Bunların her biri teşhisi saatler alan sorunlar. Bu repo, keşke elimde olsaydı dediğim referanstır.

## İçindekiler

| Doküman | İçerik |
|---------|--------|
| [docs/tr/00-getting-started.md](docs/tr/00-getting-started.md) | NX kurulumu, journal'ları headless vs. GUI çalıştırma, otomatik tamamlama için Python stub'ları, ortam notları |
| [docs/tr/01-core-api.md](docs/tr/01-core-api.md) | Session/Part yaşam döngüsü, expression'lar, extrude, revolve, section'lar, curve'ler, boolean'lar, zorunlu update döngüsü, gövde adlandırma, STEP/Parasolid export |
| [docs/tr/02-verified-recipes.md](docs/tr/02-verified-recipes.md) | 11 kopyala-kullan reçete: edge blend, chamfer, draft, symbolic thread, shell, mirror body, hole package, malzeme atama, kütle özellikleri, PMI notları |
| [docs/tr/03-pitfalls.md](docs/tr/03-pitfalls.md) | Derlenmiş tuzak listesi — belirti → çözüm biçiminde 29 çalışma-anı hatası |
| [docs/tr/04-boolean-and-geometry-rules.md](docs/tr/04-boolean-and-geometry-rules.md) | Prosedürel modelleme için güvenilir-boolean kuralları: neyin gerçekten kaynadığı, sessiz öksüz gövdelerin nasıl tespit edileceği, vertex tabanlı bounding box |
| [docs/tr/05-capability-inventory.md](docs/tr/05-capability-inventory.md) | Feature fabrikalarının, bağımsız boolean/move builder'larının, montaj kısıtlarının, tam export listesinin, helix/spline, renk & niteliklerin stub-taranmış envanteri |
| [docs/tr/06-resources.md](docs/tr/06-resources.md) | Topluluk siteleri, açık kaynak kütüphaneler ve yer imine değer resmi referanslar |
| [docs/tr/07-freeform-lofting.md](docs/tr/07-freeform-lofting.md) | Sketch'siz spline'lar, Through-Curves lofting, bir loft'u tek veya iki noktaya kapatma, isimle sağlam datum arama, kendi kendini temizleyen tekrar-çalıştırılabilir üreticiler, parametrik Expression okuma/geri-yazma, Boolean-Intersect hacim doğrulama |
| [docs/tr/08-primitives-sweeps-and-surfacing.md](docs/tr/08-primitives-sweeps-and-surfacing.md) | Block/silindir/koni/küre primitifleri, 3B yol boyunca tube, Swept, Ruled, sheet iş akışı (thicken/sew), trim & split, hangi-araç karar tablosu *(referans katmanı — banner'a bak)* |
| [docs/tr/09-sketches-patterns-and-feature-editing.md](docs/tr/09-sketches-patterns-and-feature-editing.md) | Headless sketch ne zaman değer ve minimal kalıbı, doğrusal/dairesel Pattern Feature, gövde ölçekleme & kopyalama, var olan feature'ları suppress etme/yeniden parametrelendirme/silme *(referans katmanı — banner'a bak)* |
| [docs/tr/10-selecting-geometry-without-a-mouse.md](docs/tr/10-selecting-geometry-without-a-mouse.md) | Programatik seçim: topoloji gezintisi, yüzey/kenar sınıflandırma, üst-yüzeyi-bul yardımcıları, vertex bounding box, isimler/nitelikler/katmanlar, ölçüm, neden `FindObject` değil *(referans katmanı — banner'a bak)* |

Çalıştırılabilir örnek: [examples/block_with_boss.py](examples/block_with_boss.py) — bir block + boss kurar, edge blend ve chamfer uygular, çelik atar, kütle ölçer ve STEP dışa aktarır; yalnızca bu repodaki reçeteleri kullanır.

## Hızlı başlangıç

```powershell
# NX kurulumunu işaret et ve bir journal'ı headless çalıştır (GUI gerekmez):
$env:UGII_ROOT_DIR = "C:\Program Files\Siemens\NX2506\NXBIN"   # kendi kurulumuna göre ayarla
& "$env:UGII_ROOT_DIR\run_journal.exe" examples\block_with_boss.py -args out.prt
```

Bir headless journal, GUI zaten açıkken bile temiz bir **ikinci** NX oturumu açar — yerel bir lisans için çakışma olmaz. Bkz. [docs/tr/00-getting-started.md](docs/tr/00-getting-started.md).

## Kapsam & dürüstlük

- **İki güven katmanı.** 00–07 dokümanları NX 2506'da **canlı doğrulandı**. 08–10 dokümanları **referans katmanıdır**: API referansından, kayıtlı-journal kalıplarından ve topluluk örneklerinden derlendi, henüz-doğrulanmadı diye açıkça banner'landı — birini çalıştır, doğrula, bir PR onu terfi ettirir.
- **Sürüm:** her şey NX 2506'da kanıtlandı. NXOpen sürümler arası değişir; imzalar değiştiğinde işaretlenmiştir ama daima kendi sürümünüzde doğrulayın. Emin değilseniz yerel stub'larınızı tarayın (`.../UGOPEN/pythonStubs/`) — oradaki imzalar tam kurulumunuzla eşleşir.
- **Siemens ile bağlantılı değildir.** NX, NXOpen ve Parasolid, Siemens Digital Industries Software'in ticari markalarıdır. Bu, bağımsız bir topluluk referansıdır.
- **Garanti yok.** Bu reçeteler CAD geometrisini değiştirir ve dosyaların üzerine yazabilir. Çalıştırmadan önce okuyun.

## Bu projeye destek

Bu ücretsiz bir bilgidir ve en iyi destek hiçbir maliyet gerektirmez:

- ⭐ Zaman kazandırdıysa repoyu **yıldızla** — projenin istediği tek ödül bu.
- 👀 Yeni reçeteleri ve sürüm notlarını yakalamak için **izle / takip et**.
- 🔧 Doğrulanmış bir reçete ya da sürüme özel bir düzeltme **katkıla** (bkz. [CONTRIBUTING.md](CONTRIBUTING.md)) — en değerli destek budur.
- 🔗 NX otomatikleştiren herkesle **paylaş** ya da bir NX topluluk başlığından bağlantı ver.

> Bağış yok, sponsorluk yok — bu repoda bilinçli olarak hiçbiri yok. Prosedürel/parametrik CAD işinde iş birliği yapmak istersen bir issue aç ya da bir discussion başlat.

## Lisans

[MIT](LICENSE) — özgürce kullan, atıf makbule geçer.

## Katkı

Düzeltmeler ve sürüme özgü notlar çok makbule geçer — bkz. [CONTRIBUTING.md](CONTRIBUTING.md). Bir reçete sizin NX sürümünüzde farklı davranıyorsa, sürüm ve tam hata metniyle bir issue açın; bu repo tam da bu tür bilgiyi toplamak için var.
