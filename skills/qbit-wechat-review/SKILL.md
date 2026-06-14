---
name: qbit-wechat-review
description: 量子位微信公众号内容复盘与同题分析工作流。Use when the user provides 微信公众号/量子位文章数据明细 Excel、CSV、文章标题、微信公众号文章链接、同题三家文章链接、qbitai.com 链接，要求读取微信文章正文、导入或更新飞书多维表格、计算内容指标、生成 AI 复盘、沉淀优缺点洞察、对比量子位/新智元/机器之心同题文章。尤其适用于「微信公众号内容复盘」Base、公众号后台数据明细、mp.weixin.qq.com 文章正文读取、量子位官网备用检索、AI 复盘优缺点分析、同题分析。
---

# 量子位公众号内容复盘

## First-Run Setup

Before the first real review run on a new computer, initialize the local WeChat backend.

Trigger this setup when any of these are true:

- `/Users/jay/Documents/Lark/tools/wechat-article-exporter` is missing.
- `/Users/jay/Documents/Lark/tools/wxdown-service` is missing.
- `http://127.0.0.1:3000/api/public/v1/download` is unavailable.
- `127.0.0.1:65000` or `127.0.0.1:65001` cannot listen after starting `wxdown-service`.
- `~/.mitmproxy/mitmproxy-ca-cert.pem` is missing or is not trusted by macOS System Keychain.
- `/Users/jay/Documents/Lark/tools/wxdown-service/resources/data/credentials.json` is missing, empty, expired, or lacks credentials for the target公众号.

Read `references/wechat-exporter-backend.md` and run its `First-Run Install And Credential Warmup` section before continuing.

The default warmup accounts are:

- 量子位: `https://mp.weixin.qq.com/s/xOm_f8iEmdHjiD9v3p3wFg`
- 新智元: `https://mp.weixin.qq.com/s/jqBsN_2UDie47GVQj8L5MQ`
- 机器之心: `https://mp.weixin.qq.com/s/BQbWcPzPKv7gn1sGbR3ixw`

After all three credentials are captured, tell the user: `准备好了，可以开始使用。`

## Qbit-Owned Article Entry Points

For 量子位自有文章, use one of these two fixed entry points.

### Entry A: WeChat Links

When the user provides one or more `mp.weixin.qq.com/s/...` links, treat each link as authoritative and run the complete WeChat article workflow:

1. Fetch article JSON, Markdown/text body, title, author/source, publish metadata, and cover/image context with the local `wechat-article-exporter` backend.
2. Fetch article metrics with the local `wxdown-service` credential backend and `getappmsgext`.
3. Extract `负责人/作者` from the body byline.
4. Update Feishu Base record data, upload the readable Markdown attachment, and write `AI复盘`.

### Entry B: Title List

When the user provides a list of 量子位 article titles without WeChat links, first use the local Official Account backend login session through `wechat-article-exporter` `appmsgpublish` search to resolve each title to its WeChat URL.

- Use date, read count, and publication position only as disambiguation hints.
- Accept only high-confidence title/date matches. If multiple candidates remain plausible, report the uncertainty and ask for confirmation before writing that row.
- After a title is resolved to a WeChat URL, immediately continue with Entry A for body, metrics, author, attachment, and `AI复盘`.
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
- Process each link with the same local WeChat body and metrics path.
- Upsert the 量子位 article into `文章复盘`.
- Upsert 新智元 and 机器之心 articles into `竞品文章池`.
- Upsert one row into `同题分析`, link the three article records, and write structured analysis.
- Upsert six rows into `同题统计表`, one per dimension, linked back to the `同题分析` row through `统计表`.
- If any of the three links is missing or cannot be resolved, mark the same-topic row `需确认` or report the missing account before writing a complete analysis.
- Same-topic competitor discovery should first use ordinary web search with `媒体名 + topic keywords`, for example `新智元 Siri Gemini 库克 WWDC` and `机器之心 Siri Gemini 库克 WWDC`. Prefer public web search results that mirror or reference the original article title, publication date, and media name. Use 搜狗微信 only as a fallback when ordinary web search cannot find plausible candidates.
- When ordinary web search finds a high-confidence competitor title or mirror page but no original WeChat URL, write the candidate title into `入口表`, set `同题状态=需确认`, and ask the user for the original `mp.weixin.qq.com/s/...` link for that media before attempting full metrics or final same-topic analysis.

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

