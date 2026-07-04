> 🌐 [English](../02-verified-recipes.md) · **Türkçe**

# 02 · Doğrulanmış Reçeteler

Kopyala-yapıştır feature reçeteleri. **Bunların her biri canlı, headless bir NX 2506 journal'ında başarıyla commit edildi** ve ortaya çıkan gövde (face sayıları, hacim, kütle) incelendi. Yaygın olarak belirtilen bir imza yanlışsa, doğrusu burada.

Ortak preamble:

```python
import NXOpen, NXOpen.Features, NXOpen.GeometricUtilities, NXOpen.Annotations
session = NXOpen.Session.GetSession()
part = session.Parts.NewBaseDisplay(path, NXOpen.BasePart.Units.Millimeters)
```

> **Aşağıdaki tüm builder'lar için altın kural:** başarısız bir `Commit()` **builder'ı zehirler** — aynı nesne üzerinde tekrar denemeyin. Her denemede builder'ı sıfırdan yeniden oluşturun. Ve `import NXOpen.SubModule` ifadesini asla *bir fonksiyonun içinde* kullanmayın (bu, `NXOpen`'ı tüm fonksiyon için yerel bir isim yapar → *"cannot access local variable 'NXOpen'"*); alt modül import'larını modülün en üstüne koyun.

---

## 2.1 Edge Blend (fillet)

Kanıt: face sayısı 8 → 12 oldu.

```python
ebb  = part.Features.CreateEdgeBlendBuilder(NXOpen.Features.Feature.Null)
col  = part.ScCollectors.CreateCollector()
rule = part.ScRuleFactory.CreateRuleEdgeDumb(edges)      # edges: list[Edge]
col.ReplaceRules([rule], False)
ebb.AddChainset(col, "4")                                # radius is a STRING EXPRESSION, not a number/index
feat = ebb.CommitFeature(); ebb.Destroy()
```

> Çevrimiçi en yaygın EdgeBlend hatası yanlış imzadan kaynaklanır. Doğrusu **`AddChainset(ScCollector, "radius")`** — bir smart-collector artı bir radius *string*'i — `AddChainset(edge, index)` **değil**. `AddVariableRadiusData`, değişken yarıçaplı blend'ler içindir ve tamamen farklı bir imzaya sahiptir.

---

## 2.2 Chamfer

Kanıt: face sayısı 12 → 13.

```python
cb  = part.Features.CreateChamferBuilder(NXOpen.Features.Feature.Null)
col = part.ScCollectors.CreateCollector()
col.ReplaceRules([part.ScRuleFactory.CreateRuleEdgeDumb(edges)], False)
cb.SmartCollector = col                                            # edges go here, as a collector
cb.Option      = NXOpen.Features.ChamferBuilder.ChamferOption.SymmetricOffsets
cb.FirstOffset = "2"                                               # string; FirstOffsetExp is read-only
feat = cb.CommitFeature(); cb.Destroy()
```

> `AddChainsToCollector([edge])` diye bir metot **yoktur**. Collector'ı `SmartCollector`'a atayın.

---

## 2.3 Draft (Face)

Setin en cilveli olanı — açı bir expression-collector seti üzerinden gelir ve tolerans değerleri açıkça ayarlanmalıdır.

```python
db = part.Features.CreateDraftBuilder(NXOpen.Features.Feature.Null)
db.AngleTolerance    = 0.5          # REQUIRED — default 0 → "Angle tolerance is too small"
db.DistanceTolerance = 0.001
db.TypeOfDraft = NXOpen.Features.DraftBuilder.Type.Face
db.DraftReferencesMethod = NXOpen.Features.DraftBuilder.DraftReferencesMethods.StationaryFace
db.Direction = part.Directions.CreateDirection(origin, z_vec, NXOpen.SmartObject.UpdateOption.WithinModeling)

db.StationaryReference.ReplaceRules(
    [part.ScRuleFactory.CreateRuleFaceDumb([stationary_face])], False)   # a horizontal stationary face

col = part.ScCollectors.CreateCollector()
col.ReplaceRules([part.ScRuleFactory.CreateRuleFaceDumb(faces_to_draft)], False)
ecs = part.CreateExpressionCollectorSet(col, "3", "", 0)   # angle "3"; UNIT ARG MUST BE EMPTY STRING ""
db.FaceSetAngleExpressionList.Append(ecs)                  # Append only accepts an ExpressionCollectorSet
feat = db.CommitFeature(); db.Destroy()
```

