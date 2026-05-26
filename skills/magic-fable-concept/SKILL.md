---
name: magic-fable-concept
description: Create a Chinese fable around a user-provided concept using Detective Conan characters, then present it as an immersive web experience. Use when the user asks to (1) write a fable/parable/story around a concept with Conan characters, (2) present a concept through a story-webpage combination, (3) create an immersive web page for a philosophical/cinematic concept, or (4) any task involving "concept + fable + web presentation". The skill covers both the narrative writing (1000-word fable with concept analysis and test questions) and the frontend webapp (theatrical immersive single-page experience with visual metaphors and core effects).
---

# Magic Fable Concept

## Overview

This skill produces a two-part deliverable:

1. **A Chinese fable** (1000 words) using 2-3 Detective Conan characters that indirectly wraps around a user-provided concept, followed by explicit concept analysis and two test questions
2. **An immersive web experience** that presents the fable and concept with visual metaphors, core effects, and theatrical interactions

## Workflow

### Phase 1: Write the Fable

1. Understand the user's concept
2. Select 2-3 Conan characters whose traits map to the concept's dimensions (see references/fable-writing.md for full character guide)
3. Choose a concrete daily-life scene (cafe, school, train, backstage, etc.)
4. Write the fable following all constraints (no concept names in body, no banned openings, 2-3 characters only)
5. Write concept analysis mapping story elements to the concept
6. Write two test questions (comprehension + transfer)
7. Run quality check

**For full writing rules, character guide, and quality checklist: read references/fable-writing.md**

### Phase 2: Design the Web Experience

1. Determine the core visual metaphor based on the concept and fable content
2. Select aesthetic direction (dark brutalism, zen minimal, cyberpunk, retro film, organic nature, industrial)
3. Write design PRD (design.md) covering: visual system, page structure, core effects, animations, interactions
4. For full design guidelines: read references/web-presentation.md

### Phase 3: Build the Webapp

1. Use webapp-building skill to init project
2. Install additional deps: `gsap @studio-freight/lenis three threejs-toys`
3. Generate images using generate_image (6-10 images, grayscale/dark palette, 16:9 or 2:3)
4. Implement sections in order:
   - LoadingCurtain (click-to-open, sessionStorage persistence)
   - HeroSection (title, spotlight canvas, SVG decorations)
   - Act1Fable (two-column: character card + fable text, scroll reveal)
   - Act2Analysis (concept name display, definition block, mapping table)
   - TransitionIntermission (full-screen visual break, elastic ribbon or particles)
   - Act3Questions (focus-mode hover cards with test questions)
   - Act4Farewell (quote, closing statement, replay button)
   - Footer
5. Implement global effects: ParticleBackground (Three.js), ActIndicator, smooth scroll
6. Build and deploy

**For full web implementation details, tech stack, and effect patterns: read references/web-presentation.md**

## Standard Page Sections

```
LoadingCurtain    →  Click to open, sessionStorage remembers state
HeroSection       →  Title + subtitle + spotlight + scroll indicator
Act1Fable         →  Character cards + fable text, scroll reveal
Act2Analysis      →  Concept name + definition + mapping table
Transition        →  Full-screen visual intermission
Act3Questions     →  Two question cards with focus-mode hover
Act4Farewell      →  Quote + closing + replay button
Footer            →  Minimal
```

## Standard Color Palette (Dark Brutalism Default)

```css
--color-bg: #111111;
--color-bg-alt: #1a1a1a;
--color-text: #ffffff;
--color-text-dim: #808080;
--color-border: #333333;
```

Adapt based on chosen aesthetic direction.

## Core Effects Library

| Effect | When to Use | Tech |
|--------|------------|------|
| WebGL Particles | Global atmosphere | Three.js ShaderMaterial |
| Canvas 2D Spotlight | Hero section | requestAnimationFrame |
| GSAP Scroll Reveal | Text sections | ScrollTrigger |
| Curtain Transition | Opening/closing | GSAP x-transform |
| Focus Mode Cards | Questions section | CSS hover + siblings |
| Elastic Ribbon | Intermission | Canvas 2D sine waves |
| 3D Text Ripple | Title entrances | GSAP rotateX stagger |

Pick 3-5 effects max. Each must serve the concept metaphor.

## Quality Checklist

Before delivery, verify:

**Fable:**
- [ ] No concept name or terminology in body text
- [ ] No banned opening phrases
- [ ] Only 2-3 characters used
- [ ] Clear scene + at least one twist
- [ ] Analysis accurately maps story to concept
- [ ] Both questions are specific, answerable, test comprehension + transfer

**Web:**
- [ ] Visual metaphor maps to concept
- [ ] All 8 sections present
- [ ] Loading curtain has sessionStorage persistence
- [ ] Smooth scroll works (Lenis)
- [ ] Scroll-driven text reveal in Act 1
- [ ] Focus mode hover on question cards
- [ ] Replay button resets and reloads
- [ ] Mobile responsive (768px breakpoint)
- [ ] Images generated and placed in public/images/
- [ ] Build succeeds without errors
