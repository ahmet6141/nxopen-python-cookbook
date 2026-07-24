# 10 · Selecting Geometry Without a Mouse

> 🌐 **English** · [Türkçe](tr/10-selecting-geometry-without-a-mouse.md)

Every verified recipe in [02](02-verified-recipes.md) takes `edges`, `faces` or a `body` as input — in the GUI you would click them. Headless, **programmatic selection is the skill that makes everything else usable**: walk the topology, classify what you find, and pick by geometry. This page collects those patterns.

> ⚠️ **Verification status:** unlike docs 01–07, the recipes on this page are **not yet live-verified on NX 2506**. The traversal calls (10.1–10.2) are bedrock API used by every journal ever recorded; the UF calls and measure signatures are the ones to double-check against your stubs. Verify and report per [CONTRIBUTING](../CONTRIBUTING.md).

All snippets assume the boilerplate from [01-core-api.md](01-core-api.md), plus the UF session used below:

```python
import NXOpen, NXOpen.UF
session = NXOpen.Session.GetSession()
uf = NXOpen.UF.UFSession.GetUFSession()
```

---

## 10.1 The topology walk

Everything hangs off the body:

```python
for body in part.Bodies:                 # all solid & sheet bodies in the part
    faces = body.GetFaces()              # list[Face]
    edges = body.GetEdges()              # list[Edge]

for face in faces:
    face_edges = face.GetEdges()         # the edges bounding this face
    owning_body = face.GetBody()

for edge in edges:
    verts = edge.GetVertices()           # list[Point3d] — EMPTY for closed edges (circles)!
    length = edge.GetLength()
```

> The **empty-vertices case** is the classic crash: a full circle has no vertices, so any code that assumes `GetVertices()[0]` dies on the first round hole. Guard every vertex access with a length check.

`feat.GetBodies()`, `feat.GetFaces()`, `feat.GetEdges()` scope the same walk to what **one feature** created — usually the cleanest way to blend "the edges the boss just made" without touching the rest of the part.

## 10.2 Classifying faces and edges by type

`Face.SolidFaceType` / `Edge.SolidEdgeType` return enum values — the coarse filter that replaces the mouse:

```python
planar   = [f for f in body.GetFaces() if f.SolidFaceType == NXOpen.Face.FaceType.Planar]
round_fs = [f for f in body.GetFaces() if f.SolidFaceType == NXOpen.Face.FaceType.Cylindrical]
lines    = [e for e in body.GetEdges() if e.SolidEdgeType == NXOpen.Edge.EdgeType.Linear]
circles  = [e for e in body.GetEdges() if e.SolidEdgeType == NXOpen.Edge.EdgeType.Circular]
```

For *where* a face is and *which way* it points, drop to the UF layer — `AskFaceData` returns the analytic data for a face in one call:

```python
def face_data(face):
    # returns (type_code, point[3], dir[3], box[6], radius, rad_data, norm_dir)
    # type codes: 22 planar, 16 cylindrical, 17 conical, 18 spherical…  — check your stubs
    return uf.Modl.AskFaceData(face.Tag)
```

`point` is a representative point on the face, `dir` its normal (planar) or axis (cylindrical), `radius` the cylinder/sphere/cone radius. This one call powers every "find me the…" helper below.

## 10.3 "Find me the…" helpers

```python
def top_planar_face(body, tol=1e-6):
    """The planar face with the highest Z whose normal points up."""
    best, best_z = None, float("-inf")
    for f in body.GetFaces():
        if f.SolidFaceType != NXOpen.Face.FaceType.Planar:
            continue
        t, pt, dr, box, radius, rad_data, norm_dir = uf.Modl.AskFaceData(f.Tag)
        if abs(dr[2] - 1.0) < tol and pt[2] > best_z:
            best, best_z = f, pt[2]
    return best

def cylindrical_faces_of_diameter(body, diameter, tol=1e-3):
    """Every cylindrical face matching a diameter — bores, bosses, pins."""
    out = []
    for f in body.GetFaces():
        if f.SolidFaceType == NXOpen.Face.FaceType.Cylindrical:
            t, pt, dr, box, radius, rad_data, norm_dir = uf.Modl.AskFaceData(f.Tag)
            if abs(2.0 * radius - diameter) < tol:
                out.append(f)
    return out

def vertical_edges(body, tol=1e-6):
    """Linear edges parallel to Z — the classic chamfer/blend candidates."""
    out = []
    for e in body.GetEdges():
        vs = e.GetVertices()
        if len(vs) != 2:
            continue                                   # closed edges have no vertices (10.1)
        dx, dy, dz = vs[1].X - vs[0].X, vs[1].Y - vs[0].Y, vs[1].Z - vs[0].Z
        length = (dx * dx + dy * dy + dz * dz) ** 0.5
        if length > 0 and abs(abs(dz) / length - 1.0) < tol:
            out.append(e)
    return out
```

