# ADR-005: Submit Diagrams as Structured JSON, Not Images

- **Status:** Accepted
- **Date:** 2026-04-30
- **Deciders:** Project owner
- **Related:** ADR-001 (ports & adapters), ADR-003 (direct OpenAI), DESIGN.md §3.2, §8.2

---

## Context

The design canvas (Batch 4) lets a user drag and connect components on a React Flow surface, then submit the resulting architecture for AI feedback. There are two reasonable ways to send the user's design to the LLM:

1. **As a structured JSON document** describing nodes (id, type, label, position) and edges (from-id, to-id, optional label).
2. **As a rasterized image** (PNG) captured from the canvas.

Both can work. The choice cascades into prompt design, caching strategy, debuggability, and cost.

---

## Decision

Submit the design as **structured JSON**. Specifically: a `Diagram` Pydantic model with `nodes: list[DiagramNode]` and `edges: list[DiagramEdge]`. Frontend serializes from React Flow state, strips UI-only fields (positions, selected/dragging state, render dimensions), validates with Zod, and sends as the request body.

The LLM is given the JSON directly along with the question prompt. It receives no image of any kind.

---

## Consequences

### Positive

- **Caching becomes trivial.** With a structured representation, we can canonically normalize and hash it (sort nodes by `(type, label)`, sort edges by `(source_type, target_type)`, drop UI-only fields, JSON-serialize with sorted keys, SHA-256). Two users who built the same architecture in different layouts produce the same hash and share one cached LLM response. Image-based submission has no equivalent — pixel-level differences (drag a node 5 pixels) would invalidate the cache, even though the design is identical.
- **The LLM's "vision" is more reliable on structured data than images.** Vision models can hallucinate connections, miss small text, or misread arrows in a screenshot. A JSON list of nodes and edges leaves no ambiguity about what the user drew.
- **Cost is roughly 10× lower.** A typical diagram serializes to ~2–5 KB of JSON, costing ~500–1500 tokens. The same diagram as a 1024×768 PNG processed by GPT-4o vision is ~50–100 KB and costs the equivalent of ~5000–8000 tokens for image tiles alone, before the prompt or response.
- **Debuggability.** When something goes wrong, we can read the JSON. It diffs cleanly. We can replay it. An image gives us pixels to squint at.
- **Schema validation at the edge.** Pydantic enforces that submissions have valid node types (from a whitelist), no orphan edges, no excess size. An image bypasses all that — the LLM has to infer shape from rendering.
- **Component highlighting in the response is straightforward.** Feedback can reference nodes by ID (`affected_components: ["node-7"]`), which the frontend maps back to the React Flow node and visually highlights it. With image submission, the LLM would have to describe nodes positionally ("the load balancer in the upper right") and we'd have to fuzzy-match. Brittle.
- **Smaller request bodies = faster, cheaper, more reliable.** Especially relevant for the rate-limited `POST /attempts/design` endpoint where we want submissions to feel instant up to the LLM-call portion.
- **No vision-specific prompt engineering.** Vision prompts have their own quirks (image-first vs text-first, tiling effects, etc.). Text-only is well-understood territory.

### Negative

- **Hand-drawn nuance is lost.** A user can't, e.g., draw a custom shape representing some bespoke component the palette doesn't have. They're constrained to the 14 component types in the palette. We accept this — pedagogically, system design interviews are about _common_ components, not novel ones.
- **No spatial reasoning.** The LLM doesn't know that the user put the cache "next to" the load balancer. It only knows that an edge connects them. In practice, spatial layout in system-design diagrams is documentation, not architecture — it doesn't change correctness. Acceptable loss.
- **Frontend state and submission state must be kept consistent.** The Zod schema has to match the Pydantic schema; the UI-strip step has to be reliable. We test this with an integration test that round-trips a sample diagram. Slight maintenance burden.
- **Screenshots-for-portfolio-share aren't free.** If we ever want a "share my design as an image" feature, we'd need a separate render step (e.g., HTML-to-image library). For MVP this isn't a feature, so it costs nothing.

### Neutral

- **The user's mental model is unchanged.** They still drag boxes and connect them visually. The JSON serialization is invisible to them.

---

## Alternatives considered

### 1. Image submission via GPT-4o vision

- ✅ "Read whatever the user drew."
- ❌ ~10× more expensive per submission.
- ❌ No clean caching primitive.
- ❌ Component highlighting is brittle.
- ❌ Higher hallucination risk.
- **Rejected** — costs and caching are decisive.

### 2. Both — JSON for the LLM, image for caching

- This is incoherent: if we submit JSON, we have everything we need. The image adds nothing.
- **Rejected.**

### 3. JSON + image for the LLM (multimodal)

- ✅ "Belt and suspenders."
- ❌ Doubles the cost without measurable accuracy gain on this task.
- ❌ Adds a vision-call dependency.
- **Rejected** — JSON alone is sufficient.

### 4. A custom DSL (e.g., Mermaid, Graphviz) sent as text

- ✅ More compact than JSON; mature LLM understanding.
- ❌ Adds a serialization step (React Flow JSON → Mermaid).
- ❌ Round-tripping back to React Flow for component highlighting is harder.
- ❌ Mermaid's syntax constrains what can be represented (less flexible than free JSON).
- **Rejected** — JSON gives us the same readability without the round-trip cost.

### 5. JSON via a strictly typed Pydantic model AND a free-text "user notes" field

- ✅ This is what we're doing. The user notes are the escape hatch for nuance the structured form can't capture.
- ✅ Matches situation-practice attempts (Batch 3) — same pattern.
- **Accepted.** This is part of the chosen approach, not an alternative.

---

## Implementation outline

### Frontend (Batch 4)

```ts
const submission = {
  question_id: questionId,
  diagram: {
    nodes: nodes.map((n) => ({
      id: n.id,
      type: n.data.componentType,
      label: n.data.label,
    })),
    edges: edges.map((e) => ({
      id: e.id,
      source_id: e.source,
      target_id: e.target,
    })),
  },
  user_notes: notesText || null,
};
```

UI fields stripped in `useDiagramExport`. Zod validates before POSTing.

### Backend (Batch 4)

- `Diagram` Pydantic model in `core/domain/diagram.py` with size constraints (`max_items=200` on nodes, `max_items=500` on edges).
- `DiagramHashService` normalizes and hashes for cache lookup.
- LLM is given the question prompt + canonical JSON of the diagram in the user message. System prompt tells it to produce structured `DesignFeedback` JSON.

### Prompt shape (excerpt)

````
The user submitted this architecture:

```json
{...diagram JSON...}
````

In response to: {question.prompt}

Their notes: {user_notes or "none provided"}

Produce DesignFeedback JSON matching this schema: {...}

```

---

## Open questions

- **Should we also store the React Flow JSON (with positions) on the `Attempt` record?** Yes — for a future "view past attempt" feature, the user needs to see their original layout. We store both: the canonical (UI-stripped) JSON as `diagram` for the LLM, and the original React Flow state as `submitted_diagram_layout` for visual replay. Adds ~5% storage, not significant.
- **Do we ever want vision-based feedback (e.g., for whiteboard photos)?** Plausibly a stretch feature. Would require a separate `vision_feedback_service` and would not share cache with the JSON path. Out of scope.

---

## References

- DESIGN.md §3.2 (this repo) — request flow for design submission
- DESIGN.md §8.2 (this repo) — diagram hashing
- ADR-003 (this repo) — direct OpenAI choice
- [OpenAI image input pricing](https://platform.openai.com/docs/guides/vision)
```
