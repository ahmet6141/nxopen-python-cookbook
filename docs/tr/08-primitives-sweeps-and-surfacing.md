> 🌐 [English](../08-primitives-sweeps-and-surfacing.md) · **Türkçe**

# 08 · Primitifler, Süpürmeler & Yüzey İşlemleri

Extrude, revolve (01) ve Through-Curves loft'lar (07) prosedürel katıların çoğunu kapsar — bu sayfa **modelleme araç kutusunun geri kalanının** haritasını çıkarır: analitik primitifler, 3B yollar boyunca tube ve süpürmeler, ruled gövdeler ve yüzeyleri katıya dönüştüren sheet-body iş akışı (offset → thicken → sew → trim).

> ⚠️ **Doğrulama durumu:** 01–07 dokümanlarının aksine, bu sayfadaki reçeteler **henüz NX 2506'da canlı doğrulanmadı**. Resmî API referansından, GUI'den kaydedilmiş journal kalıplarından ve topluluk örneklerinden derlendiler; `# stub'larını kontrol et` işaretli satırlar sürümler arasında en çok değişme ihtimali olanlardır. Bu sayfayı bir harita olarak kullan, kendi kurulumunda doğrula ve sonuçları [CONTRIBUTING](../../CONTRIBUTING.md) uyarınca bildir — bir öncesi/sonrası yüzey sayısı ya da hacim, bir reçeteyi doğrulanmışa terfi ettirmeye yeter.

Tüm parçacıklar [01-core-api.md](01-core-api.md) içindeki boilerplate'i varsayar: `session = NXOpen.Session.GetSession()` ve `part` çalışma parçasıdır.

---

## 8.1 Analitik primitifler — Block, Cylinder, Cone, Sphere

Dikdörtgen ya da silindirik stok için bunlar sketch + extrude'dan daha basit ve hızlıdır ve extrude/revolve ile aynı satır-içi boolean mekanizmasını (`BooleanOption`) taşırlar — dolayısıyla [04 boolean kuralları](04-boolean-and-geometry-rules.md) aynen geçerlidir.

```python
# Block — orijin köşesi + üç kenar uzunluğu (string expression'lar)
blk = part.Features.CreateBlockFeatureBuilder(NXOpen.Features.Feature.Null)
blk.SetOriginAndLengths(NXOpen.Point3d(0.0, 0.0, 0.0), "80", "60", "30")
blk.BooleanOption.Type = NXOpen.GeometricUtilities.BooleanOperation.BooleanType.Create
feat = blk.CommitFeature(); blk.Destroy()
body = feat.GetBodies()[0]
```

```python
# Cylinder — eksen (nokta + yön) + çap/yükseklik expression'ları
cyl = part.Features.CreateCylinderBuilder(NXOpen.Features.Feature.Null)
cyl.Axis = part.Axes.CreateAxis(
    part.Points.CreatePoint(NXOpen.Point3d(0.0, 0.0, 30.0)),
    part.Directions.CreateDirection(NXOpen.Point3d(0.0, 0.0, 30.0), NXOpen.Vector3d(0.0, 0.0, 1.0),
                                    NXOpen.SmartObject.UpdateOption.WithinModeling),
    NXOpen.SmartObject.UpdateOption.WithinModeling)          # stub'larını kontrol et: bazı sürümler ekseni farklı alır
cyl.Diameter.RightHandSide = "20"
cyl.Height.RightHandSide   = "25"
cyl.BooleanOption.Type = NXOpen.GeometricUtilities.BooleanOperation.BooleanType.Unite
cyl.BooleanOption.SetTargetBodies([body])
feat = cyl.CommitFeature(); cyl.Destroy()
```

```python
# Cone — iki çap + yükseklik
cone = part.Features.CreateConeBuilder(NXOpen.Features.Feature.Null)
cone.Type = NXOpen.Features.ConeBuilder.Types.DiametersAndHeight
cone.BaseDiameter.RightHandSide = "40"
cone.TopDiameter.RightHandSide  = "10"       # 0 -> tepesi sivri tam koni
cone.Height.RightHandSide       = "35"
feat = cone.CommitFeature(); cone.Destroy()

# Sphere — merkez noktası + çap
sph = part.Features.CreateSphereBuilder(NXOpen.Features.Feature.Null)
sph.Type = NXOpen.Features.SphereBuilder.Types.CenterPointAndDiameter
sph.Diameter.RightHandSide = "30"
sph.CenterPoint = part.Points.CreatePoint(NXOpen.Point3d(0.0, 0.0, 0.0))
feat = sph.CommitFeature(); sph.Destroy()
```

