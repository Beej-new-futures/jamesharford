import html
import json
import os
import re
import time
import urllib.request

BASE = "https://www.jamesharford.com"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) jamesharford-archive-script/1.0"

ROOT = os.environ.get("PROJECT_ROOT")
if not ROOT:
    raise SystemExit("PROJECT_ROOT env var not set")

PROJECTS_DIR = os.path.join(ROOT, "content", "projects")
SITE_DIR = os.path.join(ROOT, "content", "site")
ASSETS_SITE_DIR = os.path.join(ROOT, "assets", "site")

SLUGS = [
    "aurora", "aurora-2", "barclays", "formula-e", "four-to-the-floor",
    "home-grid-experiment", "inside-the-machine", "jd-reid", "little-simz",
    "little-simz-brits", "nbc", "nike", "nike-verona", "old-home",
    "space-jungle", "tate-late", "together-we-rise", "wildfarmed",
    "yearning-for-the-infinite", "reels", "barcelona",
]

HOME_TITLES = {
    "little-simz": "Little Simz: Tour Visuals",
    "aurora-2": "Mizuno: Brand Film",
    "formula-e": "Formula E",
    "together-we-rise": "Together We Rise",
    "wildfarmed": "Wildfarmed: A Story About Bread",
    "old-home": "Redbull Formula 1: Aston Martin Release",
    "yearning-for-the-infinite": "Yearning for the Infinite",
    "little-simz-brits": "Little Simz Performance Visuals: The Brits",
    "aurora": "Aurora: Main Film",
    "nbc": "NBC Upfront Award Ceremony Graphics",
    "nike-verona": "Nike Verona Shoe Launch Campaign",
    "inside-the-machine": "Inside the Machine: Art Installation Barcelona",
    "jd-reid": "JD Reid - Just Know",
    "nike": "Nike Mercurial Boot Campaign",
    "barclays": "Vice x AI Machine Learning",
    "tate-late": "Circles - Art Series TATE LATE",
    "four-to-the-floor": "Four to the Floor",
    "space-jungle": "The Space Jungle",
}


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def download(url, dest_path):
    if os.path.exists(dest_path):
        return "skip"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as resp, open(dest_path, "wb") as f:
        f.write(resp.read())
    return "ok"


def clean_text(t):
    t = html.unescape(t)
    t = t.replace("‍", "")  # zero-width joiner used as spacer
    t = re.sub(r"<br\s*/?>", "\n", t)
    t = re.sub(r"<[^>]+>", "", t)
    lines = [ln.strip() for ln in t.split("\n")]
    # collapse 3+ blank lines, strip leading/trailing blanks
    out = []
    blank_run = 0
    for ln in lines:
        if ln == "":
            blank_run += 1
            if blank_run > 1:
                continue
        else:
            blank_run = 0
        out.append(ln)
    while out and out[0] == "":
        out.pop(0)
    while out and out[-1] == "":
        out.pop()
    return "\n".join(out)


def extract_ordered(html_text):
    """Extract h1.main-heading, h4.main-heading, p.paragraph-2, img src, iframe src
    in document order as a list of (kind, value) tuples."""
    events = []
    # tag pattern matches opening tag + its content up to the matching close for simple non-nested cases
    tag_re = re.compile(
        r'<h1[^>]*class="[^"]*main-heading[^"]*"[^>]*>(.*?)</h1>'
        r'|<h4[^>]*class="[^"]*main-heading[^"]*"[^>]*>(.*?)</h4>'
        r'|<p[^>]*class="[^"]*paragraph-2[^"]*"[^>]*>(.*?)</p>'
        r'|<img\s+([^>]*)/?>'
        r'|<iframe\s+([^>]*)>',
        re.DOTALL,
    )
    for m in tag_re.finditer(html_text):
        if m.group(1) is not None:
            events.append(("h1", clean_text(m.group(1))))
        elif m.group(2) is not None:
            events.append(("h4", clean_text(m.group(2))))
        elif m.group(3) is not None:
            events.append(("p", clean_text(m.group(3))))
        elif m.group(4) is not None:
            attrs = m.group(4)
            cls_m = re.search(r'class="([^"]*)"', attrs)
            cls = cls_m.group(1) if cls_m else ""
            if "image-16" in cls:
                continue  # nav logo
            src_m = re.search(r'src="([^"]*)"', attrs)
            if src_m:
                events.append(("img", html.unescape(src_m.group(1))))
        elif m.group(5) is not None:
            attrs = m.group(5)
            src_m = re.search(r'src="([^"]*)"', attrs)
            if src_m:
                raw_src = src_m.group(1)
                decoded_src = urllib.parse.unquote(raw_src)
                if "vimeo" in decoded_src:
                    vid_m = re.search(r"vimeo\.com/video/(\d+)", decoded_src)
                    if vid_m:
                        events.append(("vimeo", vid_m.group(1)))
                    else:
                        events.append(("embed", html.unescape(raw_src)))
                elif "youtube" in decoded_src:
                    events.append(("youtube", html.unescape(raw_src)))
    return events


