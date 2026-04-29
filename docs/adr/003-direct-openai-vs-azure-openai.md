# ADR-003: Direct OpenAI API over Azure OpenAI Service

- **Status:** Accepted
- **Date:** 2026-04-21
- **Deciders:** Project owner
- **Related:** ADR-001 (ports & adapters), DESIGN.md §4.3, §9, §14

---

## Context

The platform uses LLMs in two places: generating reference answers for situation questions (one-time, during seeding) and producing structured feedback on user-submitted system designs (per request, the headline feature). Both currently target OpenAI's `gpt-4o` and `gpt-4o-mini`.

The platform deploys to Azure for production. There are two ways to consume those models on Azure:

1. **Direct OpenAI API** — call `api.openai.com` from code running on Azure. Same SDK, same models, same auth (API key).
2. **Azure OpenAI Service** — Microsoft-hosted deployment of OpenAI models, accessed via an Azure-region endpoint with managed identity or key-based auth. Different SDK initialization, slightly different request shape, models accessed by _deployment name_ rather than model id.

Both are "AI/ML on Azure" from a portfolio standpoint — a recruiter reading the README sees Azure infrastructure either way. The decision only affects how LLM calls are routed.

---

## Decision

Use the **direct OpenAI API** as the primary LLM provider. Calls go to `api.openai.com` regardless of where the backend is hosted. The `LLMProvider` port (ADR-001) means we can add an Azure OpenAI adapter later without touching business logic — the choice is reversible.

### What this means concretely

- Batch 4 implements `OpenAILLMProvider` (a single adapter) that calls OpenAI directly via `httpx`.
- Production reads `OPENAI_API_KEY` from Azure Key Vault. Same code path locally and in production.
- The DI container does not branch on environment for the LLM port — both `local` and `azure` resolve to the same `OpenAILLMProvider`. (Other ports DO branch. The LLM is the exception.)
- A future `AzureOpenAILLMProvider` adapter can be added in a day if the trade-offs shift.

---

## Consequences

### Positive

- **No approval friction.** Azure OpenAI Service requires per-subscription approval (a form, a review, can take days to weeks). The direct API requires only an OpenAI account and a credit card. For a portfolio project on a 1-month timeline, this matters.
- **Simpler billing.** OpenAI usage shows up on one OpenAI bill. No Azure resource to provision, monitor, or pay for separately. Wallet protection lives in our application logic (rate limits + caching) regardless.
- **Faster local iteration.** Same endpoint locally and in production means no "works on Azure, fails locally" surprises caused by deployment-name mismatches or region issues.
- **Latest models on launch day.** OpenAI ships new models on its API the day they're announced. Azure OpenAI typically lags by weeks for parity. For a learning project this matters.
- **Portability.** If we ever migrate off Azure (say, to Cloudflare Workers + R2), the LLM call doesn't change at all.
- **Smaller blast radius.** One credential to manage (`OPENAI_API_KEY`). Azure OpenAI adds a tenant + region + deployment name + Key Vault reference — more moving parts for the same outcome.

### Negative

- **Egress cost from Azure.** Calls leave the Azure data center to reach `api.openai.com`. For our traffic volume (rate-limited to ~100 design submissions/day globally) the egress cost is negligible — pennies/month. At scale this would matter.
- **No "data stays in Azure" story.** Some enterprises mandate that prompt content not leave Azure boundary. Not relevant for this portfolio project; would be a hard blocker for some real customers.
- **No managed-identity auth.** API key is the only option, stored in Key Vault. Azure OpenAI supports passwordless auth via managed identity, which is genuinely better for production. We accept this trade-off.
- **No SLA-tied-to-Azure-account.** Azure OpenAI gets credited if you hit your Azure SLA. OpenAI's API has its own SLA, separate. Negligible at our scale.

### Neutral

- **Same Pydantic schemas, same prompt templates.** The OpenAI SDK and Azure OpenAI SDK accept the same message shapes and return the same response shapes — abstraction at the port level papers over the small differences.

---

## Alternatives considered

### 1. Azure OpenAI Service from day one

- ✅ Cleaner "fully on Azure" story for a recruiter.
- ✅ Managed identity auth is genuinely nicer than API keys.
- ❌ Approval delay risks the 1-month timeline.
- ❌ Models trail OpenAI's by weeks.
- ❌ Adds Azure resource to provision, monitor, and pay for (even at $0 with free tier, more cognitive load).
- **Rejected** for the timeline and approval-risk reasons. May revisit in Batch 5+ if approval lands quickly.

### 2. Anthropic Claude (or another provider) via the same port

- ✅ Cheaper for some prompt sizes; competitive quality.
- ✅ Demonstrates port abstraction working across providers.
- ❌ Adds a credential and a vendor relationship for no functional gain in MVP.
- ❌ Loses the "OpenAI integration" resume keyword that hiring managers recognize fastest.
- **Rejected** for MVP. Trivial to add as a second adapter later if we want a head-to-head comparison.

### 3. Self-hosted open-source model (Ollama / vLLM on a VM)

- ✅ Zero per-token cost.
- ✅ Maximum portability.
- ❌ Quality gap on system-design feedback is significant for current open-source models.
- ❌ Self-hosting cost (a GPU VM) far exceeds what API calls would cost at our volume.
- ❌ Operational overhead — model updates, monitoring, scaling.
- **Rejected** as cost-negative and quality-negative at our scale.

### 4. Both providers behind a feature flag

- ✅ Maximum optionality.
- ❌ Two adapters to maintain, two credentials, two test paths.
- ❌ YAGNI for MVP — pick one, swap if needed.
- **Rejected** as premature abstraction. The port already gives us swap-ability.

---

## Open questions

- **When (if ever) do we add the Azure OpenAI adapter?** Trigger conditions worth watching:
  - A real enterprise wants their data to stay in Azure boundary.
  - Egress cost becomes meaningful (would need ~100x current traffic).
  - Direct OpenAI's API has an outage and Azure OpenAI doesn't (uncorrelated failures argue for both).
  - Azure OpenAI Service ships a feature direct OpenAI doesn't have (unlikely).
- **Do we cache embeddings** if/when we add semantic search to find similar past attempts? _(Out of scope for MVP.)_

---

## References

- [OpenAI API documentation](https://platform.openai.com/docs/)
- [Azure OpenAI Service documentation](https://learn.microsoft.com/azure/ai-services/openai/)
- ADR-001 (this repo) — ports & adapters
- DESIGN.md §9 (this repo) — LLM integration
