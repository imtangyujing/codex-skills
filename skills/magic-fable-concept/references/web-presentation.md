# Web Presentation Reference

## Overview
将写好的寓言和概念解析以沉浸式网页形式呈现。网页不仅是内容的容器，其视觉语言和交互设计本身就是对"概念"的具象化表达。

## Workflow
1. 先完成寓言写作（见 fable-writing.md）
2. 根据概念和寓言内容，确定网页的核心视觉隐喻
3. 选择视觉风格（aesthetic direction）
4. 编写设计 PRD（design.md）
5. 使用 webapp-building skill 初始化项目
6. 生成所需图片/视频资源
7. 开发核心特效与页面结构
8. 构建并部署

## Aesthetic Direction Selection
根据概念和寓言选择合适的视觉风格：

| 风格 | 适合的概念类型 | 特征 |
|------|-------------|------|
| 暗色粗野主义 | 身份、边界、制度、压迫 | 纯黑背景、超大字重、零圆角、混凝土灰度 |
| 东方禅意极简 | 时间、留白、虚无、心境 | 大面积留白、宣纸质感、书法体、低饱和度 |
| 赛博朋克霓虹 | 信息、控制、虚拟、未来 | 深色背景+高饱和霓虹、故障艺术、网格线 |
| 复古胶片质感 | 记忆、怀旧、时间流逝 | 暖色调、噪点纹理、胶片边框、手写字 |
| 自然有机 | 生态、循环、生长、联系 | 大地色系、有机曲线、植物纹理、渐变 |
| 工业机械 | 结构、系统、精密、冰冷 | 金属灰、铆钉纹理、齿轮图案、等宽字体 |

## Core Visual Metaphor
网页的视觉元素必须与概念形成映射：
- 页面结构 = 概念的层次/维度
- 色彩变化 = 概念的情绪/张力
- 动画效果 = 概念的动态/过程
- 交互行为 = 概念的参与/体验

例如：
- 概念"入戏" → 戏台作为核心场景，帷幕开合隐喻"进入/退出"，聚光灯隐喻"注意力聚焦"
- 概念"身份边界" → 模糊/清晰的视觉切换，镜像反射，面具元素
- 概念"信息不对称" → 部分隐藏的文本，鼠标揭示，视差层次

## Page Structure
标准的单页沉浸体验结构：

1. **Loading / Curtain** - 加载转场，建立仪式感
2. **Hero** - 标题+核心视觉隐喻，第一眼定调
3. **Act I: Fable** - 寓言正文，滚动逐段揭示
4. **Act II: Analysis** - 概念解析，映射表格
5. **Transition** - 视觉过渡，给用户消化时间
6. **Act III: Questions** - 检验问题，交互卡片
7. **Act IV: Farewell** - 收束引用+重播按钮
8. **Footer** - 极简收尾

## Typography
- **Display**: "Noto Sans SC", weight 900, 超大尺寸 clamp(48px, 10vw, 120px)
- **Body**: "Noto Sans SC", weight 400, 16-18px
- **Labels**: 12px, letter-spacing 0.15em, uppercase
- **Fable text**: 17-18px, line-height 2.2, 逐段揭示
- 标题行高 0.9，正文行高 1.8-2.2
- 大量使用 letter-spacing 作为韵律手段

## Color Palette
根据选定风格定义 CSS 变量：
```css
--color-bg: #111111;       /* 主背景 */
--color-bg-alt: #1a1a1a;   /* 次级背景 */
--color-text: #ffffff;     /* 主文本 */
--color-text-dim: #808080; /* 次文本 */
--color-border: #333333;   /* 边框 */
--color-accent: #ffffff;   /* 强调 */
```

## Core Effects
根据概念选择 3-5 个核心特效：

| 特效 | 技术 | 适用场景 |
|------|------|---------|
| WebGL Particle System | Three.js | 全局背景大气 |
| Canvas 2D Spotlight | requestAnimationFrame | 聚焦、引导 |
| GSAP Text Reveal | GSAP ScrollTrigger | 文本逐段揭示 |
| Curtain Transition | GSAP / CSS | 幕间转场 |
| Parallax Scroll | GSAP ScrollTrigger | 层次深度 |
| Focus Mode Hover | CSS hover + siblings | 注意力聚焦 |
| Elastic Ribbon | Canvas 2D | 过渡装饰 |
| SVG Morphing | CSS animation | 装饰元素 |
| Dithered Gradient | SVG feTurbulence | 纹理背景 |

## Interaction Design
- 帷幕点击开启（sessionStorage 记忆状态）
- 平滑滚动（Lenis）
- 文本随滚动从模糊到清晰
- 角色卡片视差
- 问题卡片 Focus 模式 hover
- 重播按钮重置并刷新
- 右侧 Act 导航指示器

## Tech Stack
- React 19 + TypeScript + Vite + Tailwind CSS
- GSAP (含 ScrollTrigger)
- Three.js (如需 WebGL)
- Canvas 2D (原生，requestAnimationFrame)
- Lenis (平滑滚动)

## Quality Check
- 视觉隐喻是否与概念形成映射
- 特效是否服务于内容而非炫技
- 移动端是否降级优雅
- 加载性能是否合理
- 重播体验是否完整
