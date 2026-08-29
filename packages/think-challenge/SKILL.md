---
name: think-challenge
description: Use this skill when the user wants their ideas challenged with real-world counter-arguments, opposing evidence or critic perspectives found online, so the ideas become stronger. Trigger on challenge this, think-challenge, steel-man the opposition, find counter-arguments, what would critics say, stress-test this idea. Always ground counters in search results. Store lasting conclusions via Atlas remember when useful.
---

# Think Challenge

Act as a rigorous but constructive critic. Search for the strongest real-world counter-arguments, failure cases and opposing viewpoints, then present them clearly so the user can harden their thinking.

## Process

1. Identify the exact idea or claim to challenge (from the current conversation or a named page in an available store).
2. If durable context is needed, load the skill named **atlas** via the multi-harness substrate contract and follow its `query` path (or open the named page directly). Do not invent a parallel query path. If no store is present, work from the conversation only.
3. Formulate 2–4 sharp search queries aimed at:
   - Known criticisms or controversies
   - Documented failures or limitations
   - Alternative approaches that contradict the idea
   - Data or case studies that cut against the claim
4. Perform the searches and extract the strongest, most credible counters (prefer primary sources, reputable analysis, concrete examples).
5. Present the counters in a clear, structured way:
   - State the counter-argument
   - Give the evidence / source
   - Note how serious the challenge appears
6. Optionally persist a short “challenged” note via the multi-harness substrate contract applied to skill **atlas** (load its `remember` path) with links to the original idea.
7. Invite the user to respond, refine, or request a deeper dive on any counter.

## Rules

- Never invent counter-arguments. Every point must be grounded in search results.
- Stay constructive and intellectual — the goal is stronger ideas, not winning a debate.
- Prefer quality over quantity (3–5 strong counters beat 15 weak ones).
- Ground in search; optionally persist conclusions through Atlas (`query` / `remember`) when a store is available.
- Cite sources inline so the user can verify.
- Conversation-only use remains fully supported when no Atlas (or other store) is present.
