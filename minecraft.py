"""The Minecraft talk's README images, drawn in that deck's own style instead of the house style.

build.py calls build() for any talk with style='minecraft'. Same rules as the rest of the repo:
hand-written SVG, text turned into outlines, a light and a dark version, a desktop and a phone (-m)
layout, CSS animations that play once and stay still for people who prefer reduced motion.

The pixel font (Jersey 10) and the sunset landscape are taken straight out of the deck's index.html,
the icons are the deck's own pixel maps below, so nothing new lives in the repo except this file.
"""
import json, os, re
from xml.sax.saxutils import escape

# ─── the deck's palette and pixel icons ─────────────────────────────────────
PAL = {
    'K': '#141018', 'k': '#2A2430', 'W': '#FFFFFF', 'w': '#D8D8E0', 'g': '#9A9AA6',
    'G': '#5DA130', 'L': '#7CC242', 'H': '#3F7A22',
    'b': '#9C6B3A', 'B': '#7A5230', 'd': '#5E3F25', 'Y': '#FFD23F', 'y': '#E0A82E',
    'R': '#E5383B', 'r': '#A4161A', 'P': '#9B5DE5', 'p': '#5A2E91', 'Q': '#C9A2FF',
    'C': '#5EE6E0', 'c': '#2BA8A3', 'O': '#FF8A1F', 'o': '#FFB547', 'S': '#8E8E99', 's': '#6A6A75',
    'N': '#3A86FF', 'n': '#1F5BC4',
}
ICONS = {
 'grass': ["GGLGGGLGGGHGGLGG", "GLGGHGGGLGGGGGLG", "GGGGGGLGGGHGLGGG", "HGGdGGGHGGdGGHGG",
           "dGBdHBdGBdBdGBdH", "BdBbBdBbBdBbBdBb", "bBdBbBdbBdBbdBbB", "BbBdBbBdBbBdBbBd",
           "dBbBdBbBdbBdBbBd", "BdbBbdBbBdBbBdbB", "bBdBbBbdBbBdbBdB", "BbBdBdBbBdBbBdBb",
           "dBbBbBdBbBdBbBdB", "BdBbdBbBdBbdBbBd", "bBdBbBdBbBdBbBdB", "BbBdBbBdBbdBbBdB"],
 'door': ["KKKKKKKKKK", "KbbbbbbbbK", "KbCCbbCCbK", "KbCCbbCCbK", "KbbbbbbbbK", "KBBBBBBBBK",
          "KbbbbbbbbK", "KbBBbbBBbK", "KbBBbbBBYK", "KbBBbbBBbK", "KbbbbbbbbK", "KbBBbbBBbK",
          "KbBBbbBBbK", "KbbbbbbbbK", "KBBBBBBBBK", "KKKKKKKKKK"],
 'portal': ["KKKKKKKKKKKK", "KkkkkkkkkkkK", "KkPQPpPPQPkK", "KkpPPQPpPPkK", "KkPPpPPQPpkK",
            "KkQPPpPPPPkK", "KkPpPPQpPQkK", "KkPPQPPPpPkK", "KkpPPpPQPPkK", "KkPQPPpPPpkK",
            "KkPPpPQPPPkK", "KkPpPPPpQPkK", "KkkkkkkkkkkK", "KKKKKKKKKKKK"],
 'sword': ["...........KK", "..........KWK", ".........KWwK", "........KWwK.", ".......KWwK..",
           "......KWwK...", "..KK.KWwK....", "..KyKWwK.....", "...KyyK......", "...KdKyK.....",
           "..KdK.KyK....", ".KdK...KK....", "KKK.........."],
 'chest': ["KKKKKKKKKKKKKK", "KbbbbbbbbbbbbK", "KbBBBBBBBBBBbK", "KbbbbbbbbbbbbK", "KddddKYYKddddK",
           "KbbbbKyyKbbbbK", "KbBBBBBBBBBBbK", "KbbbbbbbbbbbbK", "KbBBBBBBBBBBbK", "KbbbbbbbbbbbbK",
           "KKKKKKKKKKKKKK"],
 'heart': [".KK.KK.", "KRWKRRK", "KRRRRRK", "KRRRRrK", ".KRRrK.", "..KrK..", "...K..."],
 'shield': ["KKKKKKKKKK", "KSSSSSSSsK", "KSNNNNNNsK", "KSNnNNNNsK", "KSNNNNNNsK", "KSNNYYNNsK",
            "KSNNYYNNsK", "KSNNNNNNsK", ".KSNNNNsK.", ".KSNNNNsK.", "..KSNNsK..", "...KSsK...",
            "....KK...."],
 'star': ["....KK....", "....KYK...", "...KYYK...", "KKKKYYKKKK", "KYYYYYYYyK", ".KyYYYYyK.",
          "..KYYYYK..", ".KYYKKYyK.", ".KYK..KyK.", "KKK....KKK"],
 'phone': ["KKKKKKK", "KkkkkkK", "KCCCCCK", "KCcCCCK", "KCCCCcK", "KCCCCCK", "KCcCCCK",
           "KCCCCCK", "KCCCcCK", "KkkkkkK", "KkkWkkK", "KKKKKKK"],
 'pc': ["KKKKKKKKKKKK", "KsSSSSSSSSsK", "KSSSSSSSSSSK", "KSssssssssSK", "KSSSSSSSSSSK",
        "KSSSSSSSSSSK", "KSSSSSSSSLSK", "KsSSSSSSSSsK", "KKKKKKKKKKKK"],
}
HOTBAR = ['grass', 'pc', 'door', 'phone', 'portal', 'sword', 'chest', 'heart', 'shield']

