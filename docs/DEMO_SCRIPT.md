# Demo Script — System Design Teacher Platform

A 2-minute walkthrough you can record with Loom, OBS, or QuickTime. The script is intentionally tight — every sentence either shows the product or explains the engineering. No filler.

## Setup before you hit record

- Browser at `https://zealous-cliff-07bce210f.7.azurestaticapps.net`, signed out, fresh load
- Backend warmed up (hit `/health` once before recording so the first request isn't a cold start)
- A second tab open at `https://github.com/sarthakdixit/system-design-teacher` showing the README
- DevTools closed
- Notifications muted; phone on silent
- Window at 1280×800 or 1920×1080
- Microphone tested

If you have GPT-4o credits to spare, do the design-canvas submission once before recording so the cache is warm — your demo submission returns in under a second instead of 10–30 seconds. Mention this in the cache-hit section.

## Beat 1 — The hook (0:00–0:15)

**Show**: The signed-out home page.

**Say**:

> "This is System Design Teacher — a platform for practicing system-design interviews. Two modes: situation-based questions where you study a reference answer, and a design canvas where you submit an architecture and an LLM gives you structured feedback. Built to demonstrate cloud-native architecture on Azure. I'll show you the product, then walk through how it's built."

## Beat 2 — Sign in (0:15–0:30)

**Show**: Click "Sign in with Microsoft." Microsoft popup. Land on home page logged in.

**Say**:

> "Authentication uses Microsoft Entra. The frontend gets a Microsoft ID token via MSAL, the backend validates it against Microsoft's JWKS, and issues its own short-lived JWT. JWT lives in memory only — never in localStorage, no XSS surface."

## Beat 3 — Situation practice (0:30–0:50)

**Show**: Navigate to Situation Practice. Filter to "scalability" / "mid". Click Get Question. Read the prompt for two seconds. Click Reveal Answer.

**Say**:

> "Situation questions are pre-seeded — fifty of them — with reference answers generated once via GPT-4o for about fifty cents. After that, fetching them is free. Rate-limited at five per user per day, fifty per day globally."

## Beat 4 — Design canvas + AI feedback (0:50–1:30)

**Show**: Navigate to Design Canvas. Pick a question (e.g., "Design a URL shortener"). Drag four or five components onto the canvas — User, Load Balancer, API Gateway, Cache, Database. Connect them. Add edge labels (e.g., "redirect path", "write path"). Click Submit.

**Say while building**:

> "The canvas is React Flow. Each node type maps to a component palette item — load balancer, cache, queue, database, and so on. I label edges to tell the LLM which path is which — that's a Batch 6 feature that fixed a class of false-positive critiques the LLM kept generating."

**Show**: Loading state for ~10 seconds. Feedback panel slides in.

**Say while it loads**:

> "Submission goes through a rate limiter, then a cache keyed by a normalized hash of the diagram structure. Cache hit returns at zero cost. Cache miss calls GPT-4o, which returns structured JSON validated by Pydantic. Retries once on schema failure."

**Show**: Read out one critique from the feedback panel — pick a critical or important one.

**Say**:

> "The feedback comes back as severity-graded gaps with affected components highlighted. The LLM also asks trade-off questions and estimates the candidate's level — junior, mid, or senior."

## Beat 5 — History (1:30–1:45)

**Show**: Click into History. List of past attempts. Click into one. View its full feedback again without re-paying.

**Say**:

> "Every attempt is persisted in Cosmos. You can re-read past feedback any time. The cache means submitting the same diagram twice is instant — second call costs zero."

## Beat 6 — Architecture (1:45–2:10)

**Show**: Switch to the GitHub tab. Scroll to the architecture diagram in the README.

**Say**:

> "Here's how it's built. React frontend on Static Web Apps. FastAPI backend on Container Apps with system-assigned Managed Identity. Cosmos for storage, Key Vault for secrets, App Insights for telemetry, all provisioned by Bicep. Hexagonal architecture — seven ports for external systems, local adapters for development, Azure adapters for production, swapped by a single environment variable. CI/CD on every push to main. Steady-state cost is zero dollars on free tiers, with a five-dollar-per-month budget alert as a hard cap."

## Beat 7 — Close (2:10–2:20)

**Show**: README's "Live demo" link or back to the home page.

**Say**:

> "Live URL is in the README. Source is on GitHub. Thanks for watching."

## Total: 2:20

If your recording goes over 2:30, cut Beat 5 (History) — it's the most expendable. If under 2:00, you spoke too fast; re-record slower.

## Tone notes

- **Don't apologize for limitations.** "It scales to zero so the first request is cold" is fine. "I know it's slow, sorry" is not.
- **Don't read the script verbatim.** Adapt the phrasing to your speaking voice. The bullets are the structure, not the script.
- **Don't show DevTools or terminal.** Recruiters skim videos; visible code dumps lose them.
- **Cursor movements: deliberate.** Pause on the thing you're describing for half a second before moving on.

## After recording

- Upload to Loom, YouTube (unlisted), or another shareable host
- Add the link to the README's "Live demo" section
- If you re-record after a feature change (e.g., when History page lands), update the link in one place — README — not in resumes or LinkedIn posts that you cannot easily update later

## Re-recording prompts

You'll probably want to re-record after each of these:

- Edge labels feature lands (Beat 4 changes — currently the script already mentions it as a "Batch 6 feature")
- History page lands (Beat 5 currently mentions History; if not yet shipped, skip Beat 5 and go straight from Beat 4 to Beat 6)
- Custom domain, if you ever add one (URLs change)
- A new feature you're proud of (replace one of the existing beats)

Keep the script in this file so it stays reproducible.
