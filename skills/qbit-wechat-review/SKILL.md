---
name: qbit-wechat-review
description: 量子位微信公众号内容复盘与同题分析工作流。Use when the user provides 微信公众号文章链接、文章标题、后台数据明细截图/表格、同题三家文章链接，要求读取微信文章正文、导入或更新飞书多维表格、生成多角度 AI 复盘、对比量子位/新智元/机器之心同题文章。
---

# 量子位公众号内容复盘

## Terminology

- **用户指标来源**: user-provided WeChat backend screenshots, screenshot OCR results, or user-provided metric tables. This is the only metric source during ordinary review runs. Credential-based metric retrieval (`wxdown-service`, proxy capture, `getappmsgext`) is offline; do not ask the user to refresh WeChat credentials or provide `app_secret`.
- **ordinary review run**: a standard article review or same-topic analysis session, as opposed to first-run setup or explicit structure changes.

## First-Run Setup

Before the first review run, ensure the local article discovery/body backend is available. Trigger setup when either condition is true:

- `~/Documents/Lark/tools/wechat-article-exporter` is missing.
- `http://127.0.0.1:3000/api/public/v1/download` is unavailable.
- article list auth check at `http://127.0.0.1:3000/api/public/v1/authkey` returns invalid when title-only or same-topic discovery is needed.

→ Read `references/wechat-exporter-backend.md` §First-Run Install and follow it.

After ready, tell the user: `文章列表和正文抓取准备好了，指标请提供后台截图。`

## Entry Points

### Entry A — WeChat Links

When the user provides `mp.weixin.qq.com/s/...` links:

1. Fetch article body/JSON via local backend (see `references/wechat-exporter-backend.md` §Fetch Article Body).
2. Read metrics from **用户指标来源**. Field mapping in `references/metrics-and-schema.md` §Screenshot/Table Field Mapping.
3. Extract `负责人/作者` from body byline (`<name> 发自 ...` → write `<name>`).
4. Upsert Feishu Base record, upload readable Markdown to `附件`, write `AI复盘`.

### Entry B — Title List

When the user provides titles without links:

1. Use local `wechat-article-exporter` account search + article list first (see `references/wechat-exporter-backend.md` §Fetch Account And Article List).
2. Search the likely media account (`量子位` by default; `新智元`/`机器之心` when provided), then match title against returned `appmsgex.title`.
3. Accept only high-confidence matches. If ambiguous, report uncertainty and ask for confirmation.
4. If resolved URL is a WeChat URL → continue with Entry A.
5. If resolved URL is a repost/media page → use for body and attachment only; metrics still require **用户指标来源**.
6. Use ordinary web search only as a fallback when local exporter cannot resolve the article.
7. Do not stop after writing only title/link/date/read count.

### Entry C — Same-Topic Analysis

Use when the user provides one topic plus three links (量子位, 新智元, 机器之心), or when a `同题分析` table row is queued.

Expected chat input:

```text
同题：<topic name>
量子位：https://mp.weixin.qq.com/s/...
新智元：https://mp.weixin.qq.com/s/...
机器之心：https://mp.weixin.qq.com/s/...
```

Workflow:

1. Fetch body for all three links via local backend. Read metrics from **用户指标来源**.
2. Upsert 量子位 article into `文章复盘`.
3. Upsert 新智元 and 机器之心 into `竞品文章池`.
4. Upsert one `同题分析` row, link the three records, write seven `同题统计表` rows and four structured analysis fields.
5. If any link is missing → mark `需确认`, report before writing analysis.

For competitor discovery when links are missing, use local `wechat-article-exporter` account search + article list first with `媒体名 + topic keywords` (e.g. `新智元 Siri Gemini 库克`). Use ordinary web search only as fallback. Treat 搜狗微信 as last fallback due to captcha risk.

**Base queue workflow** and **同题统计表 dimensions/fields** → see `references/metrics-and-schema.md` §Same-Topic V1 Schema.

**Structured analysis fields** on the `同题分析` record:

- `结论摘要`: who performed best, where 量子位 sits. Mention reading scale as context only; main judgment from seven dimensions + secondary metrics.
- `标题差异`: `标题` dimension only. Focus on information density, emotional intensity, core entities, numbers, contrast, share hooks.
- `内容差异`: synthesize `起笔/叙事/证据/扩展/风格`. Use 点赞率 for recognition, 在看率 for endorsement, 转发率 for shareability. Include metric-combination reading (e.g. high reads + low likes).
- `AI复盘`: practical next-step advice for 量子位 only. No repetition of the other three fields.

**Completion checklist:**

1. `文章复盘` has 量子位 article with body, metrics, attachment, `AI复盘`.
2. `竞品文章池` has 新智元 and 机器之心 with body, metrics, attachments, `AI复盘`.
3. `同题统计表` has exactly seven linked rows (`结论/标题/起笔/叙事/证据/扩展/风格`), strongest handling marked `🟨 `.
4. `同题分析` record links all seven stats rows through `统计表`, has all four analysis fields filled.
5. Read back the record and stats rows to verify links and content before reporting done.

## Core Workflow

For any entry point, the end-to-end path is:

1. Read user's data source (Excel/CSV, screenshot OCR, or metric notes) → extract title + raw metrics.
2. Fetch article body via local backend or resolved URL.
3. Read metrics from **用户指标来源**.
4. Extract `负责人/作者` from body byline.
5. Upsert Feishu Base record. Use `文章标题` or `文章链接` as identifier.
6. Upload readable Markdown to `附件`.
7. Let Feishu formulas calculate secondary metrics and `内容质量分`; do not manually write formula fields.
8. Write `AI复盘` per `references/ai-review-rubric.md`.

## AI Review

→ Read `references/ai-review-rubric.md` before writing any `AI复盘`.

Key principle: data comparison gives the clue, the article content explains the cause, the final judgment lands on content choices. Cite specific body evidence; avoid generic claims.

## Field And Metric Rules

→ Read `references/metrics-and-schema.md` before changing fields, formulas, or view order.

Key constraints during ordinary review runs: do not modify Base structure; do not recreate deprecated fields; do not infer `发布位置` from title alone.

## Required Companion Skills

- `lark-base`: Feishu Base structure, fields, views, records, formulas.
- Spreadsheet tooling: parsing `.xls`, `.xlsx`, `.csv`.
- Local `wechat-article-exporter`: account search, article list, article body retrieval.
- Screenshot/OCR or user-provided tables: metrics.
- Web search: title-to-URL resolution and competitor discovery.

## Source Selection And Article Matching

- Prefer user-provided WeChat URL as authoritative source.
- For title lists, resolve via local `wechat-article-exporter` account search + article list before fetching body; use web search only as fallback.
- Accept near matches for punctuation/truncation/headline variants.
- If multiple candidates are plausible, compare publication date, topic entities, and opening paragraphs.
- Record uncertainty instead of pretending the match is exact.
- WeChat covers are authoritative over website covers.
