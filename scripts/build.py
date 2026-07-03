"""Static site generator for jamesharford.com.

Reads content/projects/<slug>/content.md + content/site/projects.json
and writes index.html, /<slug>/index.html and /reels/index.html into the
repo root. Re-run after editing content:

    python3 scripts/build.py
"""
import html
import json
import os
import re
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT = os.path.join(ROOT, "content", "projects")

SITE_TITLE = "Beej — Digital Artist & Director"
SITE_DESC = "The portfolio of digital artist and director Beej (James Harford)."

# pages generated but excluded from the homepage grid
EXTRA_PAGES = ["barcelona"]
SKIP_PAGES = ["home-grid-experiment"]


def esc(s):
    return html.escape(s, quote=True)


def parse_content_md(slug):
    """Parse a crawled content.md back into an ordered list of blocks."""
    path = os.path.join(CONTENT, slug, "content.md")
    with open(path, encoding="utf-8") as f:
        lines = f.read().split("\n")

    blocks = []  # (kind, value)
    para = []

    def flush():
        nonlocal para
        text = "\n".join(para).strip()
        if text:
            blocks.append(("p", text))
        para = []

    for ln in lines:
        if ln.startswith("# ") or ln.startswith("- Source URL:") or ln.startswith("- Slug:"):
            continue
        if ln.startswith("## "):
            flush()
            blocks.append(("h1", ln[3:].strip()))
        elif ln.startswith("**Role/Credit:**"):
            flush()
            blocks.append(("role", ln.replace("**Role/Credit:**", "").strip()))
        elif ln.startswith("**Video (Vimeo):**"):
            flush()
            m = re.search(r"vimeo\.com/(\d+)", ln)
            if m:
                blocks.append(("vimeo", m.group(1)))
        elif ln.startswith("!["):
            flush()
            m = re.search(r"\]\(images/([^)]+)\)", ln)
            if m:
                blocks.append(("img", m.group(1)))
        elif ln.strip() == "":
            flush()
        else:
            para.append(ln)
    flush()
    return blocks


def page_shell(title, desc, body, depth=0):
    rel = "../" * depth
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<link rel="icon" href="{rel}assets/site/favicon-small.jpg">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Work+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{rel}assets/css/style.css">
</head>
<body>
<header class="site-header">
  <a class="wordmark" href="{rel if depth else './'}">BEEJ</a>
  <nav>
    <a href="{rel if depth else './'}">Work</a>
    <a href="{rel}reels/">Reels</a>
  </nav>
</header>
{body}
<footer class="site-footer">
  <p>&copy; 2026 James Harford &middot; Digital artist &amp; director</p>
</footer>
</body>
</html>
"""


def build_index(manifest):
    cards = []
    for p in manifest:
        role = f'<p class="card-role">{esc(p["role"])}</p>' if p["role"] else ""
        cards.append(f"""  <a class="card" href="{p['slug']}/">
    <img src="{p['thumb']}" alt="{esc(p['title'])}" loading="lazy">
    <div class="card-meta">
      <h2>{esc(p['title'])}</h2>
      {role}
    </div>
  </a>""")
    body = f"""<main>
<section class="intro">
  <h1>Digital artist &amp; director</h1>
  <p>Selected work — direction, design, animation &amp; installations.</p>
</section>
<section class="grid">
{chr(10).join(cards)}
</section>
</main>"""
    return page_shell(SITE_TITLE, SITE_DESC, body, depth=0)


def build_project(slug, grid_meta):
    blocks = parse_content_md(slug)

    title = grid_meta.get("title") if grid_meta else None
    role = grid_meta.get("role") if grid_meta else None
    for kind, val in blocks:
        if kind == "h1" and not title:
            title = val
        if kind == "role" and not role:
            role = val

    first_p = next((v for k, v in blocks if k == "p"), SITE_DESC)
    desc = re.sub(r"\s+", " ", first_p)[:155]

    out = [f'<main class="project">']
    out.append(f'<h1>{esc(title or slug)}</h1>')
    if role:
        out.append(f'<p class="role">{esc(role)}</p>')

    for kind, val in blocks:
        if kind == "p":
            paras = [esc(x.strip()) for x in val.split("\n") if x.strip()]
            out.append('<div class="copy"><p>' + "</p><p>".join(paras) + "</p></div>")
        elif kind == "vimeo":
            out.append(
                f'<div class="video"><iframe src="https://player.vimeo.com/video/{val}" '
                f'loading="lazy" allow="fullscreen" allowfullscreen title="Vimeo video"></iframe></div>'
            )
        elif kind == "img":
            src = f"../content/projects/{slug}/images/{val}"
            out.append(f'<img class="still" src="{src}" alt="" loading="lazy">')

    out.append('<p class="backlink"><a href="../">&larr; All work</a></p>')
    out.append("</main>")
    return page_shell(f"{title or slug} — Beej", desc, "\n".join(out), depth=1)


def build_reels():
    blocks = parse_content_md("reels")
    out = ['<main class="project reels">', "<h1>Reels</h1>"]
    for kind, val in blocks:
        if kind == "h1":
            out.append(f"<h2>{esc(val)}</h2>")
        elif kind == "role":
            out.append(f'<p class="role">{esc(val)}</p>')
        elif kind == "vimeo":
            out.append(
                f'<div class="video"><iframe src="https://player.vimeo.com/video/{val}" '
                f'loading="lazy" allow="fullscreen" allowfullscreen title="Vimeo video"></iframe></div>'
            )
    out.append('<p class="backlink"><a href="../">&larr; All work</a></p>')
    out.append("</main>")
    return page_shell("Reels — Beej", "Showreels — motion graphics, design & VFX.", "\n".join(out), depth=1)


def main():
    with open(os.path.join(ROOT, "content", "site", "projects.json"), encoding="utf-8") as f:
        manifest = json.load(f)
    by_slug = {p["slug"]: p for p in manifest}

    with open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8") as f:
        f.write(build_index(manifest))
    print("wrote index.html")

    slugs = [p["slug"] for p in manifest] + EXTRA_PAGES
    for slug in dict.fromkeys(slugs):  # dedupe, keep order
        if slug in SKIP_PAGES:
            continue
        os.makedirs(os.path.join(ROOT, slug), exist_ok=True)
        with open(os.path.join(ROOT, slug, "index.html"), "w", encoding="utf-8") as f:
            f.write(build_project(slug, by_slug.get(slug)))
        print(f"wrote {slug}/index.html")

    os.makedirs(os.path.join(ROOT, "reels"), exist_ok=True)
    with open(os.path.join(ROOT, "reels", "index.html"), "w", encoding="utf-8") as f:
        f.write(build_reels())
    print("wrote reels/index.html")


if __name__ == "__main__":
    main()
