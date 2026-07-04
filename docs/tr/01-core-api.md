> 🌐 [English](../01-core-api.md) · **Türkçe**

# 01 · Çekirdek NXOpen API

Neredeyse her headless journal'da kullandığın primitifler. Hepsi NX 2506 üzerinde doğrulanmıştır.

## Session & Part

```python
import NXOpen
session = NXOpen.Session.GetSession()

# Create a fresh millimetre part. NewBaseDisplay may return a tuple on some paths.
part = session.Parts.NewBaseDisplay(path, NXOpen.BasePart.Units.Millimeters)
```

> **Tuzak:** doğrusu `NXOpen.BasePart.Units.Millimeters`'dır, **`Part.Units.Millimeters` değil** — ikincisi *"Second parameter is invalid."* hatasını fırlatır.

> **Tuzak:** `NewBaseDisplay` mevcut bir `.prt`'nin **üzerine yazmayı reddeder**. Aynı yola yeniden build alacaksan önce hedef dosyayı sil.

## Expression'lar

Parametrik boyutlar expression olarak yaşar. Bunları her zaman `RightHandSide` üzerinden sür:

```python
e = part.Expressions.CreateWithUnits("width=80", unit)        # unit: Millimeter / Degrees / Number
part.Expressions.EditWithUnits(e, unit, "100")               # new RHS
```

> **Tuzak:** değerleri **`RightHandSide`** (bir string) ile ayarla, `.Value` ile değil. Bir uzunluk üzerinde `.Value` ataması ekstra bir birim dönüşümü uygular ve sessizce **25.4×** hatası alırsın (inç↔mm).

## Extrude — iş atı

```python
ext = part.Features.CreateExtrudeBuilder(NXOpen.Features.Feature.Null)
ext.Section = section
ext.Direction = part.Directions.CreateDirection(
    origin, vector, NXOpen.SmartObject.UpdateOption.WithinModeling)
ext.Limits.StartExtend.Value.RightHandSide = "0"
ext.Limits.EndExtend.Value.RightHandSide   = "length"        # literal or an expression name
ext.BooleanOperation.Type = NXOpen.GeometricUtilities.BooleanOperation.BooleanType.Unite
ext.BooleanOperation.SetTargetBodies([target_body])          # see Booleans below
feat = ext.CommitFeature()
ext.Destroy()
```

## Revolve

```python
rev = part.Features.CreateRevolveBuilder(NXOpen.Features.Feature.Null)
rev.Section = section
rev.Axis = part.Axes.CreateAxis(point, direction, NXOpen.SmartObject.UpdateOption.WithinModeling)
rev.Limits.EndExtend.Value.RightHandSide = "360"
rev.BooleanOperation.Type = bool_type
feat = rev.CommitFeature(); rev.Destroy()
```

Bir revolve, **tek bir kapalı profil** alır ve onu bir eksen etrafında döndürür — herhangi bir dönel gövde (şaft, göbek, disk, kabartma) için idealdir. Birçok silindiri union etmek yerine tek bir kapalı profili tercih et; bkz. [04-boolean-and-geometry-rules.md](04-boolean-and-geometry-rules.md).

## Section (eğri zincirleri extrude/revolve'u besler)

```python
section = part.Sections.CreateSection(0.0095, 0.001, 0.5)     # chaining / distance / angle tol
section.AllowSelfIntersection(False)
rule = part.ScRuleFactory.CreateRuleCurveDumb(curves)         # NOT CreateRuleBaseCurveDumb (deprecated)
section.AddToSection([rule], curves[0],
                     NXOpen.NXObject.Null, NXOpen.NXObject.Null,
                     help_pt, NXOpen.Section.Mode.Create, False)
```

## Eğriler

```python
line = part.Curves.CreateLine(p0, p1)                         # p = NXOpen.Point3d(x, y, z)
arc  = part.Curves.CreateArc(center, xDir, yDir, radius, start_angle, end_angle)  # angles in RADIANS
```

> **Tuzak:** her koordinat bir **float** olmalıdır. `Point3d` / arc parametrelerine bir `int` geçirmek *"Expecting double."* hatasını fırlatır. `0` değil `0.0` yaz.

## Boolean'lar

Çoğu prosedürel iş için ayrı bir boolean feature'a **ihtiyacın yoktur** — bunu doğrudan extrude/revolve builder üzerinde inline yap:

```python
builder.BooleanOperation.Type = NXOpen.GeometricUtilities.BooleanOperation.BooleanType.Unite   # or Subtract
builder.BooleanOperation.SetTargetBodies([target_body])
```

