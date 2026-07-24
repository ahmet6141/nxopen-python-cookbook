> 🌐 [English](../09-sketches-patterns-and-feature-editing.md) · **Türkçe**

# 09 · Sketch'ler, Pattern'ler & Sonradan Feature Düzenleme

Tek-seferlik journal'ları bakımı yapılabilir üreticilere dönüştüren üç modelleme yeteneği: gerçekten gerektiğinde headless **gerçek bir sketch** kurmak, builder'ları döngüye sokmak yerine feature'ları **pattern'lemek**, ve parçayı yeniden inşa etmeden **var olan feature'ları düzenlemek** — suppress, yeniden parametrelendirme, silme.

> ⚠️ **Doğrulama durumu:** 01–07 dokümanlarının aksine, bu sayfadaki reçeteler **henüz NX 2506'da canlı doğrulanmadı**. Resmî API referansından, GUI-kayıtlı journal kalıplarından ve topluluk örneklerinden derlendiler; `# stub'larını kontrol et` işaretli satırlar sürümler arasında en çok değişme ihtimali olanlardır. Kendi kurulumunda doğrula ve sonuçları [CONTRIBUTING](../../CONTRIBUTING.md) uyarınca bildir.

Tüm parçacıklar [01-core-api.md](01-core-api.md) içindeki boilerplate'i varsayar: `session = NXOpen.Session.GetSession()` ve `part` çalışma parçasıdır.

---

## 9.1 Gerçekten sketch'e ihtiyacın var mı?

Genellikle **hayır**. Headless üretim serbest eğrilerle en iyi çalışır — `part.Curves.CreateLine/CreateArc` (01) ve sketch'siz spline'lar (7.1) bir `Section`'ı doğrudan besler; sketch nesnesi yok, kısıt çözücü yok, yönetilecek aktif-sketch durumu yok. 07'nin ilk tuzağının seni `CreateSketchSplineBuilder`'dan *uzağa* yönlendirmesinin sebebi budur.

Gerçek bir sketch'e yalnızca sketch'in sana verebileceği şeyler için uzan:

- **kısıt-çözücü davranışı** — Tools → Expressions'tan bir ölçü değiştiğinde kendini yeniden çözen geometri;
- daha sonra **GUI'de bir insanın** ölçülere çift tıklayarak düzenleyeceği bir profil;
- akış aşağısında sketch bekleyen **sketch-sahipli feature'lar** (bazı delik/kanal iş akışları).

## 9.2 Minimal headless sketch

Klasik kalıp: sketch'i bir düzlemde oluştur, aktive et, dışarıda oluşturulmuş eğrileri `AddGeometry` ile ekle, deaktive et. Eğriler sketch üyesi olur ve sketch, `Section`'ı serbest eğriler gibi besler:

```python
sib = part.Sketches.CreateSketchInPlaceBuilder2(NXOpen.Sketch.Null)
sib.PlaneReference = datum_plane              # sabit bir datum plane (2.6) veya düzlemsel bir yüzey
sketch = sib.Commit()
sib.Destroy()

sketch.Activate(NXOpen.Sketch.ViewReorient.FalseValue)

l1 = part.Curves.CreateLine(NXOpen.Point3d(0.0, 0.0, 0.0),  NXOpen.Point3d(40.0, 0.0, 0.0))
l2 = part.Curves.CreateLine(NXOpen.Point3d(40.0, 0.0, 0.0), NXOpen.Point3d(40.0, 25.0, 0.0))
for c in (l1, l2):
    sketch.AddGeometry(c, NXOpen.Sketch.InferConstraintsOption.InferNoConstraints)

sketch.Update()
sketch.Deactivate(NXOpen.Sketch.ViewReorient.FalseValue,
                  NXOpen.Sketch.UpdateLevel.Model)