Composable one-liners follow from these — e.g. "blend the top rim" is `top_planar_face(body).GetEdges()` fed straight into the verified EdgeBlend recipe (2.1). This is also how the thread recipe's *"try candidate start faces in sequence"* advice (2.4) is implemented: rank the planar faces adjacent to the cylindrical face and loop until one commits.

## 10.4 Bounding box from vertices — the full helper

[04](04-boolean-and-geometry-rules.md) states there is no `AskBoundingBox` in this wrapper and sketches the approach; here is the complete function:

```python
def body_aabb(body):
    lo = [float("inf")] * 3
    hi = [float("-inf")] * 3
    for edge in body.GetEdges():
        for v in edge.GetVertices():
            for i, c in enumerate((v.X, v.Y, v.Z)):
                lo[i] = min(lo[i], c)
                hi[i] = max(hi[i], c)
    return tuple(lo), tuple(hi)
```

Two honest caveats: it sees only **vertices**, so a body whose extreme point lies mid-edge (a sphere, a barrel face) reports a box that is slightly too small; and a body with *only* closed edges (a sphere again) yields no vertices at all. For audit-grade boxes on curved bodies, sample edge midpoints too, or accept the vertex box as a lower bound.

## 10.5 Names, attributes, layers — making parts navigable

Selection's other half: mark objects **when you create them** so later code (and the cleanup filter in 7.6) can find them by name instead of geometry.

```python
body.SetName("HULL")
feat.SetName("MYPROJ_WING")                            # the 7.6 convention
hull = next(b for b in part.Bodies if b.Name == "HULL")

# attributes — richer than names, exportable to STEP/JT (see 05 for SetUserAttribute)
pn = body.GetStringUserAttribute("PART_NO", -1)        # check your stubs for the exact getter

# layers — the coarse show/hide mechanism that survives into exports
body.Layer = 20                                        # move object to layer 20
part.Layers.WorkLayer = 20                             # new objects land here from now on
```

A practical layer scheme for generated parts: solids on 1, construction curves/points on 41, datums on 61 — then a GUI user can hide all scaffolding with one layer-state change, and your exporter can select "layer 1 solids only," which also sidesteps the Parasolid-poisoning trap (pitfall #22).

## 10.6 Measuring — distance and angle

For volume/mass the verified path is `NewMassProperties` (2.9). For distances between objects:

```python
unit = part.UnitCollection.FindObject("MilliMeter")
m = part.MeasureManager.NewDistance(unit, obj_a, obj_b)   # minimum distance
print(m.Value)
# newer releases add overloads taking a MeasureType enum — check your stubs (signatures
# here shift between releases more than most of the API)
```

`MeasureManager` also exposes `NewAngle`. But note that for *pass/fail* geometry checks, the boolean-intersect probe in [7.8](07-freeform-lofting.md) is often the more trustworthy tool: it answers "how much material actually overlaps," which no distance measurement can.

## 10.7 Why not `FindObject`?

Recorded journals are full of `part.Bodies.FindObject("EXTRUDE(3)")` — resist copying them. Those **journal identifiers encode feature-creation order**, so they break the moment the recipe runs on a part with a different history; it is the same fragility as datum-by-name (pitfall #29, solved geometrically in 7.5). The robust order of preference:

1. **Capture returns** — `feat.GetBodies()[0]` at creation time; never look it up again.
2. **Your own names** — `SetName` at creation, find by `Name` later (10.5).
3. **Geometry queries** — the 10.3 helpers, when 1–2 aren't available (e.g. operating on a part you didn't build).
4. `FindObject` with a journal identifier — only inside a single journal run against a part whose history you fully control.
