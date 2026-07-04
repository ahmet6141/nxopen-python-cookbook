# 01 · Core NXOpen API

The primitives you use in almost every headless journal. All verified on NX 2506.

## Session & Part

```python
import NXOpen
session = NXOpen.Session.GetSession()

# Create a fresh millimetre part. NewBaseDisplay may return a tuple on some paths.
part = session.Parts.NewBaseDisplay(path, NXOpen.BasePart.Units.Millimeters)
```

> **Trap:** it is `NXOpen.BasePart.Units.Millimeters`, **not** `Part.Units.Millimeters` — the latter raises *"Second parameter is invalid."*

> **Trap:** `NewBaseDisplay` **refuses to overwrite** an existing `.prt`. Delete the target file first if you're rebuilding to the same path.

## Expressions

Parametric dimensions live as expressions. Always drive them through `RightHandSide`:

```python
e = part.Expressions.CreateWithUnits("width=80", unit)        # unit: Millimeter / Degrees / Number
part.Expressions.EditWithUnits(e, unit, "100")               # new RHS
```

> **Trap:** set values via **`RightHandSide`** (a string), not `.Value`. Assigning `.Value` on a length applies an extra unit conversion and you get a silent **25.4×** error (inches↔mm).

## Extrude — the workhorse

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

A revolve takes a **single closed profile** and spins it about an axis — ideal for any body of revolution (shafts, hubs, discs, bosses). Prefer one closed profile over unioning many cylinders; see [04-boolean-and-geometry-rules.md](04-boolean-and-geometry-rules.md).

## Section (curve chains feed extrude/revolve)

```python
section = part.Sections.CreateSection(0.0095, 0.001, 0.5)     # chaining / distance / angle tol
section.AllowSelfIntersection(False)
rule = part.ScRuleFactory.CreateRuleCurveDumb(curves)         # NOT CreateRuleBaseCurveDumb (deprecated)
section.AddToSection([rule], curves[0],
                     NXOpen.NXObject.Null, NXOpen.NXObject.Null,
                     help_pt, NXOpen.Section.Mode.Create, False)
```

## Curves

```python
line = part.Curves.CreateLine(p0, p1)                         # p = NXOpen.Point3d(x, y, z)
arc  = part.Curves.CreateArc(center, xDir, yDir, radius, start_angle, end_angle)  # angles in RADIANS
```

> **Trap:** every coordinate must be a **float**. Passing an `int` into `Point3d` / arc parameters raises *"Expecting double."* Write `0.0`, not `0`.

## Booleans

For most procedural work you do **not** need a standalone boolean feature — do it inline on the extrude/revolve builder:

```python
builder.BooleanOperation.Type = NXOpen.GeometricUtilities.BooleanOperation.BooleanType.Unite   # or Subtract
builder.BooleanOperation.SetTargetBodies([target_body])
```

When you genuinely need to combine two *existing* bodies, see the standalone `BooleanBuilder` and the `CreateUniteFeature` shortcut in [05-capability-inventory.md](05-capability-inventory.md). What actually fuses (and what silently doesn't) is covered in [04-boolean-and-geometry-rules.md](04-boolean-and-geometry-rules.md).

## The update loop — mandatory

NX does not refresh the model until you tell it to. Wrap every feature in an undo mark + update:

```python
mark = session.SetUndoMark(NXOpen.Session.MarkVisibility.Visible, "add boss")
# ... create the feature ...
session.UpdateManager.DoUpdate(mark)                          # REQUIRED after each feature
# on failure you can roll back:
# session.UndoToMark(mark, "add boss")
```

> **Trap:** skip `DoUpdate` and the model silently doesn't advance — later features attach to stale geometry and fail in confusing ways.

Safe deletion goes through the same manager:

```python
session.UpdateManager.AddToDeleteList(objs)
session.UpdateManager.DoUpdate(mark)
```

## Body naming (visible in Part Navigator)

```python
body.SetName("Front_Housing")        # alphanumeric + underscore, keep it under ~48 chars
```

Name every body you keep — it makes the Part Navigator (and downstream BOM/inspection) legible, and lets you count `built N bodies` vs `named N bodies` to catch orphans (see [04](04-boolean-and-geometry-rules.md)).

## STEP export (AP242)

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

## Parasolid export — opt-in and fragile

```python
# NX 2506: session.DexManager.CreateParasolidExporter()
# (older: CreateParasolidCreator / theUF.Ps.ExportData)
```

> **Trap — session poisoning:** export **selected solid bodies only**, never the entire part. If construction curves get swept into a Parasolid export you can hit *"Modeler error: please report fault,"* which corrupts the session. Treat Parasolid export as opt-in and non-fatal, and if you ever see "please report fault," **restart NX completely** — the session is unrecoverable.

## Neutralising parameters for a clean static part

To ship a dumb-solid `.prt` (no feature tree, no leftover construction curves):

```python
rpb = part.Features.CreateRemoveParametersBuilder()
rpb.Objects.Add(solids)
rpb.Commit(); rpb.Destroy()
# then delete the construction curves via the update/delete list
```

## Circular pattern (optional; signatures drift between releases)

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