THEMES = {
 'dark':  dict(bg='#15151C', panel='#23232C', ink='#F4F1E8', muted='#9C97AA', line='#0A0A0E', hl='#393946', sh='#060608',
               gold='#FFD23F', chat='#FFFF55', green='#7BD13F', xp='#80FF20', cyan='#5EE6E0',
               chatbg='rgba(0,0,0,0.55)', tshadow='#3F3F3F'),
 'light': dict(bg='#F1EEE6', panel='#FFFFFF', ink='#1E1E24', muted='#6B6675', line='#C9C3B5', hl='#FFFFFF', sh='#D5CFC1',
               gold='#A87400', chat='#7A6200', green='#3E8E1F', xp='#3E8E1F', cyan='#1D8A86',
               chatbg='rgba(30,30,36,0.08)', tshadow='#D9D3C4'),
}
FRAME, FRAME_IN = '#8A6238', '#6B4A2B'

CSS = '''
@keyframes drop{from{transform:translateY(-40px);opacity:0}to{transform:none;opacity:1}}
@keyframes rise{from{transform:translateY(14px);opacity:0}to{transform:none;opacity:1}}
@keyframes pop{0%{transform:scale(.6);opacity:0}70%{transform:scale(1.06);opacity:1}100%{transform:scale(1)}}
@keyframes wipe{from{clip-path:inset(0 100% 0 0)}to{clip-path:inset(0 0 0 0)}}
@keyframes type{from{width:0}}
@keyframes fill{from{transform:scaleX(0)}}
@keyframes blink{50%{opacity:0}}
@keyframes bob{50%{transform:translateY(-5px)}}
@keyframes press{0%,86%,100%{transform:none}90%{transform:translateY(3px)}}
@keyframes slot{0%{transform:translateX(0)}100%{transform:translateX(var(--to))}}
.a{animation-fill-mode:both;animation-timing-function:cubic-bezier(.2,.8,.2,1);transform-box:fill-box;transform-origin:50% 50%}
.drop{animation-name:drop;animation-duration:.6s}.rise{animation-name:rise;animation-duration:.5s}
.pop{animation-name:pop;animation-duration:.45s}.wipe{animation-name:wipe;animation-duration:.7s}
.fill{animation-name:fill;animation-duration:1.4s;transform-origin:0 50%}
.blink{animation:blink 1s steps(1) infinite 2s}
.bob{animation:bob 1.3s ease-in-out 1.2s 4}
.press{animation:press 4s ease-in-out 2s infinite}
@media (prefers-reduced-motion:reduce){*{animation:none!important;clip-path:none!important}}
'''

