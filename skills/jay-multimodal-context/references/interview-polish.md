---
name: interview-polish
description: Polish raw Chinese interview transcripts into polished media interview prose and, for podcast/video/audio final Markdown, add the Obsidian-ready note section, body packaging, and final filename. Use when Codex is asked to revise, clean up, rewrite, format, or package interview transcripts, Q&A drafts, speaker-labeled dialogue, timestamped transcripts, or multi-part interview text while preserving speakers, technical terms, core claims, numbers, cases, personality, and sharp phrasing.
---

# Interview Polish

## Goal

将原始采访逐字稿润色为媒体专访正文风格。普通润色任务直接输出润色后的正文，不加说明、前言、复盘或改写理由。播客、视频、音频最终 Markdown 任务按本文件的 Final Markdown Packaging 生成 `## 笔记` 和正文包装。

## Workflow

1. 识别输入类型：带时间戳逐字稿、无时间戳纯对话、说话人标注文本，或多轮对话中分批提供的片段。
2. 删除时间戳、明显口头填充、重复表达和冗余信息。
3. 保留说话人标签、核心观点、关键信息、专业术语、英文词汇、数字、时间节点、具体案例、有价值的类比和人物表达个性。
4. 精简问题为一句清楚的问题，去掉铺垫和绕路。
5. 按逻辑层次重组回答，每个自然段聚焦一个核心信息点。
6. 检查语言和排版规范后输出正文。

## Filename Rules

适用于播客、视频访谈、文字访谈和已有逐字稿润色后的最终Markdown。

- 默认格式：`<受访人>-<公司或机构>-<YYYYMMDD>.md`。
- 受访人是最高优先级。优先使用调用方提供的元数据，其次从播客标题、shownotes、逐字稿开头、说话人标签中提取。
- 公司或机构使用受访人所属公司、机构、项目、实验室或高校。缺失时可使用播客名、媒体名或核心身份。
- 当第二字段需要从播客标题、视频标题、节目标题、原文标题或核心身份中提取时，不直接使用完整原题，改写成短中文标题片段。
- 短标题片段要像书里的小章节，克制、清澈、有余味。必须是中文，4到12个汉字，不加标点，不加书名号。
- 短标题片段避开泛词：`问题`、`对话`、`思考`、`讨论`、`这个`、`事情`。
- 日期优先使用发布日期、录制日期、活动日期或原始文档日期。缺失时使用创建日期。
- 多位核心受访人时保留1到2位关键人物，例如 `张三-李四-公司-20260701.md`。超过两位时可写成 `张三等-公司-20260701.md`。
- 主持人、媒体号或提问方通常不进入文件名，除非没有明确受访人。
- 如果调用方给出的输出路径是临时名或泛名，按本规则重命名最终Markdown，并在回复中返回重命名后的完整路径。
- 清理文件名中的链接符号、斜杠、冒号、换行、引号和其它不适合文件系统的字符。

## Final Markdown Packaging

适用于普通播客、视频和音频逐字稿润色后的最终Markdown。先完成正文润色，再从润色后的正文生成笔记区。笔记区只做结构化总结、信息压缩和重点呈现。不要从原始字幕、Feishu Minutes AI总结或平台元数据生成笔记。

最终Markdown结构：

```markdown
# <document title>

## 笔记

### <根据正文内容生成的标题>

- <来自正文的精炼信息>
- <来自正文的精炼信息>

### <根据正文内容生成的标题>

#### <可选层级或维度>

- <来自正文的精炼信息>
- <来自正文的精炼信息>

#### <可选层级或维度>

- <来自正文的精炼信息>
- <来自正文的精炼信息>

## 正文

<polished transcript content>
```

Packaging rules:

- Use `## 笔记` as the required first content section immediately below the top-level title.
- Use `## 正文` as the heading before the polished transcript body unless the polished transcript already has a clearer first body heading.
- Organize the note section with flexible `###` and optional `####` headings that fit the transcript content. Do not require fixed subsections.
- Build the note from the polished transcript body after polishing is complete.
- Preserve the full polished transcript body below the note section, including useful speaker labels, headings, examples, numbers, and technical terms.
- If a previous `## 笔记` section exists, replace it instead of appending a duplicate.

Note writing rules:

