# 04 · Boolean & Geometry Rules for Procedural Modeling

> 🌐 **English** · [Türkçe](tr/04-boolean-and-geometry-rules.md)

When you generate solids from code, the boolean operations are where models quietly go wrong. NX will report a unite/subtract as *successful* and still leave you with disconnected bodies. These rules were learned the hard way building large multi-body assemblies headless; they are geometry facts, not API quirks.

## What actually fuses

- **Uniting parts must share real volume with the target.** A part must **embed ≥ 15 mm** into the target solid to merge reliably (≥ ~6 mm is enough for small hardware like nuts/bushings, ≥ ~14 mm for structural members).
- **Point contact and line contact do NOT fuse.** Corner-to-corner (point) and edge-to-edge (line) touching leave two separate bodies even though they "touch." **Face contact with zero overlap also does not unite** — you need volumetric interpenetration.
- **A tool fully outside the target fails a later subtract.** If a part offset entirely outside the target only grazes it at a corner, it stays a separate body — and any subsequent subtract aimed at the "merged" region errors *"Tool body completely outside target body."*

## Unite order matters

Booleans are applied in sequence, so **the contact must exist at the moment of the unite.** For a plate → pin → plate stack, unite in that order so each new part actually touches solid material when it's added. Get the order wrong and an intermediate unite lands on geometry that isn't there yet.

## Which builders apply booleans reliably

- Booleans apply reliably on **prism / cylinder / tube / hole / extrude / revolve** (via the extrude/revolve `BooleanOperation.SetTargetBodies` path).
- **`loft` is create-only** for boolean purposes in some builder paths — its inline unite/subtract may not apply, leaving the lofted body standalone. **Pattern:** build a hull as **one loft (create)**, then unite everything else onto it as prism/cylinder. Never rely on a loft's boolean.
- **Tube booleans need care:** the outer ring applies the op against the target *and* the bore cuts the target. So keep the bore radius **smaller** than the radius of any through-part, or the bore's subtract will sever that part into two bodies.

## Modeling a single clean profile beats a collage of cylinders

For any body of revolution or swept bar, model it as **one closed profile** (revolve) or **one swept path** (tube along a polyline) rather than unioning a stack of intersecting cylinders. A cylinder collage is fragile — the intersections create phantom edges and its axis-aligned bounding box clashes against neighbours that the *real* geometry clears. One outline = one clean, professional solid.

- Bent bars (anti-roll bars, brake/fuel lines): sweep **one tube along a 3D polyline** with tangent corner-fillet arcs, not intersecting cylinders.
- Plates with lugs/eyes: draw **one silhouette** whose lobes carry the bores directly, rather than crossing eye-cylinders.

> **Audit caveat this creates:** single-outline plates make the *prism bounding box* corners appear to clash against nearby revolves even when the true 3D geometry clears. If you run an automated clearance audit on bounding boxes, expect false positives here — verify true clearance by hand, then whitelist the known-good pair.

## Subtracts must genuinely intersect

- A **prism-subtract slot** must actually cut through the target — a slot floating just off the surface removes nothing.
- A **bore tangent to a face** fails. Leave **≥ 2 mm** of wall between a hole and any face it runs near.
- The **`hole` primitive reads its position from its own `cx / cy / z0`**, not from any shared `origin` field. A hole placed by the wrong field lands outside the target and errors.

## Detecting silent orphan bodies

The dangerous failures produce **no error at all** — a unite lands on removed/void geometry (e.g. a member spanning a cut-out tunnel) and NX just makes a *separate* body. Catch these numerically:

1. **Count bodies two ways.** After the build, compare `built N solid bodies` against `named N bodies`. A mismatch means a unite created an unnamed orphan.
2. **Name every body you intend to keep**, so anything unnamed at the end is by definition an orphan.
3. **Grep the build log** for `FAIL` and confirm the final `=== done (0 errors)` line — but don't trust it alone, because silent orphans don't log.

## What NX-free validation can and cannot catch

You can validate a lot in a plain Python venv *before* touching NX — bounding boxes, clearances, mass estimates, mate distances. But be honest about the limits:

- **Can catch:** gross clashes, floating parts, missing mates, obviously-wrong dimensions — cheap, fast, run them in unit tests.
- **Cannot catch:** tool-outside-target and point-contact-unite failures. Those depend on the kernel's actual boolean evaluation and **only appear in a real `run_journal.exe` build.** Always confirm a finished assembly with an actual NX run.

## Computing a bounding box in NX

There is **no** `uf.Modl.AskBoundingBox` in this API. Compute an axis-aligned bbox yourself from vertices:

```python
# iterate body.GetEdges() → edge.GetVertices() and min/max the coordinates
```

## Suggested defect classes for an automated assembly audit

If you build a numeric DMU gate over your generated geometry, these four classes catch most procedural-modeling defects:

| Class | Definition |
|-------|------------|
| **CLASH** | Two parts that are not supposed to mate penetrate each other beyond a small tolerance (e.g. > 3 mm). |
| **FLOATER** | A body that touches nothing — an orphan or a part placed in the wrong location. |
| **MISSING MATE** | A joint you declared should touch is not actually in contact. |
| **INTERFERENCE with moving parts** | A static body sits inside the swept envelope of a rotating/translating part. |

Model revolves as binned radial-profile maps (so dished/bored parts are represented truly, not as solid cylinders), flat-ended cylinders as capped, and prisms as AABBs — then measure per-pair distances. Whitelist the genuine mates and the single-outline false positives noted above.