> Bütün sayısal girdiler **string expression'dır** (`"20"`, ya da `"boss_dia"` gibi bir expression adı) — 01'deki extrude limitleriyle aynı kural. String beklenen yere float geçmek `Commit()` sırasında patlar.

---

## 8.2 3B yol boyunca Tube — bükülmüş çubuklar, hatlar, borular

Viraj demirleri, fren/yakıt hatları ve korkuluklar için standart araç — polyline boyunca tek bir tube'un neden silindir kolajından iyi olduğunu [04](04-boolean-and-geometry-rules.md) anlatır. Yol, teğet-sürekli eğrilerden (çizgiler + köşe yuvarlatma yayları) oluşan bir `Section`'dır:

```python
tb = part.Features.CreateTubeBuilder(NXOpen.Features.Feature.Null)
tb.OuterDiameter.RightHandSide = "10"
tb.InnerDiameter.RightHandSide = "6"                  # "0" -> boru yerine dolu çubuk
tb.OutputOption = NXOpen.Features.TubeBuilder.OutputOptions.SingleSegment

path = part.Sections.CreateSection(0.0095, 0.01, 0.5)
rule = part.ScRuleFactory.CreateRuleCurveDumb(path_curves)      # çizgiler + teğet yaylar, sırayla
path.AddToSection([rule], path_curves[0], NXOpen.NXObject.Null, NXOpen.NXObject.Null,
                  help_pt, NXOpen.Section.Mode.Create, False)
tb.PathSection = path                                  # tam property adı için stub'larını kontrol et
feat = tb.CommitFeature(); tb.Destroy()
```

