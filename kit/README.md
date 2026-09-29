# Jijñāsā social kit

Permanent tools for the scheduled X and Instagram runs. **Do not delete `kit/`.** Media under `social/` is temporary and pruned after 7 days.

| File | Does |
|---|---|
| `render.py spec.json OUT` | Branded 1080×1350 carousel slides (JPEG) + `contact.jpg`; exits 1 if any slide overflows |
| `chart.py chart.json out.png [--x]` | Brand chart (slide size, or 1600×900 for X); numbers only from the claim map |
| `check.py x thread.json` / `check.py ig post.json` | Automated Gate B checks; exit 1 on any FAIL |
| `check.py len "text"` | Weighted X length |
| `catalog.json` | Jijñāsā YouTube videos + topics, for "related video" promotion |
| `prune.py` | Remove media folders older than 7 days |

Research uses the normal web tools (WebSearch / WebFetch). The kit never touches the network.

## Hosting
Rendered files go to `social/x/<YYYY-MM-DD-HHMM-slug>/` or `social/ig/<…>/`, then are committed and pushed; their public URL is
`https://raw.githubusercontent.com/Ashok-29/jijnasa-media/main/<path>`. Check each URL returns 200 before creating the Buffer post.

## Photos (licensed, credited)
Photos are **not** composited into slides. They go into the Buffer post as their own items, by direct URL.
Scheduled runs read the web with WebFetch only, which **cannot read Wikimedia Commons or its APIs**, so Commons images are not used (licence unverifiable). Allowed:
- NASA Image and Video Library (`images-api.nasa.gov`): NASA-made media only (no third-party photographer); use the `~large.jpg` asset on `images-assets.nasa.gov`, never `~orig`.
- An image on a page that explicitly states CC BY / CC BY-SA / CC0 / public domain for that image (open-access paper, agency image page).
Credit format: `Photo: <title>, <author>, <licence>` in the caption / last X post and on the carousel's sources slide.
Instagram crops every carousel item to the first item's ratio (4:5 here): choose photos whose subject is centred. Original charts and diagrams from this kit are the mainstay; a post without a photo is fine.