F = {}       # 'pixel', 'sans', 'sans6': Face objects from build.py
HOUSE = {}   # build.py's own light/dark themes, for the card on the main page

def d(t): return f'style="animation-delay:{t:.2f}s"'

def tx(s, font, size, x, y, fill, anchor='start', ls=0, shadow=None, cls='', extra=''):
    path, w = F[font].path(s, size, x, y, ls, anchor)
    out = ''
    if shadow:
        out += f'<path d="{path}" fill="{shadow}" transform="translate({size*0.07:.1f} {size*0.07:.1f})"/>'
    out += f'<path d="{path}" fill="{fill}"/>'
    return f'<g class="{cls}" {extra}>{out}</g>' if (cls or extra) else out

def wid(s, font, size, ls=0): return F[font].width(s, size, ls)

def wrap(s, font, size, width):
    lines, cur = [], ''
    for word in s.split():
        t = (cur + ' ' + word).strip()
        if wid(t, font, size) > width and cur: lines.append(cur); cur = word
        else: cur = t
    return lines + ([cur] if cur else [])

def svg(w, h, theme, body, label, bg=None):
    T = THEMES[theme] | ({'bg': bg} if bg else {})
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h:.0f}" width="{w}" height="{h:.0f}" '
            f'shape-rendering="crispEdges" role="img" aria-label="{escape(label)}"><title>{escape(label)}</title>'
            f'<style>{CSS}</style><rect width="{w}" height="{h:.0f}" fill="{T["bg"]}"/>{body}</svg>\n')

def icon(name, x, y, size, cls='', extra=''):
    rows = ICONS[name]; ih, iw = len(rows), max(len(r) for r in rows)
    k = max(1, round(size / max(iw, ih)))
    ox, oy = x + (size - iw * k) / 2, y + (size - ih * k) / 2
    parts = []
    for yy, row in enumerate(rows):
        xx = 0
        while xx < len(row):
            ch = row[xx]
            if ch not in PAL: xx += 1; continue
            run = 1
            while xx + run < len(row) and row[xx + run] == ch: run += 1
            parts.append(f'<rect x="{ox + xx*k:.0f}" y="{oy + yy*k:.0f}" width="{run*k}" height="{k}" fill="{PAL[ch]}"/>')
            xx += run
    return f'<g class="{cls}" {extra}>{"".join(parts)}</g>'

def card(x, y, w, h, T):
    return (f'<rect x="{x-4}" y="{y-4}" width="{w}" height="{h}" fill="{T["hl"]}"/>'
            f'<rect x="{x+4}" y="{y+4}" width="{w}" height="{h}" fill="{T["sh"]}"/>'
            f'<rect x="{x+1.5}" y="{y+1.5}" width="{w-3}" height="{h-3}" fill="{T["panel"]}" stroke="{T["line"]}" stroke-width="3"/>')

def button(x, y, w, h, label, size=22, hover=False):
    edge, col = ('#FFFFFF', '#FFFFA0') if hover else ('#000000', '#FFFFFF')
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#6F6F6F" stroke="{edge}" stroke-width="3"/>'
            f'<rect x="{x+3}" y="{y+3}" width="{w-6}" height="3" fill="#A8A8A8"/><rect x="{x+3}" y="{y+h-7}" width="{w-6}" height="4" fill="#4C4C4C"/>'
            + tx(label, 'pixel', size, x + w / 2, y + h / 2 + size * 0.32, col, 'middle', shadow='#3F3F3F'))

def chat(x, y, s, T, size=20, delay=0.1, uid='c'):
    """A chat line that types itself out, with a blinking cursor."""
    w = wid(s, 'pixel', size) + 26
    n = len(s)
    return (f'<rect x="{x}" y="{y}" width="{w:.0f}" height="{size + 14}" fill="{T["chatbg"]}"/>'
            f'<clipPath id="{uid}"><rect x="{x}" y="{y}" width="{w:.0f}" height="{size + 14}" '
            f'style="animation:type {n*0.05:.2f}s steps({n}) {delay}s both"/></clipPath>'
            f'<g clip-path="url(#{uid})">' + tx(s, 'pixel', size, x + 12, y + size * 0.95 + 2, T['chat']) + '</g>'
            f'<rect class="blink" x="{x + w - 10:.0f}" y="{y + 6}" width="3" height="{size + 2}" fill="{T["chat"]}"/>')

