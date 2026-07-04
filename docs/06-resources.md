# 06 · Resources

> 🌐 **English** · [Türkçe](tr/06-resources.md)

Places worth bookmarking when you're stuck. The **single most reliable reference is your own local stubs** — they match your exact NX version, unlike anything online.

## Your local install (check here first)

- **`<install>/UGOPEN/pythonStubs/NXOpen/`** — the `.pyi` type stubs for your exact NX version. When an online example disagrees with reality, the stub is right. Point your IDE here for autocomplete, and read the stub directly to get a signature's true parameter types.
- **`<install>/UGOPEN/`** — sample journals and the UF (User Function) headers.

## Official Siemens

- **NXOpen Python API Reference** — [docs.sw.siemens.com](https://docs.sw.siemens.com) (search "NXOpen Python"). The authoritative class/method listing, though examples skew toward the GUI.
- **Siemens Community — NX forums** — [community.sw.siemens.com](https://community.sw.siemens.com) — Q&A with Siemens engineers and power users.

## Community

- **nxjournaling.com** — the long-running NX journaling community: tutorials, sample journals, and a searchable archive of real problems. Mostly VB but the API concepts transfer directly to Python.
- **eng-tips.com** (Siemens NX forum) — practical, high-signal troubleshooting threads.

## Open-source on GitHub

- **[cfs-energy/nxlib](https://github.com/cfs-energy/nxlib)** — a professional Python wrapper around NXOpen; good patterns for structuring larger automation.
- **NXOpen Python type-stub projects** (search GitHub for `nxopen pyi` / `nx nxopen stubs`) — community-maintained stubs, useful if you can't get your install's stubs into your IDE.

## How this cookbook was built

Every recipe here came from the same loop, which is a good loop to copy:

1. **Mine the stubs** for the real signatures (don't trust prose docs).
2. **Write a minimal headless journal** that exercises one feature.
3. **Run it with `run_journal.exe`** and inspect the resulting `.prt` — face counts, volume, mass, body count.
4. **Record the exact error string** on failure; those strings are the fastest route to the fix and are what make issues searchable.

If you find a recipe here behaves differently on your NX release, that loop plus an issue with your version + error string is the ideal contribution back.
