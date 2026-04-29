# AGENT.md — System Design Teacher (React Frontend)

This file tells AI coding assistants (and new human contributors) how to work effectively in the frontend codebase. Read it before making changes.

---

## Project snapshot

- **What:** React SPA for practicing system-design interviews. Two modes: situation-based Q&A, and drag-and-drop architecture design with AI feedback.
- **Where to find the big picture:** `docs/DESIGN.md` (repo root). Read it before proposing any architectural change.
- **Related:** `backend/AGENT.md` for API contracts and backend architecture.

---

## Tech stack

| Concern | Choice | Why |
|---|---|---|
| Framework | React 18 | Stable, well-known |
| Build tool | Vite | Fast HMR, simple config |
| Language | TypeScript (strict) | Type safety, portfolio signal |
| Styling | Tailwind CSS | Rapid iteration, no CSS sprawl |
| State | Zustand | Lightweight, no boilerplate |
| Server state | TanStack Query (React Query) | Caching, retries, loading states for free |
| Routing | React Router v6 | Standard |
| Diagrams | React Flow (`@xyflow/react`) | Drag-drop canvas for the Design feature |
| Auth | MSAL.js (`@azure/msal-browser` + `@azure/msal-react`) | Microsoft Entra ID |
| HTTP | Axios with interceptors | JWT injection, error handling |
| Forms | React Hook Form + Zod | Type-safe forms, minimal rerenders |
| Testing | Vitest + React Testing Library + Playwright | Unit + integration + E2E |
| Lint/format | ESLint + Prettier | Standard |

**Do not add libraries without justification.** Every dep is weight.

---

## Folder structure

```
frontend/
├── src/
│   ├── app/                    # App shell — providers, router, layout
│   │   ├── App.tsx
│   │   ├── router.tsx
│   │   └── providers.tsx       # MSAL, QueryClient, Zustand hydration
│   ├── features/               # Feature-sliced — one folder per user-facing feature
│   │   ├── auth/
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   ├── api.ts          # API calls for this feature
│   │   │   ├── store.ts        # Zustand slice (if needed)
│   │   │   └── types.ts
│   │   ├── situation-practice/
│   │   ├── design-canvas/
│   │   │   ├── components/
│   │   │   │   ├── Canvas.tsx
│   │   │   │   ├── ComponentPalette.tsx
│   │   │   │   ├── FeedbackPanel.tsx
│   │   │   │   └── nodes/      # Custom React Flow node components
│   │   │   ├── hooks/
│   │   │   │   ├── useDiagram.ts
│   │   │   │   └── useSubmitDesign.ts
│   │   │   ├── api.ts
│   │   │   ├── schema.ts       # Zod schemas for diagram JSON
│   │   │   └── types.ts
│   │   └── history/
│   ├── shared/                 # Reusable across features
│   │   ├── components/         # Button, Modal, Spinner, ErrorBoundary
│   │   ├── hooks/              # useRateLimit, useDebounce, etc.
│   │   ├── api/
│   │   │   ├── client.ts       # Axios instance + interceptors
│   │   │   └── errors.ts       # ApiError class, error parsing
│   │   └── utils/
│   ├── config/
│   │   ├── env.ts              # Typed env var access (Zod-validated)
│   │   └── msal.ts             # MSAL configuration
│   ├── types/                  # Global types, API DTOs (mirrors backend schemas)
│   └── main.tsx                # Entry point
├── public/
├── tests/
│   ├── unit/                   # Vitest + RTL
│   └── e2e/                    # Playwright
├── .env.example
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.ts
```

### Why feature-sliced, not type-sliced

Feature-sliced (`features/design-canvas/*`) keeps related code together. Type-sliced (`components/`, `hooks/`, `pages/` at the top level) scatters a feature across the tree and makes refactoring painful. Only truly cross-cutting code goes in `shared/`.

---

## Import rules

These keep the codebase navigable as it grows.

- **`shared/` can import from `shared/` only.** Never reach into a feature.
- **`features/<X>/` can import from `features/<X>/` and `shared/` only.** Never from `features/<Y>/`. If two features share code, lift it to `shared/`.
- **`app/` can import from anywhere** (it wires everything up).
- **No deep relative imports.** Use TypeScript path aliases: `@/shared/...`, `@/features/...`, `@/app/...`.

If ESLint doesn't catch it, a human reviewer should.

---

## State management — where does state go?

Four places. Pick the right one.