> Burada iki tuzak var: `SymmetricAngle` açıyı taşıyan değil, bir **bool**'dur — açı `ExpressionCollectorSet` üzerinde gider. Ve `CreateExpressionCollectorSet`'e verilen unit argümanı **`""`** olmalıdır — `"Degrees"`/`"deg"` geçmek *"invalid unit measure."* hatası verir.

---

## 2.4 Symbolic Thread (Simgesel Diş)

```python
tb = part.Features.CreateThreadBuilder(NXOpen.Features.Thread.Null)     # note: Thread.Null, not Feature.Null
tb.ThreadType  = NXOpen.Features.ThreadBuilder.Type.Symbolic
tb.ThreadInput = NXOpen.Features.ThreadBuilder.Input.Manual             # table path is fragile headless
tb.ShaftPreference = NXOpen.Features.ThreadBuilder.ShaftSizePreference.MajorDiameter
tb.CylindricalFace.Value = cylindrical_face
tb.StartObject.Value     = start_planar_face                           # required; try alternates if invalid
tb.MajorDiameterExp.RightHandSide = "20"
tb.MinorDiameterExp.RightHandSide = "17.5"        # metric: major − 1.0825 × pitch
tb.ShaftDiameterExp.RightHandSide = "18.75"       # must satisfy minor < shaft < major
tb.PitchExp.RightHandSide = "2.5"
tb.AngleExp.RightHandSide = "60"
tb.ThreadLength.RightHandSide = "20"
feat = tb.CommitFeature(); tb.Destroy()
```

Notlar:
- **`Input.Manual` kullanın.** Standart diş tablosu (`NX_Thread_Standard.xml`), headless altında *"Standard data not found"* hatası fırlatır.
- **Chamfer'den önce diş.** Bir chamfer, silindirin üst kenarını zaten yemişse, komşu başlangıç yüzü geçersiz hale gelir. Dişi önce uygulayın veya sırayla birden fazla aday `StartObject` yüzü deneyin.

---

## 2.5 Shell (Kabuk)

Kanıt: hacim 64000 → ~14000 mm³.

```python
sb = part.Features.CreateShellBuilder(NXOpen.Features.Feature.Null)
sb.Tolerance = 0.01                    # REQUIRED — default 0 → "Tolerance error"
sb.Body = body
sb.SetDefaultThickness("2")
col = part.ScCollectors.CreateCollector()
col.ReplaceRules([part.ScRuleFactory.CreateRuleFaceDumb([face_to_remove])], False)
sb.RemovedFacesCollector = col
feat = sb.CommitFeature(); sb.Destroy()
```

---

## 2.6 Mirror Body (Gövde Aynalama)

Kanıt: gövde sayısı 3 → 4.

```python
m = NXOpen.Matrix3x3()                 # rows are the X, Y, Z axes; the Z row is the plane NORMAL
m.Xx, m.Xy, m.Xz = 0.0, 1.0, 0.0
m.Yx, m.Yy, m.Yz = 0.0, 0.0, 1.0
m.Zx, m.Zy, m.Zz = 1.0, 0.0, 0.0
dp = part.Datums.CreateFixedDatumPlane(NXOpen.Point3d(-30.0, 0.0, 0.0), m)   # a FIXED datum plane

mb = part.Features.CreateMirrorBodyBuilder(NXOpen.Features.Feature.Null)
mb.MirrorBodyList.Add(body)
mb.Plane.Value = dp                    # SelectDatumPlane will NOT accept a Planes.CreatePlane result
feat = mb.CommitFeature(); mb.Destroy()
new_body = feat.GetBodies()[0]
```

> `CreateMirrorBodyBuilder` **gerçekten mevcuttur** (bazı dokümanlar aksini iddia eder). Gerçek bir **fixed datum plane** ister — bir `Planes.CreatePlane` nesnesi reddedilir.

---

## 2.7 Hole Package (Delik Paketi)

Kanıt: face sayısı 8 → 9.

