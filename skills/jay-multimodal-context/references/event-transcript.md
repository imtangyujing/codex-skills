# Event Transcript

Read this reference when a transcript comes from a salon, meetup, panel, workshop, conference sharing, roadshow, or similar event.

## Segment Classification

Classify segments by function before polishing:

- Venue chatter: logistics, seat changes, microphone checks, greetings, and food plans. Drop these unless they contain substantive industry views, named claims, useful facts, or questions that frame later content.
- Pre-event and post-event side conversations: keep substantive private exchanges as standalone sections, usually titled `#### 会前交流：...` or `#### 会后追问：...`. If a speaker identity is uncertain, label the speaker as `观众` instead of guessing a guest name.
- Host opening and transitions: polish lightly and keep only the framing, topic setup, guest introductions, and section transitions that help the reader understand the event.
- Prepared talks or presentations: preserve the speaker's first-person voice. Do not convert these into third-person summaries and do not invent an interviewer role. Format as `SpeakerName：...` followed by polished first-person paragraphs.
- Roundtables, audience Q&A, and media follow-ups: use the interview-polish Q&A style. Questions may be attributed to the host, `量子位`, `现场提问`, or `观众` when identity is unclear.

## Output Order

Keep the final Markdown in source event order:

1. Substantive pre-event side conversations.
2. Host opening and context.
3. Each guest's prepared talk, with one section per speaker.
4. Roundtable discussion.
5. Audience Q&A.
6. Substantive post-event side conversations or follow-up questions.

## Filename Rules

Use these rules for final Markdown created from salon, meetup, panel, workshop, conference sharing, roadshow, and similar event transcripts.

- Default pattern: `<organizer>-<event-topic>-<YYYYMMDD>.md`.
- Use the organizer, host brand, venue brand, community, or publication as the first field. For Qbit events, use `量子位` when it is the organizer or clear host.
- Use the event theme, series name, session title, or strongest topic label as the second field.
- Use the event date as the date field. If event date is unavailable, use publication date, transcript date, or creation date.
- Keep guest names out of the filename when the event has multiple speakers. Put guest names in the Markdown body or metadata area instead.
- If caller-provided metadata already identifies organizer, topic, and date, use it directly without rereading completed Markdown.
- If the provided output path is temporary or generic, rename the final Markdown according to this rule and return the completed path.
- Clean unsafe filename characters such as slashes, colons, line breaks, and quote marks.

## Speaker Rules

- Do not compress a prepared talk into a third-party recap such as `X提到...` or `X认为...` when the source is the speaker's own presentation.
- Prefer direct first-person polished prose such as `崔昊天：我比较看重...`.
- Do not assign a name to an early or side-channel speaker just because the same speaker number later maps to a named guest.
- Feishu speaker IDs can drift or capture nearby audience conversations. When identity is uncertain, use `观众`.

## Subagent Checks

The polishing subagent should mechanically check event outputs before reporting completion:

- Guest names the user supplied, including exact Chinese characters.
- Residual placeholder labels such as `Speaker 1`.
- Misheard names from transcript captions.
- The user's standing style constraints, such as forbidden sentence patterns and quote style.

The main agent only verifies that the output Markdown file exists unless the user explicitly asks for review, excerpting, or debugging.

## Event Polishing Prompt Template

Use this shape when assigning an event transcript polishing subagent:

```text
Use the interview-polish skill and the event transcript reference to turn <raw transcript path> into polished Chinese media event Markdown.

Skill/reference paths:
references/interview-polish.md
references/event-transcript.md

First read both files in full, then follow their rules exactly. Preserve event order, prepared-talk first-person voice, uncertain-speaker handling, and the event-specific checks.

Output path: <absolute output path>.

Use the event filename rules if the provided output path is temporary or generic. You are only responsible for this file. Do not edit other files. When done, reply with the completed output path only.
```