| State type | Example | Where it lives |
|---|---|---|
| **Server state** | User profile, questions, attempts history | **TanStack Query** (`useQuery` / `useMutation`) |
| **URL state** | Current question ID, filters, tab | **React Router params + search params** |
| **Global client state** | Auth session, theme, feature flags | **Zustand store** in `features/<X>/store.ts` or `shared/stores/` |
| **Local component state** | Form field value, modal open/close, hover | **`useState` / `useReducer`** |

### The rule

> Never put server state in Zustand. Never put URL-derivable state in Zustand or `useState`. Never put purely local UI state in Zustand.

Getting this wrong causes 80% of React bugs. TanStack Query already handles caching, refetching, loading, and errors — let it.

### Zustand conventions

- One store per concern, not one mega-store. Examples: `authStore`, `canvasStore`, `uiStore`.
- Stores export a hook and typed selectors: `useAuthStore(s => s.user)`.
- No side effects (network calls) in store actions — those go in TanStack Query mutations or custom hooks.

---

## API layer

All backend calls go through `shared/api/client.ts`.

```ts
// shared/api/client.ts
import axios from "axios";
import { env } from "@/config/env";

export const apiClient = axios.create({
  baseURL: env.VITE_API_BASE_URL,
  timeout: 30_000,
});

apiClient.interceptors.request.use(async (config) => {
  const token = await getAccessToken(); // from MSAL
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

apiClient.interceptors.response.use(
  (r) => r,
  (error) => {
    if (error.response?.status === 401) { /* trigger re-auth */ }
    if (error.response?.status === 429) { /* surface rate-limit UI */ }
    throw normalizeError(error);
  },
);
```

Each feature has its own `api.ts` that uses `apiClient`:

```ts
// features/design-canvas/api.ts
export const submitDesign = async (payload: DesignSubmission): Promise<DesignFeedback> => {
  const { data } = await apiClient.post("/api/v1/attempts/design", payload);
  return DesignFeedbackSchema.parse(data); // validate with Zod
};
```

### Rules
- **Never `fetch()` directly** in a component. Always go through a feature `api.ts`.
- **Always validate API responses with Zod** (mirrors the backend Pydantic schema). This catches backend drift early.
- **Always wrap calls in TanStack Query** (`useQuery` or `useMutation`) for consistent loading/error handling.

---

## Authentication

MSAL.js handles the Microsoft login flow.

### Flow
1. User clicks "Sign in with Microsoft" → MSAL popup/redirect.
2. MSAL returns a Microsoft ID token.
3. Frontend posts the MS token to `POST /api/v1/auth/microsoft/callback`.
4. Backend validates, issues its own JWT (HS256), returns it.
5. Frontend stores the backend JWT **in memory** (Zustand, not `localStorage`).
6. Axios interceptor attaches it to every request.
7. On expiry, MSAL silently refreshes the MS token; frontend re-exchanges for a new backend JWT.

### Security rules
- **Never use `localStorage` or `sessionStorage` for JWTs.** XSS risk. In-memory only.
- **Never log tokens** (not even in dev).
- **Redirect unauthenticated users** via a `RequireAuth` route guard, not inside each component.
- **Dev mode:** when `VITE_AUTH_MODE=mock`, skip MSAL and use a fake user. Backend's `MockAuthProvider` matches.

---

## React Flow — conventions for the design canvas

The drag-and-drop canvas is the trickiest part of the app. Follow these.

### Custom node types live in one place
`features/design-canvas/components/nodes/` — one file per component type (`LoadBalancerNode.tsx`, `CacheNode.tsx`, etc.). Register them in a single `nodeTypes` object imported by `Canvas.tsx`.

### Component palette is data-driven
Don't hardcode palette items in JSX. Define them in `features/design-canvas/palette.ts`:

```ts
export const PALETTE: PaletteItem[] = [
  { type: "load_balancer", label: "Load Balancer", icon: "⚖️", defaultData: {...} },
  { type: "cache", label: "Cache", icon: "⚡", defaultData: {...} },
  // ...
];
```

This makes adding components a one-line change and demos well in interviews.

### Diagram JSON is canonical
The source of truth is a Zod schema in `schema.ts`:

```ts
export const DiagramSchema = z.object({
  nodes: z.array(NodeSchema),
  edges: z.array(EdgeSchema),
});
```

**Only submit what the backend needs.** Strip `position`, `selected`, `dragging` and other UI-only fields before POSTing. The backend doesn't care where you put the box on screen; it cares about structure.

### State
Use React Flow's built-in `useNodesState` / `useEdgesState` for canvas state. Do NOT put the full diagram in Zustand — it updates too often.

Put derived or session-level state (current question, feedback, submission status) in a `canvasStore` Zustand slice.