- `统计表`: a real linked stats table with exactly six rows for `标题`, `发布时间`, `阅读数`, `点赞率`, `在看率`, and `转发率`; columns are fixed as 量子位, 新智元, 机器之心. Mark the best value in each comparable row with `🟨 `. 阅读数 is for scale display. 点赞率, 在看率, and 转发率 are the core analysis variables.
- `结论摘要`: one short paragraph that answers who performed best and where 量子位 sits. Mention reading scale only as visible context. The main judgment should come from secondary metrics.
- `标题差异`: analyze only titles. Focus on information density, emotional intensity, core entities, numbers,人物节点, contrast, and share hooks. Connect title choices to reading scale or transferability when useful, but do not analyze正文.
- `内容差异`: analyze body structure and writing strategy. Focus on opening judgment, main line, information organization, explanation density, examples, rhythm, and value elevation. Use 点赞率 for reader recognition, 在看率 for endorsement or identity resonance, and 转发率 for shareability and social currency. Include metric-combination reading, such as high reads with low likes, high shares with lower likes, or high likes with moderate reads.
- `AI复盘`: give practical next-step advice for 量子位 only. Do not repeat the full conclusion, title comparison, or content comparison. State what to keep, what to learn from competitors, how to adjust headline and opening, and how to improve the next article.

Same-topic field division:

- `结论摘要` says the result.
- `标题差异` says the entry point.
- `内容差异` says the body reasons and metric evidence.
- `AI复盘` says what 量子位 should do next.

Same-topic completion checklist:

1. `文章复盘` has the 量子位 article with body, metrics, attachment, and `AI复盘`.
2. `竞品文章池` has 新智元 and 机器之心 article records with body, metrics, attachments, and article-level `AI复盘`.
3. `同题统计表` has exactly six linked rows for `标题`, `发布时间`, `阅读数`, `点赞率`, `在看率`, and `转发率`.
4. The `同题分析` record `统计表` field links all six stats rows.
5. The stats rows link back to the same `同题分析` record through `同题分析记录`.
6. Best comparable values are highlighted with `🟨 ` in `阅读数`, `点赞率`, `在看率`, and `转发率`.
7. `同题分析` has all four structured fields filled: `结论摘要`, `标题差异`, `内容差异`, and `AI复盘`.
8. Before reporting completion, read back the `同题分析` record and the six stats rows to verify links and content.

## Core Workflow

Use the WeChat URL path by default when the user provides `mp.weixin.qq.com/s/...`:

1. Read the user's Excel/CSV data detail file and extract article title plus raw metrics.
2. Use the local `wechat-article-exporter` backend to fetch the WeChat article JSON, Markdown/text body, title, author/source, publish metadata, and cover/image context when available.
3. Use the local `wxdown-service` credential backend to fetch article metrics from `getappmsgext` when metrics are missing or need verification.
4. Extract `负责人/作者` from the first lines of the article body. Match the byline pattern `<name> 发自 ...`, for example `Jay 发自 凹非寺量子位 | 公众号 QbitAI`, and write only `<name>` such as `Jay`. Prefer this body byline over generic WeChat page metadata such as `关注前沿科技`.
5. Update the Feishu Base record for the article. Use `文章标题` or `文章链接` as the practical identifier, depending on available data.
6. Upload the readable article Markdown to the record's `附件` field when the field exists.
7. Let Feishu formulas calculate secondary metrics and `内容质量分`; do not manually write formula fields.
8. Write `AI复盘` with the same practical structure used by same-topic review: start with `结论摘要`, then `标题分析`, then `内容分析`, and end with `AI复盘`.

For 量子位 title-only inputs, use Entry B before considering website fallback. Search qbitai.com only when `appmsgpublish` cannot resolve a reliable WeChat URL or the local WeChat backend cannot fetch a complete body.

Read `references/wechat-exporter-backend.md` before using or changing the WeChat article backend. The validated backend is local `wechat-article-exporter` plus local `wxdown-service`. For 量子位 title-only inputs, local `appmsgpublish` search is used only for link discovery.

## Local WeChat Backend Rules