```

> Python binding'inde boolean-adlı enum üyeleri **`TrueValue` / `FalseValue`** olarak yazılır (`ViewReorient.FalseValue`, 05'teki `CloseWholeTree.TrueValue`) — sebebi 7.1'deki `MatchKnotsTypes.NotSet` tuzağıyla aynı: `True`/`False`/`None` Python anahtar kelimeleridir ve `.True` bir `SyntaxError` olurdu.
>
> **`Deactivate`'i unutmak**, sketch'i oturumun geri kalanı boyunca aktif bırakır — sonraki feature builder'ları kafa karıştırıcı şekillerde bozulur. Activate/Deactivate'i eşli parantez gibi ele al (ara kod hata fırlatabiliyorsa try/finally).

Ölçüler ve geometrik kısıtlar programatik olarak eklenebilir (`sketch.CreateDiameterDimension`, çakışıklık/paralellik kısıt builder'ları — stub'larını tara), ama kendini çok sayıda kısıt script'lerken bulursan bir adım geri çekil: koordinatları kendin hesaplayıp çözücüyü atlamak, headless'ta neredeyse her zaman daha sağlam harekettir.

---

## 9.3 Pattern Feature — doğrusal

Pattern Feature'ın API tarafı iki bilinen tuzak taşır ([03](03-pitfalls.md) #6–7): feature'lar `FeatureList.Add([feat])` ile **liste** olarak eklenir ve aralık **`SpacingType.Offset`**'tir (`CountAndPitch` yoktur):

```python
pb = part.Features.CreatePatternFeatureBuilder(NXOpen.Features.Feature.Null)
pb.FeatureList.Add([boss_feat])                       # LİSTE — tuzak #6

rect = pb.PatternService.RectangularDefinition
rect.XDirection = part.Directions.CreateDirection(
    NXOpen.Point3d(0.0, 0.0, 0.0), NXOpen.Vector3d(1.0, 0.0, 0.0),
    NXOpen.SmartObject.UpdateOption.WithinModeling)
rect.XSpacing.SpaceType = NXOpen.GeometricUtilities.PatternSpacing.SpacingType.Offset   # tuzak #7
rect.XSpacing.NCopies.RightHandSide       = "4"
rect.XSpacing.PitchDistance.RightHandSide = "25"
# isteğe bağlı ikinci yön: rect.YDirection + rect.YSpacing, aynı yapı

feat = pb.CommitFeature(); pb.Destroy()
```

## 9.4 Pattern Feature — dairesel, ve Pattern Geometry

```python
pb = part.Features.CreatePatternFeatureBuilder(NXOpen.Features.Feature.Null)
pb.FeatureList.Add([hole_feat])
pb.PatternService.PatternType = NXOpen.GeometricUtilities.PatternDefinition.PatternEnum.Circular   # stub'larını kontrol et

circ = pb.PatternService.CircularDefinition
circ.RotationAxis = part.Axes.CreateAxis(
    part.Points.CreatePoint(NXOpen.Point3d(0.0, 0.0, 0.0)),
    part.Directions.CreateDirection(NXOpen.Point3d(0.0, 0.0, 0.0), NXOpen.Vector3d(0.0, 0.0, 1.0),
                                    NXOpen.SmartObject.UpdateOption.WithinModeling),
    NXOpen.SmartObject.UpdateOption.WithinModeling)   # stub'larını kontrol et: eksen ataması değişebilir
