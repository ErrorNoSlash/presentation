#!/usr/bin/env python3
"""Builds this repo's README and its images.

Every image is a hand-written SVG in the decks' own house style: Fraunces titles,
Instrument Sans body, JetBrains Mono labels, `host ❯ command` kickers, [ BRACKETED ]
labels, chapter footers, things that draw themselves. Text is converted to outlines,
so the fonts show everywhere. The fonts come straight out of a deck's index.html,
so no font files live in this repo.

Each image comes in light and dark, and in a desktop and a phone (-m) layout.
Animations are CSS inside the SVG: they play once when the page loads (the
marquee, the cursor and the occasional key press keep going), and they switch
off for people who prefer reduced motion.

    pip install fonttools uharfbuzz brotli
    python3 build.py

To add a talk: put its folder next to the others, drop a few 960x540 screenshots
in assets/thumbs/ (cover first), add it to TALKS and run the script. A talk with
style='minecraft' gets its own page drawn by minecraft.py, in that deck's style.
"""
import base64, io, json, os, re, zlib
from xml.sax.saxutils import escape

import uharfbuzz as hb

import minecraft
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, 'assets')
THUMBS = os.path.join(OUT, 'thumbs')

# ─── content ────────────────────────────────────────────────────────────────
AUTHOR = 'Dias Stas'
YEAR = '2026'

TALKS = [
    dict(
        slug='nixos-homelab',
        title='NixOS Homelab',
        host='thalamus',
        date='nov 2026',
        slides=22,
        desc='One Blackview mini PC running NixOS from a flake: 29 containers, '
             'Matrix on k3s, and only two doors in from the network.',
        chips=['22 slides', '8 chapters', 'nixos · docker · k3s'],
        palette=[('#0D1B2E', 'navy'), ('#5277C3', 'nix blue'), ('#7EBAE4', 'light blue'),
                 ('#C9E1F3', 'sky'), ('#F2F0EA', 'cream')],
        # the talk's own page shows the real slides: (thumbnail, page, title)
        cover='nixos-homelab-01.jpg',
        gallery=[('nixos-homelab-03', 3, 'The whole lab on one page.'),
                 ('nixos-homelab-07', 7, 'Every rebuild is a generation.'),
                 ('nixos-homelab-08', 8, 'NixOS runs the host. Docker runs the apps.'),
                 ('nixos-homelab-17', 17, 'Door two: Minecraft.'),
                 ('nixos-homelab-19', 19, 'Every worry gets an answer.'),
                 ('nixos-homelab-21', 21, 'What I’d take away.')],
        chapters=[('00', 'Overview', 'the whole lab on one page', '03'),
                  ('01', 'The box', 'blackview mp60, the mini pc that runs it all', '04'),
                  ('02', 'What is NixOS', 'one flake in git, every rebuild a generation', '05–07'),
                  ('03', 'The stack', '29 containers, what they replace, the databases', '08–12'),
                  ('04', 'Two doors', 'web + minecraft, guarded by anubis + authentik', '13–17'),
                  ('05', 'Messages & safety', 'matrix, ntfy, and the threat model', '18–19'),
                  ('06', 'Uptime', 'does it actually stay up?', '20'),
                  ('07', 'Wrap-up', 'takeaways and questions', '21–22')],
        mouse=[(['Left click'], 'Next', ''), (['Right click'], 'Previous', 'no context menu'),
               (['Side →'], 'Next', 'forward button'), (['Side ←'], 'Previous', 'back button')],
        mouse_note='# off in laser mode (L), on links and buttons, and while dragging',
        # its card on the main page shows a made-up cover in the deck's style, not the real slide
        cover_mock=dict(variant='dark', host='thalamus', cmd='ssh thalamus', lead='NIXOS', big='HOMELAB',
                        sub=['One mini PC, one flake,', 'and only two doors in.'], tag='01 · NOV 2026',
                        band=['29 CONTAINERS', 'ONE MINI PC', 'TWO DOORS', 'NIXOS 26.05', 'K3S'], block='22 SLIDES',
                        colors=dict(bg='#0D1B2E', ink='#F2F0EA', a1='#5277C3', a2='#7EBAE4', soft='#C9E1F3', dim='#AFC6DD')),
    ),
    dict(
        slug='minecraft-server',
        style='minecraft',          # drawn by minecraft.py in the deck's own pixel style
        title='DS Network',
        host='minecraft',
        by='Dias & Franck',
        date='nov 2026',
        slides=14,
        desc='How my Minecraft server works, explained for everyone: one doorman, '
             'a lobby that catches you, and three worlds behind it.',
        chips=['14 slides', '6 chapters', 'Dias & Franck', 'nov 2026'],
        palette=[('#15151C', 'deepslate'), ('#7BD13F', 'grass'), ('#80FF20', 'xp green'), ('#FFD23F', 'gold'),
                 ('#FFFF55', 'chat yellow'), ('#9B5DE5', 'portal'), ('#5EE6E0', 'diamond'), ('#E5383B', 'redstone')],
        cover='minecraft-server-01.jpg',
        gallery=[('minecraft-server-05', 5, 'Every player takes the same path.'),
                 ('minecraft-server-07', 7, 'Phones, consoles, PCs: everyone gets in.'),
                 ('minecraft-server-09', 9, 'Stop 3 · Three worlds to explore'),
                 ('minecraft-server-10', 10, 'Busier worlds get more room to think.'),
                 ('minecraft-server-11', 11, 'If a world crashes, you don’t get thrown out.'),
                 ('minecraft-server-14', 14, 'Thank you!')],
        # (icon, number, chapter, what it covers, pages, presenter, colour)
        mc_chapters=[('grass', '01', 'The basics', 'What a server is, and where ours lives', '03–04', 'DIAS', 'gold'),
                     ('door', '02', 'Getting in', 'The path every player takes, on any device', '05–07', 'DIAS', 'gold'),
                     ('portal', '03', 'Lobby & worlds', 'Where you land, and where you play', '08–09', 'FRANCK', 'cyan'),
                     ('chest', '04', 'Behind the scenes', 'How one small computer shares itself out', '10', 'FRANCK', 'cyan'),
                     ('shield', '05', 'When things go wrong', 'Crashes, and the four locks that keep us safe', '11–12', 'FRANCK', 'cyan'),
                     ('star', '06', 'Recap & questions', 'The big picture, then over to you', '13–14', 'DIAS + FRANCK', 'green')],
        mouse_note='# off in laser mode (L), on links and buttons, and while dragging',
        before=['Scan the QR code on slide 14 once with your own phone. It opens <https://hello.errornoslash.be>.',
                'The speaker notes start with **[DIAS]** or **[FRANCK]**, so each of you knows when it’s your turn.',
                'Check the descriptions of **Old survival** and **Anarchy** on slide 9 against how you use those worlds.',
                'Slide 11 says players rejoin the world they left: that’s SmartRejoin’s default setting.'],
    ),
]

# Covers for talks that don't exist (yet): the banner fans these out.
# Same type and composition as the real decks, each with its own palette.
MOCK_COVERS = [
    dict(name='Self-hosted mail', layout='tape', variant='dark', host='postbox', cmd='tail -f mail.log', lead='SELF-HOSTED', big='MAIL',
         sub=['Running my own mail server,', 'and why nobody else should.'], tag='03 · DEC 2026',
         band=['SPF', 'DKIM', 'DMARC', 'PORT 25', 'BLOCKLISTS', 'REVERSE DNS'], block='DELIVERED · 98.2%',
         colors=dict(bg='#2A1215', ink='#FBF1E6', a1='#C8553D', a2='#F2A65A', soft='#F5E6CC', dim='#E9B9A6')),
    dict(name='Backups that restore', layout='split', variant='light', host='vault', cmd='restic snapshots', lead='BACKUPS THAT', big='RESTORE',
         sub=['Three copies, two media, one offsite.', 'And actually testing them.'], tag='04 · JAN 2027',
         band=['3-2-1', 'RESTIC', 'OFFSITE', 'TESTED MONTHLY', 'ZERO LOSSES'], block='LAST RESTORE · 2 DAYS AGO',
         colors=dict(bg='#E3F2E6', ink='#0F2419', a1='#2F7D4F', a2='#7CC68D', soft='#0F2419', dim='#3E6B4F')),
    dict(name='Four Pis and a cluster', layout='rack', variant='dark', host='rack', cmd='kubectl get nodes', lead='FOUR PIS AND A', big='CLUSTER',
         sub=['Bare-metal k3s on a shelf: what broke', 'first, and what stayed up.'], tag='05 · FEB 2027',
         band=['4 NODES', 'K3S', 'LONGHORN', '16 GB TOTAL', 'POE POWERED'], block='4 / 4 READY',
         colors=dict(bg='#17122B', ink='#F4F0FF', a1='#6C4AB6', a2='#B39CF0', soft='#E6DEFB', dim='#B9AEDA')),
]

KEYS = [  # (keys, what, note)
    (['→', 'Space'], 'Next', 'pgdn · clicker'),
    (['←', 'PgUp'], 'Previous', ''),
    (['S'], 'Speaker view', 'timer · next · notes'),
    (['F'], 'Fullscreen', ''),
    (['B'], 'Black screen', ''),
    (['L'], 'Laser pointer', ''),
    (['M'], 'Reduce motion', ''),
    (['Esc'], 'Back to editor', ''),
]

STYLE_RULES = [
    ('host ❯ command', 'kicker, a shell prompt'),
    ('[ SECTION ]', 'bracketed caps for labels'),
    ('# an aside', 'comments for side notes'),
    ('05 — CHAPTER · 19 / 22', 'chapter footer + progress'),
    ('own palette per talk', 'type and structure stay shared'),
    ('things draw themselves', 'wipes, strikes, marching dashes'),
]

THEMES = {
    'light': dict(bg='#F4F3EF', ink='#15171C', muted='#6B6F78', faint='rgba(21,23,28,0.05)',
                  rule='rgba(21,23,28,0.15)', card='#FFFFFF', keyedge='#D6D4CC', band='#15171C', bandink='#F4F3EF'),
    'dark':  dict(bg='#111317', ink='#EDECE8', muted='#959BA5', faint='rgba(237,236,232,0.045)',
                  rule='rgba(237,236,232,0.15)', card='#1B1E24', keyedge='#060708', band='#EDECE8', bandink='#111317'),
}

