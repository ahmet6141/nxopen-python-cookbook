# 08 · Primitives, Sweeps & Surfacing

> 🌐 **English** · [Türkçe](tr/08-primitives-sweeps-and-surfacing.md)

Extrude, revolve (01) and Through-Curves lofts (07) cover most procedural solids — this page maps the **rest of the modeling toolbox**: analytic primitives, tubes and sweeps along 3D paths, ruled bodies, and the sheet-body workflow (offset → thicken → sew → trim) that turns surfaces into solids.

> ⚠️ **Verification status:** unlike docs 01–07, the recipes on this page are **not yet live-verified on NX 2506**. They are assembled from the official API reference, GUI-recorded journal patterns, and community examples; lines marked `# check your stubs` are the ones most likely to differ between releases. Treat this page as a map, verify on your install, and report results per [CONTRIBUTING](../CONTRIBUTING.md) — a before/after face count or volume is enough to promote a recipe to verified.

All snippets assume the boilerplate from [01-core-api.md](01-core-api.md): `session = NXOpen.Session.GetSession()` and `part` is the work part.

---

## 8.1 Analytic primitives — Block, Cylinder, Cone, Sphere

For rectangular or cylindrical stock these are simpler and faster than sketch + extrude, and they carry the same inline-boolean mechanism (`BooleanOption`) as extrude/revolve — so the [04 boolean rules](04-boolean-and-geometry-rules.md) apply unchanged.

```python
# Block — origin corner + three edge lengths (string expressions)
blk = part.Features.CreateBlockFeatureBuilder(NXOpen.Features.Feature.Null)
blk.SetOriginAndLengths(NXOpen.Point3d(0.0, 0.0, 0.0), "80", "60", "30")
blk.BooleanOption.Type = NXOpen.GeometricUtilities.BooleanOperation.BooleanType.Create
feat = blk.CommitFeature(); blk.Destroy()
body = feat.GetBodies()[0]
```

```python
# Cylinder — axis (point + direction) + diameter/height expressions
cyl = part.Features.CreateCylinderBuilder(NXOpen.Features.Feature.Null)
cyl.Axis = part.Axes.CreateAxis(
    part.Points.CreatePoint(NXOpen.Point3d(0.0, 0.0, 30.0)),
    part.Directions.CreateDirection(NXOpen.Point3d(0.0, 0.0, 30.0), NXOpen.Vector3d(0.0, 0.0, 1.0),
                                    NXOpen.SmartObject.UpdateOption.WithinModeling),
    NXOpen.SmartObject.UpdateOption.WithinModeling)          # check your stubs: some releases take the axis pieces differently
cyl.Diameter.RightHandSide = "20"
cyl.Height.RightHandSide   = "25"
cyl.BooleanOption.Type = NXOpen.GeometricUtilities.BooleanOperation.BooleanType.Unite
cyl.BooleanOption.SetTargetBodies([body])
feat = cyl.CommitFeature(); cyl.Destroy()
```

```python
# Cone — two diameters + height
cone = part.Features.CreateConeBuilder(NXOpen.Features.Feature.Null)
cone.Type = NXOpen.Features.ConeBuilder.Types.DiametersAndHeight
cone.BaseDiameter.RightHandSide = "40"
cone.TopDiameter.RightHandSide  = "10"       # 0 -> a full cone with an apex
cone.Height.RightHandSide       = "35"
feat = cone.CommitFeature(); cone.Destroy()

# Sphere — center point + diameter
sph = part.Features.CreateSphereBuilder(NXOpen.Features.Feature.Null)
sph.Type = NXOpen.Features.SphereBuilder.Types.CenterPointAndDiameter
sph.Diameter.RightHandSide = "30"
sph.CenterPoint = part.Points.CreatePoint(NXOpen.Point3d(0.0, 0.0, 0.0))
feat = sph.CommitFeature(); sph.Destroy()
```

> All numeric inputs are **string expressions** (`"20"`, or an expression name like `"boss_dia"`), the same convention as extrude limits in 01. Passing a float where a string is expected fails at `Commit()`.

---

## 8.2 Tube along a 3D path — bent bars, lines, pipes

The canonical tool for anti-roll bars, brake/fuel lines and handrails — [04](04-boolean-and-geometry-rules.md) explains *why* one tube along a polyline beats a collage of cylinders. The path is a `Section` of tangent-continuous curves (lines + corner-fillet arcs):

```python
tb = part.Features.CreateTubeBuilder(NXOpen.Features.Feature.Null)
tb.OuterDiameter.RightHandSide = "10"
tb.InnerDiameter.RightHandSide = "6"                  # "0" -> solid rod instead of a tube
tb.OutputOption = NXOpen.Features.TubeBuilder.OutputOptions.SingleSegment

path = part.Sections.CreateSection(0.0095, 0.01, 0.5)
rule = part.ScRuleFactory.CreateRuleCurveDumb(path_curves)      # lines + tangent arcs, in order
path.AddToSection([rule], path_curves[0], NXOpen.NXObject.Null, NXOpen.NXObject.Null,
                  help_pt, NXOpen.Section.Mode.Create, False)
tb.PathSection = path                                  # check your stubs for the exact property name
feat = tb.CommitFeature(); tb.Destroy()
```

> **Boolean care (from 04):** a tube's bore also cuts the target during an inline boolean — keep the bore radius smaller than any through-part, or the subtract severs it. `SingleSegment` vs `MultipleSegments` decides whether corners produce one body or one per segment.

---

## 8.3 Swept — an arbitrary profile along a guide

Where Tube is limited to round sections, Swept carries **any closed profile** along one or more guide curves. Same `Section` mechanics as the loft in 07 — one section list plus a guide list:

