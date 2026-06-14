# Metrics And Base Schema

## Main Base

Current target Base:

- Base: `微信公众号内容复盘`
- Base token: `YSItbTTRMaMioBsYBQrcKu1znFh`
- Table: `文章复盘`
- Table ID: `tblcDbhMFaYWfdEu`
- Competitor table: `竞品文章池`
- Competitor table ID: `tbl8WwB6ant8NeQ1`
- Same-topic table: `同题分析`
- Same-topic table ID: `tblx2Kuzvm5KMi0E`
- Same-topic stats table: `同题统计表`
- Same-topic stats table ID: `tblxmGa9SxhxEoCp`

If the user provides a different Base URL or token, use the provided target instead of hardcoding any previous token.

## Modification Boundary

During ordinary review runs, only fill or update record data.

Do not modify the Feishu Base structure unless the user explicitly asks. This includes creating, deleting, renaming, reordering, hiding, or reformatting fields, formulas, tables, views, dashboards, or forms.

The approved same-topic V1 setup created `竞品文章池`, `同题分析`, and `同题分析看板`. Future same-topic runs should treat the structure as fixed and only upsert records, upload attachments, and write analysis fields unless the user explicitly asks for another structure change.

## Field Order

Current daily visible order:

1. `文章标题`
2. `发布时间`
3. `文章链接`
4. `负责人/作者`
5. `发布位置`
6. `内容体裁`
7. `选题标签`
8. `阅读数 R`
9. `点赞率`
10. `在看率`
11. `转发率`
12. `内容质量分`
13. `同题分析`
14. `AI复盘`
15. `人工复盘`
16. `附件`

Daily views should hide raw interaction metrics except `阅读数 R`. Keep those raw fields in the table for formula calculation and audit.

## Same-Topic V1 Schema

Same-topic analysis uses one Base with three tables:

- `文章复盘`: 量子位 self-owned articles.
- `竞品文章池`: 新智元 and 机器之心 articles.
- `同题分析`: one row per topic, linking the three article records and storing metric snapshots plus structured analysis.
- `同题统计表`: one row per comparison dimension per topic, used as the real table shown in `同题分析` detail.

### Competitor Article Table

`竞品文章池` mirrors the main article metrics:

- Identity fields: `文章标题`, `媒体来源`, `发布时间`, `文章链接`, `负责人/作者`, `发布位置`, `内容体裁`, `选题标签`.
- Raw metric fields: `阅读数 R`, `点赞数 L`, `评论数 C`, `转发数 S`, `收藏数`, `在看数`.
- Formula fields: `点赞率`, `在看率`, `转发率`, `内容质量分`.
- Review fields: `AI复盘`, `人工复盘`, `附件`.
- Reverse link fields may exist from `同题分析`, including `新智元同题分析` and `机器之心同题分析`.

Only `新智元` and `机器之心` should be written to `竞品文章池` in V1. Keep 量子位 articles in `文章复盘`.

### Same-Topic Table

`同题分析` stores one topic group per row.

Core fields:

- `同题名称`
- `同题状态`: `待处理`, `已完成`, `需确认`, `失败`
- `量子位文章`
- `新智元文章`
- `机器之心文章`
- `入口表`
- `统计表`
- `主题标签`
- `创建时间`

Structured analysis fields:

- `结论摘要`
- `标题差异`
- `内容差异`
- `AI复盘`

Current MVP review view:

- View name: `同题复盘 MVP`
- View ID: `vewC8ILsrz`
- Visible fields: `同题名称`, `同题状态`, `主题标签`, `统计表`, `结论摘要`, `标题差异`, `内容差异`, `AI复盘`.

Do not use the text field `统计分析` as the primary display table. Use `同题统计表` and link its rows back to `同题分析` through the reverse link field `统计表`.

Queue/button workflow:

- Prefer reading the qbit title and link from the linked `量子位文章` record.
- `入口表` stores the discovered title and user-pasted original WeChat link for each media source.
- `/Users/jay/Documents/dev/Feishu/scripts/run_same_topic_queue.py run-queue` scans rows where `同题状态=待处理`.
- If competitor links are missing, the script writes three media rows into `入口表`, then sets `同题状态=需确认`.
- Successful full runs set `同题状态=已完成` and write links, stats, and structured analysis.

`入口表` is the table-form candidate and article corridor:

- Table ID: `tblLNAucjQMJAwtl`
- Required fields: `媒体来源`, `文章标题`, `文章链接`, `同题分析记录`
- The script writes one row each for 量子位, 新智元, and 机器之心.
- The 量子位 row is filled from the linked `文章复盘` record; 新智元 and 机器之心 title rows come from public WeChat/web search until the user pastes original links.

`同题统计表` should contain one real table row for each comparison dimension:

- `标题`
- `发布时间`
- `阅读数`
- `点赞率`
- `在看率`
- `转发率`