> **Boolean dikkat (04'ten):** satır-içi boolean sırasında tube'un iç deliği de hedefi keser — delik yarıçapını içinden geçen her parçadan küçük tut, yoksa subtract o parçayı ikiye böler. `SingleSegment` vs `MultipleSegments`, köşelerin tek gövde mi segment başına bir gövde mi ürettiğine karar verir.

---

## 8.3 Swept — bir kılavuz boyunca serbest profil

Tube yuvarlak kesitlerle sınırlıyken Swept, **herhangi bir kapalı profili** bir veya birden çok kılavuz eğrisi boyunca taşır. 07'deki loft ile aynı `Section` mekaniği — bir kesit listesi artı bir kılavuz listesi:

```python
sw = part.Features.CreateSweptBuilder(NXOpen.Features.Swept.Null)   # not: Swept.Null, 2.4'teki Thread gibi
sw.G0Tolerance = 0.01
sw.G1Tolerance = 0.5

sec = part.Sections.CreateSection(0.0095, 0.01, 0.5)     # profil — katı için kapalı olmalı
# ...profil eğrileriyle AddToSection, tam 01'deki gibi...
sw.SectionList.Append(sec)

guide = part.Sections.CreateSection(0.0095, 0.01, 0.5)   # yol
# ...kılavuz eğri(ler)iyle AddToSection...
sw.GuideList.Append(guide)

feat = sw.CommitFeature(); sw.Destroy()
```

Üç "yol boyunca profil" aracı arasında seçim:

| Araç | Profil | Yol | Tipik kullanım |
|------|--------|-----|----------------|
| **Tube** (8.2) | yalnız daire/halka | 3B polyline + yaylar | çubuklar, borular, kablolar |
| **Swept** (8.3) | herhangi bir eğri zinciri | 1–3 kılavuz | raylar, contalar, karmaşık kesitler |
| **Through Curves** ([07](07-freeform-lofting.md)) | N farklı kesit | örtük (kesit sırası) | kanatlar, gövdeler, şekli değişen her şey |

---

## 8.4 Ruled — iki kesitli düz loft

Ruled gövde, **tam olarak iki kesitin düz çizgilerle birleştirildiği** kısıtlı bir loft'tur — geçiş parçaları, kamalar, oluk segmentleri. Elinizde yalnızca iki kesit varken tam loft'tan daha ucuz ve öngörülebilirdir:

```python
rb = part.Features.CreateRuledBuilder(NXOpen.Features.Feature.Null)
# 7.2'deki loft kesitleri gibi kurulmuş iki Section:
rb.FirstSection  = sec1
rb.SecondSection = sec2
feat = rb.CommitFeature(); rb.Destroy()
```

7.2'deki burulma-kontrol kuralı burada iki kat güçlü geçerlidir: iki kesiti de **aynı nokta sayısı ve sırayla** üret, yoksa düz-çizgi eşleşmesi gövdeyi papyon gibi katlar.

---

## 8.5 Sheet iş akışı — offset, thicken, sew

Bazı şekilleri önce **yüzey olarak** kurmak, sonra katıya çevirmek daha kolaydır. Üç temel araç:

```python
# Thicken — sheet gövde -> katı duvar
th = part.Features.CreateThickenBuilder(NXOpen.Features.Feature.Null)
th.Tolerance = 0.01                                   # Shell (2.5) ile aynı "varsayılan 0 patlar" ailesi
th.FirstOffset.RightHandSide  = "2"
th.SecondOffset.RightHandSide = "0"
col = part.ScCollectors.CreateCollector()
col.ReplaceRules([part.ScRuleFactory.CreateRuleFaceDumb(sheet_faces)], False)
th.FaceCollector = col                                # stub'larını kontrol et: property adı sürüme göre değişir
feat = th.CommitFeature(); th.Destroy()
```

```python
# Sew — komşu sheet'leri tek parçaya dik (su geçirmez sheet'ler -> kapalı katı)
swb = part.Features.CreateSewBuilder(NXOpen.Features.Feature.Null)
swb.SewType = NXOpen.Features.SewBuilder.Types.Sheet
swb.Tolerance = 0.01
swb.TargetSheets.Add(sheet_a)                         # stub'larını kontrol et: SelectObjectList vs collector
swb.ToolSheets.Add(sheet_b)
feat = swb.CommitFeature(); swb.Destroy()
```

`CreateOffsetSurfaceBuilder` (bir yüzeyi yeni bir sheet'e offset'ler) seti tamamlar — [05](05-capability-inventory.md) envanterine bak. Klasik hat: **loft/swept'i sheet olarak kur → kapakları sew'le → (veya) thicken** — katı loft kendi kendini keserken kabuğu kesmiyorsa işe yarar.

> Bir gövde `body.IsSheetBody` true ise **sheet**'tir; loft/swept builder'larındaki `BodyPreference` (7.2) çıktının katı-mı-sheet-mi olacağına karar verir.

---

## 8.6 Trim & split — düzlem ya da yüzeyle kesme

`TrimBody2` araç yüzeyinin/düzleminin bir tarafındaki her şeyi atar; `SplitBody` iki yarımı ayrı gövdeler olarak tutar. İkisi de aracı iç-içe `BooleanTool.FacePlaneTool` yolundan alır — API'nin en az tahmin edilebilir kısmı, ama GUI-kayıtlı journal'ların gösterdiği budur:

```python
tb = part.Features.CreateTrimBody2Builder(NXOpen.Features.Feature.Null)
tb.TargetBodyCollector.ReplaceRules(
    [part.ScRuleFactory.CreateRuleBodyDumb([body])], False)
tb.BooleanTool.FacePlaneTool.ToolFaces.FaceCollector.ReplaceRules(
    [part.ScRuleFactory.CreateRuleFaceDumb([tool_face])], False)   # veya bir datum plane besle
feat = tb.CommitFeature(); tb.Destroy()
```

Hangi tarafın kalacağını builder üzerindeki bir yön bayrağı belirler (`tb.Direction` / bir ters çevirme anahtarı — stub'larını kontrol et). `SplitBodyBuilderUsingCollector` aynı yapıyı yansıtır ve her split gibi, sonrasında [04'teki öksüz-gövde disiplinini](04-boolean-and-geometry-rules.md) gerektiren gövdeler üretir.

---

## 8.7 Doğru aracı seçmek — karar tablosu

| Şekil… | Aracın |
|--------|--------|
| düz itilmiş sabit bir profil | **Extrude** (01) |
| bir dönel gövde | **Revolve** (01) — silindir yığını değil, tek kapalı profil (04) |
| dikdörtgen / silindirik stok | **Primitifler** (8.1) |
| bükülmüş yol boyunca yuvarlak kesit | **Tube** (8.2) |
| yol boyunca serbest kesit | **Swept** (8.3) |
| iki bilinen kesit, düz geçiş | **Ruled** (8.4) |
| sürekli değişen N kesit | **Through Curves loft** ([07](07-freeform-lofting.md)) |
| karmaşık yüzey üstünde ince duvar | **sheet + Thicken** (8.5) |
| bir düzlemin ötesi atılmış katı | **TrimBody2** (8.6) |

Her satırın satır-içi boolean'ı [04](04-boolean-and-geometry-rules.md) kurallarına göre davranır — ve loft/swept ailesinin **create-only** eğilimini unutma: önce gövdeyi kur, basit şekilleri üstüne unite et.