---

## Styling — Tailwind conventions

### Rules
- **Prefer utility classes over custom CSS.** If you're writing a `.css` file, ask why.
- **Extract components, not class names.** Don't make a `.btn-primary` CSS class; make a `<Button variant="primary">` React component.
- **Use `clsx` or `cn` utility** for conditional classes. Never string-concatenate class names.
- **Design tokens** (spacing, colors, radii) live in `tailwind.config.ts`. Don't hardcode hex values in components.
- **Responsive by default.** Test at 375px (mobile), 768px (tablet), 1280px (desktop).

### Accessibility is not optional
- All interactive elements must be keyboard-reachable (Tab, Enter, Escape).
- Use semantic HTML (`<button>`, not `<div onClick>`).
- Provide `aria-label` for icon-only buttons.
- Focus rings are never removed without a visible replacement.
- Color contrast meets WCAG AA (4.5:1 for text).

---

## Components — how to write them

### Rules
- **Function components only.** No class components.
- **One component per file.** File name matches component name (`Button.tsx` exports `Button`).
- **Props are typed explicitly.** Use `type Props = {...}`, not inline generics for clarity.
- **No `React.FC`.** It adds implicit children and obscures signatures.
- **Destructure props at the top.** No `props.foo` sprinkled throughout.

### Structure
```tsx
// 1. Imports (grouped: react → external → @/ aliases → relative)
import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Button } from "@/shared/components/Button";
import { submitDesign } from "../api";

// 2. Types
type Props = {
  questionId: string;
  onSuccess: () => void;
};

// 3. Component
export function DesignSubmitButton({ questionId, onSuccess }: Props) {
  const [isConfirming, setIsConfirming] = useState(false);
  const mutation = useMutation({
    mutationFn: submitDesign,
    onSuccess,
  });

  return (
    <Button
      onClick={() => mutation.mutate({ questionId })}
      disabled={mutation.isPending}
    >
      {mutation.isPending ? "Submitting..." : "Submit"}
    </Button>
  );
}
```

### Hooks
- Custom hooks start with `use`.
- One hook per file in `features/<X>/hooks/` or `shared/hooks/`.
- Hooks return objects, not tuples, when returning 3+ values (better readability).

---

## Error handling & loading states

### Every async boundary shows three states
- Loading (skeleton or spinner, not blank screen)
- Error (friendly message + retry button)
- Empty (guidance, not just "no data")

TanStack Query makes this easy:
```tsx
const { data, isLoading, isError, refetch } = useQuery({...});

if (isLoading) return <Skeleton />;
if (isError) return <ErrorState onRetry={refetch} />;
if (!data?.length) return <EmptyState message="No attempts yet — try one!" />;
return <AttemptList data={data} />;
```

### Error boundaries
Wrap each feature route in an `<ErrorBoundary>` from `shared/components/`. An uncaught error should never blank the whole app.

### Rate limit UI
When the backend returns 429, show a specific UI: "You've used today's 2 design submissions. Resets at midnight UTC." Do not just show a generic error.

---

## Environment variables

Read via typed helper in `config/env.ts`:

```ts
import { z } from "zod";

const EnvSchema = z.object({
  VITE_API_BASE_URL: z.string().url(),
  VITE_MICROSOFT_CLIENT_ID: z.string(),
  VITE_MICROSOFT_TENANT_ID: z.string(),
  VITE_AUTH_MODE: z.enum(["msal", "mock"]).default("msal"),
});

export const env = EnvSchema.parse(import.meta.env);
```

### Required vars

| Var | Local | Azure |
|---|---|---|
| `VITE_API_BASE_URL` | `http://localhost:8000` | `https://<your-app>.azurestaticapps.net/api` |
| `VITE_MICROSOFT_CLIENT_ID` | dev app reg | prod app reg |
| `VITE_MICROSOFT_TENANT_ID` | `common` | your tenant |
| `VITE_AUTH_MODE` | `mock` (for dev) or `msal` | `msal` |

**Only `VITE_*` vars are exposed to the client.** Never put secrets in frontend env vars — they end up in the bundle.

---

## Testing