# ─── fonts, taken out of a deck ─────────────────────────────────────────────
B86 = "!#$%()*+,./0123456789:;=?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[]^_`abcdefghijklmnopqrstuvwxyz|}~"
B86V = {c: i for i, c in enumerate(B86)}

def b86decode(t):
    out, i, n = bytearray(), 0, len(t)
    while i + 5 <= n:
        v = 0
        for k in range(5): v = v * 86 + B86V[t[i + k]]
        out += v.to_bytes(4, 'big'); i += 5
    if i < n:
        r, v = n - i, 0
        for k in range(5): v = v * 86 + (B86V[t[i + k]] if k < r else 85)
        out += v.to_bytes(4, 'big')[:r - 1]
    return bytes(out)

def deck_fonts(html_path):
    """Every embedded woff2 in a Bento deck (the slide data and the packed runtime), by family name."""
    html = open(html_path, encoding='utf-8').read()
    blobs = [html]
    m = re.search(r'<script id="bento-rt"[^>]*type="bento/deflate-b86"[^>]*>(.*?)</script>', html, re.S)
    if m: blobs.append(zlib.decompress(b86decode(m.group(1).strip()), -15).decode('utf-8'))
    fonts = {}
    for blob in blobs:
        for uri in re.findall(r'data:font/woff2;base64,([A-Za-z0-9+/=]+)', blob):
            f = TTFont(io.BytesIO(base64.b64decode(uri)))
            fonts.setdefault(f['name'].getDebugName(1), f)
    return fonts

def instance(font, axes):
    f = TTFont(io.BytesIO(_save(font)))
    if 'fvar' in f: instantiateVariableFont(f, {k: v for k, v in axes.items() if k in [a.axisTag for a in f['fvar'].axes]}, inplace=True)
    f.flavor = None
    return _save(f)

def _save(f):
    b = io.BytesIO(); f.save(b); return b.getvalue()

class Face:
    def __init__(self, data):
        self.hb = hb.Font(hb.Face(hb.Blob(data)))
        self.tt = TTFont(io.BytesIO(data))
        self.gs, self.upem, self.order = self.tt.getGlyphSet(), self.tt['head'].unitsPerEm, self.tt.getGlyphOrder()

    def shape(self, s):
        buf = hb.Buffer(); buf.add_str(s); buf.guess_segment_properties()
        hb.shape(self.hb, buf, {'kern': True, 'liga': True})
        return buf.glyph_infos, buf.glyph_positions

    def width(self, s, size, ls=0):
        _, pos = self.shape(s)
        return sum(p.x_advance for p in pos) * size / self.upem + ls * max(len(pos) - 1, 0)

    def path(self, s, size, x, y, ls=0, anchor='start'):
        infos, pos = self.shape(s)
        sc = size / self.upem
        w = sum(p.x_advance for p in pos) * sc + ls * max(len(pos) - 1, 0)
        if anchor == 'end': x -= w
        elif anchor == 'middle': x -= w / 2
        pen = SVGPathPen(self.gs, ntos=lambda v: ('%.1f' % v).rstrip('0').rstrip('.'))
        for info, p in zip(infos, pos):
            self.gs[self.order[info.codepoint]].draw(
                TransformPen(pen, (sc, 0, 0, -sc, x + p.x_offset * sc, y - p.y_offset * sc)))
            x += p.x_advance * sc + ls
        return pen.getCommands(), w

F = {}

def load_fonts():
    src = deck_fonts(os.path.join(ROOT, TALKS[0]['slug'], 'index.html'))
    need = {'Fraunces': 'Fraunces', 'Instrument Sans': 'Instrument Sans', 'JetBrains Mono': 'JetBrains Mono'}
    found = {k: next((f for n, f in src.items() if n and n.startswith(v)), None) for k, v in need.items()}
    missing = [k for k, f in found.items() if f is None]
    if missing: raise SystemExit(f'fonts not found in the deck: {missing}')
    F['serif'] = Face(instance(found['Fraunces'], {'opsz': 72}))
    F['sans'] = Face(instance(found['Instrument Sans'], {'wght': 500}))
    F['mono'] = Face(instance(found['JetBrains Mono'], {'wght': 400}))
    F['monob'] = Face(instance(found['JetBrains Mono'], {'wght': 700}))
    F['sans6'] = Face(instance(found['Instrument Sans'], {'wght': 600}))
    for talk in TALKS:
        if talk.get('style') == 'minecraft':
            pix = deck_fonts(os.path.join(ROOT, talk['slug'], 'index.html'))
            jersey = next((f for n, f in pix.items() if n and n.startswith('Jersey')), None)
            if jersey is None: raise SystemExit(f'Jersey 10 not found in {talk["slug"]}/index.html')
            F['pixel'] = Face(instance(jersey, {}))

# ─── svg helpers ────────────────────────────────────────────────────────────
DRAWN = '→←❯'   # the decks ship trimmed fonts without these, so they are drawn as strokes

def _runs(s):
    run = ''
    for ch in s:
        if ch in DRAWN:
            if run: yield run
            yield ch; run = ''
        else: run += ch
    if run: yield run

def _adv(ch, font, size):
    return size * (0.6 if font.startswith('mono') else 0.9)

def _glyph(ch, x, y, size, adv, fill, font):
    sw = size * (0.12 if font in ('monob', 'serif') else 0.085)
    my = y - size * 0.33; a, b = x + adv * 0.12, x + adv * 0.88; hh = size * 0.2
    if ch == '→': d = f'M {a:.1f} {my:.1f} H {b:.1f} M {b - hh:.1f} {my - hh:.1f} L {b:.1f} {my:.1f} L {b - hh:.1f} {my + hh:.1f}'
    elif ch == '←': d = f'M {b:.1f} {my:.1f} H {a:.1f} M {a + hh:.1f} {my - hh:.1f} L {a:.1f} {my:.1f} L {a + hh:.1f} {my + hh:.1f}'
    else:
        c = x + adv * 0.35; d = f'M {c:.1f} {my - hh * 1.2:.1f} L {c + hh * 1.1:.1f} {my:.1f} L {c:.1f} {my + hh * 1.2:.1f}'
    return (f'<path d="{d}" fill="none" stroke="{fill}" stroke-width="{sw:.1f}" '
            f'stroke-linecap="round" stroke-linejoin="round"/>')

def W(s, font, size, ls=0):
    total, n = 0, 0
    for r in _runs(s):
        total += _adv(r, font, size) if r in DRAWN else F[font].width(r, size)
        n += 1 if r in DRAWN else len(r)
    return total + ls * max(n - 1, 0)

def T(s, font, size, x, y, fill, cls='', ls=0, anchor='start', style=''):
    w = W(s, font, size, ls)
    if anchor == 'end': x -= w
    elif anchor == 'middle': x -= w / 2
    c = f' class="{cls}"' if cls else ''
    st = f' style="{style}"' if style else ''
    if not any(ch in DRAWN for ch in s):
        d, _ = F[font].path(s, size, x, y, ls)
        return f'<path{c}{st} d="{d}" fill="{fill}"/>', w
    parts = []
    for r in _runs(s):
        if r in DRAWN:
            adv = _adv(r, font, size); parts.append(_glyph(r, x, y, size, adv, fill, font)); x += adv + ls
        else:
            d, rw = F[font].path(r, size, x, y, ls); parts.append(f'<path d="{d}" fill="{fill}"/>'); x += rw + ls
    return f'<g{c}{st}>' + ''.join(parts) + '</g>', w

def wrap(s, font, size, maxw):
    lines, cur = [], ''
    for word in s.split():
        t = (cur + ' ' + word).strip()
        if W(t, font, size) <= maxw or not cur: cur = t
        else: lines.append(cur); cur = word
    return lines + ([cur] if cur else [])

def chevron(x, y, size, color):
    """The decks' `❯` prompt (JetBrains Mono has no U+276F, so it is drawn)."""
    h = size * 0.34
    return (f'<path d="M {x:.1f} {y - size * 0.62:.1f} l {h:.1f} {h:.1f} l {-h:.1f} {h:.1f}" fill="none" '
            f'stroke="{color}" stroke-width="{size * 0.13:.1f}" stroke-linecap="round" stroke-linejoin="round"/>')

def thumb_uri(name):
    return 'data:image/jpeg;base64,' + base64.b64encode(open(os.path.join(THUMBS, name), 'rb').read()).decode()

BASE_CSS = '''
.wipe{animation:wipe .62s cubic-bezier(.65,0,.35,1) both}
.rise{animation:rise .5s cubic-bezier(.22,.61,.36,1) both}
.pop{transform-box:fill-box;transform-origin:center;animation:pop .42s cubic-bezier(.34,1.56,.64,1) both}
.draw{animation:draw .7s cubic-bezier(.65,0,.35,1) both}
.blink{animation:blink 1.05s steps(1) infinite}
@keyframes wipe{from{clip-path:inset(-20% 100% -20% 0)}to{clip-path:inset(-20% -2% -20% 0)}}
@keyframes rise{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:none}}
@keyframes pop{from{transform:scale(0)}to{transform:scale(1)}}
@keyframes draw{to{stroke-dashoffset:0}}
@keyframes blink{50%{opacity:0}}
@media (prefers-reduced-motion:reduce){*{animation:none!important}}
'''

def svg(w, h, t, body, label, css=''):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            f'role="img" aria-label="{escape(label)}"><title>{escape(label)}</title>'
            f'<style>{BASE_CSS}{css}</style><rect width="{w}" height="{h}" fill="{t["bg"]}"/>{body}</svg>\n')

def at(delay):
    return f'animation-delay:{delay:.2f}s'

def write(name, text):
    with open(os.path.join(OUT, name), 'w', encoding='utf-8') as f: f.write(text)

