# Event Transcript

Read this reference when a transcript comes from a salon, meetup, panel, workshop, conference sharing, roadshow, or similar event.

## Segment Classification

Classify segments by function before polishing:

- Venue chatter: logistics, seat changes, microphone checks, greetings, and food plans. Drop these unless they contain substantive industry views, named claims, useful facts, or questions that frame later content.
- Pre-event and post-event side conversations: keep substantive private exchanges as standalone sections with localized headings carrying the meaning of pre-event exchange or post-event follow-up. If a speaker identity is uncertain,use the localized generic audience label instead of guessing a guest name.
- Host opening and transitions: polish lightly and keep only the framing, topic setup, guest introductions, and section transitions that help the reader understand the event.
- Prepared talks or presentations: preserve the speaker's first-person voice. Do not convert these into third-person summaries and do not invent an interviewer role. Format as `SpeakerName：...` followed by polished first-person paragraphs.
- Roundtables,audience Q&A,and media follow-ups: use the interview-polish Q&A style. Generic host,on-site question,and audience labels follow `output_language`;proper media and speaker names retain their canonical forms.

## Output Order

Keep the final Markdown in source event order:

1. Substantive pre-event side conversations.
2. Host opening and context.
3. Each guest's prepared talk, with one section per speaker.
4. Roundtable discussion.
5. Audience Q&A.
6. Substantive post-event side conversations or follow-up questions.

## Final Filename Entry

Before choosing or changing a final Markdown filename,read and apply the `Final Filename Contract` in `references/article-note.md`. Do not restate or override naming rules here. If caller-provided metadata already identifies the first-hand source,primary topic,source date,and date source,pass those values directly into the contract.

## Speaker Rules

- Do not compress a prepared talk into a third-party recap such as `X提到...` or `X认为...` when the source is the speaker's own presentation.
- Prefer direct first-person polished prose such as `崔昊天：我比较看重...`.
- Do not assign a name to an early or side-channel speaker just because the same speaker number later maps to a named guest.
- Feishu speaker IDs can drift or capture nearby audience conversations. When identity is uncertain, use `观众`.

## Source Owner Checks

The current source owner should mechanically check event outputs before reporting completion:

- Guest names the user supplied, including exact Chinese characters.
- Residual placeholder labels such as `Speaker 1`.
- Misheard names from transcript captions.
- The user's standing style constraints, such as forbidden sentence patterns and quote style.

In batch mode,the coordinator only verifies that the output Markdown file exists unless the user explicitly asks for review,excerpting,or debugging.

## Event Owner Contract

The same source owner that acquired or received the event transcript must polish and package it:

```text
Use the interview-polish rules and the event transcript reference to turn <converted transcript path> into polished media event Markdown in <output_language>.

Skill/reference paths:
references/interview-polish.md
references/event-transcript.md
references/article-note.md

First read both files in full,then follow their rules exactly. Preserve event order,prepared-talk first-person voice,uncertain-speaker handling,and the event-specific checks. Use localized headings and generic speaker labels while preserving canonical proper names.

Output path: <absolute output path>.

Use the Final Filename Contract in article-note.md if the provided output path is temporary or generic. You are only responsible for this source. Do not call spawn_agent or delegate polishing,note packaging,or validation. When done,return the completed output path or the batch Worker Result JSON.
```
