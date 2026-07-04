# 00 · Getting Started with Headless NX Journaling

> 🌐 **English** · [Türkçe](tr/00-getting-started.md)

## What "headless journaling" means

A **journal** is a Python (or VB/C#) script that drives NX through the NXOpen API. NX can run a journal two ways:

1. **Headless / batch** — `run_journal.exe script.py -args ...`. No GUI window; NX loads the geometry kernel, runs your script, exits. This is the workflow this cookbook targets: parameters in, `.prt`/STEP out, fully automated.
2. **Interactive playback** — inside the NX GUI via `Tools → Journal → Play` (or `Alt+F8`). Useful for stepping and for anything that genuinely needs the graphics window (see the PNG note below).

## Environment

| Thing | Notes |
|-------|-------|
| **NX version** | This cookbook was verified on **NX 2506** (Continuous Release). Behaviour differs across releases — verify on yours. |
| **Python** | NX ships an **embedded** Python 3.10 with **no third-party packages**. You cannot `pip install` into the NX interpreter; standard library only inside journals. |
| **Install root** | The environment variable **`UGII_ROOT_DIR`** must point at your `NXBIN` directory (the folder containing `run_journal.exe`). |
| **Type stubs** | `<install>/UGOPEN/pythonStubs/NXOpen/` holds `.pyi` stubs matching your exact install. Point your IDE at them for autocomplete and — more importantly — to read **the real signatures for your version**. |

## Running a journal headless

```powershell
# PowerShell — use $env: and the & call operator (NOT cmd's %VAR%)
$env:UGII_ROOT_DIR = "C:\Program Files\Siemens\NX2506\NXBIN"   # adjust to your install
& "$env:UGII_ROOT_DIR\run_journal.exe" my_journal.py -args arg1 arg2 arg3
```

Your script reads the trailing `-args` values from `sys.argv[1:]`.

**A headless run coexists with an open GUI.** On a local seat, launching `run_journal.exe` while the NX GUI is already open starts a clean *second* session with no license clash. This was exercised many times back-to-back with no issue — handy for building in batch while you inspect the previous result in the GUI.

## The one thing that does NOT work headless: image export

Generating a PNG/screenshot of the model from a headless journal is **impossible** — there is no graphics window to render into. Both documented paths fail under `run_journal.exe`:

- `part.Views.CreateImageExportBuilder()` → `Commit()` raises **"Invalid object state"**.
- `theUF.Disp.CreateImage(png, DispImageFormat.PNG, DispBackgroundColor.WHITE)` → **"The image file could not be created."**

If you need rendered images, run the export step **inside the interactive GUI**, or capture the OS window separately. Plan your pipeline so visual output is a GUI-only step; keep the headless path to geometry + neutral-format export (STEP/JT/Parasolid).

## A note on GUI automation

Trying to drive the NX ribbon by simulating clicks is unreliable: the ribbon does not expose itself as clean UI-Automation `TabItem` elements, and display scaling (e.g. 125% DPI) desynchronizes cursor coordinates from window rectangles. **Capturing** a window image (PrintWindow / CopyFromScreen) is safe; **clicking** into NX from the outside is not. Drive NX through NXOpen, not through synthetic input.

## Recommended project shape

For a procedural pipeline, keep the NXOpen-touching code thin and everything else pure:

```
params  →  pure-math blueprint (plain dicts/JSON, no NXOpen import)
        →  a small list of "build steps"
        →  one builder module that turns steps into NXOpen features
        →  run_journal.exe executes it headless
```

Keeping the blueprint layer free of any `import NXOpen` lets you validate geometry (bounding boxes, clearances, mass estimates) in a normal Python venv with fast unit tests — then only the final build touches NX. See [docs/04-boolean-and-geometry-rules.md](04-boolean-and-geometry-rules.md) for what that validation can and cannot catch.
