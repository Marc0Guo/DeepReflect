# Recipe: AI Chat History Roast Report

A brief for any LLM generating a **single self-contained HTML file** — **Vibe Roast** (轻松搞怪，不是年终总结 / annual review deck, not playlist clone) — from a developer's AI coding history.

Output: `roast-report.html` in the user's language. Optional second file if they want both locales.

Reference samples:

- Chinese (more 梗): [`../examples/sample/roast-report.zh.html`](../examples/sample/roast-report.zh.html)
- English: [`../examples/sample/roast-report.en.html`](../examples/sample/roast-report.en.html)
- Index: [`../examples/sample/roast-report.html`](../examples/sample/roast-report.html)

---

## Goal

Given pasted or exported chat history (Claude Code, Cursor, ChatGPT, commits, terminal, TODOs), produce a page that:

1. Performs **real forensic analysis** (not generic jokes).
2. Feels like an AI **psychological profile** mixed with a **dev postmortem**.
3. Branded **Vibe Roast** — candy colors, emoji tabs, playful fonts. Inspired by playlist-roast energy but **different fonts, palette, layout** (no Caveat/Patrick beige scrapbook). **Never** title it 年终总结 / Annual Report / Year in Review.
4. Captures cleanly at **~900px width**, long vertical layout.

Tone: clever, observant, slightly unhinged, accurate enough to feel personal — *"an AI secretly judging your engineering habits."*

---

## Prerequisite (agent — before this recipe)

The skill owner should have completed **Step 0** in [`../SKILL.md`](../SKILL.md): user chose **agent memory (1)** or **disk extract (2/3)**.

- If you were told to generate HTML but never got that choice → **stop and ask** (see SKILL.md). Do not run extract scripts while writing HTML.
- This recipe assumes history is **already available** in context or from a finished extract output.

---

## Step 1: Read the history and find the angle

Before HTML, scan everything for:

| Signal | What to look for |
|--------|------------------|
| Debugging loops | Same error 3+ times, "still broken", stack trace déjà vu |
| Overengineering | Premature abstractions, microservices for a script |
| Framework obsession | New stack every session, "rewrite in X" |
| Copy-paste behavior | Huge pasted logs, "fix this" without context |
| Commit vibe | `wip`, `maybe fix`, `asdf`, revert chains |
| Emotional arc | Polite → desperate → ALL CAPS → "nvm ill sleep" |
| Late-night spiral | Timestamps or tone shift after midnight |
| AI dependency | "just do it for me", refusal to read docs |
| Abandoned side quests | "also can we add…" then never mentioned again |
| Search patterns | "why doesn't it work", tab-completion energy |
| Delusional decision | Funniest architecture / tool choice |
| Aura moment | One prompt that was actually senior-engineer energy |
| 2am sentence | Most likely message typed at 2am (verbatim style) |

Write the **angle** in one sentence. All sections support it.

---

## Step 2: Content blocks (required, in order)

### 1. Vibe Roast header + score sticker

- **Brand line** (always): `Vibe Roast` in Fredoka uppercase
- Ribbon: e.g. `🔥 vibe check failed` / `vibe check 未通过`
- Main title (localized, punchy — **not** 年终总结):
  - zh: e.g. **你的聊天记录被公开处刑了** (ZCOOL KuaiLe + Fredoka)
  - en: e.g. **Your Chat History Got Cooked**
- Sub line disclaiming annual-review vibe
- **Score sticker**: score **/100** + funny label (zh can use more internet slang)

### 2. Stat bubbles (4 cells)

- Rounded candy-color bubbles with slight rotation; big Fredoka numbers

### 3. 🎤 开场白 — vibe summary

- Comic `.tab` label + pastel `.block` card
- Lead line + `<em>` highlights + one paragraph of **specific** patterns

### 4. 📊 离谱数据 — engineering spectrum

- Emoji tab + mint/sky block
- 4–8 chunky rounded **bars** with pink→purple gradient fill (div-based, not Chart.js)
- Labels tailored to *this* user, e.g.:
  - `Debugging in circles`
  - `Asking AI to read docs for you`
  - `Actually shipping`
  - `Framework tourism`
- Percentages inferred from evidence (rough is fine; be consistent)
- Row of **stat pills** below: e.g. `Cursor ×47`, `git reset ×3`, `it works on my machine ×∞`

### 5. 🧃 踩坑口味 — debugging taxonomy

- 2×2 **mini-grid** emoji cards (not numbered corporate ledger)
- Examples: `🔄 等等为啥循环`, `📋 堆栈降神`

### 6. 💥 年度名场面

- **Speech bubble** for most chaotic prompt (trim ~120 chars) + side-note 鉴定
- Two-column mini cards: repeated mistake + “should have been a script”
- Risk line in pop color (wavy `.danger` OK)

### 7. Most repeated mistake (inside §6)

- What they keep doing wrong (wrong API, same typo, re-introducing the bug)
- Count if possible: *"asked about CORS 6 times"*

### 7. Most "this should have been a script"

- A moment they used 40 prompts for a 10-line automation task
- Sarcastic one-liner justification

### 8. Most dangerous architecture decision

- Funniest/scariest structural choice (microservices, blockchain, 12 env vars)
- Red underline energy

### 9. 🎢 情绪过山车

- Playful dashed SVG path + colored dots + Nunito labels (vibe map, not accurate chart)
- 5 phases: hope → paste repo → rage → new stack → sleep?

### 10. AI Dependency Report