# ─── pieces ─────────────────────────────────────────────────────────────────
def typed(text_a, text_b, x, y, size, t, start=0.15, per=0.07):
    """`host ❯ command` kicker; the command types itself out, the cursor keeps blinking."""
    b, wa = T(text_a, 'mono', size, x, y, t['muted'])
    out = [b, chevron(x + wa + size * 0.55, y, size, t['muted'])]
    cx = x + wa + size * 1.25
    cw = W('M', 'mono', size)
    for i, ch in enumerate(text_b):
        if ch != ' ':
            p, _ = T(ch, 'mono', size, cx + i * cw, y, t['ink'])
            out.append(p.replace('<path ', f'<path class="key" style="{at(start + i * per)}" '))
    end = start + len(text_b) * per
    out.append(f'<rect class="cur" style="{at(end)}" x="{cx + len(text_b) * cw + 4:.1f}" y="{y - size * 0.82:.1f}" '
                f'width="{size * 0.55:.1f}" height="{size:.1f}" fill="{t["ink"]}"/>')
    return ''.join(out), ('.key{animation:keyin .01s linear both}@keyframes keyin{from{opacity:0}to{opacity:1}}'
                          '.cur{animation:keyin .01s linear both,blink 1.05s steps(1) infinite}')

def segs(x, y, w, n, on, t, start):
    gap = 10; sw = (w - gap * (n - 1)) / n; out = []
    for i in range(n):
        out.append(f'<rect x="{x + i * (sw + gap):.1f}" y="{y}" width="{sw:.1f}" height="4" rx="2" fill="{t["rule"]}"/>')
        if i < on:
            out.append(f'<rect class="wipe" style="{at(start + i * 0.12)}" x="{x + i * (sw + gap):.1f}" y="{y}" '
                       f'width="{sw:.1f}" height="4" rx="2" fill="{t["ink"]}"/>')
    return ''.join(out)

def slide(uri, x, y, w, rot, cls, delay, clip_id, origin=None):
    h = w * 9 / 16
    ox, oy = origin or (x + w / 2, y + h)
    return (f'<g class="{cls}" style="{at(delay)};transform-origin:{ox:.0f}px {oy:.0f}px;--r:{rot}deg;transform:rotate({rot}deg)">'
            f'<g filter="url(#sh)"><image href="{uri}" x="{x}" y="{y}" width="{w}" height="{h:.1f}" clip-path="url(#{clip_id})"/></g></g>'
            f'<clipPath id="{clip_id}"><rect x="{x}" y="{y}" width="{w}" height="{h:.1f}" rx="{w * 0.022:.1f}"/></clipPath>')

def _r(x, y, w, h, fill, rx=0, op=1, extra=''):
    o = f' opacity="{op}"' if op != 1 else ''
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}"{o}{extra}/>'

def _bars(x, y, widths, h, fill, gap=14, op=1):
    out = []
    for w_ in widths:
        out.append(_r(x, y, w_, h, fill, h / 2, op)); x += w_ + gap
    return ''.join(out)

def mock_content(kind, talk, uid):
    """A made-up slide in the talk's palette, composed like the decks' own (1280x720 units)."""
    P = [c for c, _ in talk['palette']]
    navy, blue, light, sky, cream = (P + P)[:5]
    o = []
    foot = lambda ink, on: ''.join(_r(96 + i * 156.6, 682, 148.6, 4, ink if i == on else ink, 2, 1 if i == on else 0.25) for i in range(7))
    if kind == 'cover':
        o.append(_r(0, 0, 1280, 720, navy))
        o.append(_bars(24, 10, [180, 120, 220, 150, 200, 130, 170], 9, light, 22, 0.35))
        o.append(_bars(96, 58, [96], 13, light) + _bars(206, 58, [168], 13, cream, op=0.85))
        o.append(f'<circle cx="1050" cy="64" r="6" fill="{light}"/>' + _bars(1064, 58, [120], 13, light, op=0.6))
        words = talk['title'].upper().split()
        title, lead = words[-1], ' '.join(words[:-1])     # the last word goes huge, like the decks' covers
        size = min(300, 1090 / max(W(title, 'serif', 1), 1))
        y = 300 + size * 0.7
        if lead: o.append(T(lead, 'serif', 46, 98, 120, cream)[0])
        for k, (c, dy) in enumerate([(blue, -0.62), (light, -0.32)]):   # the cover's stacked, cut-off title
            band = f'm{uid}{k}'
            o.append(f'<clipPath id="{band}"><rect x="0" y="{y + dy * size - size * 0.72:.0f}" width="1280" height="{size * 0.3:.0f}"/></clipPath>')
            o.append(f'<g clip-path="url(#{band})">' + T(title, 'serif', size, 92, y + dy * size, c)[0] + '</g>')
        o.append(T(title, 'serif', size, 92, y, sky)[0])
        o.append(_bars(96, y + 40, [380], 16, cream, op=0.9) + _bars(96, y + 66, [280], 16, cream, op=0.9) + _bars(96, y + 96, [190], 10, light, op=0.6))
        o.append(_r(930, 486, 350, 154, sky))
        o.append(f'<path d="M 978 512 v 52 m -19 -19 l 19 19 l 19 -19" fill="none" stroke="{navy}" stroke-width="9" stroke-linecap="round" stroke-linejoin="round"/>')
        o.append(_bars(960, 600, [150], 10, navy, op=0.6))
        o.append(_r(0, 640, 1280, 80, light))
        o.append(_bars(-30, 672, [150, 210, 170, 240, 190, 160, 230], 16, navy, 34, 0.85))
    elif kind == 'grid':
        o.append(_r(0, 0, 1280, 720, navy))
        o.append(_bars(96, 50, [96], 12, light) + _bars(206, 50, [150], 12, cream, op=0.8))
        o.append(_r(96, 88, 560, 46, cream, 10))
        for r in range(2):
            for c in range(3):
                x, y = 96 + c * 196, 200 + r * 172
                fill = light if (r + c) % 3 else blue
                o.append(_r(x, y, 180, 152, fill, 10))
                o.append(_r(x + 18, y + 20, 44, 58, navy, 6, 0.9))
                o.append(_bars(x + 18, y + 96, [120], 11, navy, op=0.7) + _bars(x + 18, y + 118, [90], 9, navy, op=0.45))
        o.append(f'<rect x="712" y="190" width="472" height="342" rx="12" fill="none" stroke="{light}" stroke-width="3" stroke-dasharray="14 10" opacity="0.8"/>')
        for i in range(3):
            o.append(_r(740, 222 + i * 96, 416, 72, blue if i == 1 else '#ffffff', 10, 1 if i == 1 else 0.08))
            o.append(_bars(762, 250 + i * 96, [180, 90], 14, cream, op=0.75))
        o.append(_r(96, 560, 1088, 64, cream, 10, 0.92) + _bars(124, 586, [260, 140], 14, navy, op=0.7))
        o.append(foot(light, 2))
    else:  # 'list'
        o.append(_r(0, 0, 1280, 720, sky))
        o.append(_bars(96, 50, [96], 12, blue) + _bars(206, 50, [150], 12, navy, op=0.7))
        o.append(_r(96, 88, 640, 46, navy, 10))
        for i in range(5):
            y = 168 + i * 96
            o.append(_r(96, y, 1088, 80, '#ffffff', 14, 0.5))
            o.append(_bars(124, y + 34, [28], 12, blue))
            o.append(_bars(170, y + 34, [210], 12, navy, op=0.45) + _r(166, y + 39, 218, 2.5, navy, 0, 0.7))
            o.append(''.join(f'<circle cx="{404 + k * 12}" cy="{y + 40}" r="2.6" fill="{blue}"/>' for k in range(6)))
            o.append(_r(484, y + 10, 400, 60, navy, 10))
            o.append(f'<circle cx="516" cy="{y + 40}" r="15" fill="{light}"/>'
                     f'<path d="M 509 {y + 40} l 5 5 l 9 -10" fill="none" stroke="{navy}" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>')
            o.append(_bars(546, y + 32, [200 - i * 18], 16, cream))
            o.append(_bars(912, y + 26, [230], 11, navy, op=0.55) + _bars(912, y + 46, [160], 11, navy, op=0.4))
        o.append(foot(navy, 4))
    return ''.join(o)

def _stack(o, big, x, y, size, a1, a2, face, uid, anchor='start'):
    """The decks' signature title: the word, with two cut-off copies stacked above it."""
    for k, (col, dy) in enumerate([(a1, -0.62), (a2, -0.32)]):
        band = f'v{uid}{k}'
        o.append(f'<clipPath id="{band}"><rect x="0" y="{y + dy * size - size * 0.72:.0f}" width="1280" height="{size * 0.3:.0f}"/></clipPath>')
        o.append(f'<g clip-path="url(#{band})">' + T(big, 'serif', size, x, y + dy * size, col, anchor=anchor)[0] + '</g>')
    o.append(T(big, 'serif', size, x, y, face, anchor=anchor)[0])

def _kicker(o, c, x, y, host_col, cmd_col, tag_col, dot_col, right=1184):
    p, wa = T(c['host'], 'mono', 22, x, y, host_col); o.append(p)
    o.append(T('❯', 'mono', 22, x + wa + 8, y, host_col)[0])
    o.append(T(c['cmd'], 'mono', 22, x + wa + 38, y, cmd_col)[0])
    o.append(f'<circle cx="{right - W(c["tag"], "monob", 16, 2) - 22:.0f}" cy="{y - 7}" r="6" fill="{dot_col}"/>')
    o.append(T(c['tag'], 'monob', 16, right, y, tag_col, ls=2, anchor='end')[0])

def _ticker(o, c, col, y=26, op=0.45):
    o.append(f'<g opacity="{op}">' + T('  ·  '.join(c['band'] + c['band']), 'mono', 15, 28, y, col, ls=1)[0] + '</g>')

def _arrow(x, y, col, size=56, sw=9):
    h = size * 0.38
    return (f'<path d="M {x} {y} v {size} m {-h:.0f} {-h:.0f} l {h:.0f} {h:.0f} l {h:.0f} {-h:.0f}" fill="none" stroke="{col}" '
            f'stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"/>')

