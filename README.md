# NixOS Homelab — the presentation

A 22-slide talk about my homelab: one Blackview MP60 mini PC (`thalamus`) running
NixOS 26.05 from a flake, 29 Docker containers, Matrix on k3s, and only two doors
into it from the network.

**[▶ Open the presentation](index.html)** — it's a single self-contained HTML file
made with [Bento Slides](https://bento.page). No install, no server, no internet
needed: download `index.html` and open it in a browser.

## Presenting

| Key | Does |
|---|---|
| `→` / `PageDown` / click | next slide |
| `←` / `PageUp` | previous slide |
| `S` | speaker view (timer, next slide, notes) |
| `Esc` | open the editor |

Mouse side buttons: map them to PageUp / PageDown (e.g. `services.input-remapper.enable = true;`),
since by default they act as the browser's Back/Forward and Back leaves the deck.

## Chapters

1. **The box** — the MP60 and what's in it
2. **What is NixOS** — declarative config, my flake, generations and rollback
3. **The stack** — 29 containers, what they do and what they replace
4. **Two doors** — Nginx Proxy Manager, Anubis, Authentik, and the Minecraft network behind Velocity
5. **Messages & safety** — Matrix, Ntfy, and what keeps it all safe
6. **Uptime** — does it actually stay up?
7. **Wrap-up** — takeaways and questions

## Editing

Open `index.html`, press `Esc`, edit, and save with `⌘S` / `Ctrl+S` — the file
rewrites itself. The slides are plain JSON inside the `bento-doc` script block.

## Credits

Built with Bento Slides (MIT). Fonts: Fraunces and Instrument Sans (embedded by
Bento) and JetBrains Mono, all under the SIL Open Font License 1.1.
No secrets, keys or private addresses are included in this deck.
