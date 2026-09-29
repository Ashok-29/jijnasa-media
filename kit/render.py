#!/usr/bin/env python3
"""Jijñāsā carousel renderer — branded 1080x1350 JPEG slides from a JSON spec (text only, no web access).

  python3 kit/render.py spec.json OUTDIR            # renders slide_01.jpg ... + contact.jpg, exits 1 on overflow
  python3 kit/render.py --example                   # prints an example spec

Slide types (fields):
  cover    kicker, title, sub                         — the hook; big serif title
  text     kicker, title, body                        — one idea, <= 45 words body
  stat     kicker, number, unit, label, body          — one giant number
  quiz     kicker, question, options[2-4], footer     — "guess first"; answer goes on the next slide
  reveal   kicker, answer, body                       — pays off the quiz
  steps    kicker, title, steps[2-4]                  — mechanism as a numbered flow
  compare  kicker, title, left{label,points[]}, right{label,points[]}
  chart    kicker, title, image (local png from chart.py), caption, credit
  unknowns kicker, title, items[2-4], confidence (HIGH/MEDIUM/LOW), reason
  discuss  kicker, question, sides[0-2], prompt       — invites comments
  sources  items[{name, what}], credits[str], handle
Every slide may add "credit" (small line above the footer), e.g. for the photo shown on the previous slide.
Remote photos are NOT rendered here: they go into the Buffer carousel as their own items (see README).
"""
import json, sys, html, os, pathlib

KIT = pathlib.Path(__file__).resolve().parent
W, H = 1080, 1350
E = lambda s: html.escape(str(s or ""))

