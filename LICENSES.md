# Third-party components

Nothing third-party is bundled in this skill except a small patch file and the Critic's calibration frames. The
rest was installed from its official source on this machine, under its own licence. `scripts/check.sh` verifies it.

| component | how it's used | licence |
|---|---|---|
| HyperFrames CLI + skills | `scripts/hf` (runs `npx hyperframes` without Gemini) | see github.com/heygen-com/hyperframes |
| ACE-Step 1.5 (code + models) | cloned from github.com/ACE-Step/ACE-Step-1.5, models from Hugging Face | MIT (see its repository and model cards) |
| `scripts/music/acestep-mps-bf16.patch` | 3-line local patch to ACE-Step (bfloat16 on Apple GPUs) | same as ACE-Step (MIT) |
| demucs | vocal / instrumental separation | MIT |
| whisper.cpp + large-v3-turbo (the user's build) | word timestamps | MIT |
| Kokoro-82M via `kokoro-onnx` (`hf tts`) | English Narration | Apache-2.0 / MIT |
| GSAP 3 | loaded from the jsDelivr CDN by compositions | GSAP standard licence (free, including commercial use) |
| uv | Python project manager used to run ACE-Step | MIT / Apache-2.0 |
| `assets/critic-frames/` (16 PNGs) | the Critic's "10" anchor: frames of the viral videos and "The Lantern", grabbed from YouTube video zke3bTtvmLo | © their authors; local reference only, never redistribute |

Music you generate with ACE-Step and sound effects synthesized by `scripts/sfx/sfx_lib.py` are yours to use.
Fonts: use the HyperFrames bundled fonts or SIL Open Font License fonts (Google Fonts). Don't ship proprietary fonts.
