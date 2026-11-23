<p align="center">
  <picture><source media="(max-width: 600px) and (prefers-color-scheme: dark)" srcset="assets/banner-m-dark.svg"><source media="(max-width: 600px)" srcset="assets/banner-m-light.svg"><source media="(prefers-color-scheme: dark)" srcset="assets/banner-dark.svg"><img src="assets/banner-light.svg" alt="presentations ❯ ls -1 — Every talk, one file. The slides for my talks, one folder each." width="100%"></picture>
</p>

<p align="center">
  <picture><source media="(max-width: 600px) and (prefers-color-scheme: dark)" srcset="assets/covers-m-dark.svg"><source media="(max-width: 600px)" srcset="assets/covers-m-light.svg"><source media="(prefers-color-scheme: dark)" srcset="assets/covers-dark.svg"><img src="assets/covers-light.svg" alt="Mock covers in the house style, for talks that don't exist (yet): Self-hosted mail; Backups that restore; Four Pis and a cluster" width="100%"></picture>
</p>

<p align="center">
  <a href="nixos-homelab/"><picture><source media="(max-width: 600px) and (prefers-color-scheme: dark)" srcset="assets/talk-nixos-homelab-m-dark.svg"><source media="(max-width: 600px)" srcset="assets/talk-nixos-homelab-m-light.svg"><source media="(prefers-color-scheme: dark)" srcset="assets/talk-nixos-homelab-dark.svg"><img src="assets/talk-nixos-homelab-light.svg" alt="01 — NixOS Homelab: One Blackview mini PC running NixOS from a flake: 29 containers, Matrix on k3s, and only two doors in from the network." width="100%"></picture></a>
</p>

<p align="center">
  <a href="minecraft-server/"><picture><source media="(max-width: 600px) and (prefers-color-scheme: dark)" srcset="assets/talk-minecraft-server-m-dark.svg"><source media="(max-width: 600px)" srcset="assets/talk-minecraft-server-m-light.svg"><source media="(prefers-color-scheme: dark)" srcset="assets/talk-minecraft-server-dark.svg"><img src="assets/talk-minecraft-server-light.svg" alt="02 — DS Network: How my Minecraft server works, explained for everyone: one doorman, a lobby that catches you, and three worlds behind it." width="100%"></picture></a>
</p>

<p align="center">
  <picture><source media="(max-width: 600px) and (prefers-color-scheme: dark)" srcset="assets/keys-m-dark.svg"><source media="(max-width: 600px)" srcset="assets/keys-m-light.svg"><source media="(prefers-color-scheme: dark)" srcset="assets/keys-dark.svg"><img src="assets/keys-light.svg" alt="Presenting: → / Space = Next; ← / PgUp = Previous; S = Speaker view; F = Fullscreen; B = Black screen; L = Laser pointer; M = Reduce motion; Esc = Back to editor" width="100%"></picture>
</p>

> [!TIP]
> **To open a talk**, open its folder, download `index.html` and open it in a browser. It runs offline;
> GitHub itself only shows the file as source code.

<p align="center">
  <picture><source media="(max-width: 600px) and (prefers-color-scheme: dark)" srcset="assets/style-m-dark.svg"><source media="(max-width: 600px)" srcset="assets/style-m-light.svg"><source media="(prefers-color-scheme: dark)" srcset="assets/style-dark.svg"><img src="assets/style-light.svg" alt="House style: Fraunces Black titles, Instrument Sans body, JetBrains Mono labels, shell-prompt kickers, bracketed labels, # asides, chapter footers, its own palette per talk" width="100%"></picture>
</p>

<details>
<summary><code>[ HOW THIS README WORKS ]</code></summary>

<br>

No screenshots of text, no third-party cards. Every image is an SVG drawn by [`build.py`](build.py) in the decks'
own style, with the text turned into outlines. The fonts are taken straight out of a deck's `index.html`. Each image
has a light and a dark version and a phone layout, and they follow your system theme.

| piece | what moves |
| --- | --- |
| **banner** | the prompt types `ls -1`, the title draws in, three made-up talk covers fan out, the marquee keeps scrolling |
| **covers** | three mock covers for talks that don't exist (yet) wipe in, one after another |
| **talk cards** | a mock of the talk's cover wipes in, the title draws, the chips and the talk's own palette pop in |
| **keys** | the keycaps pop in; every few seconds the `→` key gets pressed |
| **house style** | the specimens draw in under a marching dashed rule |
| **footer** | the prompt types `exit`, the progress bar fills, the cursor blinks |

The covers in the banner are for talks that don't exist (yet), drawn in the decks' style; the real slides are on each talk's own page. Edit `MOCK_COVERS` to change them.
The Minecraft talk breaks the house style on purpose: its card and its own page are drawn by [`minecraft.py`](minecraft.py) in that deck's pixel style.
Everything plays once on load and stays still for people who prefer reduced motion.

**Adding a talk:** put its folder next to `nixos-homelab/` with the deck as `index.html`, save its cover and a few
other slides as 960×540 (plus 640×360 `-s`) JPEGs in `assets/thumbs/`, add it to `TALKS` in `build.py`, and run:

```sh
pip install fonttools uharfbuzz brotli
python3 build.py
```

It writes this README, every talk's own README and all the images.

**Editing a deck:** open its `index.html`, press `Esc`, edit, then save with `⌘S` / `Ctrl+S`.

</details>

<p align="center">
  <picture><source media="(max-width: 600px) and (prefers-color-scheme: dark)" srcset="assets/footer-m-dark.svg"><source media="(max-width: 600px)" srcset="assets/footer-m-light.svg"><source media="(prefers-color-scheme: dark)" srcset="assets/footer-dark.svg"><img src="assets/footer-light.svg" alt="presentations ❯ exit — Dias Stas, 2026" width="100%"></picture>
</p>

<p align="center">
  <a href="https://bento.page"><picture><source media="(max-width: 600px) and (prefers-color-scheme: dark)" srcset="assets/credits-m-dark.svg"><source media="(max-width: 600px)" srcset="assets/credits-m-light.svg"><source media="(prefers-color-scheme: dark)" srcset="assets/credits-dark.svg"><img src="assets/credits-light.svg" alt="Credits: Bento Slides (MIT); Fraunces (OFL 1.1); Instrument Sans (OFL 1.1); JetBrains Mono (OFL 1.1); Jersey 10 (OFL 1.1)" width="100%"></picture></a>
</p>
