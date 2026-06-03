---
name: qbit-aigc-summit
description: "Use when the user wants to run or automate the Feishu AIGC summit summary workflow end to end: build the overall draft skeleton, create empty per-speaker docs, monitor Feishu Minutes by naming convention, extract viewpoint bullets into the overall draft, sync confirmed sections to individual docs, export Word files, and update the status table after every stage."
---

# AIGC Summit SOP

## Purpose

用状态化飞书流程跑AIGC峰会总结:

- 先建立总稿骨架;
- 总稿骨架经人工确认后，再创建单人空文档和单独圆桌文档;
- 按命名规范在中午12点和下午6点检查飞书妙记;
- 把观点精华写入匹配的总稿section;
- 人工确认后，把已确认section同步进单人文档;
- 按统一命名导出Word文件;
- 每个模块结束时更新状态表。

Use this skill as the control layer. Load only the reference or script needed for the current stage.

## Required Local Skills

- `lark-doc`: fetch, create, update, and export docx content with `--api-version v2`.
- `lark-base`: read guest and assignment records when the status table or guest sheet lives in Base.
- `lark-minutes` or `lark-vc`: search妙记, fetch AI产物, and download逐字稿.
- `lark-drive`: set editable permissions, delete exact generated docs when explicitly asked, and export files.
- `lark-whiteboard`:用户要求Feishu画板版SOP时更新流程图。

Prefer `--as user` for user-owned Feishu assets.

## Operating Model

1. Open [references/workflow.md](references/workflow.md) to identify the current stage.
2. Read [references/status_schema.md](references/status_schema.md) before touching the status table.
3. Pick exactly one end-to-end module for the current state:
   - 建稿: `scripts/assignment_doc_builder.py`
   - 状态表同步: `scripts/base_status_sync.py`
   - 妙记发现与拉取: `scripts/minutes_monitor.py`
   - 观点精炼与总稿回写: `scripts/viewpoint_writer.py`
   - 确认后同步: `scripts/confirmed_doc_sync.py`
   - Word导出: `scripts/word_exporter.py`
4. Run the module with `--dry-run` first when the target doc, status table, or naming pattern is new.
5. Run without `--dry-run` only after the inputs map cleanly.
6. Verify the Feishu result by fetching the changed doc or status table.
7. Return the smallest useful status update: completed item, changed links, blocked items, and next state.

每个模块都把更新Feishu Base状态表作为最后一步。模块失败时，只要状态表可访问，就写入失败状态、错误摘要和重试提示。

## Key Rules

- 总稿是实时工作面。单人文档初始为空，只在人工确认后接收内容。
- 建稿第一步只生成总稿骨架，不能同时拆分或创建单人/圆桌文档；总稿骨架必须先进入人工确认，用户确认后才继续拆分单人文档和圆桌文档。
- 圆桌保持独立，不按负责人分组，除非用户明确要求。
- 状态跟踪使用Feishu Base。Base表至少包含`对象`、`类型`、`状态`、`负责人`、`角色`、`主题`、`文档链接`、`总稿链接`、`更新时间`、`备注`字段。
- 创建或更新文档后，运行`base_status_sync.py`同步Base状态表。返回给用户时带Base链接和下一状态。
- 建稿骨架必须贴合正确大会总结稿模板：总稿从`标题：`、署名、导语占位开始，随后按嘉宾生成`##姓名，title`section；每个section包含引入语、`以下是他的观点精华提炼：`和5个空bullet；圆桌使用总段落加每位嘉宾`###姓名，title`。
- 不要在总稿或单人稿开头自动插入流程说明、内容形式说明、checkbox、callout或SOP说明文字，除非用户明确要求。
- 单人稿/圆桌稿从对应section骨架开始，文档标题用`<title>`写入真实名称，避免创建成untitled。
- 空观点必须保留为空bullet，不要写`待补充`、说明性占位或其他占位文案。
- 妙记自动化依赖命名一致性。链接可作备份，稳定触发依赖录音编号、嘉宾名、公司名、主题。
- 观点精炼必须包含回写总稿section，不能交给导出或同步脚本处理。
- `word_exporter.py`只按命名规则导出Word，不改写内容。
- Use XML for Feishu doc updates when spacing, headings, or bullets matter.
- Do not insert spaces between Chinese text and English words, acronyms, or numbers. Spaces inside English phrases are fine.
- Do not use the Chinese contrast pattern banned by the workspace instructions.

## Viewpoint Style

When extracting观点, load [references/viewpoint_style.md](references/viewpoint_style.md). Stable defaults:

- five bullets per speaker unless the user asks otherwise;
-贴近讲者原意、逻辑、关键词和比喻;
-少PR，多洞见，优先判断、约束、方法论、非共识结论;
- bullet text should start with the idea itself, without `XXX认为`、`他强调`、`他建议`;
- keep concise media-summary cadence.

## Human Checkpoints

Load [references/human_checkpoints.md](references/human_checkpoints.md) when moving across a boundary that needs user confirmation:

- name/title/topic mismatch check before建稿;
- 总稿骨架创建后必须进入`待骨架确认`；收到用户明确确认后才进入拆分/创建单人文档。
-观点写入总稿后进入`待人工确认`;
- 人工确认后才同步到单人文档;
- Word export after sync verification.

## Whiteboard Note

更新Feishu画板版SOP时，加载[references/whiteboard_rules.md](references/whiteboard_rules.md)。流程步骤文字直接写入步骤节点内部，不在每个步骤里另加文本框。