- Short bullets or mini cards:
  - % prompts that are "just fix it"
  - Tool loyalty (Claude vs Cursor vs ChatGPT)
  - "Would have Googled in 2019" index
- One **diagnosis line** in Kalam font

### 11. 🏆 Vibe Roast grand prize (gradient award block)

- Purple→pink `.award` card: 4 short paragraphs, specific observations
- Final **Vibe score** + playful upgrade quest (not corporate OKR)

### 12. Footer diagnosis card

- White centered card, therapist parody quote
- Sign-off: `— Vibe Roast Lab · [date]`

---

## Language rules

| Locale | Copy tone | Filename |
|--------|-----------|----------|
| **zh** | More 梗/网络语：班味、已读乱回、冥场面、脚手架批发商、电子咸菜 — still specific to user's logs | `roast-report.html` or `roast-report.zh.html` |
| **en** | Dev-Twitter roast: "got cooked", "brain rot metrics", "vibe bankruptcy" | `roast-report.html` or `roast-report.en.html` |

If user writes in Chinese → zh HTML. English → en HTML. If they want **both**, generate two files with the same data and cross-link (`lang-pill` anchor optional).

Match the visual system from the matching sample (`.zh.html` / `.en.html`).

---

## Step 3: Visual design system

**Playful party roast** — light, cheerful, slightly unhinged. Take **energy** from playlist-roast (pastel blocks, rotation, pills, roast tone) but **do not clone**:

| Avoid (playlist) | Use instead (this skill) |
|------------------|---------------------------|
| Beige `#fef9e7` paper | Mint→lavender **gradient** background + confetti dots |
| Caveat, Patrick Hand, Kalam | **Fredoka**, **Nunito**, **ZCOOL KuaiLe** |
| `⌜ THE VIBE ⌝` yellow sticky | Emoji **`.tab`** labels (🎤 📊 🧃 💥 🎢) |
| Circular double-border stamp | Tilted **score sticker** rectangle |
| Washi tape `::before` | Bold 2px borders + offset box-shadow |

### Color tokens

```css
:root {
  --ink: #2a2340;
  --pop: #ff4d8d;
  --pop2: #7c5cff;
  --hi: #fff066;
  --mint: #b8f5e4;
  --lemon: #fff3a8;
  --coral: #ffd4e8;
  --sky: #c8e4ff;
  --lilac: #e4d4ff;
}
```

### Fonts (one Google Fonts link)

- **ZCOOL KuaiLe** — main Chinese title
- **Fredoka** — section leads, speech bubble, pills
- **Nunito** — body

### Page shell

- `.page` ~900px on gradient bg; `#report-page` for export
- Slight `rotate()` on `.block` cards and stat bubbles — vary ±1deg
- `.block` = 2px ink border + rounded corners + candy fill

### Marker highlight (`em`)

html2canvas-safe — single-color gradient only:

```css
em {
  background-image: linear-gradient(var(--hi), var(--hi));
  background-size: 100% 0.38em;
  background-position: 0 100%;
}
```

### Decorations

- Speech bubble for chaotic prompt (CSS triangle tail)
- Dashed SVG coaster line for emotional arc
- Gradient `.award` closing — not navy corporate footer
- `.danger` = hot pink wavy underline

---

## Step 4: Technical requirements

| Rule | Detail |
|------|--------|
| Output | **One** complete `.html` file only |
| CSS/JS | Inline only — no external CSS except Google Fonts + html2canvas CDN |
| No React | No build step, no backend |
| Width | ~900px content column |
| Export target | `#report-page` (exclude `.export-bar`) |
| Responsive | Readable on mobile; optimized for screenshot |

### Export bar (fixed, outside `#report-page`)

```html
<div class="export-bar" id="export-bar">
  <button type="button" id="save-png">Save as PNG</button>
</div>
```

```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
```

```js
async function exportPNG() {
  if (document.fonts?.ready) await document.fonts.ready;
  const bar = document.getElementById('export-bar');
  bar.style.display = 'none';
  const target = document.getElementById('report-page');
  const canvas = await html2canvas(target, {
    backgroundColor: '#e8f7ff',
    scale: 2,
    useCORS: true,
    logging: false,
    windowWidth: 972,
  });
  const link = document.createElement('a');
  link.download = 'ai-roast-report.png';
  link.href = canvas.toDataURL('image/png');
  link.click();
  bar.style.display = '';
}
document.getElementById('save-png').addEventListener('click', exportPNG);
```

### html2canvas gotchas

- Never use multi-stop `linear-gradient` on `<em>` for highlights
- Always `await document.fonts.ready`
- Pass explicit `backgroundColor` and `scale: 2`
- Capture `#report-page`, not `body`

---

## Step 5: Tone personas (optional)

Default: **forensic roast friend**. User may request:

| Persona | Effect |
|---------|--------|
| Gentle roast | Pointed but affectionate |
| Senior engineer deadpan | "Interesting choice." |
| Startup founder brain | Everything is a pivot |
| 2am therapist | Validates spirals while roasting them |

Persona changes copy only — keep the **Vibe Roast** visual system and brand name.

---

## Step 6: Output checklist

Before finishing, verify:

- [ ] All 12 sections present
- [ ] No placeholder / lorem text
- [ ] At least 5 specifics from the user's actual history
- [ ] `#report-page` wraps shareable content
- [ ] Save as PNG works (fonts + highlight CSS safe)
- [ ] File opens offline except CDN fonts/canvas

Suggest: `open roast-report.html`
