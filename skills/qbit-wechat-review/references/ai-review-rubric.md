# AI Review Rubric

## Goal

Write `AI复盘` that explains the article from several practical review angles by connecting editorial choices, article content, and performance data.

## Required Output

For `文章复盘` self-owned article rows, always write one card-like text block with exactly these four section labels:

```text
结论摘要：
...

标题分析：
...

内容分析：
...

AI复盘：
...
```

Do not use the old `优点/缺点` structure. Do not write numbered lists such as `1. 2. 3.` inside the field unless the user explicitly asks.

Section roles:

- `结论摘要`: one short paragraph that states the main performance result and likely reason.
- `标题分析`: analyze the title as the entry point. Focus on attention, clarity, novelty, conflict, entities, numbers, and share hook.
- `内容分析`: analyze the body. Focus on opening judgment, main line, information organization, explanation density, examples, rhythm, and value elevation. Cite concrete正文 evidence from the article instead of relying on generic descriptors.
- `AI复盘`: end with practical next-step advice for the next article. State what to keep, what to tighten, and what to move earlier.

## Inputs To Consider

- Article title
- Publication time and position, if reliable
- `内容体裁`
- Raw metrics: reads, likes, comments when available, shares, saves, and `在看数`
- Secondary metrics: `点赞率`, `在看率`, `转发率`, and `内容质量分`
- Batch medians for `阅读数 R`, `点赞率`, `在看率`, and `转发率`; use them as the first signal layer before analyzing causes.
- Article body from the provided WeChat URL when available
- qbitai.com body only when WeChat source is missing, inaccessible, or incomplete

## Analysis Principles

- First compare the article against the current batch median for reading scale, reader recognition, endorsement, and shareability. Name the metric direction before explaining it.
- Tie every point to a concrete content action: title framing, narrative structure, information density, protagonist choice, controversy, utility, emotional hook, timeliness, or ending.
- Separate traffic attraction from content recognition. High reads alone do not mean quality.
- Use `点赞率` as reader recognition, `在看率` as endorsement or identity resonance, and `转发率` as shareability or social currency.
- Treat high share rate plus low like or low `在看率` as possible utility/news forwarding, not necessarily deep approval.
- Treat low share rate plus high like or high `在看率` as possible niche resonance or weak distribution hook.
- For people stories, check whether the article makes the person memorable beyond famous-name adjacency.
- For news stories, check whether the article provides context, stakes, and judgment beyond fast information delivery.
- For hands-on tests, check whether the article gives readers useful conclusions, reproducible details, and comparison anchors.
- For humanistic pieces, check whether emotional resonance is supported by concrete scenes instead of abstract praise.
- For every `内容分析`, include at least two concrete body evidence points. Good evidence includes an opening judgment, named person/company/model, concrete number, comparison setup, example scene, section rhythm, or ending call-to-action. Do not quote long passages; paraphrase or quote only short fragments.

## Style

- Write as compact paragraphs, not a numbered checklist.
- Be concise and specific.
- Avoid vague claims like "选题不错" unless followed by the exact reason.
- Mention numbers sparingly; use them to support a judgment, not to restate the table.
- Do not invent facts that are not in the article or data.
- If the WeChat URL is accessible, treat it as the authoritative article context.
- If article matching is uncertain because qbitai.com fallback was required, say so in the final response and make the review more cautious.
