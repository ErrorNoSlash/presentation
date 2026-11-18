<picture>
  <source media="(prefers-color-scheme: dark)" srcset=".github/readme/banner-dark.svg">
  <img alt="presentations ❯ ls -1 — Every talk, one file." src=".github/readme/banner-light.svg" width="100%">
</picture>

`# one folder per talk · one self-contained html file each · no install, no server, no internet`

## `[ TALKS ]`

<a href="nixos-homelab/">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset=".github/readme/talk-nixos-homelab-dark.svg">
    <img alt="01 — NixOS Homelab: one mini pc, nixos 26.05, 29 containers, two doors. 22 slides, Nov 2026." src=".github/readme/talk-nixos-homelab-light.svg" width="100%">
  </picture>
</a>

| `#` | Talk | Covers | Slides | |
|:--|:--|:--|--:|:--|
| `01` | **[NixOS Homelab](nixos-homelab/)** | `# one mini pc, nixos 26.05, 29 containers, two doors` | 22 | [`▶ index.html`](nixos-homelab/index.html) |

## `[ OPEN ONE ]`

1. Open the talk's folder and its `index.html`.
2. Download it (**⋯ → Download** or **Download raw file**).
3. Open the file in Chrome, Edge, Firefox or Safari. It runs fully offline.

`# GitHub shows the .html as source code; it only becomes slides once it's opened in a browser.`

## `[ PRESENTING ]`

| Input | Does |
|:--|:--|
| `→` · `PageDown` · `Space` · clicker | next slide |
| `←` · `PageUp` | previous slide |
| `S` | speaker view: timer, next slide, notes |
| `F` | fullscreen |
| `B` | black screen |
| `L` | laser pointer |
| `M` | reduce motion |
| `Esc` | stop presenting and go back to the editor |

Talks that include mouse navigation also take **left click** = next, **right click** = previous, and the
mouse's **side buttons** = back / forward. Each talk's README says whether it does.

## `[ EDITING ]`

Open `index.html`, press `Esc`, edit, then save with `⌘S` / `Ctrl+S`. The file rewrites itself, or
downloads an updated copy in browsers that can't write files in place. The slides are plain JSON inside
the `bento-doc` script block.

## `[ HOUSE STYLE ]`

Every talk shares the same type and structure. Each one gets **its own colours**.

| Element | Style |
|:--|:--|
| Titles | **Fraunces Black**: a short sentence ending in a full stop. `What's coming.` |
| Body | **Instrument Sans** |
| Labels, code, captions | **JetBrains Mono** |
| Kicker | a shell prompt: `host ❯ command`, e.g. `thalamus ❯ cat agenda.md` |
| Section labels | bracketed caps: `[ WORRY ]` `[ ANSWER ]` `[ HOW ]` |
| Asides | code comments: `# the mini pc that runs it all` |
| Footer | chapter `NN — NAME`, page `NN / NN`, a progress bar split per chapter |
| Background | the chapter number as a huge faint numeral |
| Motion | morph transitions between slides; things that *happen* draw themselves (strike-throughs, checks, marching dashes) |

## `[ ADDING A TALK ]`

1. Make a folder `kebab-case-name/` holding `index.html` and a short `README.md` (copy
   [`nixos-homelab/README.md`](nixos-homelab/README.md)).
2. Add a row to **`[ TALKS ]`**, using the next number, with an image in `.github/readme/` that matches the
   others (the row shows the talk's own palette as swatches).

## `[ CREDITS ]`

Built with [Bento Slides](https://bento.page) (MIT). Fonts: Fraunces, Instrument Sans and JetBrains Mono,
all under the SIL Open Font License 1.1. The README images are those fonts converted to outlines.