- Default code path for `mp.weixin.qq.com/s/...`: call the local `wechat-article-exporter` public download API for article body and base JSON.
- Title-only code path for 量子位自有文章: use local `wechat-article-exporter` login state to search `appmsgpublish`, resolve each title to a WeChat URL, then run the same `mp.weixin.qq.com/s/...` workflow.
- Metrics path: use `wxdown-service` credentials for the target公众号, then call `https://mp.weixin.qq.com/mp/getappmsgext` with the captured `key`, `pass_ticket`, `appmsg_token`, and cookie.
- Credentials are公众号-scoped and short-lived, usually about 25-30 minutes. Reuse a valid credential for all articles under the same `__biz`.
- When credentials are missing or expired, automatically run `scripts/auto_refresh_wechat_credentials.py` with the target account names and URLs. This script starts local services, saves current proxy settings, switches Wi-Fi HTTP/HTTPS proxy to `127.0.0.1:65000`, opens the article links in desktop WeChat or the default URL handler, waits for fresh `appmsg_token` values, and restores the saved proxy settings.
- If automatic credential refresh does not produce metrics, if `credentials.json` still contains stale credentials, or if `getappmsgext` returns without `appmsgstat`, actively ask the user to open or refresh the exact article in desktop WeChat. Name the media and title/link that needs action, keep the listener running when practical, and continue metrics collection after the user confirms.
- For same-topic analysis, credential capture is required for all three media before final comparison. If 新智元 or 机器之心 credentials are missing or stale, ask the user for help opening those exact articles; do not silently skip competitor metrics or finish the analysis with only 量子位 data.
- When switching macOS proxy to `127.0.0.1:65000` for credential capture, always restore the prior proxy setting after capture.
- Never paste captured credentials, cookies, `key`, `pass_ticket`, or `appmsg_token` into final answers, skill files, examples, or logs intended for sharing.
- The WeChat Official Account OpenAPI/App Secret path is not part of the default workflow. Do not ask for `app_secret` unless the user explicitly asks to use that path.

Only consider the Official Account OpenAPI path when the user explicitly asks to use it and provides credentials through environment variables or an approved secure channel.

## Required Companion Skills

- Use `lark-base` for Feishu Base structure, fields, views, records, and formulas.
- Use spreadsheet tooling when parsing `.xls`, `.xlsx`, or `.csv` files.
- Use local `wechat-article-exporter`/`wxdown-service` backend when `mp.weixin.qq.com/s/...` is provided.
- For 量子位 title lists, resolve WeChat URLs with local `appmsgpublish` search before article processing.
- For same-topic analysis, use the fixed three-link chat input and write to `文章复盘`, `竞品文章池`, and `同题分析`.
- For same-topic competitor discovery, use ordinary web search first with the media name plus compact topic keywords. Search examples: `新智元 <keyword>`, `机器之心 <keyword>`, `新智元 Siri Gemini 库克`, `机器之心 Siri Gemini 库克`. Treat 搜狗微信 as fallback because it may trigger captcha and slow down the workflow.
- Browse/search qbitai.com only as fallback when `appmsgpublish` cannot find a reliable WeChat URL or the WeChat URL is inaccessible.

## Field And Metric Rules

Read `references/metrics-and-schema.md` before changing fields, formulas, or view order.

Key current rules:

- Do not modify Feishu Base structure unless the user explicitly asks. Default to filling or updating record data only.
- Do not create, delete, rename, reorder, hide, or reformat fields, formulas, tables, views, dashboards, or forms during ordinary review runs.
- Same-topic setup is the explicit exception already approved by the user. After setup, same-topic runs should only fill or update records and upload attachments.
- `内容体裁` is the only content category field.
- Allowed `内容体裁` options: `资讯`, `人物`, `实测`, `人文`.
- Local backend metric mapping: `readNum`/`read_num` -> `阅读数 R`; `oldLikeNum`/`old_like_num` -> `点赞数 L`; `commentNum`/`comment_count` -> `评论数 C`; `shareNum`/`share_num` -> `转发数 S`; `collectNum`/`collect_num` -> `收藏数`; `likeNum`/`like_num` -> `在看数`.
- If the metrics API does not return `comment_count`/`commentNum`, leave `评论数 C` blank. Write `0` only when the source explicitly returns a numeric zero.
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

For 量子位 self-owned article review, write `AI复盘` in this format:

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

`结论摘要` comes first and should state the main result and likely reason in one short paragraph. `标题分析` should connect title choices to traffic and attention. `内容分析` should connect content structure, examples, information density, rhythm, and value elevation to secondary metrics such as 点赞率, 在看率, and 转发率. `AI复盘` should give the final practical recommendation.

Keep `人工复盘` untouched unless the user explicitly provides human notes.

## Source Selection And Article Matching

When matching a data row to an article:

- Prefer the user-provided WeChat URL as the authoritative source for body, title, and cover context.
- For 量子位 self-owned title lists, use local `appmsgpublish` search to resolve the title to a WeChat URL before fetching body and metrics.
- If no WeChat URL can be resolved through `appmsgpublish`, prefer exact title match on qbitai.com as fallback context.
- Accept near matches when punctuation, truncation, or headline variants differ.
- If multiple candidates are plausible, compare publication date, topic entities, and opening paragraphs.
- Record uncertainty in the final response instead of pretending the match is exact.

Website covers may differ from WeChat covers. When a WeChat URL is provided, treat the WeChat page as the more authoritative source for cover and presentation context. Do not treat qbitai.com cover images as authoritative WeChat covers unless the user accepts that limitation.
