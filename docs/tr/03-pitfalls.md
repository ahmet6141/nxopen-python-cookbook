> 🌐 [English](../03-pitfalls.md) · **Türkçe**

# 03 · Tuzaklar — çalışma zamanı tuzak listesi

NXOpen, import sırasında değil çalışma zamanında hata verir ve hata metinleri gerçek nedeni nadiren açıklar. Bu, her biri **belirti → çözüm** biçiminde birleştirilmiş listedir. Isırdıkları yere göre gruplandırılmıştır.

## API yüzeyi / imzalar

| # | Tuzak | Belirti → Çözüm |
|---|------|---------------|
| 1 | Yanlış birim enum'u | `Part.Units.Millimeters` → *"Second parameter is invalid."* **`BasePart.Units.Millimeters`** kullanın. |
| 2 | Kullanımdan kaldırılmış section rule | **`CreateRuleCurveDumb`** kullanın; `CreateRuleBaseCurveDumb` kullanımdan kaldırılmıştır (deprecated). |
| 3 | EdgeBlend imzası | `AddChainset(edge, index)` başarısız olur. Doğrusu **`AddChainset(ScCollector, "radius")`** — collector + radius *string*. |
| 4 | Chamfer kenar ataması | `AddChainsToCollector` yoktur. Kenarları **`SmartCollector`**'a atayın; mesafe `FirstOffset = "2"` (string) şeklindedir. |
| 5 | Thread builder null | **`Features.Thread.Null`** ile oluşturun, `Feature.Null` ile değil. |
| 6 | Pattern feature ekleme | **`FeatureList.Add([feat])`**; `AddFeatureToPattern` diye bir şey yoktur. |
| 7 | Pattern aralığı | **`PatternSpacing.SpacingType.Offset`**; `CountAndPitch` mevcut değildir. |
| 8 | Mirror body "kayıp" | `CreateMirrorBodyBuilder` **mevcuttur** ve çalışır — ona bir `Planes.CreatePlane` değil, **sabitlenmiş (fixed) bir datum plane** verin. |
| 9 | Material API'si | `LoadMaterialsFromLibrary` / `AssignMaterialToBody` mevcut değildir. `PhysicalMaterials.LoadFromNxmatmllibrary(name)` → `mat.AssignObjects([body])` kullanın. |
| 10 | PMI note API'si | `PmiNotes.CreatePmiNote` mevcut değildir. `Annotations.CreatePmiNoteBuilder(None)` → `Text.TextBlock.SetText([...])` kullanın. |

## Değerler ve expression'lar

| # | Tuzak | Belirti → Çözüm |
|---|------|---------------|
| 11 | Expression değeri | `.Value` değil **`RightHandSide`**'ı (string) ayarlayın — bir uzunluk üzerinde `.Value` sahte bir **25.4×** dönüşüm uygular. |
| 12 | Float gereksinimi | `Point3d` / arc argümanları **float** olmalıdır — bir `int` *"Expecting double."* hatası verir. `0.0` yazın. |
| 13 | Draft toleransı | Varsayılan `AngleTolerance` 0 → *"Angle tolerance is too small."* **`AngleTolerance = 0.5`** ayarlayın. |
| 14 | Shell toleransı | Varsayılan `Tolerance` 0 → *"Tolerance error."* **`Tolerance = 0.01`** ayarlayın. |
| 15 | Hole package through-body | ThroughBody → *"Tolerance Specification requires three numbers."* `Value` + derinlik + uç açısı + `Tolerance = 0.01` kullanın. |
| 16 | Hole package hedefi | Hedefi atlamak → *"Missing target body."* `BooleanOperation.SetTargetBodies([body])` çağırın. |
| 17 | Expression collector birimi | `CreateExpressionCollectorSet(col, "3", "", 0)` — birim argümanı **boş string** `""` olmalıdır. `"Degrees"`/`"deg"` → *"invalid unit measure."* |
| 18 | Thread table headless | Standard table → *"Standard data not found."* `Input.Manual` kullanın ve diameter/pitch expression'larını kendiniz ayarlayın. |
| 19 | Thread start face | *"Invalid thread start face"* — bitişik bir düzlemsel (planar) yüz kullanın; **chamfer'dan önce thread**; aday yüzleri sırayla deneyin. |

## Yaşam döngüsü ve oturum

| # | Tuzak | Belirti → Çözüm |
|---|------|---------------|
| 20 | Eksik update | Model ilerlemiyor → bir undo mark ayarlayın ve **her feature'dan sonra `UpdateManager.DoUpdate(mark)`** çağırın. |
| 21 | Üzerine yazma reddedildi | `NewBaseDisplay` var olan bir `.prt` üzerine yazmaz → **önce dosyayı silin**. |
| 22 | Parasolid zehirlenmesi | *Tüm part*'ı (construction curve'lerle birlikte) dışa aktarmak → *"Modeler error: please report fault."* Yalnızca **seçili solid gövdeleri (bodies)** dışa aktarın. |
| 23 | Zehirlenmiş builder | Başarısız bir `Commit()` builder'ı bozar — **yeniden oluşturun**, asla aynı nesneyi tekrar denemeyin. |
| 24 | Oturum zehirlenmesi | *"please report fault"* mesajını bir kez gördüğünüzde, oturum kurtarılamaz → **NX'i tamamen kapatıp yeniden başlatın**. |
| 25 | Fonksiyon-yerel import | *Bir fonksiyonun içinde* `import NXOpen.X` yapmak `NXOpen`'ı yerel bir isim haline getirir → *"cannot access local variable 'NXOpen'."* Alt modül import'larını **modülün en üstüne** koyun. |

## Geometri (yalan söyleyen boolean'lar)

Bunlar kendi sayfalarını hak ediyor çünkü doğrulama (validation), gerçek bir build olmadan bunları yakalayamaz — bkz. **[04-boolean-and-geometry-rules.md](04-boolean-and-geometry-rules.md)**:

- Unite takımları (tool) hedefe **≥15 mm gömülmelidir (embed)**; nokta ve çizgi teması asla kaynaşmaz (fuse).
- `loft`, bazı builder'larda boolean'lar için etkin biçimde **yalnızca oluşturma (create-only)** işlemidir — gövdeleri (hull) tek bir loft olarak oluşturun, geri kalan her şeyi prism/cylinder olarak unite edin.
- Hedefin tamamen **dışında** olan bir subtract takımı (tool) *"Tool body completely outside target body."* hatasıyla başarısız olur.
- `hole` primitifi, konumu paylaşılan bir origin'den değil kendi `cx/cy/z0` değerlerinden okur.
- Kaldırılmış/boş (void) geometri üzerine düşen "başarılı" bir unite, hatasız biçimde sessizce **ayrı bir gövde (body)** bırakır — bunu `built N bodies` ≠ `named N bodies` üzerinden tespit edin.
