---
name: qbit-wechat-review
description: 量子位微信公众号内容复盘与同题分析工作流。Use when the user provides 微信公众号/量子位文章数据明细 Excel、CSV、文章标题、微信公众号文章链接、同题三家文章链接，要求读取微信文章正文、导入或更新飞书多维表格、计算内容指标、生成多角度卡片式 AI 复盘、对比量子位/新智元/机器之心同题文章。尤其适用于「微信公众号内容复盘」Base、公众号后台数据明细、mp.weixin.qq.com文章正文读取、标题全网检索、同题分析。
---

# 量子位公众号内容复盘

## First-Run Setup

Before the first real review run on a new computer, initialize the local article body backend. The `Hybrid` route keeps article retrieval local and uses user-provided metric screenshots as the default metric source.

Trigger this setup when any of these are true:

- `/Users/jay/Documents/Lark/tools/wechat-article-exporter` is missing.
- `http://127.0.0.1:3000/api/public/v1/download` is unavailable.

Read `references/wechat-exporter-backend.md` and run its article-exporter setup section before continuing.

The credential capture route using `wxdown-service`, proxy capture, and `getappmsgext` is temporarily offline. Do not ask the user to refresh WeChat credentials during ordinary review runs.

After the article body backend is available, tell the user: `正文抓取准备好了，指标请提供后台截图。`

## Qbit-Owned Article Entry Points

For 量子位自有文章, use one of these two fixed entry points.

### Entry A: WeChat Links

When the user provides one or more `mp.weixin.qq.com/s/...` links, treat each link as authoritative and run the complete WeChat article workflow:

1. Fetch article JSON, Markdown/text body, title, author/source, publish metadata, and cover/image context with the local `wechat-article-exporter` backend.
2. Read article metrics from user-provided WeChat backend screenshots or user-provided metric tables. Do not fetch metrics with credentials by default.
3. Extract `负责人/作者` from the body byline.
4. Update Feishu Base record data, upload the readable Markdown attachment, and write `AI复盘`.

### Entry B: Title List

When the user provides article titles without WeChat links, first use ordinary web search to resolve each title to an article URL.

- Use date, read count, and publication position only as disambiguation hints.
- Accept only high-confidence title/date matches. If multiple candidates remain plausible, report the uncertainty and ask for confirmation before writing that row.
- Take the first usable high-confidence search result as the body source. If the first result is blocked, unreadable, or clearly mismatched, record that failure and try the next result.
- Prefer results from 量子位, 机器之心, 新智元, or established repost platforms that clearly preserve the original title and source.
- If the resolved URL is a WeChat URL, immediately continue with Entry A for body, metrics, author, attachment, and `AI复盘`.
- If the resolved URL is a repost or media page, use it for body context and attachment only. Metrics still require user-provided screenshots or user-provided metric tables.
- Do not stop after creating or updating rows with only title, link, date, and read count.

## Same-Topic Analysis Entry Point

Use same-topic analysis when the user provides one topic name plus links for the three fixed accounts: 量子位, 新智元, and 机器之心, or when a queued row in the Feishu Base `同题分析` table is marked for processing.

Expected input:

```text
同题：<topic name>
量子位：https://mp.weixin.qq.com/s/...
新智元：https://mp.weixin.qq.com/s/...
机器之心：https://mp.weixin.qq.com/s/...
```

V1 rules:

- The three media are fixed: 量子位, 新智元, 机器之心.
- Treat all three WeChat links as authoritative. Do not use `appmsgpublish` for 新智元 or 机器之心.
- Process each link with the same local WeChat body path and user-provided screenshot metrics path.
- Upsert the 量子位 article into `文章复盘`.
- Upsert 新智元 and 机器之心 articles into `竞品文章池`.
- Upsert one row into `同题分析`, link the three article records, and write structured analysis.
- Upsert seven rows into `同题统计表`, one per analysis dimension, linked back to the `同题分析` row through `统计表`.
- If any of the three links is missing or cannot be resolved, mark the same-topic row `需确认` or report the missing account before writing a complete analysis.
- Same-topic competitor discovery should first use ordinary web search with `媒体名 + topic keywords`, for example `新智元 Siri Gemini 库克 WWDC` and `机器之心 Siri Gemini 库克 WWDC`. Prefer public web search results that mirror or reference the original article title, publication date, and media name. Use 搜狗微信 only as a fallback when ordinary web search cannot find plausible candidates.
- When ordinary web search finds a high-confidence competitor title or mirror page but no original WeChat URL, write the candidate title into `入口表`, set `同题状态=需确认`, and ask the user for the original `mp.weixin.qq.com/s/...` link plus metric screenshots for that media before attempting final same-topic analysis.

