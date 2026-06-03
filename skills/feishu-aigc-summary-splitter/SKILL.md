---
name: feishu-aigc-summary-splitter
description: Use when the user asks to process a Feishu/Lark conference summary assignment document, verify speaker names/titles/topics against a Feishu Base guest sheet, create or rebuild one overall draft plus per-section docx drafts, open editable sharing permissions, clean up older generated drafts, and return links grouped by assignee. Optimized for AIGC summit summary workflows using lark-cli docs v2 and Base records.
---

# Feishu AIGC Summary Splitter

## Purpose

Turn a Feishu conference-summary assignment doc into clean draft documents:

- read the latest assignment doc and guest Base;
- double-check name, title, topic, assignee, contact, and priority;
- create an overall draft or one doc per section;
- open tenant-editable sharing permissions for generated docs when needed;
- delete older generated drafts when asked;
- return links grouped by person, with roundtable kept as its own item unless the user says otherwise.

## Required Skills And Tools

Use these local skills before acting:

- `lark-doc` for `docs +fetch`, `docs +create`, and `docs +update` with `--api-version v2`.
- `lark-base` when the assignment doc embeds a guest Base `<cite ... token="..." table-id="..." view-id="...">`.
- `lark-drive` for deleting old generated docs and updating public link permissions.
- `lark-shared` for identity, permission, and rate-limit handling.

Prefer `--as user` for user-owned Feishu docs.

## Output Style

These are user preferences for this workflow:

- Do not write the opener `第四届中国AIGC产业峰会上，`.
- Keep the useful intro, e.g. `风行在线CEO易正朝带来主题为《...》的分享。`
- Use five empty quote bullets only:
  ```text
  *
  *
  *
  *
  *
  ```
- Use simple image placeholder text: `（配图）`.
- Do not write verbose placeholders such as `【待补充金句1】...`.
- When filling `观点精华提炼` from a transcript, select the strongest five points but keep wording close to the speaker's original meaning, logic, key terms, and memorable metaphors. Smooth the transcript into readable prose without rebuilding it into a new abstract framing.
- Keep viewpoint bullets concise and direct. Avoid framing phrases such as `XXX认为`, `他强调`, `他判断`, or `他建议`; write the idea itself.
- Avoid product-PR style when extracting viewpoints. Do not center bullets on product releases, user counts, partnerships, certifications, sales, or brand praise unless they directly support a core insight. Prioritize the speaker's underlying judgment, industry logic, technical/operational challenge, methodology, and useful counterintuitive观点.
- Ban the common Chinese contrast pattern built from `bu shi` + `er shi`, including expanded variants. Rewrite them as direct positive statements or split them into shorter sentences.
- Match the user's preferred media-summary style: short, forceful bullets that preserve speaker keywords and memorable phrasing, e.g. `Token已然成为AI时代的“电力消耗”`; `要么小白，要么大神`; `做第二名`. It is acceptable to slightly polish rhythm and emphasis, but do not invent new claims.
- Learn from the user's edited draft style: the final bullet should feel like a journalist's conference-summary note, not a product one-pager. Preserve vivid phrases from the speaker when they carry meaning, such as `水电煤`, `一座桥`, `iPhone4`, `制氧机`, `楼梯`, `站在原地等确定性`, and `交付结果`.
- Prefer the speaker's concrete formulation over polished abstraction. If the transcript says `讲故事的人、创造idea的人、定义美的人`, keep that Chinese phrasing instead of translating into broad English labels. If the transcript uses a striking analogy or direct judgment, keep the analogy and tighten the sentence around it.
- Keep each speaker to five bullets unless the user asks otherwise. Each bullet should usually capture one complete judgment: phenomenon + cause/result, method + implication, or analogy + conclusion. Avoid turning one bullet into a long list of product functions.
- Use concrete numbers and examples only when they strengthen the idea. Numbers such as `10倍`, `70%-80%`, `212倍`, `100倍`, `50万`, or `1000万` should support a judgment; do not include them as promotional proof points by themselves.
- For company-heavy talks, translate product details into higher-level lessons: enterprise落地鸿沟,数据平台挑战,组织方式变化,算力生态护城河,推理算力持续需求,医疗证据链,物理世界数据空白. Mention a product name only when it is necessary to understand the point.
- Keep a natural Chinese cadence. Short declarative sentences are preferred. It is fine to use question-like or spoken phrasing from the transcript when it makes the point sharper, such as `怎么出精品，反而成为更高的挑战` or `解药就是交付结果`.
- Remove boilerplate and task-management residue when producing publishable drafts: assignee parentheses, `确认信息`, priority/status notes, and plain `(配图)` placeholders are for working docs; edited article text can use section headings and `[图片]` if the target format is a final稿.
- Do not insert spaces between Chinese characters and English words, acronyms, or numbers. Keep spaces inside English phrases only, e.g. `AI Agent`, `Claude Code`; use compact mixed forms such as `iPhone4`.
- Skip crossed-out / canceled speakers such as `吴玮杰（不来了）`.
- For roundtables, keep the roundtable as one separate document unless the user explicitly asks to split by guest.
- When returning links for the chat group, group by assignee and put `圆桌` in a separate section.

