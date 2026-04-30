# ADR-004: Two-Layer Rate Limiting (Per-User + Global Cap)

- **Status:** Accepted
- **Date:** 2026-04-29
- **Deciders:** Project owner
- **Related:** ADR-001 (ports & adapters), DESIGN.md §7

---

## Context

The platform uses LLMs in places where cost compounds with traffic — most notably in Batch 4's design-feedback flow, but also (potentially) in any future "AI variation" feature on situation questions. A naive implementation lets a single user, a buggy frontend, or a script kiddie burn through the developer's OpenAI budget.

Rate limits address two distinct concerns:

1. **Fairness / abuse protection** — one user shouldn't dominate the platform's capacity.
2. **Wallet protection** — total spend must be bounded regardless of how many users exist.

These are different problems with different solutions. A per-user limit doesn't help if 200 distinct users each hit the limit on the same day. A global cap doesn't help if a single user with one account refreshes endlessly to deny others.

We need both, and they should compose cleanly without the application code juggling complexity.

---

## Decision

Implement a **two-layer rate limiter** behind a single `RateLimiter` port:

- **Layer 1 — Per-user daily limits.** Counter keyed by `user:{microsoft_oid}:{action}:{YYYY-MM-DD}` (UTC). Each user gets their own bucket per action type per day.
- **Layer 2 — Global daily caps.** Counter keyed by `global:{action}:{YYYY-MM-DD}`. Sum of all users' usage of an action across the platform per day.

Both layers share the same `RateLimiter` port (atomic check-and-increment). The composition lives in a `RateLimitService` that checks **global first, then per-user**, and increments both on success.

### Default limits (configurable via env vars)

| Action                   | Per-user/day | Global/day |
| ------------------------ | ------------ | ---------- |
| Situation question fetch | 5            | 50         |
| Design submission        | 2            | 100        |

### Why "global first, then per-user"

If global is exhausted, we should fail fast — no point checking the user's bucket. Cheaper for the database (one read avoided when the global gate is closed). Users see a friendlier "service is busy today" message rather than "you've used 0/5".

### Why both increment on every successful pass

If both pass, both counters tick up. We don't want a request to spend a global token but not a user token (or vice versa) — the two views must agree.

### Failure mode if a counter increments but the protected work fails

Acceptable trade-off: the user has "spent" a fetch even if the downstream operation crashed. The alternative (transactional rollback of counters) is complex and opens compensating-action bugs. Rate limits are about smoothing demand, not perfect accounting.

### Window: UTC day, resets at midnight UTC

Fixed 24-hour buckets keyed by date. Simpler than sliding windows, easier to reason about as a user ("you have N left today"), and trivially atomic in MongoDB.

---

## Consequences

### Positive

- **One port, two behaviors.** The application layer doesn't see the two-layer structure — it calls `RateLimitService.check_and_consume(action, user_id)` and gets a yes/no with the right error context.
- **Wallet protected.** Even if a misconfigured or malicious frontend issues thousands of requests, the global cap stops outflow at a known multiple of cost-per-call.
- **Fairness preserved.** No single user can starve others by gaming the global pool.
- **Easy to tune.** Limits live in env vars; bumping them up or down is a deploy, not a code change.
- **Easy to monitor.** Telemetry emits a `rate_limit_rejection` metric tagged with layer and action — graphing this in production tells us exactly when limits bite.

### Negative

- **Two counter writes per successful request.** Trivial cost (microseconds per write), but worth noting for very high traffic. We're at <100 requests/day in MVP — irrelevant.
- **Race window between global and per-user check.** A request that passes global at the limit boundary could push global over by one if many requests arrive simultaneously. Acceptable: at 50/day the boundary is a once-per-day event, and the worst case is 51 instead of 50.
- **No grace for verified high-trust users.** Everyone gets the same limit. Future enhancement: a user-level role with higher limits. Out of scope.
- **Coarse granularity.** UTC day means a user in Asia/Tokyo "loses" half their day at midnight Tokyo time. Acceptable for MVP; revisit if user feedback indicates pain.