Use three media columns in fixed order: `量子位`, `新智元`, `机器之心`. Use a numeric `排序` field to keep the row order above, and hide `排序` plus `同题分析记录` in the stats table display view.

The display view for the stats table is:

- View name: `统计表`
- View ID: `vewTdGuLzY`
- Visible fields: `维度`, `量子位`, `新智元`, `机器之心`.

When writing `内容差异`, use the secondary metrics in `同题统计表` as evidence, not only subjective reading impressions:

- `点赞率`: evidence for direct recognition and approval.
- `在看率`: evidence for resonance, identity, and willingness to endorse.
- `转发率`: evidence for shareability, information utility, and social currency.

Start from the rate gaps, then connect them to concrete content differences such as opening strength, information density, narrative rhythm, framing, examples, emotional intensity, and value elevation. Prefer practical claims like `新智元转发率更高，说明其标题和开头更适合快速转发` over generic comments like `内容更好`.

When writing same-topic stats rows, calculate rates as plain numbers before formatting them into `同题统计表`:

- 点赞率 = `点赞数 L / 阅读数 R`
- 在看率 = `在看数 / 阅读数 R`
- 转发率 = `转发数 S / 阅读数 R`
- 质量分 = `MIN((点赞率 * 0.4 + 在看率 * 0.3 + 转发率 * 0.3) * 400, 10)`

For the display table, format rates as percentages for readability.

## Author Field

Fill `负责人/作者` from the article body byline, not from generic WeChat metadata. In the first lines of the body, match `<name> 发自 ...`, for example `Jay 发自 凹非寺量子位 | 公众号 QbitAI`, and write only `<name>` such as `Jay`.

## Core Raw Fields

- `阅读数 R`
- `点赞数 L`
- `评论数 C`
- `转发数 S`
- `收藏数`
- `在看数`

These raw fields should exist in the table but remain hidden from daily review views:

- `点赞数 L`
- `评论数 C`
- `转发数 S`
- `收藏数`
- `在看数`

Do not add `分享带来的阅读人数` unless the user explicitly asks.

## Content Category

Keep one category field only:

- Field: `内容体裁`
- Type: single select
- Options: `资讯`, `人物`, `实测`, `人文`

Do not recreate `内容类型判断`; it overlaps with `内容体裁` and confused the review workflow.

## Secondary Metrics

Use Feishu formula fields when possible:

- `点赞率` = `点赞数 L / 阅读数 R`
- `在看率` = `在看数 / 阅读数 R`
- `转发率` = `转发数 S / 阅读数 R`

Zero-safe pattern:

```text
IF(OR(ISBLANK([阅读数 R]),[阅读数 R]=0),0,IFBLANK([点赞数 L],0)/[阅读数 R])
```

Adjust the numerator field for `在看率` and `转发率`.

Use plain ratio formulas. Leave percentage display and decimal precision to Feishu field formatting.

```text
IF(OR(ISBLANK([阅读数 R]),[阅读数 R]=0),0,IFBLANK([在看数],0)/[阅读数 R])
```

Do not multiply by 100, round inside the formula, or convert rate fields to text for formatting.

## Content Quality Score

Use the user's preferred weighted scaling:

```text
MIN((点赞率 * 0.4 + 在看率 * 0.3 + 转发率 * 0.3) * 400, 10)
```

If Feishu formula syntax or OpenAPI does not support `MIN`, use:

```text
IF(
  ([点赞率]*0.4+[在看率]*0.3+[转发率]*0.3)*400 > 10,
  10,
  ([点赞率]*0.4+[在看率]*0.3+[转发率]*0.3)*400
)
```

Do not recalculate raw metric ratios inside `内容质量分`. Reuse `点赞率`, `在看率`, and `转发率` so the score tracks the visible secondary indicators.

## Self-Owned Article Review Format

For `文章复盘` self-owned article rows, write `AI复盘` in the same practical structure used by same-topic review:

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

Rules:

- Put `结论摘要` first. It should quickly state the article's main result and likely reason.
- `标题分析` should connect title choices to attention, click motivation, clarity, novelty, conflict, and search/social spread.
- `内容分析` should use secondary metrics as evidence where available: 点赞率 for recognition, 在看率 for resonance, and 转发率 for shareability.
- `AI复盘` should end with practical actions for the next article.
- Do not use the older fixed `优点/缺点` structure for new self-owned article reviews unless the user explicitly asks for it.

## Deprecated Fields

Do not recreate these unless the user explicitly reverses the decision:

- `内容类型判断`
- `点赞评论比`
- `转发点赞比`
- `分享带来的阅读人数`
- `新增关注`
- `平均停留时长(秒)`
- `完读率`
- `评论率`

`完读率` can remain if it already exists in an older table, but do not recreate it for the current `微信公众号内容复盘` workflow.

## Publish Position

`发布位置` must be based on reliable source data:

- backend export indicating order,
- complete same-day push order,
- user-provided manual label.

If not available, leave it blank or ask the user whether to mark it manually. Do not infer it from title, article popularity, or article type.