### Base Queue Entry

The same-topic queue is implemented in `/Users/jay/Documents/dev/Feishu/scripts/run_same_topic_queue.py`.

The `同题分析` table has these entry/trigger fields:

- `同题名称`
- `同题状态`
- `量子位文章`
- `入口表`
- `统计表`

The `入口表` table is the table-form discovery surface. It stores one row per media source with:

- `媒体来源`
- `文章标题`
- `文章链接`
- `同题分析记录`

Use the queue when the user wants a Base-driven or button-driven workflow:

1. In `同题分析`, associate the existing `量子位文章`.
2. A Feishu button should set `同题状态=待处理`. Directly setting `同题状态=待处理` is also valid.
3. Run `python3 scripts/run_same_topic_queue.py run-queue --limit 10` manually or from the local LaunchAgent.
4. If 新智元 or 机器之心 links are missing, the script reads the linked 量子位 article, fills the 量子位 row in `入口表`, searches ordinary web results with `媒体名 + keywords` for competitor candidate titles, writes the competitor rows, and sets `同题状态=需确认`.
5. The user pastes original `mp.weixin.qq.com/s/...` links into the matching 新智元 and 机器之心 rows in `入口表`.
6. Clicking the button again sets `同题状态=待处理`; the script then runs the complete same-topic workflow and sets `同题状态=已完成`.

The Base button itself is configured in Feishu UI as an action that modifies the current record. The local script treats `同题状态=待处理` as the trigger signal.

Structured same-topic analysis fields:

- `统计表`: a real linked stats table with exactly seven rows for `结论`, `标题`, `起笔`, `叙事`, `证据`, `扩展`, and `风格`; columns are fixed as 量子位, 新智元, 机器之心. Each cell should be a compact qualitative judgment for that media's handling of the dimension. Mark the strongest or most transferable handling in each comparable row with `🟨 `. Use阅读数、点赞率、在看率和转发率 as supporting evidence inside the relevant cells, not as separate dimension rows.
- `结论摘要`: one short paragraph that answers who performed best and where 量子位 sits. Mention reading scale only as visible context. The main judgment should come from the seven dimensions and secondary metrics together.
- `标题差异`: analyze only the `标题` dimension. Focus on information density, emotional intensity, core entities, numbers,人物节点, contrast, and share hooks. Connect title choices to reading scale or transferability when useful, but do not analyze正文.
- `内容差异`: synthesize the `起笔`, `叙事`, `证据`, `扩展`, and `风格` dimensions. Focus on opening judgment, main line, information organization, explanation density, examples, rhythm, and value elevation. Use 点赞率 for reader recognition, 在看率 for endorsement or identity resonance, and 转发率 for shareability and social currency. Include metric-combination reading, such as high reads with low likes, high shares with lower likes, or high likes with moderate reads.
- `AI复盘`: give practical next-step advice for 量子位 only. Do not repeat the full conclusion, title comparison, or content comparison. State what to keep, what to learn from competitors, how to adjust headline and opening, and how to improve the next article.

Same-topic field division:

- `结论摘要` says the result and corresponds to the `结论` row.
- `标题差异` says the entry point and corresponds to the `标题` row.
- `内容差异` says the body reasons and metric evidence, covering `起笔`, `叙事`, `证据`, `扩展`, and `风格`.
- `AI复盘` says what 量子位 should do next.

Same-topic completion checklist:

1. `文章复盘` has the 量子位 article with body, user-provided screenshot metrics, attachment, and `AI复盘`.
2. `竞品文章池` has 新智元 and 机器之心 article records with body, user-provided screenshot metrics, attachments, and article-level `AI复盘`.
3. `同题统计表` has exactly seven linked rows for `结论`, `标题`, `起笔`, `叙事`, `证据`, `扩展`, and `风格`.
4. The `同题分析` record `统计表` field links all seven stats rows.
5. The stats rows link back to the same `同题分析` record through `同题分析记录`.
6. The strongest or most transferable handling is highlighted with `🟨 ` in each comparable dimension row.
7. `同题分析` has all four structured fields filled: `结论摘要`, `标题差异`, `内容差异`, and `AI复盘`.
8. Before reporting completion, read back the `同题分析` record and the seven stats rows to verify links and content.

## Core Workflow

Use the WeChat URL path by default when the user provides `mp.weixin.qq.com/s/...`:

1. Read the user's Excel/CSV data detail file, screenshot OCR result, or screenshot-derived metric notes and extract article title plus raw metrics.
2. Use the local `wechat-article-exporter` backend to fetch the WeChat article JSON, Markdown/text body, title, author/source, publish metadata, and cover/image context when available.
3. Use user-provided WeChat backend screenshots as the default source for article metrics. If metrics are missing, ask for screenshots or a metric table instead of refreshing credentials.
4. Extract `负责人/作者` from the first lines of the article body. Match the byline pattern `<name> 发自 ...`, for example `Jay 发自 凹非寺量子位 | 公众号 QbitAI`, and write only `<name>` such as `Jay`. Prefer this body byline over generic WeChat page metadata such as `关注前沿科技`.
5. Update the Feishu Base record for the article. Use `文章标题` or `文章链接` as the practical identifier, depending on available data.
6. Upload the readable article Markdown to the record's `附件` field when the field exists.
7. Let Feishu formulas calculate secondary metrics and `内容质量分`; do not manually write formula fields.
8. Write `AI复盘` as a concise numbered review. Use metric comparison as the clue, then analyze the article itself for causes, and make the final landing point the content.

For title-only inputs, use Entry B's ordinary web search path. Do not use any fixed official-site path.

Read `references/wechat-exporter-backend.md` before using or changing the WeChat article backend. The validated body backend is local `wechat-article-exporter`; metrics come from screenshots or user-provided tables. For title-only inputs, ordinary web search is used for URL discovery.

## Local WeChat Backend Rules

- Default code path for `mp.weixin.qq.com/s/...`: call the local `wechat-article-exporter` public download API for article body and base JSON.
- Title-only code path: use ordinary web search, take the first usable high-confidence result, then fetch body from that result. Use the local WeChat workflow only after a WeChat URL is resolved.
- Metrics path: use user-provided WeChat backend screenshots or user-provided metric tables by default.
- Credential-based metrics through `wxdown-service`, proxy capture, and `getappmsgext` are temporarily offline for this `Hybrid` branch.
- Do not run `scripts/auto_refresh_wechat_credentials.py` during ordinary review runs.
- Do not ask the user to open articles in desktop WeChat for credential capture.
- The WeChat Official Account OpenAPI/App Secret path is not part of the `Hybrid` workflow. Do not ask for `app_secret`.

Only revisit credential-based or OpenAPI metric retrieval if the user explicitly asks to bring that route back online.

## Required Companion Skills

- Use `lark-base` for Feishu Base structure, fields, views, records, and formulas.
- Use spreadsheet tooling when parsing `.xls`, `.xlsx`, or `.csv` files.
- Use local `wechat-article-exporter` for article body retrieval when `mp.weixin.qq.com/s/...` is provided.
- Use screenshot/OCR or user-provided tables for metrics.
- For title lists, resolve article URLs through ordinary web search before article processing.
- For same-topic analysis, use the fixed three-link chat input and write to `文章复盘`, `竞品文章池`, and `同题分析`.
- For same-topic competitor discovery, use ordinary web search first with the media name plus compact topic keywords. Search examples: `新智元 <keyword>`, `机器之心 <keyword>`, `新智元 Siri Gemini 库克`, `机器之心 Siri Gemini 库克`. Treat 搜狗微信 as fallback because it may trigger captcha and slow down the workflow.

## Field And Metric Rules

Read `references/metrics-and-schema.md` before changing fields, formulas, or view order.

Key current rules:

