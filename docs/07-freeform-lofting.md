# 07 · Free-Form Lofting: Splines, Point-Closed Lofts & Parametric Generators

> 🌐 **English** · [Türkçe](tr/07-freeform-lofting.md)

Everything in [01-core-api.md](01-core-api.md) builds from a **single** profile (extrude/revolve). This page covers the other family: solids **lofted through a stack of curved cross-sections** — the technique behind wings, fuselages, nacelles, blades, and any body whose shape changes continuously along an axis. Verified live across multiple large headless builds (multi-hundred-body parametric aircraft/UCAV generators, NX 2506).

**In this page:** sketch-free splines (7.1) · Through-Curves lofting (7.2) · closing a loft to a point at one end (7.3) or both ends (7.4) · robust datum-plane lookup (7.5) · idempotent re-runs (7.6) · Expression-driven parameters (7.7) · overlap-volume verification (7.8).

All snippets assume the boilerplate from [01-core-api.md](01-core-api.md): `session = NXOpen.Session.GetSession()` and `part` is the work part.

---

## 7.1 An independent spline, no sketch required

```python
b = part.Features.CreateStudioSplineBuilderEx(None)
b.DrawingPlaneOption = NXOpen.Features.StudioSplineBuilderEx.DrawingPlaneOptions.General
b.DrawingPlane = part.Planes.CreatePlane(origin, normal, NXOpen.SmartObject.UpdateOption.WithinModeling)
b.InputCurveOption = NXOpen.Features.StudioSplineBuilderEx.InputCurveOptions.Hide
b.MatchKnotsType    = NXOpen.Features.StudioSplineBuilderEx.MatchKnotsTypes.NotSet
b.IsAssociative = False     # independent of the points once built — robust for generated geometry
b.IsPeriodic    = False     # True = seamless closed loop (fuselage ring); False = sharp trailing edge (airfoil)
b.Degree        = 3

temp_points = []
for p in points:                                        # points: list[Point3d]
    pt = part.Points.CreatePoint(p)
    temp_points.append(pt)
    gcd = b.ConstraintManager.CreateGeometricConstraintData()
    gcd.Point = pt
    b.ConstraintManager.Append(gcd)

b.Commit()
spline = b.Curve            # read BEFORE Destroy() — the result lives on this property
b.Destroy()

# clean up the construction points (safe once IsAssociative=False):
for pt in temp_points:
    part.Points.DeletePoint(pt)
```

