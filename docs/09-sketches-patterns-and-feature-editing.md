# 09 · Sketches, Patterns & Editing Features After the Fact

> 🌐 **English** · [Türkçe](tr/09-sketches-patterns-and-feature-editing.md)

Three modeling capabilities that turn one-shot journals into maintainable generators: creating a **real sketch** headless when you genuinely need one, **patterning** features instead of looping builders, and **editing features that already exist** — suppress, re-parameterize, delete — without rebuilding the part.

> ⚠️ **Verification status:** unlike docs 01–07, the recipes on this page are **not yet live-verified on NX 2506**. They are assembled from the official API reference, GUI-recorded journal patterns, and community examples; lines marked `# check your stubs` are the ones most likely to differ between releases. Verify on your install and report results per [CONTRIBUTING](../CONTRIBUTING.md).

All snippets assume the boilerplate from [01-core-api.md](01-core-api.md): `session = NXOpen.Session.GetSession()` and `part` is the work part.

---

## 9.1 Do you actually need a sketch?

Usually **no**. Headless generation works best with free curves — `part.Curves.CreateLine/CreateArc` (01) and sketch-free splines (7.1) feed a `Section` directly, with no sketch object, no constraint solver, no active-sketch state to manage. That is why 07's first trap steers you *away* from `CreateSketchSplineBuilder`.

Reach for a real sketch only when you need what only a sketch gives you:

- **constraint-solver behavior** — geometry that re-solves when a driving dimension changes from Tools → Expressions;
- a profile a **human will edit later in the GUI**, double-clicking dimensions;
- **sketch-owned features** downstream that expect a sketch (some hole/slot workflows).

## 9.2 A minimal headless sketch

The classic pattern: create the sketch on a plane, activate it, add externally-created curves with `AddGeometry`, deactivate. The curves become sketch members and the sketch feeds `Section` exactly like free curves do:

```python
sib = part.Sketches.CreateSketchInPlaceBuilder2(NXOpen.Sketch.Null)
sib.PlaneReference = datum_plane              # a fixed datum plane (2.6) or a planar face
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

> Boolean-named enum members in the Python binding are spelled **`TrueValue` / `FalseValue`** (`ViewReorient.FalseValue`, `CloseWholeTree.TrueValue` in 05) — for the same reason as the `MatchKnotsTypes.NotSet` trap in 7.1: `True`/`False`/`None` are Python keywords and `.True` would be a `SyntaxError`.
>
> Forgetting **`Deactivate`** leaves the sketch active for the rest of the session — later feature builders then misbehave in confusing ways. Treat Activate/Deactivate like a matched pair (try/finally if the middle can raise).

Dimensions and geometric constraints can be added programmatically (`sketch.CreateDiameterDimension`, coincident/parallel constraint builders — mine your stubs), but if you find yourself scripting many constraints, step back: computing the coordinates yourself and skipping the solver is nearly always the more robust headless move.

---

## 9.3 Pattern Feature — linear

The API-side of Pattern Feature carries two known traps ([03](03-pitfalls.md) #6–7): features are added as a **list** via `FeatureList.Add([feat])`, and spacing is **`SpacingType.Offset`** (`CountAndPitch` does not exist):

```python
pb = part.Features.CreatePatternFeatureBuilder(NXOpen.Features.Feature.Null)
pb.FeatureList.Add([boss_feat])                       # a LIST — pitfall #6

rect = pb.PatternService.RectangularDefinition
rect.XDirection = part.Directions.CreateDirection(
    NXOpen.Point3d(0.0, 0.0, 0.0), NXOpen.Vector3d(1.0, 0.0, 0.0),
    NXOpen.SmartObject.UpdateOption.WithinModeling)
rect.XSpacing.SpaceType = NXOpen.GeometricUtilities.PatternSpacing.SpacingType.Offset   # pitfall #7
rect.XSpacing.NCopies.RightHandSide       = "4"
rect.XSpacing.PitchDistance.RightHandSide = "25"
# optional second direction: rect.YDirection + rect.YSpacing, same shape

feat = pb.CommitFeature(); pb.Destroy()
```

## 9.4 Pattern Feature — circular, and Pattern Geometry

```python
pb = part.Features.CreatePatternFeatureBuilder(NXOpen.Features.Feature.Null)
pb.FeatureList.Add([hole_feat])
pb.PatternService.PatternType = NXOpen.GeometricUtilities.PatternDefinition.PatternEnum.Circular   # check your stubs

