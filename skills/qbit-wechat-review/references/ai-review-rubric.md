# AI Review Rubric

## Goal

Write `AI复盘` that uses data comparison as the clue, then analyzes the article itself for causes, and finally lands the judgment on content choices.

## Required Output

For `文章复盘` self-owned article rows, do not force fixed section labels. Let the model choose the most useful review angles for the article, then present them as a concise numbered list:

```text
1. ...
2. ...
3. ...
```

Do not use the old `优点/缺点` structure. Numbered points are now the default for self-owned article review.

Output roles:

- Start from the metric gap against the fixed historical baseline.
- Use the article body to explain the metric signal.
- End each point on a content-level judgment or concrete content adjustment.
- Keep each numbered point within three sentences when practical.

## Inputs To Consider

- Article title
- Publication time and position, if reliable
- `内容体裁`
- Raw metrics from user-provided screenshots, screenshot OCR, or user-provided tables: reads, likes, comments when available, shares, saves, and `在看数`
- Secondary metrics: `点赞率`, `在看率`, `转发率`, and `内容质量分`
- Fixed historical medians for normal headline articles: load `/Users/lzw/Documents/Lark/exports/qbit-wechat-review/historical-headline-baseline.json` and use `阅读数 R`, `点赞率`, `在看率`, and `转发率` as the first signal layer before analyzing causes. Use a current-batch baseline only when the user explicitly asks for temporary batch comparison.
- Article body from the provided WeChat URL when available
- Repost or media-page body only when WeChat source is missing, inaccessible, or incomplete

## Analysis Principles

- First compare the article against the fixed historical normal-headline median for reading scale, reader recognition, endorsement, and shareability. Name the metric direction before explaining it.
- Tie every point to a concrete content action: title framing, narrative structure, information density, protagonist choice, controversy, utility, emotional hook, timeliness, or ending.
- Give the model room to choose the best analytical frame for the article. The field should be insight-led, not template-led.
- Separate traffic attraction from content recognition. High reads alone do not mean quality.
- Use `点赞率` as reader recognition, `在看率` as endorsement or identity resonance, and `转发率` as shareability or social currency.
- Treat high share rate plus low like or low `在看率` as possible utility/news forwarding, not necessarily deep approval.
- Treat low share rate plus high like or high `在看率` as possible niche resonance or weak distribution hook.
- For people stories, check whether the article makes the person memorable beyond famous-name adjacency.
- For news stories, check whether the article provides context, stakes, and judgment beyond fast information delivery.
- For hands-on tests, check whether the article gives readers useful conclusions, reproducible details, and comparison anchors.
- For humanistic pieces, check whether emotional resonance is supported by concrete scenes instead of abstract praise.
- Include concrete body evidence. Good evidence includes an opening judgment, named person/company/model, concrete number, comparison setup, example scene, section rhythm, or ending call-to-action. Do not quote long passages; paraphrase or quote only short fragments.

## Style

- Write as a compact numbered list.
- Be concise and specific.
- Avoid vague claims like "选题不错" unless followed by the exact reason.
- Mention numbers sparingly; use them to support a judgment, not to restate the table.
- Do not invent facts that are not in the article or data.
- If the WeChat URL is accessible, treat it as the authoritative article context.
- If article matching is uncertain because a repost or media-page source was required, say so in the final response and make the review more cautious.