```python
hp = part.Features.CreateHolePackageBuilder(NXOpen.Features.HolePackage.Null)
hp.HoleType = NXOpen.Features.HolePackageBuilder.Holetype.Simple
hp.GeneralSimpleHoleDiameter.SetFormula("8")
hp.HoleDepthLimitOption = NXOpen.Features.HolePackageBuilder.HoleDepthLimitOptions.Value
hp.GeneralSimpleHoleDepth.SetFormula("40")     # ThroughBody path errored "Tolerance Specification
hp.GeneralTipAngle.SetFormula("118")           #   requires three numbers" → use Value + depth
hp.Tolerance = 0.01                            #   + tip angle + Tolerance instead

sec = hp.HolePosition
sec.SetAllowedEntityTypes(NXOpen.Section.AllowTypes.OnlyPoints)
pt   = part.Points.CreatePoint(NXOpen.Point3d(175.0, 10.0, 30.0))
rule = part.ScRuleFactory.CreateRuleCurveDumbFromPoints([pt])
sec.AddToSection([rule], pt, NXOpen.NXObject.Null, NXOpen.NXObject.Null,
                 NXOpen.Point3d(175.0, 10.0, 30.0), NXOpen.Section.Mode.Create, False)

hp.BooleanOperation.SetTargetBodies([body])    # REQUIRED — omit and you get "Missing target body"
feat = hp.CommitFeature(); hp.Destroy()
```

---

## 2.8 Malzeme atama (NX MatML kütüphanesi)

Kanıt: Steel yüklendi, kütle 1.1847 kg → ρ = 7.83 g/cm³ (NX Steel için doğru).

```python
pm  = part.MaterialManager.PhysicalMaterials
mat = pm.LoadFromNxmatmllibrary("Steel")       # from the NX MatML library
mat.AssignObjects([body])                      # assignment lives on the MATERIAL object, not the collection

# to reuse an already-loaded material instead of loading twice:
# pm.GetLoadedLibraryMaterial("physicalmateriallibrary.xml", "Steel")
```

> Sıkça belirtilen `MaterialManager.LoadMaterialsFromLibrary` / `AssignMaterialToBody` **mevcut değildir**. Yukarıdaki iki çağrıyı kullanın.

---

## 2.9 Kütle özellikleri ölçümü

Kanıt: V = 151324.66 mm³, A = 19258.49 mm², m = 1.1847 kg.

```python
uc = part.UnitCollection
units = [uc.FindObject(n) for n in
         ("SquareMilliMeter", "CubicMilliMeter", "Kilogram", "MilliMeter", "Newton")]   # exactly 5
mp = part.MeasureManager.NewMassProperties(units, 0.99, [body])    # accuracy 0.99
volume, area, mass, centroid = mp.Volume, mp.Area, mp.Mass, mp.Centroid
```

---

## 2.10 PMI Notu

Kanıt: bir PmiNote nesnesi oluşturuldu.

```python
nb = part.Annotations.CreatePmiNoteBuilder(NXOpen.Annotations.SimpleDraftingAid.Null)
nb.Text.TextBlock.SetText(["LINE 1", "LINE 2"])         # SetText is on TextBlock, not on Text
nb.Origin.Origin.SetValue(NXOpen.TaggedObject.Null, part.Views.WorkView,
                          NXOpen.Point3d(0.0, 0.0, 80.0))
note = nb.Commit(); nb.Destroy()
```

> Doğru giriş noktası `Annotations.CreatePmiNoteBuilder(None)`'dır; `PmiNotes.CreatePmiNote(...)` mevcut değildir. Metin `.Text.TextBlock.SetText([...])` üzerinden ayarlanır.

---

## 2.11 Headless görüntü dışa aktarma — MÜMKÜN DEĞİL

Kimse bununla vakit kaybetmesin diye buraya listelendi: headless bir journal'dan PNG render etmek çalışamaz — çünkü grafik penceresi yoktur. Bkz. [00-getting-started.md](00-getting-started.md#the-one-thing-that-does-not-work-headless-image-export). Görüntü dışa aktarmayı etkileşimli GUI'de yapın.

---

### Bunların gerçek olduğuna dair akıl sağlığı kontrolü

80×60×30 bir blok + Ø20×25 bir boss, tam olarak analitik toplama (144000 + 7853.98) eşit **V = 151853.98 mm³** ölçüldü. Bir blend + chamfer sonrasında **151324.66 mm³**'e düştü (makul miktarda malzeme kaldırılmış). Steel atamak **1.1847 kg → ρ = 7.829 g/cm³** verdi, bu da NX'in Steel'iyle eşleşiyor. [examples/block_with_boss.py](../examples/block_with_boss.py) içindeki örnek bunu yeniden üretir.