Gerçekten iki *mevcut* gövdeyi birleştirmen gerektiğinde, [05-capability-inventory.md](05-capability-inventory.md) içindeki ayrı `BooleanBuilder`'a ve `CreateUniteFeature` kısayoluna bak. Neyin gerçekten kaynaştığı (ve neyin sessizce kaynaşmadığı) [04-boolean-and-geometry-rules.md](04-boolean-and-geometry-rules.md) içinde ele alınmıştır.

## Update döngüsü — zorunlu

NX, sen söyleyene kadar modeli yenilemez. Her feature'ı bir undo mark + update ile sar:

```python
mark = session.SetUndoMark(NXOpen.Session.MarkVisibility.Visible, "add boss")
# ... create the feature ...
session.UpdateManager.DoUpdate(mark)                          # REQUIRED after each feature
# on failure you can roll back:
# session.UndoToMark(mark, "add boss")
```

> **Tuzak:** `DoUpdate`'i atlarsan model sessizce ilerlemez — sonraki feature'lar eski (stale) geometriye bağlanır ve kafa karıştırıcı şekillerde başarısız olur.

Güvenli silme aynı manager üzerinden yapılır:

```python
session.UpdateManager.AddToDeleteList(objs)
session.UpdateManager.DoUpdate(mark)
```

## Gövde adlandırma (Part Navigator'da görünür)

```python
body.SetName("Front_Housing")        # alphanumeric + underscore, keep it under ~48 chars
```

Tuttuğun her gövdeyi adlandır — bu, Part Navigator'ı (ve alt akıştaki BOM/inceleme süreçlerini) okunabilir kılar ve `built N bodies` ile `named N bodies` sayılarını karşılaştırarak yetim (orphan) gövdeleri yakalamanı sağlar (bkz. [04](04-boolean-and-geometry-rules.md)).

## STEP dışa aktarma (AP242)

```python
sc = session.DexManager.CreateStepCreator()
sc.ExportAs = NXOpen.StepCreator.ExportAsOption.Ap242            # Ap203 / Ap214 / Ap242 / Ap242ED2
sc.ObjectTypes.Solids = True
sc.ExportSelectionBlock.SelectionScope = NXOpen.ObjectSelector.Scope.SelectedObjects
sc.ExportSelectionBlock.SelectionComp.Add(bodies)               # SOLID BODIES ONLY
sc.InputFile  = part.FullPath
sc.OutputFile = out_path
sc.Commit(); sc.Destroy()
```

## Parasolid dışa aktarma — isteğe bağlı ve kırılgan

```python
# NX 2506: session.DexManager.CreateParasolidExporter()
# (older: CreateParasolidCreator / theUF.Ps.ExportData)
```

> **Tuzak — session zehirlenmesi:** yalnızca **seçili solid gövdeleri** dışa aktar, asla tüm part'ı değil. Yardımcı (construction) eğriler bir Parasolid export'a dahil olursa *"Modeler error: please report fault,"* hatasıyla karşılaşabilirsin; bu da session'ı bozar. Parasolid export'u isteğe bağlı ve ölümcül olmayan bir işlem olarak ele al ve "please report fault" gördüğünde **NX'i tamamen yeniden başlat** — session artık kurtarılamaz.

## Temiz bir statik part için parametrelerin nötrleştirilmesi

Aptal-solid (dumb-solid) bir `.prt` göndermek için (feature ağacı yok, artakalan yardımcı eğri yok):

```python
rpb = part.Features.CreateRemoveParametersBuilder()
rpb.Objects.Add(solids)
rpb.Commit(); rpb.Destroy()
# then delete the construction curves via the update/delete list
```

## Dairesel pattern (opsiyonel; imzalar sürümler arasında değişkenlik gösterir)

```python
pfb = part.Features.CreatePatternFeatureBuilder(NXOpen.Features.Feature.Null)
pfb.PatternService.PatternType = NXOpen.GeometricUtilities.PatternDefinition.PatternEnum.Circular
pfb.FeatureList.Add([feature])                                  # NOT AddFeatureToPattern
circ = pfb.PatternService.CircularDefinition
circ.RotationAxis = axis_obj
circ.AngularSpacing.SpaceType = NXOpen.GeometricUtilities.PatternSpacing.SpacingType.Offset  # NOT CountAndPitch
circ.AngularSpacing.NCopies.RightHandSide       = str(count)
circ.AngularSpacing.PitchDistance.RightHandSide = str(angle)
```
