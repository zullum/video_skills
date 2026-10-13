# Costs (Gemini API, standard tier, checked 2026-10-13)

| Image | Price | Use |
|---|---|---|
| 1K | ~$0.067 | quick tests |
| 2K | ~$0.101 | **default** for base poses and grids up to ~9–12 cells |
| 4K | ~$0.151 | 24-cell grids where a frame would be < ~400 px tall, extreme close-ups |

Batch tier is about half. Reference images in the prompt cost ~1,120 input tokens each (well under a cent).
Rendering, tracing and Claude itself add nothing per clip.

Typical clip: base (2K) + one grid (2K) = **~$0.20**; with one guided in-between sheet ~$0.30.
Budget one retry per new motion while you tune the guides.

For comparison, 5 s of Veo 3.1 (per-second pricing, via benchlm.ai, Sept 2026): Lite 1080p ~$0.40,
Fast 4K ~$1.50, Standard 4K ~$3.00. Check current prices at https://ai.google.dev/pricing.

Measured in the first project: flex clip $0.71 and push-up clip $0.50 including misses, before the
2K-plus-SVG rule; the 2K push-up re-run cost $0.10 and gave the same 4K result.
