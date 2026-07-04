> 🌐 [English](../05-capability-inventory.md) · **Türkçe**

# 05 · Yetenek Envanteri

Gündelik feature'ların ötesinde, NXOpen geniş bir araç kutusu sunar. Bu, headless çalışma için bilinmeye değer parçaların stub'lardan taranmış, imzaları (signature) doğrulanmış bir envanteridir. Kesin imzaları kendi `.../UGOPEN/pythonStubs/` dizininize göre teyit edin — onlar sizin kurulumunuzla eşleşir.

## `part.Features` üzerindeki feature factory'leri

Var olduğunu bilmeyebileceğiniz kullanışlı builder'lar (hepsi `Create*`):

```
BlockFeatureBuilder, CylinderBuilder, ConeBuilder, SphereBuilder, TubeBuilder,
HelixBuilder, SweptBuilder, RuledBuilder, ThroughCurvesBuilder, ThroughCurveMeshBuilder,
StudioSplineBuilderEx, FitCurveBuilder, TextBuilder, ThickenBuilder, SewBuilder,
TrimBody2Builder, SplitBodyBuilderUsingCollector, DeleteFaceBuilder,
MoveObjectBuilder, ScaleBuilder, PatternGeometryBuilder, ExtractFaceBuilder (copy a body),
WaveLinkBuilder (WAVE link), BooleanBuilderUsingCollector, DatumPlaneBuilder,
DatumCsysBuilder, HoleFeatureBuilder (legacy hole), EmbossBuilder, OffsetSurfaceBuilder
```

## Var olan iki gövdeyi birleştirme / çıkarma

Bağımsız (standalone) boolean feature'ı (satır içi extrude/revolve yolu uymadığında):

```python
bb = part.Features.CreateBooleanBuilderUsingCollector(NXOpen.Features.BooleanFeature.Null)
bb.Operation = NXOpen.Features.Feature.BooleanType.Subtract
bb.Target = target_body
bb.Tool   = tool_body                    # or use the Target/Tool body collectors
feat = bb.CommitFeature()
```

Builder'sız kısayol:

```python
part.Features.CreateUniteFeature(target, keep_target, [tools], keep_tools, allow_nonassociative)
```

## Bir gövdeyi parametrik olarak taşıma / döndürme

```python
mo = part.Features.CreateMoveObjectBuilder(NXOpen.Features.MoveObject.Null)
mo.ObjectToMoveObject.Add(body)
mo.TransformMotion.Option = NXOpen.GeometricUtilities.ModlMotion.Options.DeltaXyz
mo.TransformMotion.DeltaX = 25.0
mo.TransformMotion.DeltaY = 0.0
mo.TransformMotion.DeltaZ = 10.0
mo.MoveObjectResult = NXOpen.Features.MoveObjectBuilder.MoveObjectResultOptions.CopyOriginal  # or move in place
mo.Commit(); mo.Destroy()
# Rotate: Option = Angle, then set AngularAxis (Axis) and Angle (Expression)
```

## Montajlar (assembly) — bir bileşen (component) ekleme ve kısıtlama (constraint)

```python
comp, status = part.ComponentAssembly.AddComponent(
    "C:/parts/widget.prt", "MODEL", "WIDGET_1", NXOpen.Point3d(0, 0, 0), orient_m3x3, 1)

pos = part.ComponentAssembly.Positioner
pos.BeginAssemblyConstraints()
c = pos.CreateConstraint(True)
c.ConstraintType      = NXOpen.Positioning.Constraint.Type.Touch          # there is no "Align" type…
c.ConstraintAlignment = NXOpen.Positioning.Constraint.Alignment.CoAlign   # …Touch + CoAlign = an align
c.CreateConstraintReference(comp,  geo1, False, False)
c.CreateConstraintReference(comp2, geo2, False, False)
c.SetExpression("10")                                                     # for a Distance constraint
pos.EndAssemblyConstraints()

# Move a placed component:
# part.ComponentAssembly.MoveComponent(comp, Vector3d, Matrix3x3)
```

## Dışa aktarma (export) formatları (`session.DexManager.Create*`)

```
STEP (Ap203 / Ap214 / Ap242 / Ap242ED2), Parasolid, IGES, ACIS,
CATIA v4/v5, DXF/DWG, STL, 3MF, OBJ, IFC, USDZ, NXto2d …
```

> **JT başka bir yerde yaşar:** `session.PvtransManager.CreateJtCreator()` — `DexManager` üzerinde `CreateJtCreator` **yoktur**.

## Eğriler — helis (helix) & serbest form spline

- **Helis** — `CreateHelixBuilder`: `SizeOption` (Diameter/Radius), `PitchLaw`/`SizeLaw` (LawBuilder), `NumberOfTurns` (string), `TurnDirection` (RightHand/LeftHand), `CoordinateSystem`.
- **Spline** — `CreateStudioSplineBuilderEx(None)`: `Type` = ThroughPoints/ByPoles, `Degree`, ve noktalar şu şekilde eklenir:
  `ConstraintManager.CreateGeometricConstraintData()` → `.Point = part.Points.CreatePoint(...)` → `Append`.
  (`CurveCollection` üzerinde `CreateSpline` yoktur.)

## Görsel ayrım & metadata

```python
# Body colour (helps tell parts apart in the Part Navigator / exports)
dm = session.DisplayManager.NewDisplayModification()
dm.NewColor = 186
dm.ApplyToAllFaces = True
dm.Apply([body]); dm.Dispose()

# Manufacturing/BOM attribute on a body
body.SetUserAttribute("PART_NO", -1, "WIDGET-0042", NXOpen.Update.Option.Now)
```

## Oturum (session) & parça (part) yaşam döngüsü (çok parçalı toplu derlemeler)

```python
# Close one part (whole tree):
part.Close(NXOpen.BasePart.CloseWholeTree.TrueValue,
           NXOpen.BasePart.CloseModified.CloseModified, None)

# Close everything between builds:
session.Parts.CloseAll(NXOpen.BasePart.CloseModified.CloseModified, None)

# Undo marks bracket every feature; DoUpdate applies them:
mark = session.SetUndoMark(NXOpen.Session.MarkVisibility.Visible, "step")
session.UpdateManager.DoUpdate(mark)

# Safe delete = queue + update:
session.UpdateManager.AddToDeleteList(objs)
session.UpdateManager.DoUpdate(mark)
```
