# Metrics And Base Schema

## Main Base

Target Base is usually named `微信公众号内容复盘`, table `文章复盘`. If the user provides a different Base URL or token, use the provided target instead of hardcoding any previous token.

## Field Order

Recommended visible order:

1. `文章标题`
2. `负责人/作者`
3. `发布时间`
4. `发布位置`
5. `内容体裁`
6. `选题标签`
7. Raw metrics from Excel/backend
8. Secondary metric formulas
9. `内容质量分`
10. `AI复盘`
11. `人工复盘`
12. `文章链接`

## Core Raw Fields

- `阅读数 R`
- `点赞数 L`
- `评论数 C`
- `转发数 S`
- `收藏数`
- `新增关注`
- `平均停留时长(秒)`
- `完读率`

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
- `评论率` = `评论数 C / 阅读数 R`
- `转发率` = `转发数 S / 阅读数 R`

Zero-safe pattern:

```text
IF(OR(ISBLANK([阅读数 R]),[阅读数 R]=0),0,IFBLANK([点赞数 L],0)/[阅读数 R])
```

Adjust the numerator field for `评论率` and `转发率`.

## Content Quality Score

Use the user's preferred weighted scaling:

```text
MIN((点赞率 * 0.4 + 评论率 * 0.3 + 转发率 * 0.3) * 400, 10)
```

If Feishu formula syntax or OpenAPI does not support `MIN`, use:

```text
IF(
  ((IFBLANK([点赞数 L],0)/[阅读数 R])*0.4
  +(IFBLANK([评论数 C],0)/[阅读数 R])*0.3
  +(IFBLANK([转发数 S],0)/[阅读数 R])*0.3)*400 > 10,
  10,
  ((IFBLANK([点赞数 L],0)/[阅读数 R])*0.4
  +(IFBLANK([评论数 C],0)/[阅读数 R])*0.3
  +(IFBLANK([转发数 S],0)/[阅读数 R])*0.3)*400
)
```

Wrap it with the zero-safe guard:

```text
IF(OR(ISBLANK([阅读数 R]),[阅读数 R]=0),0,<score expression>)
```

## Deprecated Fields

Do not recreate these unless the user explicitly reverses the decision:

- `内容类型判断`
- `点赞评论比`
- `转发点赞比`
- `分享带来的阅读人数`

## Publish Position

`发布位置` must be based on reliable source data:

- backend export indicating order,
- complete same-day push order,
- user-provided manual label.

If not available, leave it blank or ask the user whether to mark it manually. Do not infer it from title, article popularity, or article type.