### Unit + component tests (Vitest + React Testing Library)
- Test behavior, not implementation. Query by role/label/text, not by CSS class or test ID (unless there's no alternative).
- Mock the API layer (`api.ts` functions), not `fetch` or Axios directly.
- Every feature has at least smoke tests for critical flows.

```tsx
// Good
const button = screen.getByRole("button", { name: /submit/i });

// Bad
const button = container.querySelector(".btn-submit");
```

### E2E tests (Playwright)
- One happy-path test per feature for MVP.
- Run against `docker compose up` + frontend dev server.
- Use mock auth mode in E2E (bypass MSAL).

### What NOT to test
- Third-party libraries (we trust React Flow, TanStack Query).
- Generated code (API types).
- Styling details (unless critical to UX).

---

## Performance

### Defaults that matter
- **Route-level code splitting** via `React.lazy` + `Suspense`. The design canvas (with React Flow) is heavy — don't load it on the login page.
- **Memoize expensive computations** with `useMemo`, expensive components with `React.memo`. But profile first; premature memo is just clutter.
- **Debounce user input** that triggers queries (search, filters) with `useDebouncedValue` from `shared/hooks/`.
- **Images:** use appropriate sizes, `loading="lazy"` on below-fold.

### Watch for
- Huge React Flow diagrams → virtualize if nodes > 100.
- Rerenders from Zustand → use selector functions (`useStore(s => s.user)`), not whole-state subscriptions.

---

## Things AI assistants commonly get wrong — avoid these

1. **Putting server data in Zustand.** Use TanStack Query. Always.
2. **Using `localStorage` for auth tokens.** In-memory only.
3. **Calling `fetch()` or `axios` directly in components.** Go through `features/<X>/api.ts` + TanStack Query.
4. **Hardcoding API URLs.** Use `env.VITE_API_BASE_URL`.
5. **Writing custom CSS files.** Use Tailwind utilities and reusable components.
6. **Reaching across features** (`features/auth/` importing from `features/design-canvas/`). Lift to `shared/` instead.
7. **Skipping Zod validation on API responses.** The backend can drift; catch it at the boundary.
8. **Putting React Flow node state in Zustand.** Use React Flow's built-in hooks.
9. **Submitting raw React Flow JSON to the backend.** Strip UI-only fields first.
10. **Forgetting loading / error / empty states.** Every async boundary needs all three.
11. **Using `any`.** If TypeScript complains, fix the type, don't bypass it.
12. **Inline arrow functions in JSX props for memoized children.** Breaks memoization.

---

## Adding a new feature — the playbook

1. **Create the folder:** `features/<feature-name>/` with the standard subfolders.
2. **Define types first:** Create `types.ts` and (if needed) `schema.ts` with Zod schemas that mirror the backend.
3. **Write the API layer:** `api.ts` with typed functions using `apiClient`.
4. **Build the hooks:** `hooks/` with TanStack Query wrappers (`useQuery`, `useMutation`).
5. **Build the components:** Start with the dumbest presentational component, wire up behavior via hooks.
6. **Add the route:** Register in `app/router.tsx`, lazy-load if heavy.
7. **Test:** Smoke test via RTL, happy-path E2E.
8. **Accessibility pass:** Tab through every interactive element. Fix what's broken.

---

## Commit & PR conventions

- Conventional Commits (`feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `style:`, `chore:`).
- One feature or fix per PR.
- PR description: what changed, screenshots/GIFs for UI changes, verification steps.
- Run `npm run check` (lint + typecheck + test) locally before pushing.

---

## Tooling commands

| Command | What it does |
|---|---|
| `npm run dev` | Start Vite dev server at `localhost:3000` |
| `npm run build` | Production build to `dist/` |
| `npm run preview` | Serve the production build locally |
| `npm run lint` | ESLint check |
| `npm run format` | Prettier write |
| `npm run typecheck` | `tsc --noEmit` |
| `npm run test` | Vitest in watch mode |
| `npm run test:run` | Vitest single run (for CI) |
| `npm run test:e2e` | Playwright E2E suite |
| `npm run check` | Lint + typecheck + test:run (pre-commit) |

---

## Glossary of shorthand

- **"feature slice"** — a folder under `features/` containing everything for one user-facing feature
- **"the client"** — the Axios instance in `shared/api/client.ts`
- **"the canvas"** — the React Flow surface in `features/design-canvas/`
- **"a node"** — a React Flow node (represents a system component like a load balancer)
- **"the palette"** — the draggable sidebar of component types
- **"the spec"** — `docs/DESIGN.md`
- **"mock auth"** — `VITE_AUTH_MODE=mock`, bypasses MSAL for local dev

---

## When in doubt

- Architectural question? → `docs/DESIGN.md`
- API shape? → `backend/AGENT.md` + backend's OpenAPI at `localhost:8000/docs`
- Component conventions? → this file
- Why a tech was chosen? → `docs/adr/`

If none of those answer your question, pause and ask the human before inventing a pattern.
