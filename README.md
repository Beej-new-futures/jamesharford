# jamesharford

Rebuild of jamesharford.com (portfolio site for director/designer "Beej"). Replacing the Webflow original with a static HTML/CSS/JS site, deployed on GitHub Pages.

## Status

Content archive complete, modernized static site generated into the repo root, auto-deploying to Cloudflare Pages (jamesharford.pages.dev). The live domain still points at Webflow until the rebuild is approved.

## Adding a new project

Drop a folder into `content/projects/` with images and/or `.mp4` files in it, then rebuild:

```bash
python3 scripts/build.py
```

- Folder name becomes the URL and title (`my-new-thing` → "My New Thing")
- Media is laid out in filename order; newest project folders appear first in the homepage grid
- Optional `thumb.jpg`/`thumb.png` sets the homepage thumbnail (otherwise the first image is used)
- Optional `content.md` adds custom title/credits/copy — same format as the crawled projects

Commit and push, and Cloudflare Pages redeploys automatically.

## Project structure

```
jamesharford/
├── content/
│   ├── projects/<slug>/
│   │   ├── content.md      # title, credits, body copy, video links
│   │   └── images/         # full-resolution downloaded images
│   ├── site/
│   │   └── nav.md          # nav structure, homepage grid order, identity assets
│   └── crawl-summary.json  # machine-readable crawl results
├── assets/site/            # logo, favicons
├── scripts/crawl.py        # crawler used to generate content/ (re-runnable)
└── src/                    # rebuilt site (not started)
```

## Projects archived

21 pages crawled from jamesharford.com: 18 projects from the homepage grid, plus `nike` (dual-purpose nav + project page), `reels` (showreel video links), and `barcelona` (legacy "Zero Point" installation, orphan page not linked from the homepage grid). See `content/site/nav.md` for full ordering and notes.

## Re-running the crawler

```bash
PROJECT_ROOT=/path/to/jamesharford python3 scripts/crawl.py
```

Downloads are skipped if the target file already exists, so re-runs are cheap.