- Do not modify Feishu Base structure unless the user explicitly asks. Default to filling or updating record data only.
- Do not create, delete, rename, reorder, hide, or reformat fields, formulas, tables, views, dashboards, or forms during ordinary review runs.
- Same-topic setup is the explicit exception already approved by the user. After setup, same-topic runs should only fill or update records and upload attachments.
- `内容体裁` is the only content category field.
- Allowed `内容体裁` options: `资讯`, `人物`, `实测`, `人文`.
- Screenshot/table metric mapping: `阅读`/`阅读数` -> `阅读数 R`; `点赞`/`点赞数` -> `点赞数 L`; `评论`/`评论数` -> `评论数 C`; `分享`/`转发`/`转发数` -> `转发数 S`; `收藏`/`收藏数` -> `收藏数`; `在看`/`在看数` -> `在看数`.
- If the screenshot or user-provided table does not show `评论数 C`, leave `评论数 C` blank. Write `0` only when the source explicitly shows a numeric zero.
- When `评论数 C` is blank, do not mention zero comments or zero comment rate in `AI复盘`; describe the metric as unavailable if needed.
- Do not create or maintain `新增关注`, `平均停留时长(秒)`, or `完读率` for this Base workflow.
- Use `在看率` instead of `评论率`; formula is `在看数 / 阅读数 R`.
- Do not recreate `内容类型判断`.
- Do not recreate `点赞评论比` or `转发点赞比`.
- `发布位置` must come from source data, backend order, or user input. Do not infer `头条/次条/三条` from the article title alone.
- `内容质量分` should preserve weighted metric logic and scale to 0-10:
  `MIN((点赞率 * 0.4 + 在看率 * 0.3 + 转发率 * 0.3) * 400, 10)`.

## AI Review Rules

Read `references/ai-review-rubric.md` before writing `AI复盘`.

The review must connect content actions to data results. Avoid generic comments such as 「数据表现较好」 unless tied to a concrete editorial move.

Before writing `AI复盘`, load the fixed historical baseline for normal headline articles, currently stored at `/Users/lzw/Documents/Lark/exports/qbit-wechat-review/historical-headline-baseline.json`. This baseline uses only `发布位置=头条` normal content rows, excludes abnormal traffic entries such as recruitment, submission, event, summit, signup, and campaign posts, and keeps normal 10万+ headline hits because the median is robust to capped爆款. Use the fixed medians for `阅读数 R`, `点赞率`, `在看率`, and `转发率` as the first signal layer. Only use a current-batch baseline when the user explicitly asks for a temporary batch comparison.

After deriving the metric signal, analyze the article at a concrete body level. The core route is: data comparison gives the clue, the article content explains the cause, and the final judgment lands back on content choices. Cite specific正文 evidence such as the opening judgment, a named example, a key contrast, a concrete scene, a data point, a structure choice, or a memorable phrase from the body. Avoid generic claims such as 「信息密度高」 unless followed by the actual information pattern or example.

For 量子位 self-owned article review, do not force fixed section labels such as `结论摘要/标题分析/内容分析/AI复盘`. Let the model use its judgment to decide the most useful angles for the article. Present the result as a numbered list:

```text
1. ...
2. ...
3. ...
```

Each numbered point should normally be no more than three sentences. Write clearly and compactly, with no filler. Prefer points that answer: what the data says, what in the content caused it, and what the next version should change in the content itself.

Keep `人工复盘` untouched unless the user explicitly provides human notes.

## Source Selection And Article Matching

When matching a data row to an article:

- Prefer the user-provided WeChat URL as the authoritative source for body, title, and cover context.
- For title lists, use ordinary web search to resolve the title to the first usable high-confidence article URL before fetching body context.
- If the resolved URL is a repost or media page, use it only as body context and report the source limitation.
- Accept near matches when punctuation, truncation, or headline variants differ.
- If multiple candidates are plausible, compare publication date, topic entities, and opening paragraphs.
- Record uncertainty in the final response instead of pretending the match is exact.

Website covers may differ from WeChat covers. When a WeChat URL is provided, treat the WeChat page as the more authoritative source for cover and presentation context. Do not treat repost or media-site cover images as authoritative WeChat covers unless the user accepts that limitation.
