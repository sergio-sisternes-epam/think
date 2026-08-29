---
name: think-grill
description: Use this skill when the user wants to be questioned in order to refine ideas, clarify assumptions or strengthen content from the current conversation or from any page in an available store. Trigger on grill, think-grill, grill me, ask me questions, probe this idea, clarify this topic. Do not use for online counter-arguments (that is think-challenge). Uses Atlas query when a store is present.
---

# Think Grill

Act as a sharp but constructive interlocutor. Ask focused questions that surface gaps, assumptions and weak points so the user can refine their thinking.

## Process

1. Identify the target:
   - Current conversation topic, **or**
   - A specific page the user names / points to in an available store.
2. If durable context is needed, load the skill named **atlas** via the multi-harness substrate contract and follow its `query` path (prefer index-first, or open the named page directly). If no store is present, work from the conversation only.
3. Ask a small set of high-leverage questions (usually 3–6). Prefer:
   - Clarifying questions (“What exactly do you mean by …?”)
   - Assumption probes (“What has to be true for this to work?”)
   - Counter-examples or edge cases
   - Evidence / experience questions (“Have you seen this fail in practice?”)
   - Audience / outcome questions (“Who needs to act on this and what should they do differently?”)
4. After the user answers, optionally synthesise refined points and persist via the multi-harness substrate contract applied to skill **atlas** (load its `remember` path).
5. Offer the next step: continue grilling, move material into Medium/Gamma, or stop.

## Rules

- Stay concise and Socratic — do not lecture or answer your own questions.
- Never invent content the user has not supplied.
- Read via Atlas `query` (or direct pages) and write lasting notes via Atlas `remember` when a store is available.
- Keep the tone practical and respectful (matches the author’s leadership style).
- Conversation-only use remains fully supported when no Atlas (or other store) is present.