def hotbar(cx, y, sel, slot=44, animate_to=None):
    x0 = cx - 9 * slot / 2
    out = f'<rect x="{x0}" y="{y}" width="{9*slot}" height="{slot}" fill="rgba(14,14,18,0.85)" stroke="#000" stroke-width="3"/>'
    for k, n in enumerate(HOTBAR):
        out += f'<rect x="{x0 + k*slot + 2}" y="{y+2}" width="{slot-4}" height="{slot-4}" fill="none" stroke="#5A5A68" stroke-width="2"/>'
        out += icon(n, x0 + k * slot + 7, y + 7, slot - 14)
    anim = ''
    if animate_to is not None:
        anim = f'style="--to:{(animate_to - sel) * slot}px;animation:slot 1.6s steps({abs(animate_to - sel)}) .6s both"'
    out += f'<rect x="{x0 + sel*slot - 3}" y="{y-3}" width="{slot+6}" height="{slot+6}" fill="none" stroke="#FFF" stroke-width="4" {anim}/>'
    return out

# ─── pieces ─────────────────────────────────────────────────────────────────
def hero(talk, theme, mobile):
    T = THEMES[theme]
    W, H = (640, 560) if mobile else (1280, 520)
    b = (f'<image href="{talk["_land"]}" x="0" y="0" width="{W}" height="{H}" preserveAspectRatio="xMidYMid slice" style="image-rendering:pixelated"/>'
         f'<rect width="{W}" height="{H}" fill="rgba(10,8,24,0.28)"/>')
    b += chat(28 if mobile else 48, 28 if mobile else 34, '» cat README.md', T | {'chat': '#FFFF55', 'chatbg': 'rgba(0,0,0,0.55)'}, 20, uid=f'h{theme}{int(mobile)}')
    size = 92 if mobile else 150
    ty = 190 if mobile else 230
    title = talk['title'].upper()
    layers = ''.join(tx(title, 'pixel', size, W / 2 + i * 3, ty + i * 3, '#4A2208' if i > 1 else '#7A3A0E', 'middle') for i in range(6, 0, -1))
    gid = f'g{theme}{int(mobile)}'
    grad = (f'<linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FFF6B0"/>'
            f'<stop offset=".55" stop-color="#FFD23F"/><stop offset="1" stop-color="#F29A2E"/></linearGradient>')
    b += f'<defs>{grad}</defs><g class="a drop" {d(0.5)}>{layers}{tx(title, "pixel", size, W / 2, ty, f"url(#{gid})", "middle")}</g>'
    sx, sy = (W / 2 + 150, ty + 26) if mobile else (W / 2 + 330, ty + 12)
    b += (f'<g transform="rotate(-12 {sx} {sy})"><g class="bob">'
          + tx('Now with zero tech talk!', 'pixel', 18 if mobile else 24, sx, sy, '#FFFF55', 'middle', shadow='#3F3F15') + '</g></g>')
    ss = 26 if mobile else 34
    for i, line in enumerate(['How my Minecraft server works,', 'explained for everyone.']):
        b += tx(line, 'pixel', ss, W / 2, ty + (64 if mobile else 80) + i * ss * 1.15, '#FFFFFF', 'middle', shadow='#3F3F3F',
                cls='a rise', extra=d(1.0 + i * 0.1))
    by = f'A talk by {talk["by"]} · {talk["slides"]} slides · {talk["date"]}'
    b += tx(by, 'pixel', 17 if mobile else 20, W / 2, ty + (150 if mobile else 190), '#E0E0E0', 'middle', shadow='#3F3F3F', cls='a rise', extra=d(1.3))
    b += f'<g class="a rise" {d(1.5)}>' + hotbar(W / 2, H - (60 if mobile else 64), 0, 40 if mobile else 44, animate_to=8) + '</g>'
    return svg(W, H, theme, b, f'» cat README.md — {talk["title"]}. {talk["desc"]}')

