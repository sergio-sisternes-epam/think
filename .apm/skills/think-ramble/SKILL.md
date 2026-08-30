---
name: think-ramble
description: Use this skill when the user wants to dump free-form thoughts, half-formed ideas, observations or random notes so they are captured and consolidated into an available store. Trigger on ramble, think-ramble, brain dump, random ideas, capture this, store these thoughts, I’m just thinking out loud. Routes storage through Atlas remember when a store is present.
---

# Think Ramble

Capture unstructured thinking: immutable raw → Atlas remember (when a store is available).

## Process

1. Accept the user’s free-form text (even if messy or incomplete).
2. If a durable store is available, load the skill named **atlas** via the multi-harness substrate contract and follow its `remember` path (prefer light capture; strict if the user asks):
   - Capture the raw text as an experience or suitable typed page
   - Extract key ideas with links as appropriate
   - Leave the store compile-green
   If no store is present, acknowledge the dump in conversation and offer to capture later when a store is available.
3. Confirm briefly what was captured (or that it remains conversation-only); offer grill, challenge, or Medium/Gamma next steps.

## Rules

- Do not polish or invent content.
- Prefer focused pages over one giant dump.
- Never edit raw after write.
- Conversation-only use remains fully supported when no Atlas (or other store) is present.