```python
sw = part.Features.CreateSweptBuilder(NXOpen.Features.Swept.Null)   # note: Swept.Null, like Thread in 2.4
sw.G0Tolerance = 0.01
sw.G1Tolerance = 0.5

sec = part.Sections.CreateSection(0.0095, 0.01, 0.5)     # the profile — closed for a solid
# ...AddToSection with the profile curves, exactly as in 01...
sw.SectionList.Append(sec)

guide = part.Sections.CreateSection(0.0095, 0.01, 0.5)   # the path
# ...AddToSection with the guide curve(s)...
sw.GuideList.Append(guide)

feat = sw.CommitFeature(); sw.Destroy()
```

Choosing between the three "profile along a path" tools:

| Tool | Profile | Path | Typical use |
|------|---------|------|-------------|
| **Tube** (8.2) | circle/annulus only | 3D polyline + arcs | bars, pipes, wiring |
| **Swept** (8.3) | any curve chain | 1–3 guides | rails, gaskets, complex trims |
| **Through Curves** ([07](07-freeform-lofting.md)) | N different sections | implied (section order) | wings, hulls, anything that changes shape |

---

## 8.4 Ruled — the two-section straight loft

A ruled body is a loft restricted to **exactly two sections joined by straight lines** — transition pieces, wedges, chute segments. Cheaper and more predictable than a full loft when two sections are all you have:

```python
rb = part.Features.CreateRuledBuilder(NXOpen.Features.Feature.Null)
# two Sections built exactly like the loft sections in 7.2:
rb.FirstSection  = sec1
rb.SecondSection = sec2
feat = rb.CommitFeature(); rb.Destroy()
```

The twist-control rule from 7.2 applies with double force here: generate both sections with the **same point count and ordering**, or the straight-line correspondence folds the body into a bowtie.

---

## 8.5 The sheet workflow — offset, thicken, sew

Some shapes are easier to build as **surfaces first**, then turned into solids. The three workhorses:

```python
# Thicken — sheet body -> solid wall
th = part.Features.CreateThickenBuilder(NXOpen.Features.Feature.Null)
th.Tolerance = 0.01                                   # same "default 0 fails" family as Shell (2.5)
th.FirstOffset.RightHandSide  = "2"
th.SecondOffset.RightHandSide = "0"
col = part.ScCollectors.CreateCollector()
col.ReplaceRules([part.ScRuleFactory.CreateRuleFaceDumb(sheet_faces)], False)
th.FaceCollector = col                                # check your stubs: property name varies by release
feat = th.CommitFeature(); th.Destroy()
```

```python
# Sew — stitch adjacent sheets into one (watertight sheets -> a closed solid)
swb = part.Features.CreateSewBuilder(NXOpen.Features.Feature.Null)
swb.SewType = NXOpen.Features.SewBuilder.Types.Sheet
swb.Tolerance = 0.01
swb.TargetSheets.Add(sheet_a)                         # check your stubs: SelectObjectList vs collector
swb.ToolSheets.Add(sheet_b)
feat = swb.CommitFeature(); swb.Destroy()
```

`CreateOffsetSurfaceBuilder` (offset a face into a new sheet) rounds out the set — see the inventory in [05](05-capability-inventory.md). The classic pipeline: **loft/swept as a sheet → sew the caps → (or) thicken** — useful when a solid loft self-intersects but its skin doesn't.

> A body is a **sheet** when `body.IsSheetBody` is true; `BodyPreference` on the loft/swept builders (7.2) is what decides solid-vs-sheet output.

---

## 8.6 Trim & split — cutting with a plane or face

`TrimBody2` removes everything on one side of a tool face/plane; `SplitBody` keeps both halves as separate bodies. Both take the tool via the nested `BooleanTool.FacePlaneTool` path — the least guessable part of the API, but it is what GUI-recorded journals show:

```python
tb = part.Features.CreateTrimBody2Builder(NXOpen.Features.Feature.Null)
tb.TargetBodyCollector.ReplaceRules(
    [part.ScRuleFactory.CreateRuleBodyDumb([body])], False)
tb.BooleanTool.FacePlaneTool.ToolFaces.FaceCollector.ReplaceRules(
    [part.ScRuleFactory.CreateRuleFaceDumb([tool_face])], False)   # or feed a datum plane instead
feat = tb.CommitFeature(); tb.Destroy()
```

Which side survives is controlled by a direction flag on the builder (`tb.Direction` / a reverse toggle — check your stubs). `SplitBodyBuilderUsingCollector` mirrors the same structure and, like all splits, produces bodies that then need the orphan-detection discipline from [04](04-boolean-and-geometry-rules.md#detecting-silent-orphan-bodies).

---

## 8.7 Choosing the right tool — a decision table

| The shape is… | Reach for |
|---------------|-----------|
| a constant profile pushed straight | **Extrude** (01) |
| a body of revolution | **Revolve** (01) — one closed profile, not a cylinder stack (04) |
| rectangular / cylindrical stock | **Primitives** (8.1) |
| a round section along a bent path | **Tube** (8.2) |
| an arbitrary section along a path | **Swept** (8.3) |
| two known sections, straight transition | **Ruled** (8.4) |
| N sections changing continuously | **Through Curves loft** ([07](07-freeform-lofting.md)) |
| a thin wall over a complex surface | **sheet + Thicken** (8.5) |
| a solid minus everything past a plane | **TrimBody2** (8.6) |

Every row's inline boolean behaves per [04](04-boolean-and-geometry-rules.md) — and remember the loft/swept family leans **create-only**: build the hull first, unite simple shapes onto it.
