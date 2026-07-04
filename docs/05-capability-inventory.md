# 05 · Capability Inventory

Beyond the everyday features, NXOpen exposes a large toolbox. This is a stub-mined, signature-checked inventory of the parts worth knowing about for headless work. Confirm exact signatures against your own `.../UGOPEN/pythonStubs/` — they match your install.

## Feature factories on `part.Features`

Useful builders you may not know exist (all `Create*`):

```
BlockFeatureBuilder, CylinderBuilder, ConeBuilder, SphereBuilder, TubeBuilder,
HelixBuilder, SweptBuilder, RuledBuilder, ThroughCurvesBuilder, ThroughCurveMeshBuilder,
StudioSplineBuilderEx, FitCurveBuilder, TextBuilder, ThickenBuilder, SewBuilder,
TrimBody2Builder, SplitBodyBuilderUsingCollector, DeleteFaceBuilder,
MoveObjectBuilder, ScaleBuilder, PatternGeometryBuilder, ExtractFaceBuilder (copy a body),
WaveLinkBuilder (WAVE link), BooleanBuilderUsingCollector, DatumPlaneBuilder,
DatumCsysBuilder, HoleFeatureBuilder (legacy hole), EmbossBuilder, OffsetSurfaceBuilder
```

## Combine / subtract two existing bodies

Standalone boolean feature (when the inline extrude/revolve path doesn't fit):

```python
bb = part.Features.CreateBooleanBuilderUsingCollector(NXOpen.Features.BooleanFeature.Null)
bb.Operation = NXOpen.Features.Feature.BooleanType.Subtract
bb.Target = target_body
bb.Tool   = tool_body                    # or use the Target/Tool body collectors
feat = bb.CommitFeature()
```

Builder-free shortcut:

```python
part.Features.CreateUniteFeature(target, keep_target, [tools], keep_tools, allow_nonassociative)
```

## Move / rotate a body parametrically

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

## Assemblies — add a component and constrain it

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

## Export formats (`session.DexManager.Create*`)

```
STEP (Ap203 / Ap214 / Ap242 / Ap242ED2), Parasolid, IGES, ACIS,
CATIA v4/v5, DXF/DWG, STL, 3MF, OBJ, IFC, USDZ, NXto2d …
```

> **JT lives elsewhere:** `session.PvtransManager.CreateJtCreator()` — there is **no** `CreateJtCreator` on `DexManager`.

## Curves — helix & freeform spline

- **Helix** — `CreateHelixBuilder`: `SizeOption` (Diameter/Radius), `PitchLaw`/`SizeLaw` (LawBuilder), `NumberOfTurns` (string), `TurnDirection` (RightHand/LeftHand), `CoordinateSystem`.
- **Spline** — `CreateStudioSplineBuilderEx(None)`: `Type` = ThroughPoints/ByPoles, `Degree`, and points added via
  `ConstraintManager.CreateGeometricConstraintData()` → `.Point = part.Points.CreatePoint(...)` → `Append`.
  (There is no `CreateSpline` on `CurveCollection`.)

## Visual distinction & metadata

```python
# Body colour (helps tell parts apart in the Part Navigator / exports)
dm = session.DisplayManager.NewDisplayModification()
dm.NewColor = 186
dm.ApplyToAllFaces = True
dm.Apply([body]); dm.Dispose()

# Manufacturing/BOM attribute on a body
body.SetUserAttribute("PART_NO", -1, "WIDGET-0042", NXOpen.Update.Option.Now)
```

## Session & part lifecycle (multi-part batch builds)

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
