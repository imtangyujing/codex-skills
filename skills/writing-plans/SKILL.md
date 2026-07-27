---
name: writing-plans
description: Hand off an approved design or specification directly into implementation without creating a separate implementation plan. Use after brainstorming or design review has produced a user-approved design, or when a user asks to start building from an existing design.
---

# Design-to-Implementation Handoff

Use the approved design as the implementation reference and begin the work directly.

## Core Rule

Do not create another planning layer after design approval.

Never generate:

- detailed implementation-plan documents;
- task-by-task execution scripts;
- per-file change recipes;
- TDD step lists;
- checkbox plans;
- plan-review prompts;
- execution-mode menus.

Codex already knows how to inspect a codebase, choose an implementation order, write tests, and make changes. Preserve context for the implementation itself.

## Workflow

1. Identify the latest design or specification the user approved.
2. Check only for genuine blockers: unresolved product choices, missing authority, unavailable required inputs, or contradictory requirements.
3. If no blocker exists, state briefly that implementation is starting from the approved design.
4. Inspect the relevant code and implement the design.
5. Test in proportion to risk and report the completed result.

Use temporary internal coordination when useful, but do not turn it into a new user-facing or persistent implementation plan.

## When the Design Is Incomplete

Return to the applicable design or brainstorming workflow only when a missing decision would materially change the result. Ask one focused question at a time.

If the user asks for a 「计划」 before design approval, create or refine the design specification. Stop at the design level. Do not expand it into an engineer-by-engineer execution manual.

## Existing Plan Files

Treat previously generated detailed implementation plans as optional historical context. Prefer the approved design specification and current code when they disagree or when the detailed plan adds unnecessary constraints.