def title_tag(html_text):
    m = re.search(r"<title>([^<]*)</title>", html_text)
    return html.unescape(m.group(1)).strip() if m else ""


def filename_from_url(url):
    name = url.split("/")[-1].split("?")[0]
    return urllib.parse_unquote(name) if hasattr(urllib, "parse_unquote") else name


import urllib.parse


def slugify_filename(url):
    name = url.split("/")[-1].split("?")[0]
    name = urllib.parse.unquote(name)
    base, ext = os.path.splitext(name)
    base = re.sub(r"[^A-Za-z0-9._-]+", "-", base)
    base = re.sub(r"-{2,}", "-", base).strip("-")
    return f"{base}{ext}"


def process_page(slug):
    url = f"{BASE}/{slug}" if slug != "" else BASE
    print(f"=== {slug} ===")
    try:
        html_text = fetch(url)
    except Exception as e:
        print(f"  FETCH FAILED: {e}")
        return {"slug": slug, "error": str(e)}

    page_title = title_tag(html_text)
    events = extract_ordered(html_text)

    proj_dir = os.path.join(PROJECTS_DIR, slug)
    img_dir = os.path.join(proj_dir, "images")
    os.makedirs(img_dir, exist_ok=True)

    md_lines = []
    md_lines.append(f"# {page_title or HOME_TITLES.get(slug, slug)}")
    md_lines.append("")
    md_lines.append(f"- Source URL: {url}")
    md_lines.append(f"- Slug: {slug}")
    md_lines.append("")

    img_count = 0
    downloaded = []
    for kind, val in events:
        if kind == "h1":
            md_lines.append(f"## {val}")
            md_lines.append("")
        elif kind == "h4":
            md_lines.append(f"**Role/Credit:** {val}")
            md_lines.append("")
        elif kind == "p":
            if val:
                md_lines.append(val)
                md_lines.append("")
        elif kind == "vimeo":
            md_lines.append(f"**Video (Vimeo):** https://vimeo.com/{val}")
            md_lines.append("")
        elif kind == "youtube":
            md_lines.append(f"**Video (YouTube embed):** {val}")
            md_lines.append("")
        elif kind == "embed":
            md_lines.append(f"**Video (embed, unresolved ID):** {val}")
            md_lines.append("")
        elif kind == "img":
            img_count += 1
            fname = slugify_filename(val)
            dest = os.path.join(img_dir, fname)
            try:
                status = download(val, dest)
                downloaded.append((fname, status))
            except Exception as e:
                downloaded.append((fname, f"FAILED: {e}"))
            md_lines.append(f"![{fname}](images/{fname})")
            md_lines.append("")

    content_md = "\n".join(md_lines)
    with open(os.path.join(proj_dir, "content.md"), "w", encoding="utf-8") as f:
        f.write(content_md)

    n_ok = sum(1 for _, s in downloaded if s == "ok")
    n_skip = sum(1 for _, s in downloaded if s == "skip")
    n_fail = sum(1 for _, s in downloaded if isinstance(s, str) and s.startswith("FAILED"))
    print(f"  title={page_title!r} images={img_count} (new={n_ok} cached={n_skip} failed={n_fail})")
    if n_fail:
        for fname, s in downloaded:
            if isinstance(s, str) and s.startswith("FAILED"):
                print(f"    FAILED: {fname} -> {s}")

    return {
        "slug": slug,
        "title": page_title,
        "images": img_count,
        "images_new": n_ok,
        "images_failed": n_fail,
    }


def main():
    os.makedirs(PROJECTS_DIR, exist_ok=True)
    os.makedirs(SITE_DIR, exist_ok=True)
    os.makedirs(ASSETS_SITE_DIR, exist_ok=True)

    results = []
    for slug in SLUGS:
        results.append(process_page(slug))
        time.sleep(0.4)

    summary_path = os.path.join(ROOT, "content", "crawl-summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nWrote summary to {summary_path}")


if __name__ == "__main__":
    main()