## Workflow

1. Fetch the assignment document.

```bash
lark-cli docs +fetch --api-version v2 --as user --doc "<assignment_doc_url>" --format json
```

2. Extract the embedded guest Base token/table/view from any `<cite ...>` tag. Then fetch guest data.

```bash
lark-cli base +record-list --as user \
  --base-token "<base_token>" \
  --table-id "<table_id>" \
  --view-id "<view_id>" \
  --field-id 嘉宾姓名 \
  --field-id 嘉宾title \
  --field-id 分享主题 \
  --field-id 对接人 \
  --field-id 稿件优先级 \
  --limit 100 \
  --format json
```

3. Before creating or editing docs, present a check list if the user asks to verify first.

Flag differences clearly:

- title/name/topic mismatch between the assignment doc and guest Base;
- canceled items present in Base but crossed out in assignment;
- extra Base rows not present in assignment;
- roundtable guest title differences.

Do not modify documents during a verification-only request.

4. For building drafts, use the exact current assignment doc as the source of assignees. Use the guest Base as the source of title, topic, contact, and priority.

5. Use XML with `docs +create --api-version v2 --doc-format xml`. Build each section with:

```xml
<title>嘉宾，title（负责人）</title>
<h2>嘉宾，title（负责人）</h2>
<p>title嘉宾带来主题为《主题》的分享。</p>
<p>以下是他的观点精华提炼：</p>
<p>* </p><p>* </p><p>* </p><p>* </p><p>* </p>
<p>（配图）</p>
<h3>确认信息</h3>
<p>对接人：...</p>
<p>稿件优先级：...</p>
```

Use `她` for known female speaker `张璐`; otherwise default to `他`.

6. Deletion cleanup: only delete old generated docs when the user explicitly asks. Use `drive +delete --yes` only for the exact doc tokens that were generated for this workflow.

```bash
lark-cli drive +delete --as user --file-token "<doc_token>" --type docx --yes
```

7. When the user asks to "open permissions", "make editable", or wants links to send to a group, set each final docx to tenant-editable unless they explicitly ask for external public access.

```bash
lark-cli drive permission.public patch --as user --yes \
  --params '{"token":"<doc_token>","type":"docx"}' \
  --data '{"link_share_entity":"tenant_editable","share_entity":"same_tenant","comment_entity":"anyone_can_edit","security_entity":"anyone_can_edit"}'
```

If the patch reports missing scope, run:

```bash
lark-cli auth login --scope "docs:permission.setting:write_only"
```

Then retry the patch. Only verify with `permission.public get` when needed; that read check may require `docs:permission.setting:read`.

8. Rate limits are common when creating many docs. Create serially, sleep between calls, and retry on `frequency limit` / `rate_limit`. If a batch is interrupted, recover links with `drive +search --mine --created-since ... --doc-types docx`.

## Helper Script

Use `scripts/build_split_docs.py` when rebuilding many docs. It accepts a JSON spec and creates Feishu docs serially with retry. Add `--make-editable` when the generated links should be tenant-editable. Read the script only if you need to adjust the spec format or behavior.

Expected spec shape:

```json
{
  "docs": [
    {
      "title": "方汉，昆仑万维董事长兼CEO（王晔）",
      "owner": "王晔",
      "xml": "<h2>...</h2>..."
    }
  ]
}
```

The script prints JSON results containing `title`, `owner`, `url`, `doc_id`, and, when requested, `editable`.

## Final Response

For delivery, return a concise grouped list:

```markdown
**王晔**
- [方汉，昆仑万维董事长兼CEO](...)

**思懿**
- [...]

**雨晴**
- [...]

**榆景**
- [...]

**圆桌**
- [前沿圆桌：2026，Agent产品的不确定性与非共识机遇](...)
```

Mention any skipped/canceled speakers and any unresolved mismatches.
