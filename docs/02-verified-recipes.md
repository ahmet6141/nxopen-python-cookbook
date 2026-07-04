# 02 · Verified Recipes

Copy-paste feature recipes. **Every one of these was committed successfully in a live headless NX 2506 journal** and the resulting body inspected (face counts, volume, mass). Where a commonly-cited signature is wrong, the correct one is here.

Common preamble:

```python
import NXOpen, NXOpen.Features, NXOpen.GeometricUtilities, NXOpen.Annotations
session = NXOpen.Session.GetSession()
part = session.Parts.NewBaseDisplay(path, NXOpen.BasePart.Units.Millimeters)
```

> **Golden rule for all builders below:** a failed `Commit()` **poisons the builder** — do not retry on the same object. Recreate the builder from scratch each attempt. And never `import NXOpen.SubModule` *inside a function* (it makes `NXOpen` a local name for the whole function → *"cannot access local variable 'NXOpen'"*); put submodule imports at module top.

---

## 2.1 Edge Blend (fillet)

Proof: face count went 8 → 12.

```python
ebb  = part.Features.CreateEdgeBlendBuilder(NXOpen.Features.Feature.Null)
col  = part.ScCollectors.CreateCollector()
rule = part.ScRuleFactory.CreateRuleEdgeDumb(edges)      # edges: list[Edge]
col.ReplaceRules([rule], False)
ebb.AddChainset(col, "4")                                # radius is a STRING EXPRESSION, not a number/index
feat = ebb.CommitFeature(); ebb.Destroy()
```

> The single most common EdgeBlend failure online comes from the wrong signature. It is **`AddChainset(ScCollector, "radius")`** — a smart-collector plus a radius *string* — **not** `AddChainset(edge, index)`. `AddVariableRadiusData` is for variable-radius blends and has a different signature entirely.

---

## 2.2 Chamfer

Proof: face count 12 → 13.

```python
cb  = part.Features.CreateChamferBuilder(NXOpen.Features.Feature.Null)
col = part.ScCollectors.CreateCollector()
col.ReplaceRules([part.ScRuleFactory.CreateRuleEdgeDumb(edges)], False)
cb.SmartCollector = col                                            # edges go here, as a collector
cb.Option      = NXOpen.Features.ChamferBuilder.ChamferOption.SymmetricOffsets
cb.FirstOffset = "2"                                               # string; FirstOffsetExp is read-only
feat = cb.CommitFeature(); cb.Destroy()
```

> There is **no** `AddChainsToCollector([edge])` method. Assign the collector to `SmartCollector`.

---

## 2.3 Draft (Face)

The most fiddly of the set — angle comes through an expression-collector set, and tolerances must be set explicitly.

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

> Two traps here: `SymmetricAngle` is a **bool**, not the angle carrier — the angle rides on the `ExpressionCollectorSet`. And the unit argument to `CreateExpressionCollectorSet` must be **`""`** — passing `"Degrees"`/`"deg"` raises *"invalid unit measure."*

---

## 2.4 Symbolic Thread

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

Notes:
- **Use `Input.Manual`.** The standard thread table (`NX_Thread_Standard.xml`) throws *"Standard data not found"* under headless.
- **Thread before chamfer.** If a chamfer has already eaten the top edge of the cylinder, the neighbouring start face becomes invalid. Apply the thread first, or try multiple candidate `StartObject` faces in sequence.

---

## 2.5 Shell

Proof: volume 64000 → ~14000 mm³.

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

## 2.6 Mirror Body

Proof: body count 3 → 4.

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

> `CreateMirrorBodyBuilder` **does exist** (some docs claim otherwise). It needs a genuine **fixed datum plane** — a `Planes.CreatePlane` object is rejected.

---

## 2.7 Hole Package

Proof: face count 8 → 9.

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

## 2.8 Assign material (NX MatML library)

Proof: Steel loaded, mass 1.1847 kg → ρ = 7.83 g/cm³ (correct for NX Steel).

```python
pm  = part.MaterialManager.PhysicalMaterials
mat = pm.LoadFromNxmatmllibrary("Steel")       # from the NX MatML library
mat.AssignObjects([body])                      # assignment lives on the MATERIAL object, not the collection

# to reuse an already-loaded material instead of loading twice:
# pm.GetLoadedLibraryMaterial("physicalmateriallibrary.xml", "Steel")
```

> The often-cited `MaterialManager.LoadMaterialsFromLibrary` / `AssignMaterialToBody` **do not exist**. Use the two calls above.

---

## 2.9 Mass properties measurement

Proof: V = 151324.66 mm³, A = 19258.49 mm², m = 1.1847 kg.

```python
uc = part.UnitCollection
units = [uc.FindObject(n) for n in
         ("SquareMilliMeter", "CubicMilliMeter", "Kilogram", "MilliMeter", "Newton")]   # exactly 5
mp = part.MeasureManager.NewMassProperties(units, 0.99, [body])    # accuracy 0.99
volume, area, mass, centroid = mp.Volume, mp.Area, mp.Mass, mp.Centroid
```

---

## 2.10 PMI Note

Proof: a PmiNote object was created.

```python
nb = part.Annotations.CreatePmiNoteBuilder(NXOpen.Annotations.SimpleDraftingAid.Null)
nb.Text.TextBlock.SetText(["LINE 1", "LINE 2"])         # SetText is on TextBlock, not on Text
nb.Origin.Origin.SetValue(NXOpen.TaggedObject.Null, part.Views.WorkView,
                          NXOpen.Point3d(0.0, 0.0, 80.0))
note = nb.Commit(); nb.Destroy()
```

> The correct entry point is `Annotations.CreatePmiNoteBuilder(None)`; `PmiNotes.CreatePmiNote(...)` does not exist. Text is set through `.Text.TextBlock.SetText([...])`.

---

## 2.11 Headless image export — NOT possible

Listed here so nobody wastes time on it: rendering a PNG from a headless journal cannot work — there is no graphics window. See [00-getting-started.md](00-getting-started.md#the-one-thing-that-does-not-work-headless-image-export). Do image export in the interactive GUI.

---

### Sanity check that these are real

An 80×60×30 block + a Ø20×25 boss measured **V = 151853.98 mm³**, exactly the analytic sum (144000 + 7853.98). After a blend + chamfer it dropped to **151324.66 mm³** (a sensible amount of material removed). Assigning Steel gave **1.1847 kg → ρ = 7.829 g/cm³**, matching NX's Steel. The example in [examples/block_with_boss.py](../examples/block_with_boss.py) reproduces this.
