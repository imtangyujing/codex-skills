# AI Review Rubric

## Goal

Write `AI复盘` that explains what the article did right or wrong by connecting editorial choices, article content, and performance data.

## Required Output

Always write exactly:

```text
优点：
1. ...
2. ...
3. ...

缺点：
1. ...
2. ...
3. ...
```

No extra sections unless the user asks.

## Inputs To Consider

- Article title
- Publication time and position, if reliable
- `内容体裁`
- Raw metrics: reads, likes, comments, shares, saves, follows, completion rate, average stay time
- Secondary metrics: like rate, comment rate, share rate, content quality score
- Article body from the provided WeChat URL when available
- qbitai.com body only when WeChat source is missing, inaccessible, or incomplete

## Analysis Principles

- Tie every point to a concrete content action: title framing, narrative structure, information density, protagonist choice, controversy, utility, emotional hook, timeliness, or ending.
- Separate traffic attraction from content recognition. High reads alone do not mean quality.
- Treat high share rate plus low like/comment rate as possible utility/news forwarding, not necessarily deep approval.
- Treat low share rate plus high like/comment/completion as possible niche resonance or weak distribution hook.
- For people stories, check whether the article makes the person memorable beyond famous-name adjacency.
- For news stories, check whether the article provides context, stakes, and judgment beyond fast information delivery.
- For hands-on tests, check whether the article gives readers useful conclusions, reproducible details, and comparison anchors.
- For humanistic pieces, check whether emotional resonance is supported by concrete scenes instead of abstract praise.

## Style

- Be concise and specific.
- Avoid vague claims like "选题不错" unless followed by the exact reason.
- Mention numbers sparingly; use them to support a judgment, not to restate the table.
- Do not invent facts that are not in the article or data.
- If the WeChat URL is accessible, treat it as the authoritative article context.
- If article matching is uncertain because qbitai.com fallback was required, say so in the final response and make the review more cautious.
