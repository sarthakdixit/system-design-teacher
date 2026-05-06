# ADR-008: Edge Labels for the Design Canvas

- **Status**: Accepted
- **Date**: 2026-05-06
- **Deciders**: Project owner

## Context

In Batch 5 we hit a recurring failure mode in the AI feedback feature: the LLM generated generic critiques that did not match the candidate's actual diagram. Two specific examples surfaced when a user submitted a URL-shortener architecture:

1. **False "no caching" critique** when the diagram had a Cache node connected on the redirect path.
2. **False "Auth Service on the redirect path" critique** when Auth Service was a sibling route from the API Gateway, not inline on the redirect path.

Diagnosis from the logs: the LLM receives a list of nodes and a list of edges. Each edge is a structural `{source_id, target_id}` pair. There is no way for the LLM to tell what each edge _means_. When an API Gateway fans out to three services, the LLM cannot tell which downstream is the read path, which is the write path, and which is async telemetry. It pattern-matches against training data and frequently lands on the wrong interpretation.

In Batch 5 we worked around this with prompt-engineering tweaks (added a "read each edge as a separate route" section to the system prompt). That helped but is fundamentally a band-aid: we are asking the model to infer information that does not exist in its input.

The proper fix is to give the LLM the missing context: a label on each edge.

## Decision

**Add an optional free-text `label` field to each diagram edge.**

- Type: `string | null`, max 60 characters, no validation beyond length
- Surfaced in the React Flow canvas as a small pill above each edge midpoint
- Editable via a popover when the user clicks an edge
- Sent to the backend in the diagram JSON
- Included in the diagram hash (so labeled vs. unlabeled diagrams cache separately)
- Embedded in the prompt sent to the LLM, with explicit instruction to use them when present
- Backward compatible: existing diagrams with no labels continue to work

## Consequences

### Positive

- **Fixes the root cause of generic AI feedback.** When users label "redirect path" vs. "write path" vs. "analytics fan-out", the LLM's accuracy on architectural critiques rises substantially.
- **Educational value.** Forcing users to think about what an edge represents is itself good system-design practice. A user who cannot label their edges probably cannot defend their design in an interview either.
- **Cheap to implement.** One field on a Pydantic model, one field on the Zod schema, one popover component, one prompt update. ~150 lines across the stack.
- **Backward compatible.** Cached feedback for old (unlabeled) diagrams remains valid. Old attempts in Cosmos remain readable.

### Negative

- **Costs LLM tokens.** Each labeled edge adds ~15 input tokens to the prompt. At 12 edges average and 60-char labels, that is ~180 extra tokens per submission, or about $0.001 in additional GPT-4o cost per submission. Acceptable.
- **Adds a UI surface that users may ignore.** Labels are optional; a user who skips them gets the same Batch-5 feedback quality. We accept this — making them mandatory would be heavier-handed.
- **Slightly larger Cosmos documents.** Negligible.

## Alternatives considered

### Typed labels (predefined taxonomy: read-path, write-path, async, sync, telemetry)

- ✅ Forces consistency; LLM can rely on a fixed vocabulary.
- ❌ The taxonomy is brittle — every new architecture pattern requires extending the enum, and users will reach for "other" or skip labels they cannot fit. Free text is more flexible.
- ❌ Visual treatment becomes more complex (different colors per type, legend, etc.) for marginal benefit.
- **Rejected** for MVP. Could be layered on top of free-text labels later if needed.

### Inferred labels (LLM annotates edges based on node types, user can override)

- ✅ Zero user effort.
- ❌ Pre-call to LLM doubles cost per submission.
- ❌ Inference can be wrong, and a wrong label is worse than no label.
- ❌ Adds a second prompt to maintain.
- **Rejected.** Manual labels are cheaper, more accurate, and pedagogically better.

### Reference architectures (pre-seed each design question with a "good answer" diagram for the LLM to compare against)

- ✅ Best feedback quality, theoretically.
- ❌ Massive content authoring burden (one reference per question, kept in sync with feedback rubric).
- ❌ Anchors the LLM toward a single "right answer" — bad for system-design pedagogy where there are usually several valid answers.
- **Rejected** for portfolio scope. Could be a Batch 7+ stretch.

## Implementation

Touched files:

- `backend/app/api/schemas/diagrams.py` — add `label: str | None = Field(default=None, max_length=60)` to `DiagramEdge`
- `backend/app/core/domain/diagram.py` — same field on the domain model
- `backend/app/core/services/diagram_hash_service.py` — include label in hash inputs
- `backend/app/core/prompts/design_feedback.md` — add guidance on reading labels
- `frontend/src/features/design-canvas/schema.ts` — add `label` to Zod edge schema
- `frontend/src/features/design-canvas/types.ts` — add `label?: string` to Edge type
- `frontend/src/features/design-canvas/components/EdgeLabelEditor.tsx` — new popover component
- `frontend/src/features/design-canvas/components/Canvas.tsx` — render labels, wire editor

## References

- DESIGN.md §15 (Open Questions) — this resolves "extensibility" of edge data
- Batch 5 closeout notes on AI feedback inaccuracies
