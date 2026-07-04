> 🌐 [English](../00-getting-started.md) · **Türkçe**

# 00 · Headless NX Journaling'e Başlarken

## "Headless journaling" ne anlama gelir

Bir **journal**, NX'i NXOpen API üzerinden yöneten bir Python (veya VB/C#) betiğidir. NX bir journal'ı iki şekilde çalıştırabilir:

1. **Headless / batch** — `run_journal.exe script.py -args ...`. GUI penceresi yoktur; NX geometri çekirdeğini yükler, betiğinizi çalıştırır ve çıkar. Bu cookbook'un hedeflediği iş akışı budur: parametreler girer, `.prt`/STEP çıkar, tamamen otomatik.
2. **Interaktif oynatma** — NX GUI içinde `Tools → Journal → Play` (veya `Alt+F8`) üzerinden. Adım adım ilerlemek ve gerçekten grafik penceresine ihtiyaç duyan her şey için kullanışlıdır (aşağıdaki PNG notuna bakın).

## Ortam

| Konu | Notlar |
|-------|-------|
| **NX sürümü** | Bu cookbook **NX 2506** (Continuous Release) üzerinde doğrulanmıştır. Davranış sürümler arasında farklılık gösterir — kendi sürümünüzde doğrulayın. |
| **Python** | NX, **hiçbir üçüncü parti paket içermeyen**, **gömülü (embedded)** bir Python 3.10 ile birlikte gelir. NX yorumlayıcısına `pip install` yapamazsınız; journal içinde yalnızca standart kütüphane kullanılabilir. |
| **Kurulum kökü** | **`UGII_ROOT_DIR`** ortam değişkeni, `NXBIN` dizininizi (yani `run_journal.exe` dosyasını içeren klasörü) göstermelidir. |
| **Tip stub'ları** | `<install>/UGOPEN/pythonStubs/NXOpen/` dizini, tam olarak sizin kurulumunuzla eşleşen `.pyi` stub'larını barındırır. Otomatik tamamlama için ve daha da önemlisi **kendi sürümünüze ait gerçek imzaları** okumak için IDE'nizi bu dizine yönlendirin. |

## Bir journal'ı headless çalıştırmak

```powershell
# PowerShell — use $env: and the & call operator (NOT cmd's %VAR%)
$env:UGII_ROOT_DIR = "C:\Program Files\Siemens\NX2506\NXBIN"   # adjust to your install
& "$env:UGII_ROOT_DIR\run_journal.exe" my_journal.py -args arg1 arg2 arg3
```

Betiğiniz, sondaki `-args` değerlerini `sys.argv[1:]` üzerinden okur.

**Headless bir çalıştırma, açık bir GUI ile birlikte var olabilir.** Yerel bir lisansta, NX GUI zaten açıkken `run_journal.exe`'yi başlatmak, lisans çakışması olmadan temiz bir *ikinci* oturum başlatır. Bu, art arda birçok kez sorunsuz şekilde denenmiştir — önceki sonucu GUI'de incelerken toplu (batch) olarak build yapmak için kullanışlıdır.

## Headless modda ÇALIŞMAYAN tek şey: görüntü dışa aktarma

Headless bir journal'dan modelin PNG/ekran görüntüsünü oluşturmak **imkansızdır** — render edilecek bir grafik penceresi yoktur. Belgelenen iki yol da `run_journal.exe` altında başarısız olur:

- `part.Views.CreateImageExportBuilder()` → `Commit()` şu hatayı fırlatır: **"Invalid object state"**.
- `theUF.Disp.CreateImage(png, DispImageFormat.PNG, DispBackgroundColor.WHITE)` → **"The image file could not be created."**

Render edilmiş görüntülere ihtiyacınız varsa, dışa aktarma adımını **interaktif GUI içinde** çalıştırın veya işletim sistemi penceresini ayrıca yakalayın (capture). Pipeline'ınızı, görsel çıktının yalnızca GUI'ye özgü bir adım olacağı şekilde planlayın; headless yolu geometri + nötr format dışa aktarımıyla (STEP/JT/Parasolid) sınırlı tutun.

## GUI otomasyonu hakkında bir not

NX ribbon'ını tıklamaları simüle ederek yönetmeye çalışmak güvenilir değildir: ribbon kendini temiz UI-Automation `TabItem` elemanları olarak açığa çıkarmaz ve ekran ölçeklendirmesi (ör. %125 DPI) imleç koordinatlarını pencere dikdörtgenleriyle senkronsuz hale getirir. Bir pencere görüntüsünü **yakalamak** (PrintWindow / CopyFromScreen) güvenlidir; dışarıdan NX'e **tıklamak** güvenli değildir. NX'i sentetik girdi yerine NXOpen üzerinden yönetin.

## Önerilen proje yapısı

Prosedürel bir pipeline için, NXOpen'a dokunan kodu ince tutun ve geri kalan her şeyi saf (pure) tutun:

```
params  →  pure-math blueprint (plain dicts/JSON, no NXOpen import)
        →  a small list of "build steps"
        →  one builder module that turns steps into NXOpen features
        →  run_journal.exe executes it headless
```

Blueprint katmanını her türlü `import NXOpen`'dan arındırmak, geometriyi (bounding box'lar, boşluklar/clearance, kütle tahminleri) normal bir Python venv içinde hızlı unit testlerle doğrulamanızı sağlar — yalnızca son build adımı NX'e dokunur. Bu doğrulamanın neyi yakalayıp neyi yakalayamayacağı için [docs/04-boolean-and-geometry-rules.md](04-boolean-and-geometry-rules.md) belgesine bakın.