CSS = """
@font-face{font-family:Corm;font-weight:700;src:url(F/cormorant-garamond-latin-700-normal.woff2)}
@font-face{font-family:Corm;font-weight:700;src:url(F/cormorant-garamond-latin-ext-700-normal.woff2);unicode-range:U+0100-024F,U+1E00-1EFF}
@font-face{font-family:Corm;font-weight:600;font-style:italic;src:url(F/cormorant-garamond-latin-600-italic.woff2)}
@font-face{font-family:Corm;font-weight:600;font-style:italic;src:url(F/cormorant-garamond-latin-ext-600-italic.woff2);unicode-range:U+0100-024F,U+1E00-1EFF}
@font-face{font-family:Mont;font-weight:500;src:url(F/montserrat-latin-500-normal.woff2)}
@font-face{font-family:Mont;font-weight:500;src:url(F/montserrat-latin-ext-500-normal.woff2);unicode-range:U+0100-024F,U+1E00-1EFF}
@font-face{font-family:Mont;font-weight:600;src:url(F/montserrat-latin-600-normal.woff2)}
@font-face{font-family:Mont;font-weight:700;src:url(F/montserrat-latin-700-normal.woff2)}
@font-face{font-family:Mont;font-weight:700;src:url(F/montserrat-latin-ext-700-normal.woff2);unicode-range:U+0100-024F,U+1E00-1EFF}
@font-face{font-family:Mont;font-weight:800;src:url(F/montserrat-latin-800-normal.woff2)}
@font-face{font-family:Deva;font-weight:600;src:url(F/noto-serif-devanagari-devanagari-600-normal.woff2)}
:root{--navy:#0b1428;--deep:#02070f;--gold:#e8b24a;--gold2:#f6d58c;--ink:#f3ead7;--muted:#b9b09c;--line:rgba(232,178,74,.35)}
*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;height:1350px;overflow:hidden;background:radial-gradient(ellipse 90% 70% at 25% 20%,#16264a 0%,var(--navy) 50%,var(--deep) 100%);
 font-family:Mont,Deva,sans-serif;color:var(--ink);position:relative}
.stars{position:absolute;inset:0}
.frame{position:absolute;left:84px;right:84px;top:96px;bottom:190px;display:flex;flex-direction:column;justify-content:center;overflow:hidden}
.kicker{font-weight:700;letter-spacing:.28em;font-size:27px;color:var(--gold);text-transform:uppercase}
.kicker::after{content:"";display:block;width:72px;height:3px;background:var(--gold);margin-top:22px}
h1{font-family:Corm,Deva,serif;font-weight:700;font-size:128px;line-height:1;margin-top:36px;color:var(--ink)}
h2{font-family:Corm,Deva,serif;font-weight:700;font-size:90px;line-height:1.04;margin-top:32px}
h1 em,h2 em{font-style:italic;font-weight:600;color:var(--gold2)}
.sub{font-size:40px;line-height:1.45;color:var(--muted);margin-top:40px;font-weight:500}
.body{font-size:43px;line-height:1.45;margin-top:36px;font-weight:500}
.body b{color:var(--gold2);font-weight:700}
.swipe{position:absolute;right:84px;bottom:206px;font-weight:700;font-size:26px;letter-spacing:.18em;color:var(--gold)}
.num{font-family:Corm,serif;font-weight:700;font-size:300px;line-height:.9;color:var(--gold2);margin-top:30px}
.num small{font-family:Mont;font-size:56px;font-weight:700;color:var(--gold);margin-left:14px}
.label{font-size:48px;font-weight:700;margin-top:22px;line-height:1.25}
.opts{margin-top:44px;display:flex;flex-direction:column;gap:22px}
.opt{border:2px solid var(--line);border-radius:22px;padding:30px 32px;font-size:40px;line-height:1.35;font-weight:600;display:flex;gap:24px;background:rgba(255,255,255,.03)}
.opt b{color:var(--navy);background:var(--gold);border-radius:50%;min-width:56px;height:56px;display:flex;align-items:center;justify-content:center;font-size:30px}
.hint{margin-top:34px;font-size:30px;color:var(--gold);font-weight:700;letter-spacing:.06em}
.ans{font-family:Corm,serif;font-weight:700;font-size:200px;color:var(--gold2);margin-top:26px;line-height:1}
.steps{margin-top:40px;display:flex;flex-direction:column;gap:0}
.step{display:flex;gap:28px;align-items:flex-start}
.step .n{min-width:70px;height:70px;border-radius:50%;border:3px solid var(--gold);color:var(--gold2);display:flex;align-items:center;justify-content:center;font-family:Corm,serif;font-weight:700;font-size:44px}
.step p{font-size:39px;line-height:1.42;font-weight:500;padding-top:10px}
.arrow{width:3px;height:34px;background:var(--line);margin:6px 0 6px 34px}
.cols{display:flex;gap:28px;margin-top:44px}
.col{flex:1;border:2px solid var(--line);border-radius:24px;padding:30px 28px;background:rgba(255,255,255,.03)}
.col h3{font-size:30px;letter-spacing:.14em;color:var(--gold);font-weight:800;text-transform:uppercase;margin-bottom:18px}
.col li{font-size:35px;line-height:1.4;margin:0 0 14px 30px;font-weight:500}
.chart{margin-top:34px;width:100%;border-radius:18px}
.cap{font-size:33px;line-height:1.45;color:var(--muted);margin-top:24px}
ul.items{margin-top:36px}
ul.items li{font-size:40px;line-height:1.45;margin:0 0 20px 36px;font-weight:500}
.conf{margin-top:30px;display:inline-flex;gap:18px;align-items:center;font-size:30px;font-weight:700}
.conf span{background:var(--gold);color:var(--navy);padding:10px 22px;border-radius:40px;letter-spacing:.12em}
.q{font-family:Corm,serif;font-weight:700;font-size:100px;line-height:1.05;margin-top:34px}
.sides{display:flex;gap:24px;margin-top:44px}
.side{flex:1;text-align:center;border:2px solid var(--gold);border-radius:24px;padding:30px 20px;font-size:34px;font-weight:700;color:var(--gold2)}
.prompt{margin-top:40px;font-size:34px;font-weight:600;color:var(--muted)}
.src{margin-top:34px}
.src div{font-size:34px;line-height:1.38;margin-bottom:18px}
.src b{color:var(--gold2)}
.cred{font-size:22px;line-height:1.4;color:var(--muted);margin-top:8px}
.credit{position:absolute;left:84px;right:84px;bottom:150px;font-size:21px;line-height:1.35;color:var(--muted)}
.cta{font-family:Corm,serif;font-style:italic;font-weight:600;font-size:64px;color:var(--gold2);margin-top:34px}
.foot{position:absolute;left:84px;right:84px;bottom:56px;height:72px;display:flex;align-items:center;gap:20px;border-top:1px solid var(--line);padding-top:18px}
.foot img{width:64px;height:64px}
.foot .brand{font-family:Corm,Deva,serif;font-weight:700;font-size:34px;color:var(--ink)}
.foot .brand i{font-family:Deva;font-style:normal;font-size:24px;color:var(--gold);margin-left:10px}
.foot .pg{margin-left:auto;display:flex;gap:10px;align-items:center}
.wm{position:absolute;right:64px;top:34px;font-family:Corm,serif;font-weight:700;font-size:190px;line-height:1;color:transparent;-webkit-text-stroke:2px rgba(232,178,74,.13)}
.orbit{position:absolute;right:-260px;top:-180px;width:760px;height:760px;border-radius:50%;border:3px solid rgba(232,178,74,.22);box-shadow:0 0 80px rgba(232,178,74,.08) inset}
.orbit::after{content:"";position:absolute;left:118px;top:560px;width:26px;height:26px;border-radius:50%;background:var(--gold2);box-shadow:0 0 30px var(--gold)}
.dot{width:12px;height:12px;border-radius:50%;background:rgba(243,234,215,.25)}
.dot.on{background:var(--gold);width:34px;border-radius:8px}
"""

