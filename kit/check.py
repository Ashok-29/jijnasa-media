#!/usr/bin/env python3
"""Automated part of Gate B (requirements). Prints PASS/FAIL per rule; exit 1 on any FAIL.

  python3 kit/check.py x  thread.json   # {"posts":[...], "hook_image": {...}|null, "hfl": false}
  python3 kit/check.py ig post.json     # {"caption":"...", "items":[{"kind":"slide"|"photo","url":"...","credit":"..."}], "hfl": false}
  python3 kit/check.py len "text"       # weighted X length of one string

"hfl" = health / finance / law topic (needs the not-personal-advice line).
Human/agent judgement still decides: truth, hook quality, predict->reveal payoff, labels, tone.
"""
import json, re, sys, unicodedata

URL = re.compile(r"https?://\S+")
BANNED = ["delve", "in today's rapidly evolving world", "it is important to note", "game-changing", "game changer",
          "revolutionary", "mind-blowing", "mind blowing", "you won't believe", "breaking:", "thread 🧵", "🧵",
          "must-see", "shocking", "insane", "like and retweet", "follow for follow", "smash that"]
BAD_BRAND = re.compile(r"(?<![_@/.\w])(jijnasa|jignasa|jijnaasa)(?![\w.])", re.I)
EMOJI = re.compile("[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F2FF]")
HFL_LINE = "general information, not personal advice"


def xlen(t):
    t = unicodedata.normalize("NFC", t); n = 23 * len(URL.findall(t))
    for ch in URL.sub("", t):
        c = ord(ch); n += 1 if (c <= 4351 or 8192 <= c <= 8205 or 8208 <= c <= 8223 or 8242 <= c <= 8247) else 2
    return n


R = []
def rule(ok, name, detail=""):
    R.append(ok); print(("PASS " if ok else "FAIL ") + name + (f" — {detail}" if detail and not ok else ""))


def common(text, hfl):
    low = text.lower()
    hits = [b for b in BANNED if b in low]
    rule(not hits, "no banned phrases", ", ".join(hits))
    rule(not BAD_BRAND.search(URL.sub("", text)), "brand spelling (Jijñāsā, never Jijnasa)", str(BAD_BRAND.findall(URL.sub('', text))))
    i = text.find("Jijñāsā")
    rule(i < 0 or text[i:i + 20].startswith("Jijñāsā (जिज्ञासा)"), "first brand use is 'Jijñāsā (जिज्ञासा)'")
    caps = [w for w in re.findall(r"\b[A-Z]{6,}\b", URL.sub("", text)) if w not in {"NASA", "UNESCO", "CERN", "ISRO"}]
    rule(not caps, "no ALL-CAPS shouting", ", ".join(caps))
    rule(len(EMOJI.findall(text)) <= 1, "at most one emoji", str(len(EMOJI.findall(text))))
    rule(not re.search(r"(?<![\w/])@\w", URL.sub("", text).replace("@The_Jijñāsā", "").replace("@the_jijnasa", "")), "no @mentions of other accounts")
    rule("follow the question." in low, "'Follow the Question.' present")
    if hfl: rule(HFL_LINE in low, f"'{HFL_LINE}' present (health/finance/law)")


def check_x(d):
    P = d["posts"]; full = "\n".join(P)
    rule(4 <= len(P) <= 5, "4–5 posts", str(len(P)))
    for i, p in enumerate(P, 1):
        rule(xlen(p) <= 280, f"post {i} ≤ 280 weighted chars", str(xlen(p)))
        rule(p.strip() != "", f"post {i} not empty")
    rule(not URL.search(P[0]), "hook (post 1) has no link")
    rule(len(re.findall(r"#\w+", P[0])) <= 2 and len(re.findall(r"#\w+", full)) <= 3, "≤2 hashtags in hook, ≤3 total")
    rule(len(P) > 2 and "?" in P[1], "post 2 asks the predict question")
    rule("how sure are we" in full.lower(), "'How sure are we' present")
    n = len(URL.findall(P[-1])); rule(2 <= n <= 4, "last post has 2–4 links (sources + optional promo)", str(n))
    rule("?" in P[-1], "closing reply-inviting question in last post")
    if d.get("hook_image"):
        img = d["hook_image"]
        for k in ("url", "alt", "title", "author", "licence", "source_page"):
            rule(bool(img.get(k)), f"image record has {k}")
        lic = (img.get("licence") or "").lower()
        rule(not any(x in lic for x in ("nc", "nd", "all rights", "fair use", "unknown")) and
             any(x in lic for x in ("public domain", "cc0", "cc by", "pd")), "image licence is PD/CC0/CC BY/CC BY-SA", lic)
        rule(len(img.get("alt", "")) <= 1000, "alt text ≤ 1000 chars")
        rule("image:" in full.lower(), "image credit line in thread")
    common(full, d.get("hfl"))


def check_ig(d):
    c = d["caption"]; items = d["items"]
    rule(len(c) <= 2200, "caption ≤ 2200 chars", str(len(c)))
    first = c.strip().split("\n")[0]
    rule(len(first) <= 125, "first caption line ≤ 125 chars (shows before 'more')", str(len(first)))
    tags = re.findall(r"#\w+", c); rule(3 <= len(tags) <= 8, "3–8 hashtags", str(len(tags)))
    rule(5 <= len(items) <= 10, "carousel has 5–10 items", str(len(items)))
    rule(items and items[0]["kind"] == "slide", "first item is the rendered cover (sets 4:5 ratio)")
    for i, it in enumerate(items, 1):
        rule(it.get("url", "").startswith("https://"), f"item {i} has a public https URL")
        if it["kind"] == "photo":
            rule(bool(it.get("credit")), f"item {i} photo has a credit")
            rule(it.get("credit", "")[:25].lower() in c.lower(), f"item {i} photo credit repeated in caption")
            lic = (it.get("licence") or "").lower()
            rule(any(x in lic for x in ("public domain", "cc0", "cc by", "pd")) and not any(x in lic for x in ("nc", "nd")),
                 f"item {i} licence PD/CC0/CC BY/CC BY-SA", lic)
    rule("?" in c, "caption asks a question (discussion)")
    rule("sources" in c.lower(), "caption lists sources")
    common(c, d.get("hfl"))


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: print(__doc__); sys.exit(0)
    if a[0] == "len": print(xlen(a[1])); sys.exit(0)
    d = json.load(open(a[1]))
    (check_x if a[0] == "x" else check_ig)(d)
    print("GATE B AUTO: " + ("PASS" if all(R) else "FAIL")); sys.exit(0 if all(R) else 1)