circ.AngularSpacing.SpaceType = NXOpen.GeometricUtilities.PatternSpacing.SpacingType.Offset
circ.AngularSpacing.NCopies.RightHandSide    = "6"
circ.AngularSpacing.PitchAngle.RightHandSide = "60"
feat = pb.CommitFeature(); pb.Destroy()
```

**Pattern Feature vs Pattern Geometry vs Python döngüsü:**

- **Pattern Feature** bir *feature'ı* yeniden oynatır — parametriktir, ağaçta tek pattern düğümü gösterir ve master değişince yeniden çözülür. GUI'de düzenlenecek parçalar için en iyisi.
- **Pattern Geometry** (`CreatePatternGeometryBuilder`) *gövdeleri/eğrileri* feature geçmişi olmadan kopyalar — daha hafiftir ama kopyalar master'ı takip etmez.
- Builder'ı N kez çağıran **düz bir Python döngüsü** headless'ta çoğu zaman en sağlam cevaptır: her örnek bağımsızdır, tek tek adlandırılır (7.6) ve [04 kurallarına](04-boolean-and-geometry-rules.md) göre tek tek boolean'lanabilir. Pattern'ler satır-içi boolean'larla sürüme bağlı şekillerde etkileşir — bir pattern huysuzlandığında döngüye geri dön.

---

## 9.5 Gövde kopyalama, ölçekleme, taşıma

Taşıma/döndürme reçetesi [05](05-capability-inventory.md)'te (`MoveObjectBuilder`, `DeltaXyz` / `Angle`); oradaki `CopyOriginal` seçeneğini tekrar not et — var olan en ucuz "gövde kopyala" budur. İki tamamlayıcı:

```python
# Scale — bir nokta etrafında uniform
sc = part.Features.CreateScaleBuilder(NXOpen.Features.Feature.Null)
sc.Type = NXOpen.Features.ScaleBuilder.Types.Uniform
sc.BodyCollector.ReplaceRules([part.ScRuleFactory.CreateRuleBodyDumb([body])], False)
sc.Point = part.Points.CreatePoint(NXOpen.Point3d(0.0, 0.0, 0.0))
sc.Factor.RightHandSide = "1.05"                      # stub'larını kontrol et: bazı sürümlerde UniformFactor
feat = sc.CommitFeature(); sc.Destroy()
```

```python
# Extract Body — bütün bir gövdenin ilişkisel kopyası (builder 05'te listeli)
eb = part.Features.CreateExtractFaceBuilder(NXOpen.Features.Feature.Null)
eb.Type = NXOpen.Features.ExtractFaceBuilder.ExtractType.Body
eb.BodyToExtract.Add(body)                            # stub'larını kontrol et
eb.Associative = False                                # False -> kaynak düzenlemelerinden bağımsız kopya
feat = eb.CommitFeature(); eb.Destroy()
```

Aynalama için doğrulanmış reçete [2.6](02-verified-recipes.md) — **sabit** datum plane istediğini hatırla.

---

## 9.6 İnşadan sonra feature düzenleme

Üretilmiş bir parça salt-okunur değildir. Journal'ları *bakımı yapılabilir* kılan kalıp — isimle bul, sürücüyü değiştir, güncelle:

```python
feats = {f.Name: f for f in part.Features}            # SetName ile verdiğin isimler (7.6)
wing  = feats["MYPROJ_WING"]

# 1) suppress / unsuppress — ucuz "konfigürasyon" anahtarı
wing.Suppress()
# ...suppress edilmiş varyantı dışa aktar...
wing.Unsuppress()

# 2) yeniden parametrelendir: SÜRÜCÜ EXPRESSION'ı düzenle, sonra update döngüsünü çalıştır
for ex in part.Expressions:
    if ex.Name == "myproj_wing_span":
        ex.RightHandSide = "1450"                     # RightHandSide, asla .Value — tuzak #11
mark = session.SetUndoMark(NXOpen.Session.MarkVisibility.Visible, "edit span")
session.UpdateManager.DoUpdate(mark)                  # bu çalışana kadar hiçbir şey kımıldamaz — tuzak #20

# 3) feature'ı güvenle sil — kuyruk + update, asla çıplak silme
session.UpdateManager.AddToDeleteList([wing])
session.UpdateManager.DoUpdate(mark)
```

Doğrulanmış dokümanlardan taşınan üç kural, çünkü burada da aynen ısırırlar:

- Her düzenlemeden sonra **update döngüsü zorunludur** (tuzak #20) — `DoUpdate`'siz düzenlenmiş bir expression modeli bayat bırakır.
- **Parent silmek çocukları bozar** (7.3): önce `feature.GetChildren()`'a bak ya da yapraktan-köke sil. `AddToDeleteList` + `DoUpdate` en azından sessizce bozmak yerine görünür şekilde başarısız olur.
- Undo mark ile sarmalarsan **başarısız bir düzenleme hiçbir şeyi zehirlemez** — `session.UndoToMark(mark, None)` parçayı düzenleme-öncesi duruma döndürür; headless'ın Ctrl+Z'ye en yakın şeyi budur.

Bu üçlü — isimli feature'lar (7.6), expression sürücüleri (7.7), suppress/düzenle/sil (burası) — *tekrar çalıştırdığın bir üreticiyi* *bir kez çalıştırdığın bir script'ten* ayıran şeydir.