> **Trap:** `CreateSketchSplineBuilder` requires an **active sketch** — call it with none open and `Commit()` raises *"Incorrect object for this operation."* For sketch-free curve generation (the normal case when you're building geometry from parameters, not from a GUI sketch session), always use **`CreateStudioSplineBuilderEx`** instead.
>
> **Trap:** the .NET reference lists a `MatchKnotsTypes.None` member, but `None` is a reserved word in Python — `MatchKnotsTypes.None` is a **`SyntaxError`** before NX even loads the journal. The Python binding (and every GUI-recorded Python journal) spells it **`NotSet`**.

---

## 7.2 Through-Curves loft — stacking sections into one solid

```python
b = part.Features.FreeformSurfaceCollection.CreateThroughCurvesBuilder1(None)

# tolerances — these exact values are proven in production journals
b.Alignment.AlignCurve.DistanceTolerance  = 0.01
b.Alignment.AlignCurve.ChainingTolerance  = 0.0095
b.Alignment.AlignCurve.AngleTolerance     = 0.5
b.SectionTemplateString.DistanceTolerance = 0.01
b.SectionTemplateString.ChainingTolerance = 0.0095
b.SectionTemplateString.AngleTolerance    = 0.5

b.Alignment.AlignType = NXOpen.GeometricUtilities.AlignmentMethodBuilder1.Type.Parameter   # critical, see below
b.Construction   = NXOpen.Features.ThroughCurvesBuilder1.ConstructionMethod.Normal
b.PatchType      = NXOpen.Features.ThroughCurvesBuilder1.PatchTypes.Multiple
b.BodyPreference = NXOpen.Features.ThroughCurvesBuilder1.BodyPreferenceTypes.Solid   # closed section -> capped solid
b.PreserveShape = False
b.ClosedInV = False
b.NormalToEndSections = False

for spline, help_point in zip(sections, help_points):    # sections: list[Spline], in loft order;
    sec = part.Sections.CreateSection(0.0095, 0.01, 0.5)  # help_point: a Point3d on (or near) its spline —
    sec.SetAllowedEntityTypes(NXOpen.Section.AllowTypes.OnlyCurves)  # e.g. the first input point it was built from
    rule = part.ScRuleFactory.CreateRuleCurveDumb([spline])
    sec.AllowSelfIntersection(False)
    sec.AllowDegenerateCurves(False)
    sec.AddToSection([rule], spline, None, None, help_point, NXOpen.Section.Mode.Create, False)
    b.SectionsList.Append(sec)

feat = b.CommitFeature()
b.Destroy()
body = feat.GetBodies()[0]
```

> **The secret to a clean, twist-free loft:** generate every section's spline with the **same point count and the same point order** (e.g. always trailing-edge → upper surface → leading-edge → lower surface → trailing-edge for an airfoil), and set `AlignType = Parameter`. NX then matches point-index to point-index across sections instead of guessing a correspondence — leading edges line up with leading edges, trailing edges with trailing edges, with no twist. The GUI-recorded `SetStartCurveOfClosedLoop` / `ReverseDirectionOfLoop` calls you'll see in a Journal recording are manual corrections for *inconsistent* input curves — they're unnecessary if you control the generation and keep the ordering consistent from the start.
>
> Section order = `SectionsList.Append` order = the loft's V-direction. Loft is **create-only** for inline booleans in this builder — see [04-boolean-and-geometry-rules.md](04-boolean-and-geometry-rules.md); build the hull as one loft, then unite everything else onto it.

---

## 7.3 Closing a loft to a single point — a sharp nose/tip, not a stub

A capped loft whose last section is a small ring reads as a blunt stub. To get a genuinely sharp point (an ogive nose, a wingtip, a spinner), add a section that is **one single point**, placed *before* (or after) the curve sections:

```python
pole = part.Points.CreatePoint(NXOpen.Point3d(x0, 0.0, 0.0))
pole.SetVisibility(NXOpen.SmartObject.VisibilityOption.Visible)   # a "dumb" point must be visible to be used

psec = part.Sections.CreateSection(0.0095, 0.01, 0.5)
psec.SetAllowedEntityTypes(NXOpen.Section.AllowTypes.CurvesAndPoints)      # critical — points aren't curves
prule = part.ScRuleFactory.CreateRuleCurveDumbFromPoints([pole])
psec.AddToSection([prule], pole, None, None, pole.Coordinates, NXOpen.Section.Mode.Create, False)

b.SectionsList.Append(psec)          # append BEFORE the curve sections -> loft closes to this point
# ... append the curve sections as in 7.2 ...
```

> The point becomes a **parent** of the loft feature — don't delete it, `Blank()` it to hide it instead. Deleting a parent of a live feature either fails or breaks the feature.

---

## 7.4 Closing a loft to points at **both** ends

The same trick works at both ends of the same loft — useful for a fully pointed body with no motor/engine opening at either end (a glider fuselage, a flying-wing tip):

```python
def loft_with_poles(start_pole, end_pole, sections, helps, name):
    b = part.Features.FreeformSurfaceCollection.CreateThroughCurvesBuilder1(None)
    # ... tolerances/Alignment/Construction as in 7.2 ...
    if start_pole is not None:
        append_pole_section(b, start_pole)          # the section-from-point helper in 7.3
    for spline, help_pt in zip(sections, helps):
        # ... normal Section.Append as in 7.2 ...
        pass
    if end_pole is not None:
        append_pole_section(b, end_pole)             # SAME helper, appended LAST
    feat = b.CommitFeature()
    feat.SetName(name)                               # named -> cleanup_previous (7.6) can find it on re-run
    b.Destroy()
    return feat.GetBodies()[0]
```

Factor the point-section code from 7.3 into a small `append_pole_section(builder, pole)` helper — it's reused identically at both ends.

**A practical extension:** make the pole optional per end based on configuration, and clamp the minimum cross-section radius near an opening to a fixed value instead of a pole when that end needs a flat cutout (e.g. an engine/motor mount, a duct inlet):

```python
floor_r = spinner_radius if station_is_the_open_end else 2.5     # 2.5 mm = practical "near zero" floor
half_width  = max(nominal_half_width  * shape_fn(t), floor_r)
half_height = max(nominal_half_height * shape_fn(t), floor_r)
```

One generator function then produces a fully pointed body **or** a body with a flat, sized cutout at either end, purely by switching which end gets a pole vs. a `floor_r` clamp — no separate code path needed.

---

## 7.5 Robust datum-plane lookup by name

`Datums.FindObject("DATUM_CSYS(0) XZ plane")` only works if that exact absolute datum exists with that exact name — a fresh part, an empty part, or a differently-templated part won't have it, and you get *"No object found with this name."* The robust, proven fallback chain:

```python
def find_or_create_xz_plane():
    try:
        return part.Datums.FindObject("DATUM_CSYS(0) XZ plane")   # 1) fast path — template parts only
    except Exception:
        pass

    def xz_by_geometry():                                    # 2) search by geometry, not name
        for o in part.Datums:
            if isinstance(o, NXOpen.DatumPlane) and abs(abs(o.Normal.Y) - 1.0) < 1e-6 \
               and abs(o.Normal.X) < 1e-6 and abs(o.Normal.Z) < 1e-6:
                return o
        return None

    plane = xz_by_geometry()
    if plane is not None:
        return plane

    # 3) nothing found at all -> build an absolute-origin datum CSYS, then search again
    db = part.Features.CreateDatumCsysBuilder(None)
    xf = part.Xforms.CreateXform(NXOpen.Point3d(0.0, 0.0, 0.0), NXOpen.Vector3d(1.0, 0.0, 0.0),
                                  NXOpen.Vector3d(0.0, 1.0, 0.0), NXOpen.SmartObject.UpdateOption.WithinModeling, 1.0)
    csys = part.CoordinateSystems.CreateCoordinateSystem(xf, NXOpen.SmartObject.UpdateOption.WithinModeling)
    db.Csys = csys
    db.CommitFeature()
    db.Destroy()
    return xz_by_geometry()                                  # finds the plane just created
```

> **Related trap:** `DatumPlaneBuilder.SetCornerPoints(c1..c4)` called from a script raises *"Datum plane undefinable"* — even though GUI-recorded journals show it. Skip it; set `builder.ResizeDuringUpdate = True` instead and let NX size the plane automatically.

---

## 7.6 Self-cleaning re-run — idempotent regeneration

A generator you can re-run against the *same* part after changing a parameter, without hand-deleting the old geometry first:

```python
def cleanup_previous(mark, prefix):
    doomed = [f for f in part.Features if f.Name.upper().startswith(prefix)]
    doomed += [c for c in part.Curves if c.Name.upper().startswith(prefix + "_SEC")]
    doomed += [p for p in part.Points if p.Name.upper().startswith(prefix + "_SEC")]
    if doomed:
        session.UpdateManager.AddObjectsToDeleteList(doomed)
        session.UpdateManager.DoUpdate(mark)
```

Call this **before** building anything. It only works if you consistently `feature.SetName("MYPROJ_...")` every feature/curve/point you create — an unnamed object can't be matched by the filter and won't be cleaned up, leaving orphans behind on the next run.

> **Expressions are not Features** — they survive `cleanup_previous` untouched. That's the point: change a value in Tools → Expressions, re-run the journal, and only the *geometry* regenerates while your parameter edit sticks. See 7.7.

---

## 7.7 Parametric Expression read-if-exists / write-back

Pair with 7.6 to make a journal into an editable, re-runnable generator, driven from Tools → Expressions instead of hardcoded constants:

```python
def P(name, default, unit=None):
    for ex in part.Expressions:
        if ex.Name.lower() == name.lower():
            return ex.Value                                   # already exists -> read it
    rhs = str(default)
    if unit is None:
        part.Expressions.Create(f"{name}={rhs}")               # unitless (ratio, section code, count)
    else:
        u = part.UnitCollection.FindObject(unit)                # "MilliMeter" / "Degrees" / ...
        part.Expressions.CreateWithUnits(f"{name}={rhs}", u)
    return default                                              # first run: return the default too

def set_p(name, value):
    for ex in part.Expressions:
        if ex.Name.lower() == name.lower():
            ex.RightHandSide = f"{value:.3f}"
            return
```

Use a single, project-unique prefix for every expression name (`myproj_wing_span`, `myproj_root_chord`, ...) — it avoids collisions with other generators in the same part and lets `cleanup_previous`'s naming filter (7.6) stay unambiguous. If a generator runs a convergence/sizing loop, call `set_p(...)` on the converged results at the end so they're visible and hand-editable from the NX UI afterward.

---

## 7.8 Verifying real overlap volume with Boolean Intersect

`nx_inspect`-style interference counts tell you *that* two bodies overlap; this gets you *how much*, numerically — useful as a second, quantitative confirmation layer for any two parts that are supposed to just touch (or supposed to not touch at all):

```python
bb = part.Features.CreateBooleanBuilderUsingCollector(NXOpen.Features.BooleanFeature.Null)
bb.Operation = NXOpen.Features.Feature.BooleanType.Intersect
bb.RetainTarget = True
bb.RetainTool   = True                       # keep the two originals — this is a probe, not a real merge
bb.Targets.Add(body_a)
bb.Tools.Add(body_b)                         # note: .Add on a SelectObjectList, NOT a ScCollector
before = {b.Tag for b in part.Bodies}
bb.Commit()
new_bodies = [b for b in part.Bodies if b.Tag not in before]   # the intersection solid(s), if any

# volume: NewMassProperties(units[:take], 0.99, [new_body]).Volume — the proven recipe from 2.9
# cleanup: uf.Obj.DeleteObject(b.Tag) for each new body, then bb.Destroy()
```

- **No intersection → `Commit()` raises.** Treat the exception as "0 mm³ overlap" (a PASS for a should-not-touch pair), not a real error.
- There is no `AskMassProps3d` on this wrapper's `uf.Modl` — `NewMassProperties` (2.9) is still the only volume path.

---

## Pitfall recap

These are large enough to deserve rows in [03-pitfalls.md](03-pitfalls.md) rather than repeating them here — see #26–29 there: the mass-properties-collector-returns-zero trap on multi-body kits, the sketch-vs-sketch-free spline trap, `SetCornerPoints`, and datum-by-name fragility.
