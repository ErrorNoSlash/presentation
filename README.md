<picture>
  <source media="(prefers-color-scheme: dark)" srcset=".github/readme/banner-dark.png">
  <img alt="presentations ❯ ls -1 — Every talk, one file. The slides for my talks, one folder each." src=".github/readme/banner-light.png" width="100%">
</picture>

<br>

<a href="nixos-homelab/">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset=".github/readme/talk-nixos-homelab-dark.png">
    <img alt="01 — NixOS Homelab: one Blackview mini PC running NixOS from a flake, 29 containers, Matrix on k3s, two doors. 22 slides, 8 chapters." src=".github/readme/talk-nixos-homelab-light.png" width="100%">
  </picture>
</a>

<p align="center"><code>▶ <a href="nixos-homelab/index.html">nixos-homelab/index.html</a></code> &nbsp;·&nbsp; <code><a href="nixos-homelab/">chapters &amp; notes</a></code></p>

<br>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset=".github/readme/keys-dark.png">
  <img alt="Presenting: → / Space / PageDown / clicker = next, ← / PageUp = previous, S = speaker view, F = fullscreen, B = black screen, L = laser pointer, M = reduce motion, Esc = back to editor." src=".github/readme/keys-light.png" width="100%">
</picture>

> [!TIP]
> **To open a talk**, download its `index.html` (**⋯ → Download**) and open it in any modern browser. It runs fully offline.
> GitHub only shows the file as source code.

<br>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset=".github/readme/style-dark.png">
  <img alt="House style: Fraunces Black for titles, Instrument Sans for body, JetBrains Mono for labels. host ❯ command kickers, [ SECTION ] labels, # asides, chapter footers, an own palette per talk, things draw themselves." src=".github/readme/style-light.png" width="100%">
</picture>

<details>
<summary><b>Adding a talk</b></summary>
<br>

1. Make a folder `kebab-case-name/` holding the deck as `index.html` and a short `README.md`
   (copy [`nixos-homelab/README.md`](nixos-homelab/README.md)).
2. Add its card under the last one, numbered `02`, `03`, …, in the same style: cover slide on the left, title,
   one-line description, slide and chapter count, and the talk's own palette.

</details>

<details>
<summary><b>Editing a deck</b></summary>
<br>

Open `index.html`, press `Esc` to reach the editor, and save with `⌘S` / `Ctrl+S`. The file rewrites itself,
or downloads an updated copy in browsers that can't write files in place. The slides are plain JSON inside the
`bento-doc` script block.

</details>

<br>

<sub>Built with <a href="https://bento.page">Bento Slides</a> (MIT) · Fraunces, Instrument Sans and JetBrains Mono under the SIL Open Font License 1.1 · <code># EOF</code></sub>