- Summarize and reorganize the polished transcript into clearer hierarchy, shorter expression, and reusable reading notes.
- Preserve the transcript's main topics, facts, numbers, chronology, categories, methods, examples, and relationships when they are important.
- Remove intro storytelling, personal setup, screenshots, image captions, proof-of-reading chatter, defensive caveats, repeated examples, long source-specific chronology, and platform-specific detours from the note section when they do not carry information.
- Keep examples only when they make the source content easier to understand or reuse.
- Do not summarize paragraph by paragraph.
- Do not force subjective judgment, value ranking, commentary, reflection, or extrapolated implications.
- Do not force dedicated judgment, excerpt, reflection, or takeaway modules.
- Do not add invented facts, extra citations, or outside claims unless the user asks for research.
- Keep the writing dense, clean, and suitable for later retrieval in Obsidian.
- Prefer short sections and bullets where the idea is naturally list-shaped.
- Preserve useful terms such as Prompt Engineering, Harness Engineering, Agent, SOP, AI, and other source-core concepts.
- Follow any standing user style constraints in the active thread, including forbidden sentence patterns, quote style, and spacing rules.

Delivery check:

- Confirm the merged Markdown file exists.
- Confirm the file starts with the document title, then `## 笔记`, then the polished transcript body.
- Confirm the note section is a structured, concise summary of the polished transcript, not commentary, reflection, or a narrative recap.
- Confirm the file is under the routed folder unless the user selected an existing file or explicitly requested another path.
- Confirm obvious boilerplate and intro story material have been removed from the note section.

## Editing Rules

删除或改写这些内容：

- 时间戳，例如 `00:01:05`。
- 口语填充词，例如 `然后`、`就是`、`对吧`、`是的是的`、`嗯`、`啊`、`哈哈哈`、`说实话`。若情绪标记能体现语气，可简化保留。
- 重复表达、过程性自我纠正、无信息量铺垫。

保留并强化这些内容：

- 说话人标签，例如 `量子位` 或受访者姓名。
- 专业术语和英文词汇，例如 `human-centric`、`scaling law`、`VLA`、`benchmark`、`ROI`、`payback`、`infra`。
- 核心论断、观点锋芒、人物个性、具体案例、数字和时间节点。

## Language Rules

严格遵守：

- 不使用破折号。用句号或逗号改写。
- 不使用引号。把被引用内容自然融入句子。
- 不使用省略号。用句号结束或改写。
- 中文和英文之间不加空格，例如 `AI模型`。
- 英文词组内部正常加空格，例如 `AI Engine`。
- 数字和单位之间不加空格，例如 `10%`。
- 英文缩写和中文之间不加空格，例如 `VLA模型`。

## Formatting Rules

使用这种结构：

```text
说话人：内容内容内容。

内容内容，内容内容。

内容内容。

说话人：内容内容内容。
```

排版要求：

- 说话人标签与内容在同一行。
- 每个自然段之间额外空一行。编辑飞书文档时，用含不可见空格的空段落保证视觉上有明显留白，例如XML里的 `<p> </p>`，避免纯空段落被飞书吞掉。
- 每段最多3句话，保持信息密度。
- 同一回答中遇到转折、递进、举例或新论点时换段。
- 小标题在Markdown输出里只使用一组标题标记，例如 `#### 为什么LLM不是通向智能的路径`。不要在标题文本本身再保留字面量 `####` 前缀。
- 播客、视频和音频类最终Markdown的正文部分应按内容推进补充阶段性小标题。小标题根据正文本身自然生成，起到划分主题、提示推进和帮助检索的作用。不要套用固定栏目名或机械框架，优先让标题贴合材料里的真实问题、转折、案例、判断和技术线索。
- 技术论述可用 `第一`、`第二`、`第三` 标明层次，但不要改成项目符号列表，除非用户明确要求列表。

## Quality Bar

优先级从高到低：

1. 成功率：完整保留核心观点和关键信息，不丢失受访者的核心论断。
2. 效率：删除口语冗余，保留有价值表达。
3. 类人性：读起来像真实的人在说话，有温度、有锋芒、有个性。

## Examples

时间戳和填充词：

```text
原文：
丁文超 00:01:05 我觉得就是其实去年咱们聊的时候，其实主要是就是围绕我们的 AI engine，当时只是提一个概念，但是现在我们其实把它给展开了

润色后：
丁文超：去年聊的时候，主要还停留在AI Engine的概念层面，这一年我们把它真正展开了。
```

问题精简：

```text
原文：
量子位：那你们从这个，就刚才讲到了从2.0到3.0这个模型的迭代，你们在这个过程里面，你们去评价你们模型的这一个标准是什么？或者是内部的这一个评价它好坏或者是进步多少，这个标准是什么？

润色后：
量子位：从2.0到3.0的迭代过程中，你们内部评价模型好坏的标准是什么？
```

## Multi-Part Inputs

如果用户分多次提供逐字稿，每次只润色当前部分，同时保持与前文一致的说话人称谓、术语写法、语言密度和排版风格。