def cover_content(c, uid):
    """A deck cover in the house style (1280x720 units). Every cover shares the type, the
    prompt kicker and the stacked title; the 'layout' gives each one its own composition."""
    C = c['colors']; bg, ink, a1, a2, soft, dim = C['bg'], C['ink'], C['a1'], C['a2'], C['soft'], C['dim']
    lay = c.get('layout', 'classic')
    o = [_r(0, 0, 1280, 720, bg)]

    if lay == 'tape':        # title left, a live log window right, caution tape across the corner
        _ticker(o, c, a2)
        o.append(_r(0, 40, 1280, 1.5, a2, 0, 0.18))
        o.append(f'<g opacity="0.06">' + T('@', 'serif', 760, 1330, 640, ink, anchor='end')[0] + '</g>')
        _kicker(o, c, 96, 92, a2, ink, dim, a2)
        o.append(T(c['lead'], 'serif', 44, 98, 168, ink)[0])
        _stack(o, c['big'], 92, 430, 196, a1, a2, soft, uid)
        for i, line in enumerate(c['sub']):
            o.append(T(line, 'sans', 27, 98, 488 + i * 35, ink if i == 0 else dim)[0])
        o.append(T(f'/a talk by {AUTHOR}', 'mono', 16, 98, 488 + len(c['sub']) * 35 + 12, dim)[0])
        wx, wy, ww, wh = 700, 136, 484, 330            # the mail.log window
        o.append(_r(wx, wy, ww, wh, '#000000', 16, 0.28) + f'<rect x="{wx}" y="{wy}" width="{ww}" height="{wh}" rx="16" fill="none" stroke="{a2}" stroke-opacity="0.35" stroke-width="2"/>')
        o.append(''.join(f'<circle cx="{wx + 28 + k * 22}" cy="{wy + 26}" r="6.5" fill="{col}"/>' for k, col in enumerate([a1, a2, soft])))
        o.append(T('mail.log', 'mono', 16, wx + ww / 2, wy + 32, dim, anchor='middle')[0])
        o.append(_r(wx, wy + 50, ww, 1.5, a2, 0, 0.25))
        log = [('09:14', 'to=<anna@…>', '250', a2), ('09:15', 'to=<tom@…>', '250', a2), ('09:15', 'from=<spam@…>', '550', a1),
               ('09:17', 'to=<sara@…>', '250', a2), ('09:21', 'dkim=pass spf=pass', 'OK', soft), ('09:22', 'to=<jo@…>', '250', a2)]
        for i, (tm, what, code, col) in enumerate(log):
            ly = wy + 92 + i * 39
            o.append(T(tm, 'mono', 17, wx + 26, ly, dim)[0] + T(what, 'mono', 17, wx + 110, ly, ink)[0])
            cw = W(code, 'monob', 15) + 22
            o.append(_r(wx + ww - 26 - cw, ly - 19, cw, 26, col, 7, 0.95) + T(code, 'monob', 15, wx + ww - 26 - cw / 2, ly - 1, bg, anchor='middle')[0])
        for k, (col, rot, yy, txt_col) in enumerate([(a1, 4, 640, ink), (a2, -6, 620, bg)]):   # two crossed tapes
            text = '  *  '.join(c['band'] * 3)
            o.append(f'<g transform="rotate({rot} 980 {yy})">' + _r(560, yy - 30, 900, 62, col)
                     + T(text, 'monob', 22, 580, yy + 9, txt_col, ls=1.5)[0] + '</g>')

    elif lay == 'split':     # a dark 3·2·1 panel on the left, title and snapshot grid on the right
        o.append(_r(0, 0, 440, 720, ink))
        o.append(_r(440, 0, 840, 56, a1))
        o.append(T('  ·  '.join(c['band'] * 2), 'monob', 17, 470, 35, '#FFFFFF', ls=1.6)[0])
        for i, (num, what) in enumerate([('3', 'COPIES'), ('2', 'MEDIA'), ('1', 'OFFSITE')]):
            y = 250 + i * 190
            o.append(T(num, 'serif', 200, 80, y, a2)[0])
            o.append(T(what, 'monob', 20, 230, y - 70, bg, ls=3)[0])
            o.append(_r(230, y - 52, 140 - i * 30, 6, a2, 3, 0.6))
        p, wa = T(c['host'], 'mono', 22, 500, 112, a1); o.append(p)
        o.append(T('❯', 'mono', 22, 500 + wa + 8, 112, a1)[0] + T(c['cmd'], 'mono', 22, 500 + wa + 38, 112, ink)[0])
        o.append(T(c['tag'], 'monob', 16, 1184, 112, dim, ls=2, anchor='end')[0])
        o.append(T(c['lead'], 'serif', 46, 500, 196, ink)[0])
        size = min(170, 690 / max(W(c['big'], 'serif', 1), 1))
        ty = 196 + 22 + size * 1.34                       # the stack starts just under the lead line
        _stack(o, c['big'], 496, ty, size, a1, a2, ink, uid)
        gy = ty + 56                                      # snapshot grid: 4 weeks of nightly snapshots
        for r in range(4):
            for k in range(14):
                x = 500 + k * 47; y = gy + r * 34
                hit = (r, k) == (0, 9)
                o.append(_r(x, y, 39, 26, ink if hit else a1, 6, 1 if hit else 0.25 + 0.6 * ((k * 7 + r * 3) % 5) / 5))
        o.append(T('restored', 'monob', 15, 500 + 9 * 47 + 19, gy - 10, ink, anchor='middle')[0])
        sy = gy + 4 * 34 + 40
        o.append(T(c['sub'][0], 'sans', 26, 500, sy, ink)[0] + T(c['sub'][1], 'sans', 26, 500, sy + 34, dim)[0])
        o.append(T(f'/a talk by {AUTHOR}', 'mono', 16, 1184, sy + 34, dim, anchor='end')[0])

    elif lay == 'rack':      # a centred title over four boards cabled to a switch
        _ticker(o, c, a2)
        o.append(_r(0, 40, 1280, 1.5, a2, 0, 0.18))
        _kicker(o, c, 96, 92, a2, ink, dim, a2)
        o.append(T(c['lead'], 'serif', 40, 640, 160, ink, anchor='middle')[0])
        size = min(150, 1000 / max(W(c['big'], 'serif', 1), 1))
        _stack(o, c['big'], 640, 176 + size * 1.34, size, a1, a2, soft, uid, anchor='middle')
        bw, gap, by = 206, 30, 446
        x0 = 640 - (4 * bw + 3 * gap) / 2
        o.append(_r(390, 618, 500, 30, a1, 8))
        o.append(''.join(_r(414 + k * 38, 627, 22, 12, bg, 3, 0.8) for k in range(12)))
        for k in range(4):
            x = x0 + k * (bw + gap)
            o.append(f'<path d="M {x + bw / 2:.0f} {by + 120} C {x + bw / 2:.0f} {by + 150}, {414 + k * 114 + 11:.0f} {590}, {414 + k * 114 + 11:.0f} 627" '
                     f'fill="none" stroke="{a2}" stroke-width="3" stroke-dasharray="2 8" stroke-linecap="round"/>')
            o.append(_r(x, by, bw, 120, '#FFFFFF', 12, 0.06) + f'<rect x="{x:.0f}" y="{by}" width="{bw}" height="120" rx="12" fill="none" stroke="{a2}" stroke-opacity="0.5" stroke-width="2"/>')
            o.append(_r(x + 18, by + 22, 52, 52, soft, 6, 0.9) + _r(x + 80, by + 26, 26, 16, a2, 3, 0.7) + _r(x + 80, by + 50, 40, 10, a2, 3, 0.4))
            o.append(f'<circle cx="{x + bw - 26:.0f}" cy="{by + 30}" r="7" fill="{a2}"/><circle cx="{x + bw - 48:.0f}" cy="{by + 30}" r="7" fill="{soft}" opacity="0.5"/>')
            o.append(T(f'node-0{k + 1}', 'mono', 17, x + 18, by + 104, ink)[0] + T('READY', 'monob', 14, x + bw - 18, by + 104, a2, anchor='end', ls=1.5)[0])
        o.append(T(' '.join(c['sub']), 'sans', 22, 96, 696, dim)[0])
        o.append(T(f'/a talk by {AUTHOR}', 'mono', 15, 1184, 696, dim, anchor='end')[0])

    else:                    # 'classic': the NixOS deck's own cover composition
        _ticker(o, c, a2)
        o.append(_r(0, 40, 1280, 1.5, a2, 0, 0.18))
        _kicker(o, c, 96, 92, a2, ink, dim, a2)
        o.append(f'<g opacity="{0.07 if c["variant"] == "dark" else 0.09}">' + T(c['tag'][:2], 'serif', 560, 1250, 600, ink, anchor='end')[0] + '</g>')
        y = 440
        size = min(186, 1090 / max(W(c['big'], 'serif', 1), 1))
        o.append(T(c['lead'], 'serif', 50, 98, 176, ink)[0])
        _stack(o, c['big'], 92, y, size, a1, a2, soft if c['variant'] == 'dark' else ink, uid)
        for i, line in enumerate(c['sub']):
            o.append(T(line, 'sans', 28, 98, y + 58 + i * 36, ink if i == 0 else dim)[0])
        o.append(T(f'/a talk by {AUTHOR}', 'mono', 16, 98, y + 58 + len(c['sub']) * 36 + 14, dim)[0])
        bx, by, bw, bh = 914, 470, 366, 170
        o.append(_r(bx, by, bw, bh, a2 if c['variant'] == 'light' else soft))
        ac = bg if c['variant'] == 'dark' else C['ink']
        o.append(_arrow(bx + 46, by + 26, ac))
        o.append(T(c['block'], 'monob', 15, bx + 28, by + 138, ac, ls=1.6)[0])
        o.append(_r(0, 640, 1280, 80, a2 if c['variant'] == 'dark' else a1))
        o.append(T('  *  '.join(c['band'] * 3), 'monob', 26, -40, 690, bg if c['variant'] == 'dark' else '#FFFFFF', ls=1.5)[0])
    return ''.join(o)

def mock(kind, talk, x, y, w, rot, cls, delay, uid, origin=None):
    h = w * 9 / 16; s_ = w / 1280
    ox, oy = origin or (x + w / 2, y + h)
    return (f'<g class="{cls}" style="{at(delay)};transform-origin:{ox:.0f}px {oy:.0f}px;--r:{rot}deg;transform:rotate({rot}deg)">'
            f'<g filter="url(#sh)"><g transform="translate({x:.1f} {y:.1f}) scale({s_:.5f})">'
            f'<clipPath id="k{uid}"><rect width="1280" height="720" rx="28"/></clipPath>'
            f'<g clip-path="url(#k{uid})">{cover_content(kind, uid) if isinstance(kind, dict) else mock_content(kind, talk, uid)}</g></g></g></g>')

