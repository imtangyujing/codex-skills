# Metrics And Base Schema

## Main Base

Current target Base:

- Base: `微信公众号内容复盘`
- Base token: `YSItbTTRMaMioBsYBQrcKu1znFh`
- Table: `文章复盘` / `tblcDbhMFaYWfdEu`
- Competitor table: `竞品文章池` / `tbl8WwB6ant8NeQ1`
- Same-topic table: `同题分析` / `tblx2Kuzvm5KMi0E`
- Same-topic stats table: `同题统计表` / `tblxmGa9SxhxEoCp`
- Entry table: `入口表` / `tblLNAucjQMJAwtl`

If the user provides a different Base URL or token, use the provided target instead.

## Metric Source

Metrics come from **用户指标来源**（user-provided WeChat backend screenshots, screenshot OCR results, or user-provided metric tables）. Do not fetch metrics through credential-based services during ordinary review runs.

### Screenshot/Table Field Mapping

| Source label | Target field |
|---|---|
| `阅读`/`阅读数` | `阅读数 R` |
| `点赞`/`点赞数` | `点赞数 L` |
| `评论`/`评论数` | `评论数 C` |
| `分享`/`转发`/`转发数` | `转发数 S` |
| `收藏`/`收藏数` | `收藏数` |
| `在看`/`在看数` | `在看数` |

If a screenshot omits a metric, leave that field blank. Write `0` only when the source explicitly shows zero. When `评论数 C` is blank, do not mention zero comments or zero comment rate in `AI复盘`.

## Modification Boundary

During ordinary review runs, only fill or update record data. Do not modify Base structure (fields, formulas, tables, views, dashboards, forms) unless the user explicitly asks.

The same-topic V1 setup created `竞品文章池`, `同题分析`, `同题统计表`, and `同题分析看板`. Future runs treat the structure as fixed.

## Field Order

Daily visible order for `文章复盘`:

`文章标题` → `发布时间` → `文章链接` → `负责人/作者` → `发布位置` → `内容体裁` → `选题标签` → `阅读数 R` → `点赞率` → `在看率` → `转发率` → `内容质量分` → `同题分析` → `AI复盘` → `人工复盘` → `附件`

Daily views hide raw interaction metrics except `阅读数 R`.

## Core Raw Fields

- `阅读数 R`, `点赞数 L`, `评论数 C`, `转发数 S`, `收藏数`, `在看数`

Hidden from daily views: `点赞数 L`, `评论数 C`, `转发数 S`, `收藏数`, `在看数`.

## Secondary Metrics (Feishu Formulas)

- `点赞率` = `点赞数 L / 阅读数 R`
- `在看率` = `在看数 / 阅读数 R`
- `转发率` = `转发数 S / 阅读数 R`

Zero-safe pattern:

```text
IF(OR(ISBLANK([阅读数 R]),[阅读数 R]=0),0,IFBLANK([点赞数 L],0)/[阅读数 R])
```

Use plain ratio formulas. Leave percentage display and decimal precision to Feishu field formatting. Do not multiply by 100 or convert to text.

## Content Quality Score

```text
MIN((点赞率 * 0.4 + 在看率 * 0.3 + 转发率 * 0.3) * 400, 10)
```

Feishu fallback if `MIN` unsupported:

```text
IF(
  ([点赞率]*0.4+[在看率]*0.3+[转发率]*0.3)*400 > 10,
  10,
  ([点赞率]*0.4+[在看率]*0.3+[转发率]*0.3)*400
)
```

Reuse `点赞率`, `在看率`, `转发率`; do not recalculate from raw fields.

## Content Category

- Field: `内容体裁` (single select)
- Options: `资讯`, `人物`, `实测`, `人文`

## Author Field

Fill `负责人/作者` from the article body byline, not generic WeChat metadata. Match `<name> 发自 ...` pattern, write only `<name>`.

## Publish Position

`发布位置` must come from reliable source data (backend export order, complete same-day push order, or user-provided label). Do not infer from title or popularity.

## Same-Topic V1 Schema

### Competitor Article Table (`竞品文章池`)

Mirrors main article metrics. Only `新智元` and `机器之心` go here; 量子位 stays in `文章复盘`.

Fields: `文章标题`, `媒体来源`, `发布时间`, `文章链接`, `负责人/作者`, `发布位置`, `内容体裁`, `选题标签`, raw metrics, formula fields, `AI复盘`, `人工复盘`, `附件`. Reverse link fields from `同题分析` may exist.

### Same-Topic Table (`同题分析`)

One row per topic group.

Core fields: `同题名称`, `同题状态`(`待处理`/`已完成`/`需确认`/`失败`), `量子位文章`, `新智元文章`, `机器之心文章`, `入口表`, `统计表`, `主题标签`, `创建时间`.

Structured analysis fields: `结论摘要`, `标题差异`, `内容差异`, `AI复盘`.

MVP review view: `同题复盘 MVP` / `vewC8ILsrz`. Visible: `同题名称`, `同题状态`, `主题标签`, `统计表`, `结论摘要`, `标题差异`, `内容差异`, `AI复盘`.

Do not use text field `统计分析` as the primary display. Use `同题统计表` with rows linked back through `统计表`.

### Same-Topic Stats Table (`同题统计表`)

Seven rows per topic, in order: `结论`, `标题`, `起笔`, `叙事`, `证据`, `扩展`, `风格`.

Three media columns in fixed order: `量子位`, `新智元`, `机器之心`. Use numeric `排序` field for row order; hide `排序` and `同题分析记录` in display view.

Display view: `统计表` / `vewTdGuLzY`. Visible: `维度`, `量子位`, `新智元`, `机器之心`.

Each cell: compact qualitative judgment. Mark strongest/most transferable handling with `🟨 `. Use 点赞率/在看率/转发率 as evidence inside relevant cells, not as separate rows. Do not create separate stats rows for `发布时间`, `阅读数`, or rate metrics.

### Entry Table (`入口表`)

Fields: `媒体来源`, `文章标题`, `文章链接`, `同题分析记录`. One row each for 量子位, 新智元, 机器之心. The 量子位 row is filled from `文章复盘`; competitor rows from web search until user pastes original links.

### Queue Workflow

Script: `~/Documents/dev/Feishu/scripts/run_same_topic_queue.py run-queue --limit 10`.

Flow: `同题状态=待处理` → script scans → if competitor links missing, writes `入口表` rows and sets `需确认` → user pastes links → re-trigger `待处理` → script runs full analysis → `已完成`.

## Deprecated Fields

Do not recreate: `内容类型判断`, `点赞评论比`, `转发点赞比`, `分享带来的阅读人数`, `新增关注`, `平均停留时长(秒)`, `完读率`, `评论率`.