### Neutral

- **Counter resets via TTL, not a cron job.** Adapters use the storage layer's native expiry (Mongo TTL index, in-memory expiry timestamp). One less moving part.

---

## Implementation outline

### `RateLimiter` port (Batch 1, already exists)

Atomic check-and-increment with a TTL window. Returns a `RateLimitDecision` with `allowed`, `current_count`, `limit`, `remaining`, `reset_in_seconds`.

### `RateLimitService` (Batch 3, new)

Composes the two layers:

1. Compute today's UTC date string.
2. Build keys for global and per-user counters.
3. Call `rate_limiter.check_and_increment` for global. If denied → raise `RateLimitExceeded` with global context.
4. Call same for per-user. If denied → raise `RateLimitExceeded` with per-user context.
5. On success, return both decisions so the API layer can populate `X-RateLimit-Remaining` headers.

### Action enum

`SITUATION_FETCH`, `DESIGN_SUBMISSION` — finite, typed. New actions extend this enum and add their limits to settings.

### API surface

- `GET /api/v1/rate-limits` — informational; returns `peek` values for both layers per action. No counters incremented.
- Protected endpoints (`GET /questions/situation`, future `POST /attempts/design`) call `RateLimitService` via injection. On denial, the domain `RateLimitExceeded` exception propagates and the API exception handler (Batch 2) maps it to `429` with structured detail.

---

## Alternatives considered

### 1. Per-user limit only

- ✅ Simpler — one counter per user.
- ❌ N users × N requests-per-day = unbounded total. Wallet not protected.
- **Rejected.**

### 2. Global cap only

- ✅ Wallet protected.
- ❌ One bad user can starve all others.
- **Rejected.**

### 3. Token bucket / leaky bucket per user

- ✅ Smoother burst handling — short spikes allowed if the bucket has tokens.
- ❌ More complex to implement atomically.
- ❌ Harder to communicate to the user ("you have 3.7 tokens, refilling at 0.4/min").
- ❌ For our use case (5 questions/day), the daily-bucket model fits the human mental model better.
- **Rejected** for MVP. Revisit if real users complain.

### 4. Sliding-window log

- ✅ Most accurate.
- ❌ Storage cost grows with traffic; needs cleanup logic.
- ❌ Overkill for 5/day.
- **Rejected** as YAGNI.

### 5. External rate-limiter service (e.g., Redis with `INCR` + `EXPIRE`)

- ✅ Battle-tested implementations exist.
- ❌ Adds an operational dependency. We already have Mongo (and Redis locally), and the adapter pattern lets us swap if needed.
- **Deferred** — current `MemoryRateLimiter` and the future Mongo-backed Cosmos adapter are sufficient.

### 6. API gateway / WAF rate limiting (e.g., Azure API Management)

- ✅ Offloads the work; battle-tested.
- ❌ Has a non-trivial per-month base cost. We're optimizing for $0.
- ❌ Less granular ("per IP" rather than "per authenticated user").
- **Rejected** for cost.

---

## Open questions

- **When a user logs in for the first time mid-day, do they get a fresh bucket?** Yes — keys are date-scoped, the user's first request creates their bucket on demand. No special handling needed.
- **Should we expose `Retry-After` header on 429s?** Yes — included in the API exception handler. Standard HTTP practice.
- **Should we cache the `GET /rate-limits` response on the frontend?** Short stale time (30s) to keep the UI responsive without hammering the endpoint. TanStack Query's defaults handle this.

---

## References

- DESIGN.md §7 (this repo)
- ADR-001 (ports & adapters) (this repo)
- [RFC 6585 — HTTP 429 Too Many Requests](https://datatracker.ietf.org/doc/html/rfc6585)
