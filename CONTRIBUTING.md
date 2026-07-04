# Contributing

This cookbook grows by collecting **verified** NXOpen knowledge. The bar is simple: if you add a recipe, it should have run; if you fix one, say how you know.

## Good contributions

- **Version notes.** A recipe that behaves differently on your NX release. Open an issue or PR with:
  - your **NX version** (e.g. NX 2412, NX 2506),
  - the **exact error string** you got, and
  - the signature/fix that worked for you.
- **New verified recipes.** A feature not yet covered, with a note on how you confirmed it (face count, volume, mass, or body count before/after).
- **Corrections.** If a signature here is wrong for your version, that's important — send the correction and the evidence.

## Please don't

- Paste recipes you haven't run. Unverified API calls are exactly the problem this repo exists to fix.
- Include anything proprietary or export-controlled — models, part numbers, customer data, or anything you don't have the right to publish. This repo is **generic NXOpen technique only**.

## Style

- Keep recipes minimal and copy-pasteable.
- Prefer the "symptom → fix" form for pitfalls.
- Put submodule imports at module top (see the note in `docs/02-verified-recipes.md`).

Thanks for helping make headless NX automation less painful for the next person.