def shadow(t):
    a = '0.28' if t is THEMES['light'] else '0.7'
    return (f'<defs><filter id="sh" x="-20%" y="-20%" width="140%" height="160%">'
            f'<feDropShadow dx="0" dy="22" stdDeviation="20" flood-color="#000" flood-opacity="{a}"/></filter></defs>')

def marquee(y, w, h, t, items):
    text = '  ·  '.join(items) + '  ·  '
    size = h * 0.36
    unit = W(text, 'monob', size, 2.2)
    reps = int(w / unit) + 2
    parts = ''.join(T(text, 'monob', size, i * unit, y + h * 0.63, t['bandink'], ls=2.2)[0] for i in range(reps))
    css = f'.mq{{animation:mq {unit / 60:.1f}s linear infinite}}@keyframes mq{{to{{transform:translateX(-{unit:.1f}px)}}}}'
    return (f'<rect x="0" y="{y}" width="{w}" height="{h}" fill="{t["band"]}"/>'
            f'<g clip-path="url(#mqc)"><g class="mq">{parts}</g></g>'
            f'<clipPath id="mqc"><rect x="0" y="{y}" width="{w}" height="{h}"/></clipPath>'), css

def banner(t, mobile):
    w = 640 if mobile else 1280; M = 40 if mobile else 80
    css, out = '', [shadow(t)]
    if mobile:
        h = 1060
        wm, _ = T('00', 'serif', 560, w + 60, 760, t['faint'], anchor='end'); out.append(wm)
        k, kc = typed('presentations', 'ls -1', M, 76, 24, t); out.append(k); css += kc
        for i, line in enumerate(['Every talk,', 'one file.']):
            p, _ = T(line, 'serif', 92, M - 4, 200 + i * 96, t['ink'], cls='wipe', style=at(0.55 + i * 0.16), ls=-1)
            out.append(p)
        sub = wrap('The slides for my talks, one folder each. Every deck is a single HTML file: '
                   'download it, open it, present.', 'sans', 30, w - 2 * M)
        for i, line in enumerate(sub):
            p, _ = T(line, 'sans', 30, M, 370 + i * 44, t['ink'] if i == 0 else t['muted'], cls='rise', style=at(0.95 + i * 0.05))
            out.append(p)
        y0 = 370 + len(sub) * 44 + 40
        fan = [(MOCK_COVERS[2], 150, y0 + 40, 400, 8), (MOCK_COVERS[1], 110, y0 + 20, 400, 2), (MOCK_COVERS[0], 70, y0, 400, -5)]
        for i, (kind, x, y, sw, rot) in enumerate(fan):
            out.append(mock(kind, TALKS[0], x, y, sw, rot, 'fan', 1.1 + i * 0.12, f'c{i}', (x + sw / 2, y + sw * 9 / 16 + 40)))
        out.append(T('00 — INDEX', 'monob', 18, M, 912, t['muted'], ls=2.5)[0])
        out.append(T(AUTHOR.upper(), 'monob', 18, w - M, 912, t['muted'], ls=2.5, anchor='end')[0])
        out.append(segs(M, 934, w - 2 * M, 4, 1, t, 1.6))
        mq, mc = marquee(980, w, 80, t, ['EVERY TALK, ONE FILE'] + [f'{i + 1:02d} {x["title"].upper()}' for i, x in enumerate(TALKS)] + ['OPENS OFFLINE'])
        out.append(mq); css += mc
    else:
        h = 640
        wm, _ = T('00', 'serif', 640, w + 40, 700, t['faint'], anchor='end'); out.append(wm)
        k, kc = typed('presentations', 'ls -1', M, 84, 21, t); out.append(k); css += kc
        for i, line in enumerate(['Every talk,', 'one file.']):
            p, _ = T(line, 'serif', 112, M - 4, 222 + i * 112, t['ink'], cls='wipe', style=at(0.55 + i * 0.16), ls=-1.5)
            out.append(p)
        sub = wrap('The slides for my talks, one folder each. Every deck is a single HTML file: '
                   'download it, open it, present.', 'sans', 25, 560)
        for i, line in enumerate(sub):
            p, _ = T(line, 'sans', 25, M, 410 + i * 36, t['ink'] if i == 0 else t['muted'], cls='rise', style=at(0.95 + i * 0.05))
            out.append(p)
        fan = [(MOCK_COVERS[2], 770, 150, 430, 8), (MOCK_COVERS[1], 730, 120, 430, 2), (MOCK_COVERS[0], 690, 96, 430, -5)]
        for i, (kind, x, y, sw, rot) in enumerate(fan):
            out.append(mock(kind, TALKS[0], x, y, sw, rot, 'fan', 0.9 + i * 0.12, f'c{i}', (x + sw / 2, y + sw * 9 / 16 + 60)))
        out.append(T('00 — INDEX', 'monob', 15, M, 536, t['muted'], ls=2)[0])
        out.append(T(AUTHOR.upper(), 'monob', 15, w - M, 536, t['muted'], ls=2, anchor='end')[0])
        out.append(segs(M, 554, w - 2 * M, 7, 1, t, 1.5))
        mq, mc = marquee(584, w, 56, t, ['EVERY TALK, ONE FILE'] + [f'{i + 1:02d} {x["title"].upper()}' for i, x in enumerate(TALKS)]
                         + [f'{len(TALKS)} TALK' + ('S' if len(TALKS) != 1 else ''), 'OPENS OFFLINE'])
        out.append(mq); css += mc
    css += ('.fan{animation:fan .9s cubic-bezier(.34,1.3,.64,1) both}'
            '@keyframes fan{from{opacity:0;transform:rotate(0deg) translateY(30px)}to{opacity:1;transform:rotate(var(--r))}}')
    return svg(w, h, t, ''.join(out), 'presentations ❯ ls -1. Every talk, one file. The slides for my talks, one folder each.', css)

def chips_row(chips, x, y, size, t, start, maxw):
    out, cx, cy, pad = [], x, y, size * 0.75
    for i, c in enumerate(chips):
        cw = W(c, 'mono', size) + pad * 2
        if cx + cw > x + maxw and cx > x: cx, cy = x, cy + size * 2.6
        out.append(f'<g class="pop" style="{at(start + i * 0.08)}"><rect x="{cx:.1f}" y="{cy:.1f}" width="{cw:.1f}" height="{size * 2.1:.1f}" '
                   f'rx="{size * 0.55:.1f}" fill="none" stroke="{t["rule"]}" stroke-width="1.6"/>'
                   + T(c, 'mono', size, cx + pad, cy + size * 1.42, t['ink'])[0] + '</g>')
        cx += cw + size * 0.65
    return ''.join(out), cy + size * 2.1

def talk_card(n, talk, t, mobile):
    w = 640 if mobile else 1280; M = 40 if mobile else 80
    out, css = [shadow(t)], ''
    out.append(f'<rect class="wipe" style="{at(0.05)}" x="0" y="0" width="{w}" height="2" fill="{t["rule"]}"/>')
    if mobile:
        sw = w - 2 * M; sy = 64
        out.append(mock('grid', talk, M, sy + 10, sw, -3.5, 'back', 0.2, 'b0'))
        out.append(mock(talk['cover_mock'], talk, M, sy, sw, 0, 'front', 0.1, 'f0'))
        y = sy + sw * 9 / 16 + 84
        out.append(T(f'{n:02d}', 'monob', 22, M, y, t['muted'], cls='rise', style=at(0.5))[0])
        out.append(T(f'· {talk["date"]}', 'mono', 22, M + 40, y, t['muted'], cls='rise', style=at(0.5))[0])
        lines = wrap(talk['title'], 'serif', 76, w - 2 * M)
        for i, line in enumerate(lines):
            out.append(T(line, 'serif', 76, M - 3, y + 86 + i * 80, t['ink'], cls='wipe', style=at(0.6 + i * 0.12))[0])
        y = y + 86 + (len(lines) - 1) * 80 + 56
        for i, line in enumerate(wrap(talk['desc'], 'sans', 28, w - 2 * M)):
            out.append(T(line, 'sans', 28, M, y + i * 42, t['muted'], cls='rise', style=at(0.85 + i * 0.05))[0]); last = y + i * 42
        c, y = chips_row(talk['chips'], M, last + 34, 21, t, 1.1, w - 2 * M)
        out.append(c); y += 34
        for i, (col, _) in enumerate(talk['palette']):
            out.append(f'<rect class="pop" style="{at(1.35 + i * 0.07)}" x="{M + i * 50}" y="{y:.0f}" width="38" height="38" rx="10" fill="{col}" stroke="{t["rule"]}" stroke-width="1.6"/>')
        y += 100
        out.append(f'<path class="rise" style="{at(1.7)}" d="M {M} {y - 22} l 18 11 l -18 11 z" fill="{t["ink"]}"/>')
        out.append(T(f'{talk["slug"]}/', 'monob', 24, M + 32, y, t['ink'], cls='rise', style=at(1.7))[0])
        h = y + 56
        out.append(f'<rect x="0" y="{h - 2}" width="{w}" height="2" fill="{t["rule"]}"/>')
    else:
        h = 470; sw = 590; sx, sy = M, 62
        out.append(mock('grid', talk, sx, sy + 12, sw, -3.5, 'back', 0.2, 'b0'))
        out.append(mock(talk['cover_mock'], talk, sx, sy, sw, 0, 'front', 0.1, 'f0'))
        x = M + sw + 64; tw = w - M - x
        out.append(T(f'{n:02d}', 'monob', 18, x, 92, t['muted'], cls='rise', style=at(0.45))[0])
        out.append(T(f'· {talk["date"]}', 'mono', 18, x + 32, 92, t['muted'], cls='rise', style=at(0.45))[0])
        lines = wrap(talk['title'], 'serif', 66, tw)
        for i, line in enumerate(lines):
            out.append(T(line, 'serif', 66, x - 2, 160 + i * 68, t['ink'], cls='wipe', style=at(0.55 + i * 0.12))[0])
        y = 160 + (len(lines) - 1) * 68 + 50
        for i, line in enumerate(wrap(talk['desc'], 'sans', 21, tw)):
            out.append(T(line, 'sans', 21, x, y + i * 32, t['muted'], cls='rise', style=at(0.8 + i * 0.05))[0]); last = y + i * 32
        c, y = chips_row(talk['chips'], x, last + 28, 16, t, 1.05, tw)
        out.append(c); y += 28
        for i, (col, _) in enumerate(talk['palette']):
            out.append(f'<rect class="pop" style="{at(1.3 + i * 0.07)}" x="{x + i * 42}" y="{y:.0f}" width="30" height="30" rx="8" fill="{col}" stroke="{t["rule"]}" stroke-width="1.5"/>')
        out.append(T('# its own palette', 'mono', 16, x + len(talk['palette']) * 42 + 10, y + 21, t['muted'], cls='rise', style=at(1.6))[0])
        y += 78
        out.append(f'<path class="rise" style="{at(1.7)}" d="M {x} {y - 17} l 14 8.5 l -14 8.5 z" fill="{t["ink"]}"/>')
        p, pw = T(f'{talk["slug"]}/', 'monob', 18, x + 26, y, t['ink'], cls='rise', style=at(1.7)); out.append(p)
        out.append(T('index.html', 'mono', 18, x + 26 + pw + 10, y, t['muted'], cls='rise', style=at(1.7))[0])
        h = max(h, int(y + 58))
        out.append(f'<rect x="0" y="{h - 2}" width="{w}" height="2" fill="{t["rule"]}"/>')
    css += ('.front{animation:wipe .7s cubic-bezier(.65,0,.35,1) both}'
            '.back{animation:back .9s cubic-bezier(.34,1.3,.64,1) both}'
            '@keyframes back{from{opacity:0;transform:rotate(0)}to{opacity:1;transform:rotate(var(--r))}}')
    label = f'{n:02d} — {talk["title"]}: {talk["desc"]} ' + ' · '.join(talk['chips'])
    return svg(w, h, t, ''.join(out), label, css)

