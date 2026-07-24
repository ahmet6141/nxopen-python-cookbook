# NXOpen Python Cookbook

> 🌐 **English** · [Türkçe](README.tr.md)

> Verified, copy-paste recipes and hard-won pitfalls for **headless Siemens NX journaling** with the NXOpen Python API.

Most NXOpen material online is written for the interactive GUI and stops at "record a journal, tweak it." This cookbook is different: it targets **fully headless, parametric, batch geometry generation** driven by `run_journal.exe` — the workflow you need when you generate CAD from code (parameters → blueprint → solid model) with no human in the loop.

Every recipe here was **verified live** against a real NX install (release **NX 2506**, Continuous Release series) by running headless journals and inspecting the resulting `.prt` — not copied from documentation that may be stale or wrong for your version. Where a widely-cited API signature turned out to be incorrect, the correction and the evidence are documented.

## Why this exists

Automating NX from Python is powerful but the API is large, under-documented for headless use, and full of traps that only surface at runtime — a builder that silently produces a disconnected body, a boolean that reports success but never merges, an export that poisons the whole session. Each of those cost hours to diagnose. This repo is the reference I wish I'd had.

## Contents

| Doc | What's inside |
|-----|---------------|
| [docs/00-getting-started.md](docs/00-getting-started.md) | NX setup, running journals headless vs. GUI, Python stubs for autocomplete, environment notes |
| [docs/01-core-api.md](docs/01-core-api.md) | Session/Part lifecycle, expressions, extrude, revolve, sections, curves, booleans, the mandatory update loop, body naming, STEP/Parasolid export |
| [docs/02-verified-recipes.md](docs/02-verified-recipes.md) | 11 copy-paste recipes: edge blend, chamfer, draft, symbolic thread, shell, mirror body, hole package, material assignment, mass properties, PMI notes |
| [docs/03-pitfalls.md](docs/03-pitfalls.md) | The consolidated trap list — 29 runtime failures with symptom → fix |
| [docs/04-boolean-and-geometry-rules.md](docs/04-boolean-and-geometry-rules.md) | Reliable-boolean rules for procedural modeling: what actually fuses, how to detect silent orphan bodies, vertex-based bounding boxes |
| [docs/05-capability-inventory.md](docs/05-capability-inventory.md) | Stub-mined inventory of feature factories, standalone boolean/move builders, assembly constraints, the full export list, helix/spline, color & attributes |
| [docs/06-resources.md](docs/06-resources.md) | Community sites, open-source libraries, and official references worth bookmarking |
| [docs/07-freeform-lofting.md](docs/07-freeform-lofting.md) | Splines without a sketch, Through-Curves lofting, closing a loft to one or two points, robust datum-by-name lookup, self-cleaning re-runnable generators, parametric Expression read/write-back, Boolean-Intersect volume verification |
| [docs/08-primitives-sweeps-and-surfacing.md](docs/08-primitives-sweeps-and-surfacing.md) | Block/cylinder/cone/sphere primitives, tube along a 3D path, Swept, Ruled, the sheet workflow (thicken/sew), trim & split, a which-tool decision table *(reference tier — see banner)* |
| [docs/09-sketches-patterns-and-feature-editing.md](docs/09-sketches-patterns-and-feature-editing.md) | When a headless sketch is worth it and the minimal pattern, linear/circular Pattern Feature, scale & copy bodies, suppressing/re-parameterizing/deleting existing features *(reference tier — see banner)* |
| [docs/10-selecting-geometry-without-a-mouse.md](docs/10-selecting-geometry-without-a-mouse.md) | Programmatic selection: topology traversal, classifying faces/edges, find-me-the-top-face helpers, vertex bounding boxes, names/attributes/layers, measuring, why not `FindObject` *(reference tier — see banner)* |

Runnable example: [examples/block_with_boss.py](examples/block_with_boss.py) — builds a block + boss, blends and chamfers it, assigns steel, measures mass, and exports STEP, using only the recipes in this repo.

## Quickstart

```powershell
# Point at your NX install and run a journal headless (no GUI needed):
$env:UGII_ROOT_DIR = "C:\Program Files\Siemens\NX2506\NXBIN"   # adjust to your install
& "$env:UGII_ROOT_DIR\run_journal.exe" examples\block_with_boss.py -args out.prt
```

A headless journal opens a **second** NX session cleanly even while the GUI is already running — there is no license clash for a local seat. See [docs/00-getting-started.md](docs/00-getting-started.md).

## Scope & honesty

- **Two tiers of confidence.** Docs 00–07 are **live-verified** on NX 2506. Docs 08–10 are **reference tier**: assembled from the API reference, recorded-journal patterns, and community examples, clearly bannered as not-yet-verified — run one, confirm it, and a PR promotes it.
- **Version:** everything was proven on NX 2506. NXOpen shifts between releases; signatures that changed are called out, but always verify against your own version. When in doubt, mine your local stubs (`.../UGOPEN/pythonStubs/`) — the signatures there match your exact install.
- **Not affiliated with Siemens.** NX, NXOpen, and Parasolid are trademarks of Siemens Digital Industries Software. This is an independent, community reference.
- **No warranty.** These recipes mutate CAD geometry and can overwrite files. Read before you run.

## Support this project

This is free knowledge, and the best support costs nothing:

- ⭐ **Star** the repo if it saved you time — that's the whole reward this project asks for.
- 👀 **Watch / follow** to catch new recipes and version notes.
- 🔧 **Contribute** a verified recipe or a version-specific correction (see [CONTRIBUTING.md](CONTRIBUTING.md)) — that's the most valuable support of all.
- 🔗 **Share it** with anyone automating NX, or link it from an NX community thread.

> No donations, no sponsorship — this repo intentionally has none. If you want to collaborate on procedural/parametric CAD work, open an issue or start a discussion.

## License

[MIT](LICENSE) — use it freely, attribution appreciated.

## Contributing

Corrections and version-specific notes are very welcome — see [CONTRIBUTING.md](CONTRIBUTING.md). If a recipe behaves differently on your NX release, open an issue with the version and the exact error string; that's exactly the kind of knowledge this repo is meant to collect.