STARS = """<script>let s=%d;const r=()=>(s=(s*16807)%%2147483647)/2147483647;let h='';
for(let i=0;i<120;i++){const x=r()*1080,y=r()*1350,rad=r()<.9?r()*1+.3:r()*1.5+1,o=(r()*.4+.1).toFixed(2);
h+=`<circle cx="${x}" cy="${y}" r="${rad}" fill="${r()<.25?'#f6d58c':'#fff'}" opacity="${o}"/>`}
document.getElementById('st').innerHTML=h;</script>"""


def inner(s):
    t = s["type"]; k = f'<div class="kicker">{E(s.get("kicker"))}</div>' if s.get("kicker") else ""
    def rich_all(v):  # **bold** -> gold bold
        parts = E(v or "").split("**")
        if len(parts) % 2 == 0: return E(v)
        return "".join(p if i % 2 == 0 else f"<b>{p}</b>" for i, p in enumerate(parts))
    def ttl(v):  # *word* -> italic gold
        parts = E(v or "").split("*"); return "".join(p if i % 2 == 0 else f"<em>{p}</em>" for i, p in enumerate(parts))
    if t == "cover":
        return k + f'<h1>{ttl(s["title"])}</h1>' + (f'<div class="sub">{rich_all(s.get("sub"))}</div>' if s.get("sub") else "")
    if t == "text":
        return k + f'<h2>{ttl(s["title"])}</h2><div class="body">{rich_all(s.get("body"))}</div>'
    if t == "stat":
        return k + f'<div class="num">{E(s["number"])}<small>{E(s.get("unit"))}</small></div><div class="label">{E(s.get("label"))}</div>' + \
               (f'<div class="body">{rich_all(s.get("body"))}</div>' if s.get("body") else "")
    if t == "quiz":
        o = "".join(f'<div class="opt"><b>{chr(65+i)}</b><span>{E(x)}</span></div>' for i, x in enumerate(s["options"]))
        return k + f'<h2>{ttl(s["question"])}</h2><div class="opts">{o}</div><div class="hint">{E(s.get("footer") or "Guess first. Answer on the next slide →")}</div>'
    if t == "reveal":
        return k + f'<div class="ans">{E(s["answer"])}</div><div class="body">{rich_all(s.get("body"))}</div>'
    if t == "steps":
        st = '<div class="arrow"></div>'.join(f'<div class="step"><div class="n">{i+1}</div><p>{rich_all(x)}</p></div>' for i, x in enumerate(s["steps"]))
        return k + f'<h2>{ttl(s["title"])}</h2><div class="steps">{st}</div>'
    if t == "compare":
        col = lambda c: f'<div class="col"><h3>{E(c["label"])}</h3><ul>' + "".join(f"<li>{E(p)}</li>" for p in c["points"]) + "</ul></div>"
        return k + f'<h2>{ttl(s["title"])}</h2><div class="cols">{col(s["left"])}{col(s["right"])}</div>'
    if t == "chart":
        img = pathlib.Path(s["image"]).resolve().as_uri()
        return k + f'<h2 style="font-size:64px">{ttl(s["title"])}</h2><img class="chart" src="{img}">' + \
               (f'<div class="cap">{rich_all(s.get("caption"))}</div>' if s.get("caption") else "")
    if t == "unknowns":
        li = "".join(f"<li>{rich_all(x)}</li>" for x in s["items"])
        return k + f'<h2>{ttl(s.get("title") or "What we still don’t know")}</h2><ul class="items">{li}</ul>' + \
               f'<div class="conf">How sure are we? <span>{E(s.get("confidence"))}</span></div><div class="cap">{E(s.get("reason"))}</div>'
    if t == "discuss":
        sd = "".join(f'<div class="side">{E(x)}</div>' for x in s.get("sides", []))
        return k + f'<div class="q">{ttl(s["question"])}</div>' + (f'<div class="sides">{sd}</div>' if sd else "") + \
               f'<div class="prompt">{E(s.get("prompt") or "Tell us in the comments. We read every one.")}</div>'
    if t == "sources":
        it = "".join(f'<div><b>{E(x["name"])}</b> — {E(x.get("what"))}</div>' for x in s["items"])
        cr = "".join(f'<div class="cred">{E(c)}</div>' for c in s.get("credits", []))
        return '<div class="kicker">Sources</div>' + f'<div class="src">{it}</div>{cr}' + \
               f'<div class="cta">Follow the Question.</div><div class="cap">{E(s.get("handle") or "Full explainers on YouTube: @The_Jijñāsā")}</div>'
    raise ValueError(f"unknown slide type {t}")