circ = pb.PatternService.CircularDefinition
circ.RotationAxis = part.Axes.CreateAxis(
    part.Points.CreatePoint(NXOpen.Point3d(0.0, 0.0, 0.0)),
    part.Directions.CreateDirection(NXOpen.Point3d(0.0, 0.0, 0.0), NXOpen.Vector3d(0.0, 0.0, 1.0),
                                    NXOpen.SmartObject.UpdateOption.WithinModeling),
    NXOpen.SmartObject.UpdateOption.WithinModeling)   # check your stubs: axis assignment varies
circ.AngularSpacing.SpaceType = NXOpen.GeometricUtilities.PatternSpacing.SpacingType.Offset
circ.AngularSpacing.NCopies.RightHandSide    = "6"
circ.AngularSpacing.PitchAngle.RightHandSide = "60"
feat = pb.CommitFeature(); pb.Destroy()
```

**Pattern Feature vs Pattern Geometry vs a Python loop:**

- **Pattern Feature** replays a *feature* — parametric, shows one pattern node in the tree, and re-solves when the master changes. Best for GUI-editable parts.
- **Pattern Geometry** (`CreatePatternGeometryBuilder`) copies *bodies/curves* without feature history — lighter, but the copies don't follow the master.
- **A plain Python loop** calling the builder N times is often the most robust headless answer: every instance is independent, individually named (7.6), and individually boolean-able per the [04 rules](04-boolean-and-geometry-rules.md). Patterns interact with inline booleans in release-dependent ways — when a pattern misbehaves, fall back to the loop.

---

## 9.5 Copying, scaling, moving bodies

The move/rotate recipe lives in [05](05-capability-inventory.md) (`MoveObjectBuilder`, `DeltaXyz` / `Angle`); note again its `CopyOriginal` option — the cheapest "copy a body" there is. Two companions:

```python
# Scale — uniform about a point
sc = part.Features.CreateScaleBuilder(NXOpen.Features.Feature.Null)
sc.Type = NXOpen.Features.ScaleBuilder.Types.Uniform
sc.BodyCollector.ReplaceRules([part.ScRuleFactory.CreateRuleBodyDumb([body])], False)
sc.Point = part.Points.CreatePoint(NXOpen.Point3d(0.0, 0.0, 0.0))
sc.Factor.RightHandSide = "1.05"                      # check your stubs: UniformFactor on some releases
feat = sc.CommitFeature(); sc.Destroy()
```

```python
# Extract Body — an associative copy of a whole body (05 lists the builder)
eb = part.Features.CreateExtractFaceBuilder(NXOpen.Features.Feature.Null)
eb.Type = NXOpen.Features.ExtractFaceBuilder.ExtractType.Body
eb.BodyToExtract.Add(body)                            # check your stubs
eb.Associative = False                                # False -> independent copy, immune to source edits
feat = eb.CommitFeature(); eb.Destroy()
```

For mirroring, the verified recipe is [2.6](02-verified-recipes.md) — remember it wants a **fixed** datum plane.

---

## 9.6 Editing features after the build

A generated part is not read-only. The pattern that makes journals *maintainable* — find by name, change the driver, update:

```python
feats = {f.Name: f for f in part.Features}            # names you assigned via SetName (7.6)
wing  = feats["MYPROJ_WING"]

# 1) suppress / unsuppress — cheap "configuration" switching
wing.Suppress()
# ...export the suppressed variant...
wing.Unsuppress()

# 2) re-parameterize: edit the DRIVING EXPRESSION, then run the update loop
for ex in part.Expressions:
    if ex.Name == "myproj_wing_span":
        ex.RightHandSide = "1450"                     # RightHandSide, never .Value — pitfall #11
mark = session.SetUndoMark(NXOpen.Session.MarkVisibility.Visible, "edit span")
session.UpdateManager.DoUpdate(mark)                  # nothing moves until this runs — pitfall #20

# 3) delete a feature safely — queue + update, never a bare delete
session.UpdateManager.AddToDeleteList([wing])
session.UpdateManager.DoUpdate(mark)
```

Three rules carried over from the verified docs, because they all still bite here:

- **The update loop is mandatory** after any edit (pitfall #20) — an edited expression without `DoUpdate` leaves the model stale.
- **Deleting a parent breaks children** (7.3): check `feature.GetChildren()` first, or delete leaf-first. `AddToDeleteList` + `DoUpdate` at least fails visibly instead of corrupting.
- **A failed edit poisons nothing** if you bracket it with an undo mark — `session.UndoToMark(mark, None)` rolls the part back to the pre-edit state, which is the closest thing headless has to Ctrl+Z.

This trio — named features (7.6), expression drivers (7.7), suppress/edit/delete (here) — is what separates a *generator you re-run* from a *script you ran once*.
