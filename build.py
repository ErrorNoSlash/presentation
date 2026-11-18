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
in assets/thumbs/ (cover first), add it to TALKS and run the script.
"""
import base64, io, json, os, re, zlib
from xml.sax.saxutils import escape

import uharfbuzz as hb
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
        date='nov 2026',
        desc='One Blackview mini PC running NixOS from a flake: 29 containers, '
             'Matrix on k3s, and only two doors in from the network.',
        chips=['22 slides', '8 chapters', 'nixos · docker · k3s'],
        palette=['#0D1B2E', '#5277C3', '#7EBAE4', '#C9E1F3', '#F2F0EA'],
        thumbs=['nixos-homelab-1.jpg', 'nixos-homelab-2.jpg', 'nixos-homelab-3.jpg', 'nixos-homelab-4.jpg'],
    ),
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
    m = re.search(r'<script id="bento-rt"[^>]*>(.*?)</script>', html, re.S)
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
        thumbs = TALKS[0]['thumbs']
        fan = [(thumbs[3 % len(thumbs)], 150, y0 + 40, 400, 8), (thumbs[2 % len(thumbs)], 110, y0 + 20, 400, 2), (thumbs[0], 70, y0, 400, -5)]
        for i, (name, x, y, sw, rot) in enumerate(fan):
            out.append(slide(thumb_uri(name), x, y, sw, rot, 'fan', 1.1 + i * 0.12, f'c{i}', (x + sw / 2, y + sw * 9 / 16 + 40)))
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
        thumbs = TALKS[0]['thumbs']
        fan = [(thumbs[3 % len(thumbs)], 770, 150, 430, 8), (thumbs[2 % len(thumbs)], 730, 120, 430, 2), (thumbs[0], 690, 96, 430, -5)]
        for i, (name, x, y, sw, rot) in enumerate(fan):
            out.append(slide(thumb_uri(name), x, y, sw, rot, 'fan', 0.9 + i * 0.12, f'c{i}', (x + sw / 2, y + sw * 9 / 16 + 60)))
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
    th = talk['thumbs']
    if mobile:
        sw = w - 2 * M; sy = 64
        out.append(slide(thumb_uri(th[1 % len(th)]), M, sy + 10, sw, -3.5, 'back', 0.2, 'b0'))
        out.append(slide(thumb_uri(th[0]), M, sy, sw, 0, 'front', 0.1, 'f0'))
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
        for i, col in enumerate(talk['palette']):
            out.append(f'<rect class="pop" style="{at(1.35 + i * 0.07)}" x="{M + i * 50}" y="{y:.0f}" width="38" height="38" rx="10" fill="{col}" stroke="{t["rule"]}" stroke-width="1.6"/>')
        y += 100
        out.append(f'<path class="rise" style="{at(1.7)}" d="M {M} {y - 22} l 18 11 l -18 11 z" fill="{t["ink"]}"/>')
        out.append(T(f'{talk["slug"]}/', 'monob', 24, M + 32, y, t['ink'], cls='rise', style=at(1.7))[0])
        h = y + 56
        out.append(f'<rect x="0" y="{h - 2}" width="{w}" height="2" fill="{t["rule"]}"/>')
    else:
        h = 470; sw = 590; sx, sy = M, 62
        out.append(slide(thumb_uri(th[1 % len(th)]), sx, sy + 12, sw, -3.5, 'back', 0.2, 'b0'))
        out.append(slide(thumb_uri(th[0]), sx, sy, sw, 0, 'front', 0.1, 'f0'))
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
        for i, col in enumerate(talk['palette']):
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

def keys(t, mobile):
    w = 640 if mobile else 1280; M = 40 if mobile else 80
    cols = 1 if mobile else 4
    size = 22 if mobile else 17
    out, css = [], ''
    out.append(T('[ PRESENTING ]', 'monob', size - 2, M, 64, t['muted'], ls=2.4, cls='rise', style=at(0.05))[0])
    colw = (w - 2 * M) / cols; rowh = 90 if mobile else 84; capH = 54 if mobile else 48
    for i, (ks, what, note) in enumerate(KEYS):
        x0 = M + (i % cols) * colw; y0 = 110 + (i // cols) * rowh
        d = 0.15 + i * 0.07
        x = x0
        for k in ks:
            kw = max(capH, W(k, 'monob', size) + size * 1.3)
            press = ' press' if k == '→' else ''
            out.append(f'<g class="pop" style="{at(d)}"><g class="cap{press}">'
                       f'<rect x="{x:.1f}" y="{y0 + 4}" width="{kw:.1f}" height="{capH}" rx="10" fill="{t["keyedge"]}"/>'
                       f'<rect class="top" x="{x:.1f}" y="{y0}" width="{kw:.1f}" height="{capH}" rx="10" fill="{t["card"]}" stroke="{t["rule"]}" stroke-width="1.5"/>'
                       + T(k, 'monob', size, x + kw / 2, y0 + capH / 2 + size * 0.36, t['ink'], anchor='middle', cls='top')[0] + '</g></g>')
            x += kw + 10
        ty = y0 + capH / 2 + (size * 0.4 if not note else -2)
        out.append(T(what, 'sans', size + 5, x + 6, ty, t['ink'], cls='rise', style=at(d + 0.08))[0])
        if note: out.append(T(note, 'mono', size - 3, x + 6, ty + size + 4, t['muted'], cls='rise', style=at(d + 0.1))[0])
    h = 110 + ((len(KEYS) + cols - 1) // cols) * rowh + 16
    # the → key gets pressed every few seconds, like a presenter moving on
    css += ('.press .top{animation:press 4.2s cubic-bezier(.4,0,.2,1) 2.4s infinite}'
            '@keyframes press{0%,86%,100%{transform:none}90%,94%{transform:translateY(4px)}}')
    return svg(w, h, t, ''.join(out), 'Presenting: ' + '; '.join(f'{" / ".join(k)} = {wh}' for k, wh, _ in KEYS), css)

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

def footer(t, mobile):
    w = 640 if mobile else 1280; M = 40 if mobile else 80
    size = 22 if mobile else 18
    out, css = [], ''
    k, kc = typed('presentations', 'exit', M, 60, size, t, start=0.4, per=0.09); out.append(k); css += kc
    y = 112 if mobile else 108
    out.append(T(f'{len(TALKS):02d} — TALKS', 'monob', size - 3, M, y, t['muted'], ls=2.4)[0])
    out.append(T(f'{AUTHOR.upper()} · {YEAR}', 'monob', size - 3, w - M, y, t['muted'], ls=2.4, anchor='end')[0])
    out.append(segs(M, y + 20, w - 2 * M, 4 if mobile else 7, 4 if mobile else 7, t, 0.2))
    return svg(w, y + 48, t, ''.join(out), f'presentations ❯ exit — {AUTHOR}, {YEAR}', css)

# ─── README ─────────────────────────────────────────────────────────────────
def pic(name, alt, href=None):
    p = (f'<picture><source media="(max-width: 600px) and (prefers-color-scheme: dark)" srcset="assets/{name}-m-dark.svg">'
         f'<source media="(max-width: 600px)" srcset="assets/{name}-m-light.svg">'
         f'<source media="(prefers-color-scheme: dark)" srcset="assets/{name}-dark.svg">'
         f'<img src="assets/{name}-light.svg" alt="{escape(alt, {chr(34): "&quot;"})}" width="100%"></picture>')
    return f'<a href="{href}">{p}</a>' if href else p

def readme():
    cards = '\n'.join(
        f'<p align="center">\n  {pic("talk-" + x["slug"], f"{i + 1:02d} — {x[chr(116) + chr(105) + chr(116) + chr(108) + chr(101)]}: {x[chr(100) + chr(101) + chr(115) + chr(99)]}", x["slug"] + "/")}\n</p>'
        for i, x in enumerate(TALKS))
    return f'''<p align="center">
  {pic("banner", "presentations ❯ ls -1 — Every talk, one file. The slides for my talks, one folder each.")}
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
| **banner** | the prompt types `ls -1`, the title draws in, three real slides fan out, the marquee keeps scrolling |
| **talk cards** | the cover slide wipes in, the title draws, the chips and the talk's own palette pop in |
| **keys** | the keycaps pop in; every few seconds the `→` key gets pressed |
| **house style** | the specimens draw in under a marching dashed rule |
| **footer** | the prompt types `exit`, the progress bar fills, the cursor blinks |

Everything plays once on load and stays still for people who prefer reduced motion.

**Adding a talk:** put its folder next to `nixos-homelab/` with the deck as `index.html`, save a few 960×540
screenshots in `assets/thumbs/` (cover first), add it to `TALKS` in `build.py`, and run:

```sh
pip install fonttools uharfbuzz brotli
python3 build.py
```

**Editing a deck:** open its `index.html`, press `Esc`, edit, then save with `⌘S` / `Ctrl+S`.

</details>

<p align="center">
  {pic("footer", f"presentations ❯ exit — {AUTHOR}, {YEAR}")}
</p>

<p align="center"><sub>Built with <a href="https://bento.page">Bento Slides</a> (MIT) · Fraunces, Instrument Sans and JetBrains Mono under the SIL Open Font License 1.1</sub></p>
'''

def main():
    os.makedirs(OUT, exist_ok=True)
    load_fonts()
    for theme, t in THEMES.items():
        for mobile in (False, True):
            sfx = ('-m' if mobile else '') + '-' + theme
            write(f'banner{sfx}.svg', banner(t, mobile))
            for i, talk in enumerate(TALKS):
                write(f'talk-{talk["slug"]}{sfx}.svg', talk_card(i + 1, talk, t, mobile))
            write(f'keys{sfx}.svg', keys(t, mobile))
            write(f'style{sfx}.svg', house_style(t, mobile))
            write(f'footer{sfx}.svg', footer(t, mobile))
    with open(os.path.join(ROOT, 'README.md'), 'w', encoding='utf-8') as f: f.write(readme())
    print('built', len(os.listdir(OUT)) - 1, 'images and README.md')

if __name__ == '__main__':
    main()
