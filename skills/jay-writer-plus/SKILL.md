---
name: Jay Writer Plus
description: |
  Jay 的完整写作工作流系统。用于公众号长文、选题会、技术解读、商稿、招股书解读、标题生成、冷读测试和发表后迭代。用户需要从素材到选题、提纲、成稿、标题、冷读和复盘全流程推进时使用。
---

# Jay Writer Plus — 写作工作流总控

> 这是 Jay 写作系统的入口。每次写稿，先看这份文件，它告诉你这一篇走哪条路、每个节点调哪个 skill、你这个人在哪一步介入。
>
> 设计这套系统的所有底层判断，记在 `决策记录-decisions.md`。开新对话只需要贴那一个文件，不用再贴聊天记录。

## 子流程索引

根据稿件类型和用户当前阶段，路由到对应子 skill：

- 选题发散：`skills/topic-selection/SKILL.md`
- 普通长文：`../../jay-writer/SKILL.md`
- 技术解读：`skills/tech-blog-writer/SKILL.md`
- 商稿正文：`skills/commercial-article/SKILL.md`
- 商稿提纲：`skills/commercial-outline/SKILL.md`
- 招股书解读：`skills/prospectus-decoder/SKILL.md`
- 标题生成：`skills/qbitai-title-generator/SKILL.md`
- 发表前冷读：`skills/cold-reader/SKILL.md`
- 发表后迭代：`skills/skill-editor/SKILL.md`

---

## 一句话原则

**漏斗逻辑：AI 把素材铺到最厚 → 你把角度收到最准 → AI 对着契约执行 → 独立冷读把关。每个节点交给更擅长它的一方。**

这不是把人移出 loop，是把人放到唯一一个 LLM 自对弈还补不上的节点：发散端的角度取舍。

---

## 主流程（默认路径）

```
素材进来
   │
   ▼
〔你的一秒元判断〕这篇的点，明不明？
   │
   ├── 明（一眼新闻、心里已有角度）──────────────┐
   │                                              │
   └── 不明（素材厚 / 角度不清 / 自己也没想清）    │
        │                                         │
        ▼                                         │
  ① 宽搜索铺素材   topic-selection（AI 主导）      │
        │   产出带信源的素材地图，标红待查的少数    │
        ▼                                         │
  ② 你精读        人，只看标红的 5%               │
        │                                         │
        ▼                                         │
  ③ 选题会发散    topic-selection（AI 主导）       │
        │   抛 3 个互相拉开的角度提纲              │
        ▼                                         │
  ④ 你取舍        人，砍，说理由 → 锁契约          │
        │                                         │
        ▼                                         │
  ⑤【契约】angle + 骨架 + 边界 + 赌的 HKR ◄───────┘
        │
        ▼
  ⑥ 写作          henry-writer / tech-blog-writer / commercial-article
        │          （对着契约执行，按文章类型选 skill）
        ▼
  ⑦ 起标题        qbitai-title-generator
        │
        ▼
  ⑧ 冷读          cold-reader v2.0（独立空白上下文，加权）
        │
        ▼
  ⑨ 改 → 终稿
        │
        ▼
  ⑩ 你微调 → 发表
        │
        ▼
  ⑪ 数据          articles.csv（打开率/完读率/分享率/评论）
        │
        ▼
  ⑫ 校准          反复出现的信号 → skill-editor 改 criteria
                  （写作标准回 henry-writer，选题标准回 topic-selection）
```

**「明」这条捷径直接跳到 ⑤**：你心里已有角度时，自己写一句话契约（或直接口述给写作 skill），跳过①到④，省掉选题会这层负担。走不走选题会，是你一秒钟的元判断，只有你能做——它依赖你对读者、对公司定位、对自己心里有没有现成角度的体感。

---

## 节点 × skill × 谁动手

| 节点 | skill | 主导方 | 这一步在做什么 |
|------|-------|--------|----------------|
| ① 宽搜索铺素材 | topic-selection | **AI** | 扩展搜索边界，把你不会去找的信源/相邻事实/可当主体的人铺到桌上，产出带信源素材地图 |
| ② 精读 | — | **人** | 只读 AI 标红的待查项，省掉全文复核 |
| ③ 角度发散 | topic-selection | **AI** | 抛 3 个互相足够远的角度提纲（安全/主流/冒险） |
| ④ 取舍锁契约 | topic-selection | **人** | 砍角度，说理由（理由喂回选题判断的校准） |
| ⑥ 写作 | henry-writer ‖ tech-blog-writer ‖ commercial-article ‖ prospectus-decoder | **AI** | 对着契约出稿，按类型选 skill |
| ⑦ 标题 | qbitai-title-generator | AI + 人 | 出多个候选，HKR 评估，你（或领导）定 |
| ⑧ 冷读 | cold-reader v2.0 | **AI（独立上下文）** | 加权评分：工艺层轻判，设计/原创层重判 |
| ⑩ 微调 | — | **人** | 终稿按需手调 |
| ⑫ 校准 | skill-editor | 人 + AI | 数据反复指向的盲区，升级回对应 skill |

---

## 写作 skill 怎么选（节点⑥）

| 素材类型 | 用 |
|----------|-----|
| 现象解读、人物故事、调查报告类长文 | henry-writer |
| 论文 / 模型发布 / 技术博客的大众化转译 | tech-blog-writer |
| 商业合作稿（已有提纲展开成正文） | commercial-article |
| 招股书 / IPO 文件解读 | prospectus-decoder |

**所有写作 skill 的语言风格 DNA 统一由 henry-writer 定**（禁破折号、禁中式冒号乱用、「」标术语、禁 metadiscourse、人优先于事、判断在事实之后）。任何一篇稿子需要按 henry 语言风格润色，都回 henry-writer，不另起标准，避免风格分叉。

---

## 三个评估/迭代工具的分工

- **cold-reader**：发表**前**，独立空白上下文，预判读者会在哪里掉队 + 加权评分。
- **skill-editor**：发表**后**，拿真实数据回溯，把反复出现的盲区升级回 skill。
- 两者共用一套诊断语言，指向 henry-writer 同样的位置，所以一个反复出现的冷读信号能无缝升级成一次 skill-editor 修改。

校准回路是整个 loop 里唯一有真值（读者数据）喂进来的环节。做对它，其他节点会被它自动带着进化。

---

## 这套系统不做什么

- 不替你做角度取舍（④ 永远是人）。LLM 判别器在「有真值」的维度（事实、结构、违禁词）可靠，在「无真值」的维度（横向映射妙不妙、共鸣强不强）系统性偏向平庸，补不上你那 20 分。
- 不无限自对弈。主观质量上，更多轮冷读会把稿子越磨越光滑、越磨越平庸（分数不线性上升，中间某轮往往比最后一轮好）。冷读默认一轮，反复出现的问题才升级 skill。
- 不让脚手架永远在场。模型每次大版本更新，挑一篇难度适中的稿子关掉某个节点裸跑，看数据掉不掉，让数据告诉你这根脚手架还 load-bearing 不。详见 decisions。
