---
name: qbit-wechat-review
description: 量子位微信公众号内容复盘工作流。Use when the user provides 微信公众号/量子位文章数据明细 Excel、CSV、文章标题、公众号链接、qbitai.com 链接，要求反查正文、导入或更新飞书多维表格、计算内容指标、生成 AI 复盘、沉淀优缺点洞察。尤其适用于“微信公众号内容复盘”Base、公众号后台数据明细、量子位官网正文检索、AI 复盘优缺点分析。
---

# 量子位公众号内容复盘

## Core Workflow

Use the MVP path by default:

1. Read the user's Excel/CSV data detail file and extract article title plus raw metrics.
2. Search qbitai.com with the article title, find the closest matching original article, and read enough body context for analysis.
3. Update the Feishu Base record for the article. Use `文章标题` or `文章链接` as the practical identifier, depending on available data.
4. Let Feishu formulas calculate secondary metrics and `内容质量分`; do not manually write formula fields.
5. Write `AI复盘` as concise `优点` and `缺点`, exactly three points each.

If a public WeChat article link is provided and accessible, use it as an additional source. If WeChat content is blocked or incomplete, fall back to qbitai.com.

## Do Not Let The API Backup Path Dominate

The WeChat Official Account API path is only a future backup plan. Do not ask for `app_secret`, tokens, cookies, or private credentials during the MVP workflow.

Only consider the API path when the user explicitly asks to use it and provides credentials through environment variables or an approved secure channel. Never paste secrets into code, logs, or skill files.

## Required Companion Skills

- Use `lark-base` for Feishu Base structure, fields, views, records, and formulas.
- Use spreadsheet tooling when parsing `.xls`, `.xlsx`, or `.csv` files.
- Browse/search the web when finding qbitai.com articles or checking current public pages.

## Field And Metric Rules

Read `references/metrics-and-schema.md` before changing fields, formulas, or view order.

Key current rules:

- `内容体裁` is the only content category field.
- Allowed `内容体裁` options: `资讯`, `人物`, `实测`, `人文`.
- Do not recreate `内容类型判断`.
- Do not recreate `点赞评论比` or `转发点赞比`.
- `发布位置` must come from source data, backend order, or user input. Do not infer `头条/次条/三条` from the article title alone.
- `内容质量分` should preserve weighted metric logic and scale to 0-10:
  `MIN((点赞率 * 0.4 + 评论率 * 0.3 + 转发率 * 0.3) * 400, 10)`.

## AI Review Rules

Read `references/ai-review-rubric.md` before writing `AI复盘`.

The review must connect content actions to data results. Avoid generic comments such as "数据表现较好" unless tied to a concrete editorial move.

Format:

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

Keep `人工复盘` untouched unless the user explicitly provides human notes.

## Article Matching

When matching a data row to an article:

- Prefer exact title match on qbitai.com.
- Accept near matches when punctuation, truncation, or headline variants differ.
- If multiple candidates are plausible, compare publication date, topic entities, and opening paragraphs.
- Record uncertainty in the final response instead of pretending the match is exact.

Website covers may differ from WeChat covers. Do not treat qbitai.com cover images as authoritative WeChat covers unless the user accepts that limitation.