def gallery(talk, theme, mobile, thumb_uri):
    T = THEMES[theme]
    cols = 2 if mobile else 3
    W = 640 if mobile else 1280
    pad, gap = (20, 20) if mobile else (40, 32)
    tw = (W - 2 * pad - (cols - 1) * gap) / cols
    th = tw * 9 / 16
    rowh = th + 24 + 50
    H = pad + 40 + rowh * ((len(talk['gallery']) + cols - 1) // cols) + 10
    b = tx('» /tp gallery', 'pixel', 22, pad, pad + 22, T['chat'], cls='a rise', extra=d(0.1))
    for i, (name, page, cap) in enumerate(talk['gallery']):
        r, c = divmod(i, cols)
        x, y = pad + c * (tw + gap), pad + 44 + r * rowh
        fr, t = 10, 0.3 + i * 0.12
        b += (f'<g class="a pop" {d(t)}>'
              f'<rect x="{x}" y="{y}" width="{tw:.1f}" height="{th + 2*fr:.1f}" fill="{FRAME}" stroke="#3B2A17" stroke-width="3"/>'
              f'<rect x="{x+fr-3}" y="{y+fr-3}" width="{tw-2*fr+6:.1f}" height="{th+6:.1f}" fill="{FRAME_IN}"/>'
              f'<image href="{thumb_uri(name + "-s.jpg")}" x="{x+fr}" y="{y+fr}" width="{tw-2*fr:.1f}" height="{th:.1f}" preserveAspectRatio="xMidYMid slice"/></g>')
        cs = 16 if mobile else 19
        b += tx(f'{page:02d}', 'pixel', cs + 6, x, y + th + 2 * fr + 26, T['gold'], cls='a rise', extra=d(t + 0.2))
        for li, line in enumerate(wrap(cap, 'sans6', cs, tw - 44)[:2]):
            b += tx(line, 'sans6', cs, x + 36, y + th + 2 * fr + 24 + li * cs * 1.3, T['ink'], cls='a rise', extra=d(t + 0.25))
    return svg(W, H, theme, b, 'Slides: ' + '; '.join(f'{p} {ti}' for _, p, ti in talk['gallery']))

def chapters(talk, theme, mobile):
    T = THEMES[theme]
    W = 640 if mobile else 1280
    pad = 20 if mobile else 40
    rh = 74 if mobile else 64
    rows = talk['mc_chapters']
    H = pad + 50 + len(rows) * (rh + 10) + 10
    b = tx("» here's what's coming", 'pixel', 22, pad, pad + 22, T['chat'], cls='a rise', extra=d(0.1))
    for i, (ic, n, head, desc, pages, who, col) in enumerate(rows):
        y = pad + 46 + i * (rh + 10)
        w = W - 2 * pad
        row = card(pad, y, w, rh, T)
        row += f'<rect x="{pad+8}" y="{y+8}" width="{rh-16}" height="{rh-16}" fill="{T["bg"]}" stroke="{T["hl"]}" stroke-width="2"/>'
        row += icon(ic, pad + 16, y + 16, rh - 32)
        row += tx(n, 'pixel', 24, pad + rh + 6, y + (30 if mobile else 40), T[col])
        row += tx(head.upper(), 'pixel', 22 if mobile else 24, pad + rh + 46, y + (30 if mobile else 40), T['ink'])
        if mobile: row += tx(desc, 'sans', 14, pad + rh + 46, y + 54, T['muted'])
        else: row += tx(desc, 'sans', 17, 560, y + 38, T['muted'])
        row += tx(f'p.{pages}', 'pixel', 18, W - pad - (14 if mobile else 172), y + (30 if mobile else 39), T['muted'], 'end')
        if not mobile:
            cw = 140
            row += f'<rect x="{W-pad-cw-14}" y="{y+16}" width="{cw}" height="{rh-32}" fill="none" stroke="{T[col]}" stroke-width="2"/>'
            row += tx(who, 'pixel', 16, W - pad - cw / 2 - 14, y + rh / 2 + 6, T[col], 'middle', ls=1)
        b += f'<g class="a wipe" {d(0.3 + i * 0.1)}>{row}</g>'
    return svg(W, H, theme, b, 'Chapters: ' + '; '.join(f'{n} {h}, p.{p}, {who.title()}' for _, n, h, _, p, who, _ in rows))

def mouse(talk, theme, mobile):
    T = THEMES[theme]
    W = 640 if mobile else 1280
    pad = 20 if mobile else 40
    items = [('Left click', 'Next'), ('Right click', 'Previous'), ('Side »', 'Next'), ('Side «', 'Previous')]
    cols = 2 if mobile else 4
    bw = (W - 2 * pad - (cols - 1) * 16) / cols
    H = pad + 50 + ((len(items) + cols - 1) // cols) * 100 + 40
    b = tx('» mouse controls while presenting', 'pixel', 22, pad, pad + 22, T['chat'], cls='a rise', extra=d(0.1))
    for i, (k, v) in enumerate(items):
        r, c = divmod(i, cols)
        x, y = pad + c * (bw + 16), pad + 46 + r * 100
        b += f'<g class="a pop" {d(0.3 + i*0.1)}><g class="{"press" if i == 0 else ""}">' + button(x, y, bw, 50, k, 22, hover=(i == 0)) + '</g></g>'
        b += tx('= ' + v, 'sans6', 17, x + bw / 2, y + 76, T['ink'], 'middle', cls='a rise', extra=d(0.5 + i * 0.1))
    b += tx(talk['mouse_note'], 'sans', 15 if mobile else 16, pad, H - 18, T['muted'], cls='a rise', extra=d(1.0))
    return svg(W, H, theme, b, 'Mouse: Left click = Next; Right click = Previous; Side → = Next; Side ← = Previous. ' + talk['mouse_note'])

def palette(talk, theme, mobile):
    T = THEMES[theme]
    W = 640 if mobile else 1280
    pad, gap = (20 if mobile else 40), 14
    cols = 4 if mobile else 8
    bw = (W - 2 * pad - (cols - 1) * gap) / cols
    H = pad + 46 + ((len(talk['palette']) + cols - 1) // cols) * (bw + 62) + 6
    b = tx('» palette', 'pixel', 22, pad, pad + 22, T['chat'], cls='a rise', extra=d(0.1))
    for i, (hexc, name) in enumerate(talk['palette']):
        r, c = divmod(i, cols)
        x, y = pad + c * (bw + gap), pad + 44 + r * (bw + 62)
        cell = bw / 8
        R_, G_, B_ = (int(hexc[j:j+2], 16) for j in (1, 3, 5))
        tex = ''
        for yy in range(8):
            for xx in range(8):
                f = (0.9, 1.0, 1.0, 1.08)[(xx * 7 + yy * 13 + i * 5) % 4]
                cc = '#%02X%02X%02X' % tuple(min(255, int(v * f)) for v in (R_, G_, B_))
                tex += f'<rect x="{x + xx*cell:.1f}" y="{y + yy*cell:.1f}" width="{cell+0.5:.1f}" height="{cell+0.5:.1f}" fill="{cc}"/>'
        b += f'<g class="a drop" {d(0.25 + i*0.08)}>{tex}<rect x="{x}" y="{y}" width="{bw:.1f}" height="{bw:.1f}" fill="none" stroke="#000" stroke-width="3"/></g>'
        b += tx(name, 'pixel', 19, x, y + bw + 26, T['ink'], cls='a rise', extra=d(0.4 + i * 0.08))
        b += tx(hexc, 'sans', 14, x, y + bw + 46, T['muted'], cls='a rise', extra=d(0.45 + i * 0.08))
    return svg(W, H, theme, b, 'Palette: ' + ', '.join(f'{n} {c}' for c, n in talk['palette']))

def footer(talk, theme, mobile):
    T = THEMES[theme]
    W = 640 if mobile else 1280
    H = 170 if mobile else 130
    pad = 20 if mobile else 40
    b = chat(pad, 26, '» /stop', T, 22, 0.2, uid=f'f{theme}{int(mobile)}')
    b += tx(f'— {talk["slides"]} slides, {talk["date"]}', 'pixel', 22, pad + wid('» /stop', 'pixel', 22) + 46, 48, T['muted'], cls='a rise', extra=d(0.8))
    cx, y, w = (W / 2, 92, W - 2 * pad) if mobile else (W - pad - 260, 46, 520)
    b += (f'<rect x="{cx - w/2}" y="{y}" width="{w}" height="12" fill="#1B1B20" stroke="#000" stroke-width="2"/>'
          f'<rect class="a fill" {d(0.6)} x="{cx - w/2 + 2}" y="{y+2}" width="{w-4}" height="8" fill="#80FF20"/>')
    b += tx(str(talk['slides']), 'pixel', 24, cx, y - 6, T['xp'], 'middle', shadow='#000', cls='a pop', extra=d(1.9))
    return svg(W, H, theme, b, f'» /stop — {talk["slides"]} slides, {talk["date"]}')

def talk_card(n, talk, theme, mobile, thumb_uri):
    """Its card on the main page: the real cover in an item frame, title, chips, palette."""
    T = THEMES[theme]
    W = 640 if mobile else 1280
    pad = 20 if mobile else 40
    if mobile:
        cw = W - 2 * pad; ch = cw * 9 / 16
        cx, cy, tx_, ty, tw = pad, pad, pad, pad + ch + 56, W - 2 * pad
    else:
        cw = 520; ch = cw * 9 / 16
        cx, cy, tx_, ty, tw = pad, pad + 10, pad + cw + 48, pad + 56, W - pad - (pad + cw + 48)
    fr = 10
    b = card(cx - 6, cy - 6, cw + 12, ch + 12, T)
    b += (f'<g class="a wipe" {d(0.2)}><rect x="{cx-fr+6}" y="{cy-fr+6}" width="{cw+2*fr-12}" height="{ch+2*fr-12:.1f}" fill="{FRAME}"/>'
          f'<image href="{thumb_uri(talk["cover"])}" x="{cx}" y="{cy}" width="{cw}" height="{ch:.1f}" preserveAspectRatio="xMidYMid slice"/></g>')
    b += tx(f'{n:02d} — MINECRAFT', 'pixel', 20, tx_, ty - 22, T['muted'], ls=2, cls='a rise', extra=d(0.5))
    b += f'<g class="a wipe" {d(0.6)}>' + tx(talk['title'], 'pixel', 52 if mobile else 64, tx_, ty + 44, T['ink'], shadow=T['tshadow']) + '</g>'
    lines = wrap(talk['desc'], 'sans', 19, tw)
    for i, line in enumerate(lines):
        b += tx(line, 'sans', 19, tx_, ty + 84 + i * 27, T['muted'], cls='a rise', extra=d(0.8 + i * 0.05))
    x = tx_; y = ty + 84 + len(lines) * 27 + 4
    for i, c in enumerate(talk['chips']):
        w = wid(c, 'pixel', 18) + 24
        if x + w > tx_ + tw: x = tx_; y += 42
        b += (f'<g class="a pop" {d(1.0 + i*0.08)}><rect x="{x:.0f}" y="{y}" width="{w:.0f}" height="32" fill="none" stroke="{T["green"]}" stroke-width="2"/>'
              + tx(c, 'pixel', 18, x + w / 2, y + 22, T['green'], 'middle') + '</g>')
        x += w + 10
    py = y + 48
    for i, (hexc, _) in enumerate(talk['palette']):
        b += f'<rect class="a pop" {d(1.3 + i*0.05)} x="{tx_ + i*30}" y="{py}" width="22" height="22" fill="{hexc}" stroke="#000" stroke-width="2"/>'
    # the same "▶ folder/ index.html" line the house-style cards end with
    ly = py + 64
    b += f'<path class="a rise" {d(1.7)} d="M {tx_} {ly - 17} l 14 8.5 l -14 8.5 z" fill="{T["ink"]}"/>'
    b += tx(f'{talk["slug"]}/', 'pixel', 22, tx_ + 26, ly, T['ink'], cls='a rise', extra=d(1.7))
    b += tx('index.html', 'pixel', 22, tx_ + 32 + wid(f'{talk["slug"]}/', 'pixel', 22), ly, T['muted'], cls='a rise', extra=d(1.7))
    H = max((pad + ch + 20 + 260) if mobile else (pad * 2 + ch + 20), ly + 40)
    rule = HOUSE[theme]['rule']
    b = (f'<rect class="a wipe" {d(0.05)} x="0" y="0" width="{W}" height="2" fill="{rule}"/>' + b
         + f'<rect x="0" y="{H - 2:.0f}" width="{W}" height="2" fill="{rule}"/>')
    # on the main page the card sits on the house-style background, like the other talks' cards
    return svg(W, H, theme, b, f'{n:02d} — {talk["title"]}: {talk["desc"]} ' + ' · '.join(talk['chips']), bg=HOUSE[theme]['bg'])

# ─── the talk's own README ──────────────────────────────────────────────────
def readme(n, talk, pic):
    b, s = '../assets/', talk['slug']
    ch = talk['mc_chapters']
    checklist = '\n'.join(f'- {line}' for line in talk['before'])
    return f"""<p><a href="../"><code>❮ presentations</code></a></p>

<p align="center">
  {pic(f"{s}-hero", f"» cat README.md — {talk['title']}. {talk['desc']}", base=b)}
</p>

<p align="center"><a href="index.html"><code>▶ index.html</code></a> &nbsp;·&nbsp; <code>{talk['slides']} slides</code> &nbsp;·&nbsp; <code>{len(ch)} chapters</code> &nbsp;·&nbsp; <code>{escape(talk['by'])}</code></p>

<p align="center">
  {pic(f"{s}-gallery", "Slides: " + "; ".join(f"{p} {ti}" for _, p, ti in talk['gallery']), base=b)}
</p>

<p align="center">
  {pic(f"{s}-chapters", "Chapters: " + "; ".join(f"{nn} {h}, p.{p}, {who.title()}" for _, nn, h, _, p, who, _ in ch), base=b)}
</p>

<p align="center">
  {pic(f"{s}-mouse", "Mouse: Left click = Next; Right click = Previous; Side → = Next; Side ← = Previous. " + talk['mouse_note'], base=b)}
</p>

> [!TIP]
> This deck also takes every key from the [main README](../README.md): arrows, `Space`, `S` for speaker view,
> `B` for a black screen, `L` for the laser pointer.

<p align="center">
  {pic(f"{s}-palette", "Palette: " + ", ".join(f"{nm} {c}" for c, nm in talk['palette']), base=b)}
</p>

<details>
<summary><code>[ BEFORE THE TALK ]</code></summary>

<br>

{checklist}

</details>

<p align="center">
  {pic(f"{s}-footer", f"» /stop — {talk['slides']} slides, {talk['date']}", base=b)}
</p>

<p align="center"><sub>Minecraft is a trademark of Mojang Studios. This talk is a fan-made explainer, not affiliated with Mojang or Microsoft.</sub></p>
"""

# ─── entry point used by build.py ───────────────────────────────────────────
def deck_asset(html_path, key):
    """One asset (a data: URI) out of a Bento deck's document block."""
    html = open(html_path, encoding='utf-8').read()
    m = re.search(r'<script type="application/bento\+json" id="bento-doc">(.*?)</script>', html, re.S)
    return json.loads(m.group(1).replace('\\u003c', '<'))['assets'][key]

def build(n, talk, fonts, write, thumb_uri, house):
    F.update(fonts)
    HOUSE.update(house)
    talk['_land'] = deck_asset(os.path.join(talk['_root'], talk['slug'], 'index.html'), 'land')
    s = talk['slug']
    for theme in ('light', 'dark'):
        for mobile in (False, True):
            sfx = ('-m' if mobile else '') + '-' + theme
            write(f'talk-{s}{sfx}.svg', talk_card(n, talk, theme, mobile, thumb_uri))
            write(f'{s}-hero{sfx}.svg', hero(talk, theme, mobile))
            write(f'{s}-gallery{sfx}.svg', gallery(talk, theme, mobile, thumb_uri))
            write(f'{s}-chapters{sfx}.svg', chapters(talk, theme, mobile))
            write(f'{s}-mouse{sfx}.svg', mouse(talk, theme, mobile))
            write(f'{s}-palette{sfx}.svg', palette(talk, theme, mobile))
            write(f'{s}-footer{sfx}.svg', footer(talk, theme, mobile))
