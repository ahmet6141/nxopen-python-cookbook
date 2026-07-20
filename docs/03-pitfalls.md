# 03 · Pitfalls — the runtime trap list

> 🌐 **English** · [Türkçe](tr/03-pitfalls.md)

NXOpen fails at runtime, not at import, and the error strings rarely name the real cause. This is the consolidated list, each as **symptom → fix**. Grouped by where they bite.

## API surface / signatures

| # | Trap | Symptom → Fix |
|---|------|---------------|
| 1 | Wrong units enum | `Part.Units.Millimeters` → *"Second parameter is invalid."* Use **`BasePart.Units.Millimeters`**. |
| 2 | Deprecated section rule | Use **`CreateRuleCurveDumb`**; `CreateRuleBaseCurveDumb` is deprecated. |
| 3 | EdgeBlend signature | `AddChainset(edge, index)` fails. It is **`AddChainset(ScCollector, "radius")`** — collector + radius *string*. |
| 4 | Chamfer edge assignment | No `AddChainsToCollector`. Assign edges to **`SmartCollector`**; distance is `FirstOffset = "2"` (string). |
| 5 | Thread builder null | Create with **`Features.Thread.Null`**, not `Feature.Null`. |
| 6 | Pattern feature add | **`FeatureList.Add([feat])`**; there is no `AddFeatureToPattern`. |
| 7 | Pattern spacing | **`PatternSpacing.SpacingType.Offset`**; `CountAndPitch` doesn't exist. |
| 8 | Mirror body "missing" | `CreateMirrorBodyBuilder` **exists** and works — feed it a **fixed datum plane**, not a `Planes.CreatePlane`. |
| 9 | Material API | `LoadMaterialsFromLibrary` / `AssignMaterialToBody` don't exist. Use `PhysicalMaterials.LoadFromNxmatmllibrary(name)` → `mat.AssignObjects([body])`. |
| 10 | PMI note API | `PmiNotes.CreatePmiNote` doesn't exist. Use `Annotations.CreatePmiNoteBuilder(None)` → `Text.TextBlock.SetText([...])`. |

## Values & expressions

| # | Trap | Symptom → Fix |
|---|------|---------------|
| 11 | Expression value | Set **`RightHandSide`** (string), not `.Value` — `.Value` on a length applies a spurious **25.4×** conversion. |
| 12 | Float required | `Point3d` / arc args must be **floats** — an `int` raises *"Expecting double."* Write `0.0`. |
| 13 | Draft tolerance | Default `AngleTolerance` 0 → *"Angle tolerance is too small."* Set **`AngleTolerance = 0.5`**. |
| 14 | Shell tolerance | Default `Tolerance` 0 → *"Tolerance error."* Set **`Tolerance = 0.01`**. |
| 15 | Hole package through-body | ThroughBody → *"Tolerance Specification requires three numbers."* Use `Value` + depth + tip angle + `Tolerance = 0.01`. |
| 16 | Hole package target | Omitting the target → *"Missing target body."* Call `BooleanOperation.SetTargetBodies([body])`. |
| 17 | Expression collector unit | `CreateExpressionCollectorSet(col, "3", "", 0)` — the unit arg must be **empty string** `""`. `"Degrees"`/`"deg"` → *"invalid unit measure."* |
| 18 | Thread table headless | Standard table → *"Standard data not found."* Use `Input.Manual` and set the diameter/pitch expressions yourself. |
| 19 | Thread start face | *"Invalid thread start face"* — use an adjacent planar face; **thread before chamfer**; try candidate faces in sequence. |

## Lifecycle & session

| # | Trap | Symptom → Fix |
|---|------|---------------|
| 20 | Missing update | Model doesn't advance → set an undo mark and call **`UpdateManager.DoUpdate(mark)` after every feature**. |
| 21 | Overwrite refused | `NewBaseDisplay` won't write over an existing `.prt` → **delete the file first**. |
| 22 | Parasolid poisoning | Exporting the *entire part* (with construction curves) → *"Modeler error: please report fault."* Export **selected solid bodies only**. |
| 23 | Poisoned builder | A failed `Commit()` corrupts the builder — **recreate it**, never retry the same object. |
| 24 | Session poisoning | Once you see *"please report fault,"* the session is unrecoverable → **close NX fully and restart**. |
| 25 | Function-local import | `import NXOpen.X` *inside a function* makes `NXOpen` a local name → *"cannot access local variable 'NXOpen'."* Put submodule imports at **module top**. |

## Free-form / lofting

These come from [07-freeform-lofting.md](07-freeform-lofting.md) — building solids from stacked spline sections rather than a single extrude/revolve profile.

| # | Trap | Symptom → Fix |
|---|------|---------------|
| 26 | Sketch-bound spline builder | `CreateSketchSplineBuilder` needs an **active sketch** — with none open, `Commit()` raises *"Incorrect object for this operation."* Use **`CreateStudioSplineBuilderEx`** for sketch-free curves. |
| 27 | Multi-body mass properties returns zero | `NewMassProperties` on a collector holding **several** bodies (a multi-body kit) silently returns **0 volume / 0 area** — even though the single-body form works. Measure each body with its own single-body collector and sum the results. |
| 28 | `SetCornerPoints` on a scripted datum plane | Raises *"Datum plane undefinable"* even though GUI-recorded journals show it. Skip it — set `builder.ResizeDuringUpdate = True` and let NX size the plane. |
| 29 | Datum-by-name lookup | `Datums.FindObject("DATUM_CSYS(0) XZ plane")` only exists on parts built from that exact template → *"No object found with this name"* on a fresh/empty/differently-templated part. Search by **geometry** (normal direction) as a fallback, and create an absolute-origin datum CSYS as a last resort — see 07 §7.5. |

## Geometry (booleans that lie)

These deserve their own page because validation can't catch them without a real build — see **[04-boolean-and-geometry-rules.md](04-boolean-and-geometry-rules.md)**:

- Unite tools must **embed ≥15 mm** into the target; point- and line-contact never fuse.
- `loft` is effectively **create-only** for booleans in some builders — build hulls as one loft, unite everything else as prism/cylinder.
- A subtract tool fully **outside** the target fails *"Tool body completely outside target body."*
- The `hole` primitive reads position from its own `cx/cy/z0`, not a shared origin.
- A "successful" unite that lands on removed/void geometry silently leaves a **separate body** with no error — detect via `built N bodies` ≠ `named N bodies`.
