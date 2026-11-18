<p align="center">
  <picture><source media="(max-width: 600px) and (prefers-color-scheme: dark)" srcset=".github/readme/banner-m-dark.svg"><source media="(max-width: 600px)" srcset=".github/readme/banner-m-light.svg"><source media="(prefers-color-scheme: dark)" srcset=".github/readme/banner-dark.svg"><img src=".github/readme/banner-light.svg" alt="presentations ❯ ls -1 — Every talk, one file. The slides for my talks, one folder each." width="100%"></picture>
</p>

<p align="center">
  <a href="nixos-homelab/"><picture><source media="(max-width: 600px) and (prefers-color-scheme: dark)" srcset=".github/readme/talk-nixos-homelab-m-dark.svg"><source media="(max-width: 600px)" srcset=".github/readme/talk-nixos-homelab-m-light.svg"><source media="(prefers-color-scheme: dark)" srcset=".github/readme/talk-nixos-homelab-dark.svg"><img src=".github/readme/talk-nixos-homelab-light.svg" alt="01 — NixOS Homelab: One Blackview mini PC running NixOS from a flake: 29 containers, Matrix on k3s, and only two doors in from the network." width="100%"></picture></a>
</p>

<p align="center">
  <picture><source media="(max-width: 600px) and (prefers-color-scheme: dark)" srcset=".github/readme/keys-m-dark.svg"><source media="(max-width: 600px)" srcset=".github/readme/keys-m-light.svg"><source media="(prefers-color-scheme: dark)" srcset=".github/readme/keys-dark.svg"><img src=".github/readme/keys-light.svg" alt="Presenting: → / Space = Next; ← / PgUp = Previous; S = Speaker view; F = Fullscreen; B = Black screen; L = Laser pointer; M = Reduce motion; Esc = Back to editor" width="100%"></picture>
</p>

> [!TIP]
> **To open a talk**, open its folder, download `index.html` and open it in a browser. It runs offline;
> GitHub itself only shows the file as source code.

<p align="center">
  <picture><source media="(max-width: 600px) and (prefers-color-scheme: dark)" srcset=".github/readme/style-m-dark.svg"><source media="(max-width: 600px)" srcset=".github/readme/style-m-light.svg"><source media="(prefers-color-scheme: dark)" srcset=".github/readme/style-dark.svg"><img src=".github/readme/style-light.svg" alt="House style: Fraunces Black titles, Instrument Sans body, JetBrains Mono labels, shell-prompt kickers, bracketed labels, # asides, chapter footers, its own palette per talk" width="100%"></picture>
</p>

<details>
<summary><code>[ HOW THIS README WORKS ]</code></summary>

<br>

No screenshots of text, no third-party cards. Every image is an SVG drawn by [`build.py`](build.py) in the decks'
own style, with the text turned into outlines. The fonts are taken straight out of a deck's `index.html`. Each image
has a light and a dark version and a phone layout, and they follow your system theme.

| piece | what moves |
| --- | --- |
| **banner** | the prompt types `ls -1`, the title draws in, three real slides fan out, the marquee keeps scrolling |
| **talk cards** | the cover slide wipes in, the title draws, the chips and the talk's own palette pop in |
| **keys** | the keycaps pop in; every few seconds the `→` key gets pressed |
| **house style** | the specimens draw in under a marching dashed rule |
| **footer** | the prompt types `exit`, the progress bar fills, the cursor blinks |

Everything plays once on load and stays still for people who prefer reduced motion.

**Adding a talk:** put its folder next to `nixos-homelab/` with the deck as `index.html`, save a few 960×540
screenshots in `.github/readme/thumbs/` (cover first), add it to `TALKS` in `build.py`, and run:

```sh
pip install fonttools uharfbuzz brotli
python3 build.py
```

**Editing a deck:** open its `index.html`, press `Esc`, edit, then save with `⌘S` / `Ctrl+S`.

</details>

<p align="center">
  <picture><source media="(max-width: 600px) and (prefers-color-scheme: dark)" srcset=".github/readme/footer-m-dark.svg"><source media="(max-width: 600px)" srcset=".github/readme/footer-m-light.svg"><source media="(prefers-color-scheme: dark)" srcset=".github/readme/footer-dark.svg"><img src=".github/readme/footer-light.svg" alt="presentations ❯ exit — Dias Stas, 2026" width="100%"></picture>
</p>

<p align="center"><sub>Built with <a href="https://bento.page">Bento Slides</a> (MIT) · Fraunces, Instrument Sans and JetBrains Mono under the SIL Open Font License 1.1</sub></p>