def keys(t, mobile, items=None, label='[ PRESENTING ]', note=None, press='→'):
    items = items or KEYS
    w = 640 if mobile else 1280; M = 40 if mobile else 80
    size = 22 if mobile else 17
    capH = 54 if mobile else 48
    def need(item):   # width one entry takes: its keycaps, then the longer of label and note
        ks, what, sub = item
        caps = sum(max(capH, W(k, 'monob', size) + size * 1.3) + 10 for k in ks)
        return caps + 6 + max(W(what, 'sans', size + 5), W(sub, 'mono', size - 3) if sub else 0) + 24
    cols = 1 if mobile else (4 if items is KEYS or max(need(i) for i in items) <= (w - 2 * M) / 4 else 2)
    out, css = [], ''
    out.append(T(label, 'monob', size - 2, M, 64, t['muted'], ls=2.4, cls='rise', style=at(0.05))[0])
    colw = (w - 2 * M) / cols; rowh = 90 if mobile else 84
    for i, (ks, what, sub) in enumerate(items):
        x0 = M + (i % cols) * colw; y0 = 110 + (i // cols) * rowh
        d = 0.15 + i * 0.07
        x = x0
        for k in ks:
            kw = max(capH, W(k, 'monob', size) + size * 1.3)
            pr = ' press' if k == press else ''
            out.append(f'<g class="pop" style="{at(d)}"><g class="cap{pr}">'
                       f'<rect x="{x:.1f}" y="{y0 + 4}" width="{kw:.1f}" height="{capH}" rx="10" fill="{t["keyedge"]}"/>'
                       f'<rect class="top" x="{x:.1f}" y="{y0}" width="{kw:.1f}" height="{capH}" rx="10" fill="{t["card"]}" stroke="{t["rule"]}" stroke-width="1.5"/>'
                       + T(k, 'monob', size, x + kw / 2, y0 + capH / 2 + size * 0.36, t['ink'], anchor='middle', cls='top')[0] + '</g></g>')
            x += kw + 10
        ty = y0 + capH / 2 + (size * 0.4 if not sub else -2)
        out.append(T(what, 'sans', size + 5, x + 6, ty, t['ink'], cls='rise', style=at(d + 0.08))[0])
        if sub: out.append(T(sub, 'mono', size - 3, x + 6, ty + size + 4, t['muted'], cls='rise', style=at(d + 0.1))[0])
    h = 110 + ((len(items) + cols - 1) // cols) * rowh + 16
    if note:
        for j, line in enumerate(wrap(note, 'mono', size - 1, w - 2 * M)):
            out.append(T(line, 'mono', size - 1, M, h - 4 + j * (size + 8), t['muted'], cls='rise', style=at(0.15 + len(items) * 0.07))[0])
        h += 30 + (size + 8) * len(wrap(note, 'mono', size - 1, w - 2 * M))
    # the → key gets pressed every few seconds, like a presenter moving on
    css += ('.press .top{animation:press 4.2s cubic-bezier(.4,0,.2,1) 2.4s infinite}'
            '@keyframes press{0%,86%,100%{transform:none}90%,94%{transform:translateY(4px)}}')
    return svg(w, h, t, ''.join(out), 'Presenting: ' + '; '.join(f'{" / ".join(k)} = {wh}' for k, wh, _ in items) + (f'. {note}' if note else ''), css)

def house_style(t, mobile):
    w = 640 if mobile else 1280; M = 40 if mobile else 80
    out, css = [], ''
    size = 20 if mobile else 15
    out.append(T('[ HOUSE STYLE ]', 'monob', size, M, 64, t['muted'], ls=2.4, cls='rise', style=at(0.05))[0])
    lw = w - 2 * M
    out.append(f'<line class="march" x1="{M}" y1="92" x2="{w - M}" y2="92" stroke="{t["rule"]}" stroke-width="2" stroke-dasharray="8 7"/>')
    css += '.march{animation:march 1.6s linear infinite}@keyframes march{to{stroke-dashoffset:-30}}'
    specs = [('serif', 'FRAUNCES BLACK', 'Titles: a short sentence with a full stop.'),
             ('sans', 'INSTRUMENT SANS', 'Body copy and explanations.'),
             ('mono', 'JETBRAINS MONO', 'Labels, code, captions, footers.')]
    if mobile:
        y = 200
        for i, (fnt, name, use) in enumerate(specs):
            out.append(T('Aa', fnt, 110, M - 4, y, t['ink'], cls='wipe', style=at(0.2 + i * 0.15))[0])
            out.append(T(name, 'monob', 18, M + 190, y - 52, t['muted'], ls=2, cls='rise', style=at(0.35 + i * 0.15))[0])
            for j, line in enumerate(wrap(use, 'sans', 24, lw - 190)):
                out.append(T(line, 'sans', 24, M + 190, y - 14 + j * 32, t['ink'], cls='rise', style=at(0.4 + i * 0.15))[0])
            y += 140
        y -= 20
        for i, (code, what) in enumerate(STYLE_RULES):
            out.append(T(code, 'mono', 23, M, y, t['ink'], cls='rise', style=at(0.8 + i * 0.07))[0])
            out.append(T(what, 'sans', 23, M, y + 36, t['muted'], cls='rise', style=at(0.85 + i * 0.07))[0])
            y += 92
        h = y + 10
    else:
        colw = lw / 3
        for i, (fnt, name, use) in enumerate(specs):
            x = M + i * colw
            out.append(T('Aa', fnt, 116, x - 4, 248, t['ink'], cls='wipe', style=at(0.2 + i * 0.15))[0])
            out.append(T(name, 'monob', 15, x, 296, t['muted'], ls=2, cls='rise', style=at(0.35 + i * 0.15))[0])
            out.append(T(use, 'sans', 19, x, 328, t['ink'], cls='rise', style=at(0.4 + i * 0.15))[0])
        for i, (code, what) in enumerate(STYLE_RULES):
            x = M + (i % 3) * colw; y = 410 + (i // 3) * 82
            out.append(T(code, 'mono', 19, x, y, t['ink'], cls='rise', style=at(0.8 + i * 0.07))[0])
            out.append(T(what, 'sans', 19, x, y + 32, t['muted'], cls='rise', style=at(0.85 + i * 0.07))[0])
        h = 560
    return svg(w, h, t, ''.join(out), 'House style: Fraunces Black for titles, Instrument Sans for body copy, JetBrains Mono for labels. '
               + '; '.join(f'{c}: {w_}' for c, w_ in STYLE_RULES), css)

def footer(t, mobile, host='presentations', left=None, right=None):
    w = 640 if mobile else 1280; M = 40 if mobile else 80
    size = 22 if mobile else 18
    out, css = [], ''
    k, kc = typed(host, 'exit', M, 60, size, t, start=0.4, per=0.09); out.append(k); css += kc
    y = 112 if mobile else 108
    left = left or f'{len(TALKS):02d} — TALKS'; right = right or f'{AUTHOR.upper()} · {YEAR}'
    out.append(T(left, 'monob', size - 3, M, y, t['muted'], ls=2.4)[0])
    out.append(T(right, 'monob', size - 3, w - M, y, t['muted'], ls=2.4, anchor='end')[0])
    out.append(segs(M, y + 20, w - 2 * M, 4 if mobile else 7, 4 if mobile else 7, t, 0.2))
    return svg(w, y + 48, t, ''.join(out), f'{host} ❯ exit — {left}, {right}', css)

CREDITS = [  # (label, name, licence)
    ('BUILT WITH', 'Bento Slides', 'MIT'),
    ('TITLES', 'Fraunces', 'OFL 1.1'),
    ('BODY', 'Instrument Sans', 'OFL 1.1'),
    ('LABELS', 'JetBrains Mono', 'OFL 1.1'),
    ('PIXEL TITLES', 'Jersey 10', 'OFL 1.1'),
]
CREDIT_FACE = {'BUILT WITH': 'serif', 'TITLES': 'serif', 'BODY': 'sans', 'LABELS': 'mono', 'PIXEL TITLES': 'pixel'}

def credits(t, mobile):
    """The credits, set like the decks' chips: a label above each, the licence beside the name."""
    w = 640 if mobile else 1280; M = 40 if mobile else 80
    size = 21 if mobile else 16
    out = [T('[ CREDITS ]', 'monob', size - 1, M, 52, t['muted'], ls=2.4, cls='rise', style=at(0.05))[0]]
    cols = 2 if mobile else min(len(CREDITS), 5); gap = 18
    cw = (w - 2 * M - gap * (cols - 1)) / cols; ch = size * 4.6
    for i, (lab, name, lic) in enumerate(CREDITS):
        x = M + (i % cols) * (cw + gap); y = 84 + (i // cols) * (ch + gap)
        d = 0.15 + i * 0.09
        out.append(f'<g class="pop" style="{at(d)}">'
                   f'<rect x="{x:.1f}" y="{y:.1f}" width="{cw:.1f}" height="{ch:.1f}" rx="12" fill="{t["card"]}" stroke="{t["rule"]}" stroke-width="1.5"/>'
                   + T(lab, 'monob', size - 4, x + size, y + size * 1.55, t['muted'], ls=1.8)[0]
                   + T(name, CREDIT_FACE.get(lab, 'sans'), size + 7 if lab != 'PIXEL TITLES' else size + 11, x + size, y + size * 3.35,
                       t['ink'])[0]
                   + T(lic, 'mono', size - 3, x + cw - size, y + size * 1.55, t['muted'], anchor='end')[0] + '</g>')
    rows = (len(CREDITS) + cols - 1) // cols
    h = 84 + rows * (ch + gap) + 18
    label = 'Credits: ' + '; '.join(f'{n} ({l})' for _, n, l in CREDITS)
    return svg(w, int(h), t, ''.join(out), label)

# ─── a talk's own page: the real slides ─────────────────────────────────────
def photo(name, x, y, w, rot, cls, delay, uid, origin=None, small=False):
    """A real screenshot of the deck, framed like the mock slides."""
    f = name + ('-s' if small else '') + ('.jpg' if not name.endswith('.jpg') else '')
    uri = thumb_uri(f)
    h = w * 9 / 16
    ox, oy = origin or (x + w / 2, y + h)
    return (f'<g class="{cls}" style="{at(delay)};transform-origin:{ox:.0f}px {oy:.0f}px;--r:{rot}deg;transform:rotate({rot}deg)">'
            f'<g filter="url(#sh)"><image href="{uri}" x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" clip-path="url(#p{uid})"/></g></g>'
            f'<clipPath id="p{uid}"><rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{w * 0.02:.1f}"/></clipPath>')

ANIM_SLIDES = ('.front{animation:wipe .7s cubic-bezier(.65,0,.35,1) both}'
               '.back{animation:back .9s cubic-bezier(.34,1.3,.64,1) both}'
               '@keyframes back{from{opacity:0;transform:rotate(0)}to{opacity:1;transform:rotate(var(--r))}}')

def talk_hero(n, talk, t, mobile):
    w = 640 if mobile else 1280; M = 40 if mobile else 80
    out, css = [shadow(t)], ANIM_SLIDES
    cover = talk['cover'].replace('.jpg', '')
    second = talk['gallery'][2][0] if len(talk['gallery']) > 2 else cover
    if mobile:
        k, kc = typed(talk['host'], 'cat README.md', M, 70, 22, t); out.append(k); css += kc
        out.append(T(f'{n:02d} — {talk["date"].upper()}', 'monob', 18, M, 128, t['muted'], ls=2.4, cls='rise', style=at(0.3))[0])
        lines = wrap(talk['title'] + '.', 'serif', 88, w - 2 * M)
        for i, line in enumerate(lines):
            out.append(T(line, 'serif', 88, M - 3, 228 + i * 92, t['ink'], cls='wipe', style=at(0.5 + i * 0.15), ls=-1)[0])
        y = 228 + (len(lines) - 1) * 92 + 64
        for i, line in enumerate(wrap(talk['desc'], 'sans', 28, w - 2 * M)):
            out.append(T(line, 'sans', 28, M, y + i * 42, t['ink'] if i == 0 else t['muted'], cls='rise', style=at(0.85 + i * 0.05))[0]); last = y + i * 42
        c, y = chips_row(talk['chips'], M, last + 34, 21, t, 1.05, w - 2 * M); out.append(c)
        sy = y + 60; sw = w - 2 * M
        out.append(photo(second, M, sy + 14, sw, 3.5, 'back', 0.9, 'b'))
        out.append(photo(cover, M, sy, sw, 0, 'front', 0.8, 'f'))
        h = int(sy + sw * 9 / 16 + 70)
    else:
        k, kc = typed(talk['host'], 'cat README.md', M, 80, 20, t); out.append(k); css += kc
        out.append(T(f'{n:02d} — {talk["date"].upper()}', 'monob', 15, M, 134, t['muted'], ls=2.2, cls='rise', style=at(0.3))[0])
        lines = wrap(talk['title'] + '.', 'serif', 96, 560)
        for i, line in enumerate(lines):
            out.append(T(line, 'serif', 96, M - 3, 232 + i * 98, t['ink'], cls='wipe', style=at(0.5 + i * 0.15), ls=-1.2)[0])
        y = 232 + (len(lines) - 1) * 98 + 62
        for i, line in enumerate(wrap(talk['desc'], 'sans', 22, 540)):
            out.append(T(line, 'sans', 22, M, y + i * 33, t['ink'] if i == 0 else t['muted'], cls='rise', style=at(0.85 + i * 0.05))[0]); last = y + i * 33
        c, y = chips_row(talk['chips'], M, last + 30, 16, t, 1.05, 560); out.append(c)
        sw = 560; sx = w - M - sw; sy = 110
        out.append(photo(second, sx, sy + 16, sw, 4, 'back', 0.9, 'b'))
        out.append(photo(cover, sx, sy, sw, 0, 'front', 0.8, 'f'))
        h = int(max(y + 70, sy + sw * 9 / 16 + 80))
    return svg(w, h, t, ''.join(out), f'{talk["host"]} ❯ cat README.md — {talk["title"]}. {talk["desc"]}', css)

def gallery(talk, t, mobile):
    w = 640 if mobile else 1280; M = 40 if mobile else 80
    out, css = [shadow(t)], ANIM_SLIDES
    size = 20 if mobile else 15
    out.append(T('[ SLIDES ]', 'monob', size, M, 60, t['muted'], ls=2.4, cls='rise', style=at(0.05))[0])
    cols = 2 if mobile else 3; gap = 20 if mobile else 28
    sw = (w - 2 * M - gap * (cols - 1)) / cols; sh = sw * 9 / 16
    cap = 2
    rowh = sh + (26 + cap * 30 if mobile else 92)
    for i, (name, page, title) in enumerate(talk['gallery']):
        x = M + (i % cols) * (sw + gap); y = 92 + (i // cols) * rowh
        d = 0.15 + i * 0.1
        out.append(photo(name, x, y, sw, 0, 'front', d, f'g{i}', small=True))
        ty = y + sh + (34 if mobile else 30)
        out.append(T(f'{page:02d}', 'monob', size, x, ty, t['muted'], cls='rise', style=at(d + 0.3))[0])
        for j, line in enumerate(wrap(title, 'sans', size + 3, sw - (44 if mobile else 36))[:cap]):
            out.append(T(line, 'sans', size + 3, x + (44 if mobile else 36), ty + j * (size + 9), t['ink'], cls='rise', style=at(d + 0.35))[0])
    rows = (len(talk['gallery']) + cols - 1) // cols
    h = int(92 + rows * rowh + 10)
    return svg(w, h, t, ''.join(out), 'Slides: ' + '; '.join(f'{p} {ti}' for _, p, ti in talk['gallery']), css)

def chapters(talk, t, mobile):
    w = 640 if mobile else 1280; M = 40 if mobile else 80
    out, css = [], ''
    size = 20 if mobile else 15
    out.append(T('[ CHAPTERS ]', 'monob', size, M, 60, t['muted'], ls=2.4, cls='rise', style=at(0.05))[0])
    rows = talk['chapters']; top = 90; rh = 104 if mobile else 66
    # the agenda's walking highlight: a soft bar that steps down the rows
    n = len(rows); per = 1.4; dur = per * n
    keys_ = []
    for i in range(n):
        a = i / n * 100; b = (i + 0.78) / n * 100
        keys_.append(f'{a:.2f}%,{b:.2f}%{{transform:translateY({i * rh}px)}}')
    css += (f'.beam{{animation:beam {dur:.1f}s cubic-bezier(.65,0,.35,1) 1.8s infinite both}}'
            f'@keyframes beam{{{"".join(keys_)}100%{{transform:translateY(0)}}}}')
    out.append(f'<g class="rise" style="{at(1.6)}"><g class="beam"><rect x="{M - 16}" y="{top + 6}" width="{w - 2 * M + 32}" height="{rh - 12}" rx="12" '
               f'fill="{t["faint"]}" stroke="{t["rule"]}" stroke-width="1.2"/>'
               f'<rect x="{M - 8}" y="{top + rh * 0.3:.0f}" width="4" height="{rh * 0.4:.0f}" rx="2" fill="{t["ink"]}"/></g></g>')
    for i, (num, title, desc, pages) in enumerate(rows):
        y = top + i * rh; d = 0.12 + i * 0.07
        out.append(f'<rect class="wipe" style="{at(d)}" x="0" y="{y}" width="{w}" height="1.5" fill="{t["rule"]}"/>')
        if mobile:
            out.append(T(num, 'monob', 18, M + 8, y + 44, t['muted'], cls='rise', style=at(d + 0.05))[0])
            out.append(T(title.upper(), 'serif', 34, M + 56, y + 48, t['ink'], cls='wipe', style=at(d + 0.08))[0])
            out.append(T(f'p.{pages}', 'monob', 18, w - M, y + 44, t['ink'], anchor='end', cls='rise', style=at(d + 0.1))[0])
            line = wrap('# ' + desc, 'mono', 18, w - 2 * M - 56)[0]
            out.append(T(line, 'mono', 18, M + 56, y + 82, t['muted'], cls='rise', style=at(d + 0.12))[0])
        else:
            out.append(T(num, 'monob', 14, M + 8, y + 30, t['muted'], cls='rise', style=at(d + 0.05))[0])
            out.append(T(title.upper(), 'serif', 30, M + 56, y + 44, t['ink'], cls='wipe', style=at(d + 0.08))[0])
            out.append(T('# ' + desc, 'mono', 16, 640, y + 40, t['muted'], cls='rise', style=at(d + 0.12))[0])
            out.append(T(f'p.{pages}', 'monob', 16, w - M, y + 40, t['ink'], anchor='end', cls='rise', style=at(d + 0.1))[0])
    h = top + n * rh
    out.append(f'<rect class="wipe" style="{at(0.12 + n * 0.07)}" x="0" y="{h}" width="{w}" height="1.5" fill="{t["rule"]}"/>')
    return svg(w, h + 24, t, ''.join(out), 'Chapters: ' + '; '.join(f'{a} {b}, p.{dd}' for a, b, _, dd in rows), css)

def palette(talk, t, mobile):
    w = 640 if mobile else 1280; M = 40 if mobile else 80
    out = []
    size = 20 if mobile else 15
    out.append(T('[ PALETTE ]', 'monob', size, M, 60, t['muted'], ls=2.4, cls='rise', style=at(0.05))[0])
    out.append(T('# this talk only; the next one gets its own', 'mono', size, w - M, 60, t['muted'], anchor='end', cls='rise', style=at(0.1))[0]
               if not mobile else '')
    cols = 3 if mobile else len(talk['palette']); gap = 18 if mobile else 22
    sw = (w - 2 * M - gap * (cols - 1)) / cols; sh = 120 if mobile else 132
    rowh = sh + 96
    for i, (col, name) in enumerate(talk['palette']):
        x = M + (i % cols) * (sw + gap); y = 90 + (i // cols) * rowh; d = 0.15 + i * 0.08
        out.append(f'<rect class="pop" style="{at(d)}" x="{x:.1f}" y="{y}" width="{sw:.1f}" height="{sh}" rx="16" fill="{col}" stroke="{t["rule"]}" stroke-width="1.5"/>')
        out.append(T(name, 'sans', size + 6, x, y + sh + 36, t['ink'], cls='rise', style=at(d + 0.15))[0])
        out.append(T(col.upper(), 'mono', size + 1, x, y + sh + 64, t['muted'], cls='rise', style=at(d + 0.18))[0])
    rows = (len(talk['palette']) + cols - 1) // cols
    return svg(w, 90 + rows * rowh, t, ''.join(out), 'Palette: ' + ', '.join(f'{n} {c}' for c, n in talk['palette']))

def covers_strip(t, mobile):
    """The made-up covers side by side, each fully visible."""
    w = 640 if mobile else 1280; M = 40 if mobile else 80
    out, css = [shadow(t)], ANIM_SLIDES
    size = 20 if mobile else 15
    out.append(T('[ COVERS ]', 'monob', size, M, 60, t['muted'], ls=2.4, cls='rise', style=at(0.05))[0])
    if not mobile:
        out.append(T("# mock covers in the house style · talks that don't exist (yet)", 'mono', size, w - M, 60, t['muted'],
                     anchor='end', cls='rise', style=at(0.1))[0])
    cols = 1 if mobile else 3; gap = 28
    sw = (w - 2 * M - gap * (cols - 1)) / cols; sh = sw * 9 / 16
    rowh = sh + (104 if mobile else 86)
    for i, c in enumerate(MOCK_COVERS):
        x = M + (i % cols) * (sw + gap); y = (96 if not mobile else 84) + (i // cols) * rowh
        d = 0.15 + i * 0.14
        out.append(mock(c, None, x, y, sw, 0, 'front', d, f's{i}'))
        ty = y + sh + (38 if mobile else 34)
        title = c['name']
        tag = c['tag'].lower()
        out.append(T(tag, 'monob', size, x, ty, t['muted'], cls='rise', style=at(d + 0.35))[0])
        out.append(T(title, 'sans', size + 5, x + W(tag, 'monob', size) + 14, ty, t['ink'], cls='rise', style=at(d + 0.4))[0])
    if mobile:
        y = (84 + len(MOCK_COVERS) * rowh)
        out.append(T("# mock covers · talks that don't exist (yet)", 'mono', size - 1, M, y, t['muted'], cls='rise', style=at(0.6))[0])
        h = int(y + 36)
    else:
        h = int(96 + ((len(MOCK_COVERS) + cols - 1) // cols) * rowh)
    label = "Mock covers for talks that don't exist (yet): " + '; '.join(c['name'] for c in MOCK_COVERS)
    return svg(w, h, t, ''.join(out), label, css)

# ─── README ─────────────────────────────────────────────────────────────────
def pic(name, alt, href=None, base='assets/'):
    p = (f'<picture><source media="(max-width: 600px) and (prefers-color-scheme: dark)" srcset="{base}{name}-m-dark.svg">'
         f'<source media="(max-width: 600px)" srcset="{base}{name}-m-light.svg">'
         f'<source media="(prefers-color-scheme: dark)" srcset="{base}{name}-dark.svg">'
         f'<img src="{base}{name}-light.svg" alt="{escape(alt, {chr(34): "&quot;"})}" width="100%"></picture>')
    return f'<a href="{href}">{p}</a>' if href else p

def readme():
    cards = '\n\n'.join(
        f'<p align="center">\n  {pic("talk-" + x["slug"], f"{i + 1:02d} — " + x["title"] + ": " + x["desc"], x["slug"] + "/")}\n</p>'
        for i, x in enumerate(TALKS))
    return f"""<p align="center">
  {pic("banner", "presentations ❯ ls -1 — Every talk, one file. The slides for my talks, one folder each.")}
</p>

<p align="center">
  {pic("covers", "Mock covers in the house style, for talks that don't exist (yet): " + "; ".join(c["name"] for c in MOCK_COVERS))}
</p>

{cards}

<p align="center">
  {pic("keys", "Presenting: " + "; ".join(f"{' / '.join(k)} = {w}" for k, w, _ in KEYS))}
</p>

> [!TIP]
> **To open a talk**, open its folder, download `index.html` and open it in a browser. It runs offline;
> GitHub itself only shows the file as source code.

<p align="center">
  {pic("style", "House style: Fraunces Black titles, Instrument Sans body, JetBrains Mono labels, shell-prompt kickers, bracketed labels, # asides, chapter footers, its own palette per talk")}
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
  {pic("footer", f"presentations ❯ exit — {AUTHOR}, {YEAR}")}
</p>

<p align="center">
  {pic("credits", "Credits: " + "; ".join(f"{n} ({l})" for _, n, l in CREDITS), "https://bento.page")}
</p>
"""

def talk_readme(n, talk):
    b = '../assets/'
    s = talk['slug']
    return f"""<p><a href="../"><code>❮ presentations</code></a></p>

<p align="center">
  {pic(f"{s}-hero", f"{talk['host']} ❯ cat README.md — {talk['title']}. {talk['desc']}", base=b)}
</p>

<p align="center"><a href="index.html"><code>▶ index.html</code></a> &nbsp;·&nbsp; <code>{talk['slides']} slides</code> &nbsp;·&nbsp; <code>{len(talk['chapters'])} chapters</code></p>

<p align="center">
  {pic(f"{s}-gallery", "Slides: " + "; ".join(f"{p} {ti}" for _, p, ti in talk['gallery']), base=b)}
</p>

<p align="center">
  {pic(f"{s}-chapters", "Chapters: " + "; ".join(f"{a} {bb}, p.{dd}" for a, bb, _, dd in talk['chapters']), base=b)}
</p>

<p align="center">
  {pic(f"{s}-mouse", "Mouse: " + "; ".join(f"{' / '.join(k)} = {w}" for k, w, _ in talk['mouse']) + ". " + talk['mouse_note'], base=b)}
</p>

> [!TIP]
> This deck also takes every key from the [main README](../README.md): arrows, `Space`, `S` for speaker view,
> `B` for a black screen, `L` for the laser pointer.

<p align="center">
  {pic(f"{s}-palette", "Palette: " + ", ".join(f"{nm} {c}" for c, nm in talk['palette']), base=b)}
</p>

<p align="center">
  {pic(f"{s}-footer", f"{talk['host']} ❯ exit — {talk['slides']} slides, {talk['date']}", base=b)}
</p>
"""

def main():
    os.makedirs(OUT, exist_ok=True)
    load_fonts()
    for theme, t in THEMES.items():
        for mobile in (False, True):
            sfx = ('-m' if mobile else '') + '-' + theme
            write(f'banner{sfx}.svg', banner(t, mobile))
            write(f'covers{sfx}.svg', covers_strip(t, mobile))
            for i, talk in enumerate(TALKS):
                s = talk['slug']
                if talk.get('style') == 'minecraft':
                    continue                     # drawn below by minecraft.py
                write(f'talk-{s}{sfx}.svg', talk_card(i + 1, talk, t, mobile))
                write(f'{s}-hero{sfx}.svg', talk_hero(i + 1, talk, t, mobile))
                write(f'{s}-gallery{sfx}.svg', gallery(talk, t, mobile))
                write(f'{s}-chapters{sfx}.svg', chapters(talk, t, mobile))
                write(f'{s}-mouse{sfx}.svg', keys(t, mobile, talk['mouse'], '[ MOUSE ]', talk['mouse_note'], press='Left click'))
                write(f'{s}-palette{sfx}.svg', palette(talk, t, mobile))
                write(f'{s}-footer{sfx}.svg', footer(t, mobile, talk['host'],
                                                    f'{len(talk["chapters"]) - 1:02d} — {talk["chapters"][-1][1].upper()}',
                                                    f'{talk["slides"]} / {talk["slides"]}'))
            write(f'keys{sfx}.svg', keys(t, mobile))
            write(f'style{sfx}.svg', house_style(t, mobile))
            write(f'footer{sfx}.svg', footer(t, mobile))
            write(f'credits{sfx}.svg', credits(t, mobile))
    for i, talk in enumerate(TALKS):
        if talk.get('style') == 'minecraft':
            minecraft.build(i + 1, dict(talk, _root=ROOT), {'pixel': F['pixel'], 'sans': F['sans'], 'sans6': F['sans6']}, write, thumb_uri, THEMES)
    with open(os.path.join(ROOT, 'README.md'), 'w', encoding='utf-8') as f: f.write(readme())
    for i, talk in enumerate(TALKS):
        page = minecraft.readme(i + 1, talk, pic) if talk.get('style') == 'minecraft' else talk_readme(i + 1, talk)
        with open(os.path.join(ROOT, talk['slug'], 'README.md'), 'w', encoding='utf-8') as f: f.write(page)
    n = sum(1 for f in os.listdir(OUT) if f.endswith('.svg'))
    print(f'built {n} images, README.md and {len(TALKS)} talk page' + ('s' if len(TALKS) != 1 else ''))

if __name__ == '__main__':
    main()
