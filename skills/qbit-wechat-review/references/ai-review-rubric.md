# AI Review Rubric

## Goal

Write `AI复盘` that uses data comparison as the clue, analyzes the article for causes, and lands the judgment on content choices.

## Historical Baseline

Before writing, load `~/Documents/Lark/exports/qbit-wechat-review/historical-headline-baseline.json`. This baseline uses only `发布位置=头条` normal content rows (excluding recruitment, event, campaign posts), keeps normal 10万+ hits because the median is robust. Use the fixed medians for `阅读数 R`, `点赞率`, `在看率`, `转发率` as the first signal layer. Only use a current-batch baseline when the user explicitly asks.

## Output Format

For `文章复盘` self-owned articles, do not force fixed section labels. Present as a concise numbered list:

```text
1. ...
2. ...
3. ...
```

Each point: normally ≤ 3 sentences. Answer: what the data says, what in the content caused it, what the next version should change.

## Analysis Route

1. Start from the metric gap against the fixed historical baseline. Name the direction before explaining it.
2. Use the article body to explain the metric signal.
3. End each point on a content-level judgment or concrete adjustment.

## Inputs To Consider

- Title, publication time/position, `内容体裁`
- Raw metrics from **用户指标来源**: reads, likes, comments (when available), shares, saves, `在看数`
- Secondary metrics: `点赞率`, `在看率`, `转发率`, `内容质量分`
- Historical baseline medians
- Article body (WeChat URL preferred; repost/media-page body only as fallback)

## Analysis Principles

- Separate traffic attraction from content recognition. High reads alone ≠ quality.
- `点赞率` = reader recognition; `在看率` = endorsement/identity resonance; `转发率` = shareability/social currency.
- High share + low like/在看 → possible utility/news forwarding, not necessarily approval.
- Low share + high like/在看 → possible niche resonance, weak distribution hook.
- Genre-specific checks: people stories (memorable beyond famous-name adjacency), news (context/stakes/judgment beyond fast delivery), hands-on tests (useful conclusions/reproducible details/comparison anchors), humanistic pieces (concrete scenes over abstract praise).
- Cite concrete body evidence: opening judgment, named entity, number, comparison setup, section rhythm, ending CTA. Paraphrase or quote only short fragments.
- Tie every point to a concrete content action.

## Style

- Compact numbered list, concise and specific.
- Avoid vague claims like "选题不错" unless followed by the exact reason.
- Use numbers to support judgments, not to restate the table.
- Do not invent facts not in the article or data.
- If article matching used a repost/media-page source, say so and be more cautious.
- Keep `人工复盘` untouched unless the user explicitly provides human notes.
