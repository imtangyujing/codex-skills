# QbitAI Title Generator Skill

基于量子位（QbitAI）爆款文章标题深度分析的科技类标题生成器。

## 安装方法

### 方法1：直接复制
1. 将 `SKILL.md` 文件复制到你的 Agent 的 skills 目录下
2. 确保目录结构为：`your-skills-dir/quantum-bit-title-generator/SKILL.md`

### 方法2：完整导入
将整个 `quantum-bit-title-skill` 文件夹复制到你的 skills 目录：
```
your-skills-dir/
└── quantum-bit-title-generator/
    ├── SKILL.md          # 主技能文件
    ├── README.md         # 本文件
    └── evals/
        └── evals.json    # 测试用例
```

## 使用方法

当用户需要给科技类文章起标题时，Agent 会自动触发此 Skill。

**触发关键词：**
- "起标题"
- "爆款标题"
- "标题生成"
- "给这篇文章起标题"
- 等...

**输入示例：**
```
给这篇文章起几个爆款标题：OpenAI发布GPT-5，性能提升10倍...
```

**输出格式：**
- 文章主题分析
- 候选标题（按爆款潜力排序）
- 复制版标题（纯列表，方便复制）

## Skill 特点

- 基于 785 篇量子位文章数据分析
- 四大爆款公式：名人+惊人事实、数字+核心发现、突发+重大事件、反差+悬念
- 自动提取核心人物、关键数字、颠覆性发现
- 生成 5+ 个不同风格的候选标题

## 作者

通过 LobsterAI HammerChain 创建