def page(s, i, n):
    dots = "".join(f'<div class="dot{" on" if j == i else ""}"></div>' for j in range(n))
    swipe = '<div class="orbit"></div><div class="swipe">SWIPE →</div>' if s["type"] == "cover" else f'<div class="wm">{i+1:02d}</div>'
    credit = f'<div class="credit">{E(s["credit"])}</div>' if s.get("credit") else ""
    emb = (KIT / "brand/emblem.png").as_uri()
    return (f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS.replace("url(F/", "url(" + (KIT / "fonts").as_uri() + "/")}</style></head>'
            f'<body><svg class="stars" id="st" width="1080" height="1350"></svg><div class="frame" id="fr">{inner(s)}</div>{swipe}{credit}'
            f'<div class="foot"><img src="{emb}"><div class="brand">Jijñāsā<i>जिज्ञासा</i></div><div class="pg">{dots}</div></div>'
            f'{STARS % (7 + i * 31)}</body></html>')


def render(spec, out):
    from playwright.sync_api import sync_playwright
    out = pathlib.Path(out).resolve(); out.mkdir(parents=True, exist_ok=True)
    slides = spec["slides"]; n = len(slides); bad = []; files = []
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={"width": W, "height": H})
        for i, s in enumerate(slides):
            f = out / f"slide_{i+1:02d}.html"; f.write_text(page(s, i, n), encoding="utf-8")
            pg.goto(f.as_uri()); pg.wait_for_timeout(250); pg.evaluate("document.fonts.ready")
            over = pg.evaluate("(()=>{const e=document.getElementById('fr');return e.scrollHeight-e.clientHeight})()")
            if over > 2: bad.append(f"slide {i+1} ({s['type']}) overflows by {over}px — shorten text")
            png = out / f"slide_{i+1:02d}.png"; pg.screenshot(path=str(png))
            from PIL import Image
            jpg = out / f"slide_{i+1:02d}.jpg"; Image.open(png).convert("RGB").save(jpg, quality=92, optimize=True)
            png.unlink(); f.unlink(); files.append(jpg)
        b.close()
    from PIL import Image  # contact sheet for visual QC
    th = [Image.open(f).resize((270, 338)) for f in files]; cols = 5; rows = (len(th) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 280 + 10, rows * 348 + 10), "#111")
    for j, t in enumerate(th): sheet.paste(t, (10 + (j % cols) * 280, 10 + (j // cols) * 348))
    sheet.save(out / "contact.jpg", quality=85)
    print("\n".join(str(f) for f in files)); print("contact sheet:", out / "contact.jpg")
    if bad:
        print("OVERFLOW:\n" + "\n".join(bad)); sys.exit(1)
    print("RENDER OK")


EXAMPLE = {"slides": [
    {"type": "cover", "kicker": "Space", "title": "A shadow can move *faster than light*.", "sub": "Relativity is fine with it. Here's why."},
    {"type": "quiz", "kicker": "Guess first", "question": "What does the speed limit actually forbid?", "options": ["Anything moving faster than light", "Sending information faster than light"]},
    {"type": "reveal", "kicker": "The answer", "answer": "B", "body": "The limit is on **messages**. A shadow's edge carries none from one point to the next."},
    {"type": "stat", "kicker": "The number", "number": "1.28", "unit": "× c", "label": "a hand-shadow swept across the Moon", "body": "At 10 cm per second, from Earth."},
    {"type": "discuss", "kicker": "Your turn", "question": "What else looks faster than light but isn't?", "sides": ["Laser dot", "Expanding space"]},
    {"type": "sources", "items": [{"name": "Example source", "what": "what it supports"}], "credits": ["Photo on slide 2: title, author, licence"]}]}

if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] == "--example":
        print(json.dumps(EXAMPLE, ensure_ascii=False, indent=1)); sys.exit(0)
    render(json.load(open(a[0])), a[1])
