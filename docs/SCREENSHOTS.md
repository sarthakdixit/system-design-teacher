# Screenshots

The README references a screenshot at `docs/screenshots/design-canvas.png`. This file documents what screenshots the project tracks, how to capture them, and when to refresh them.

## Why screenshots are committed to the repo

- README image links work without external hosting
- Each commit's screenshot reflects the UI at that commit (good for diffs, code review)
- No dependency on third-party CDNs that could go down

The trade-off: the repo grows by a few hundred KB per screenshot. Acceptable.

## Required screenshots

The README needs these to render properly. If you delete one, the README image will 404 on GitHub:

| File                                 | What it shows                                                | Used by     |
| ------------------------------------ | ------------------------------------------------------------ | ----------- |
| `docs/screenshots/design-canvas.png` | The design canvas mid-submission with feedback panel visible | README hero |

That's it for the MVP. Future-batch additions might include a sign-in screenshot or a history-page screenshot.

## How to capture

### `design-canvas.png` (the hero shot)

1. Sign in to the live site (or local dev with `VITE_AUTH_MODE=mock`).
2. Navigate to the **Design Canvas** mode.
3. Pick the "Design a URL shortener" question (or similar high-density example).
4. Drag enough components for a meaningful diagram — 6 to 10 nodes works:
   - User → API Gateway → Cache → Database
   - API Gateway → Auth Service → Shorten Service → Database
   - Database → Queue → Analytics
5. Add edge labels where they help (e.g., "redirect path" on the cache route, "write path" on the auth → shorten edge).
6. Click **Submit**. Wait for the feedback panel to render.
7. Capture at **1600×1000 px or larger** with both the canvas and feedback panel visible. macOS: `Cmd+Shift+4` then drag. Windows: Snipping Tool. Linux: `gnome-screenshot -a` or Flameshot.
8. Save as `docs/screenshots/design-canvas.png`.

### Tips

- **Light background.** Most readers view GitHub in light mode; dark-mode screenshots look out of place against a light README.
- **No dev tools open.** No browser bookmarks bar visible. Strip distracting browser chrome by going full-screen or using a window-only capture.
- **No personally-identifying info.** If the user-profile area shows your real name and email, fine — it's already on the GitHub repo. Otherwise crop or blur.
- **Compress**. A 2 MB PNG is too large. Run through TinyPNG or `pngquant docs/screenshots/design-canvas.png` to drop it under 500 KB without visible quality loss.

## When to refresh

Re-capture and re-commit screenshots when:

- Major UI changes ship (component palette redesign, feedback panel restructure)
- Branding changes (colors, logo, title)
- Edge labels feature lands (currently in Batch 6 — mention them in the labeled diagram)
- A new feature appears in the screenshot's frame (e.g., when the History link lands in the nav bar)

For minor copy or spacing tweaks, skip the re-capture. The screenshot doesn't need to be pixel-perfect with current `main` — it just needs to look like the same product.

## Conventions

- File names: kebab-case, descriptive (`design-canvas.png`, `history-page.png`, not `screenshot1.png`).
- Format: PNG. JPG compression artifacts look bad on UI screenshots.
- Resolution: 1600px wide minimum; height proportional. GitHub will scale down for inline display.
- Compression: Run through `pngquant` or TinyPNG before committing. Target < 500 KB per screenshot.

## Why not animated GIFs or videos?

GIFs can be useful for showing interaction (e.g., dragging a component). Considered, decided against:

- Large file size (often 5–20 MB for a 5-second loop)
- Auto-loop pulls the eye away from the rest of the README
- For interaction depth, the demo video (linked in README) is the right surface

The static screenshot is the README's hero; the video link is the deeper dive.
