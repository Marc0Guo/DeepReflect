"""Generate a TechRoast-style HTML roast page from conversation history."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from jinja2 import Template
from sqlmodel import Session

from deepreflect.analysis.llm_client import LLMClient
from deepreflect.memory.db import get_concepts, get_stats

_ROAST_SYSTEM = """You are TechRoast — the brutally honest, savage-yet-loving tech personality who roasts developers' AI usage habits. Think: a mix of Gordon Ramsay, a senior engineer with too much coffee, and a comedy club MC.

Your job: roast this person's AI conversation history in the style of the TechRoast Instagram account. Be:
- Brutally funny but ultimately encouraging
- Specific — reference the ACTUAL concepts and questions they keep asking about
- Use emoji aggressively
- Use tech slang and memes
- Call out repeated questions mercilessly
- End with a genuine (but still sarcastic) compliment

Format your response as a JSON object with these exact keys:
{
  "headline": "One savage headline (max 10 words, all caps energy)",
  "opening": "2-3 sentence opening roast paragraph",
  "roasts": [
    {
      "concept": "concept name",
      "count": 5,
      "line": "One brutal roast line about asking this question N times"
    }
  ],
  "verdict": "The final 2-3 sentence verdict — still savage but with a kernel of hope",
  "title": "Short fun title for the page",
  "score": 42,
  "score_label": "What this score means (e.g. 'Certified Stack Overflow Tourist')"
}

Keep roasts array to max 5 items (the worst offenders). Score is out of 100 (higher = more of a repeat asker)."""


async def _generate_roast_data(concepts, stats, llm: LLMClient) -> dict:
    top = concepts[:10]
    concept_list = "\n".join(
        f"- '{c.name}' (category: {c.category}, asked {c.ask_count} times)"
        for c in top
    )
    prompt = (
        f"Total AI conversations: {stats['total_turns']}\n"
        f"This week: {stats['weekly_turns']}\n"
        f"Concepts tracked: {stats['total_concepts']}\n\n"
        f"Top repeated topics:\n{concept_list}"
    )

    try:
        raw = await llm.complete(_ROAST_SYSTEM, prompt, max_tokens=1500)
        import re
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            return json.loads(m.group())
    except Exception:
        pass

    # Fallback if LLM fails
    return {
        "headline": "YOUR AI IS BASICALLY YOUR RUBBER DUCK AT THIS POINT",
        "opening": "Wow. Just... wow. I've seen AI conversations before, but this? This is something special. You've turned your AI assistant into a personal tutor, therapist, and Stack Overflow combined. Let's talk about what's happening here.",
        "roasts": [
            {"concept": c.name, "count": c.ask_count, "line": f"You asked about '{c.name}' {c.ask_count} times. At this point just name your firstborn after it. 💀"}
            for c in top[:3]
        ],
        "verdict": "Look, you're clearly passionate about learning. Or you have the memory of a goldfish. Either way, DeepReflect is here to help you break the cycle. Now go read the docs. For real this time.",
        "title": "Your Annual AI Roast",
        "score": min(int(sum(c.ask_count for c in top) / max(len(top), 1) * 10), 100),
        "score_label": "Certified Repeat Asker",
    }


_ROAST_TEMPLATE = Template(r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DeepReflect — {{ data.title }}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800;900&family=Space+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --fire: #ff4500;
  --gold: #ffd700;
  --purple: #9b59b6;
  --teal: #00cec9;
  --pink: #fd79a8;
  --bg: #0d0d0d;
  --card: #161616;
  --border: #2d2d2d;
}

body {
  background: var(--bg);
  font-family: 'Space Grotesk', system-ui, sans-serif;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 32px 20px 120px;
  color: #fff;
  -webkit-font-smoothing: antialiased;
}

.page { width: 440px; max-width: 100%; }

/* FIRE HEADER */
.fire-header {
  text-align: center;
  padding: 48px 28px 40px;
  background: linear-gradient(180deg, #1a0a00 0%, #0d0d0d 100%);
  border: 1px solid #3d1a00;
  border-radius: 24px;
  margin-bottom: 14px;
  position: relative;
  overflow: hidden;
}
.fire-header::before {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(ellipse at 50% -20%, rgba(255,69,0,0.18) 0%, transparent 65%);
  pointer-events: none;
}
.fire-emoji { font-size: 48px; display: block; margin-bottom: 12px; animation: flicker 1.5s ease-in-out infinite alternate; }
@keyframes flicker {
  0% { transform: scale(1) rotate(-2deg); filter: brightness(1); }
  100% { transform: scale(1.05) rotate(2deg); filter: brightness(1.2); }
}
.roast-badge {
  display: inline-flex; align-items: center; gap: 6px;
  font-size: 11px; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase;
  color: var(--fire); background: rgba(255,69,0,0.12); border: 1px solid rgba(255,69,0,0.3);
  padding: 5px 14px; border-radius: 100px; margin-bottom: 20px;
}
.headline {
  font-family: 'Outfit', sans-serif;
  font-size: 22px; font-weight: 900; line-height: 1.2;
  color: #fff; position: relative;
}
.headline em { font-style: normal; color: var(--fire); }
.generated-at { font-size: 12px; color: #555; margin-top: 10px; }

/* SCORE CARD */
.score-card {
  background: linear-gradient(135deg, #1a0033, #0d001a);
  border: 1px solid #3d0066;
  border-radius: 20px;
  padding: 32px 24px;
  text-align: center;
  margin-bottom: 14px;
  position: relative;
  overflow: hidden;
}
.score-card::before {
  content: '';
  position: absolute; inset: 0;
  background: radial-gradient(ellipse at 50% 0%, rgba(155,89,182,0.2) 0%, transparent 70%);
  pointer-events: none;
}
.score-label-text { font-size: 10px; font-weight: 700; letter-spacing: 0.15em; text-transform: uppercase; color: #9b59b6; margin-bottom: 8px; }
.score-num {
  font-family: 'Outfit', sans-serif;
  font-size: 88px; font-weight: 900; line-height: 1;
  background: linear-gradient(135deg, var(--purple), var(--pink));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
  filter: drop-shadow(0 0 40px rgba(155,89,182,0.4));
}
.score-suffix { font-family: 'Outfit', sans-serif; font-size: 32px; font-weight: 700; color: #555; -webkit-text-fill-color: #555; }
.score-title { font-size: 14px; font-weight: 600; color: #ccc; margin-top: 10px; }

/* OPENING */
.panel {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 24px;
  margin-bottom: 14px;
}
.panel-label {
  font-size: 10px; font-weight: 700; letter-spacing: 0.15em; text-transform: uppercase;
  margin-bottom: 14px; display: flex; align-items: center; gap: 6px;
}
.panel-label .dot { width: 6px; height: 6px; border-radius: 50%; background: var(--fire); }
.opening-text { font-size: 15px; line-height: 1.7; color: #ccc; }

/* ROAST ITEMS */
.roast-item {
  display: flex; gap: 14px; align-items: flex-start;
  padding: 16px 0;
  border-bottom: 1px solid var(--border);
}
.roast-item:last-child { border-bottom: none; }
.roast-count {
  font-family: 'Outfit', sans-serif;
  font-size: 28px; font-weight: 900;
  color: var(--fire); min-width: 48px; text-align: center;
  line-height: 1;
}
.roast-count-x { font-size: 14px; font-weight: 600; color: #555; display: block; }
.roast-concept { font-size: 13px; font-weight: 700; color: var(--gold); margin-bottom: 4px; }
.roast-line { font-size: 13px; line-height: 1.6; color: #aaa; }

/* VERDICT */
.verdict-panel {
  background: linear-gradient(135deg, #0a1a0a, #001a0d);
  border: 1px solid #1a4d1a;
  border-radius: 20px;
  padding: 28px 24px;
  margin-bottom: 14px;
  position: relative;
  overflow: hidden;
}
.verdict-panel::before {
  content: '';
  position: absolute; inset: 0;
  background: radial-gradient(ellipse at 50% 100%, rgba(0,206,201,0.08) 0%, transparent 70%);
}
.verdict-label { font-size: 10px; font-weight: 700; letter-spacing: 0.15em; text-transform: uppercase; color: var(--teal); margin-bottom: 12px; }
.verdict-text { font-size: 15px; line-height: 1.7; color: #ccc; position: relative; }

/* STATS ROW */
.stats-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 14px; }
.stat-chip {
  background: var(--card); border: 1px solid var(--border);
  border-radius: 16px; padding: 20px 16px; text-align: center;
}
.stat-chip .num { font-family: 'Outfit', sans-serif; font-size: 36px; font-weight: 900; color: var(--teal); display: block; }
.stat-chip .lbl { font-size: 10px; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; color: #555; margin-top: 4px; }

/* FOOTER */
.roast-footer { text-align: center; padding: 28px 20px; }
.footer-logo { font-family: 'Outfit', sans-serif; font-size: 14px; font-weight: 800; color: #555; letter-spacing: 0.08em; }
.footer-logo .accent { color: var(--fire); }
.footer-date { font-size: 11px; color: #333; margin-top: 4px; }
.footer-tag { font-size: 12px; color: #444; margin-top: 10px; font-style: italic; }

/* EXPORT */
.export-bar { position: fixed; bottom: 24px; right: 24px; z-index: 9999; display: flex; flex-direction: column; align-items: flex-end; gap: 10px; }
.export-btn {
  background: linear-gradient(135deg, var(--fire), #ff8c00);
  border: none; border-radius: 14px; padding: 14px 24px;
  font-family: 'Outfit', sans-serif; font-weight: 700; font-size: 15px;
  color: #fff; cursor: pointer;
  box-shadow: 0 4px 24px rgba(255,69,0,0.4);
  transition: transform 0.15s, box-shadow 0.15s;
  display: flex; align-items: center; gap: 8px;
}
.export-btn:hover { transform: translateY(-2px); box-shadow: 0 8px 32px rgba(255,69,0,0.5); }
.export-btn[disabled] { opacity: 0.6; cursor: progress; }
.export-tip { background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 8px 14px; font-size: 13px; color: #ccc; display: none; }
.export-tip.show { display: block; }
</style>
</head>
<body>
<div class="page" id="report-page">

  <div class="fire-header">
    <span class="fire-emoji">🔥</span>
    <div class="roast-badge">🎤 TechRoast × DeepReflect</div>
    <div class="headline">{{ data.headline }}</div>
    <div class="generated-at">Roasted on {{ generated_at }}</div>
  </div>

  <div class="score-card">
    <div class="score-label-text">Repeat Asker Score</div>
    <div class="score-num">{{ data.score }}<span class="score-suffix">/100</span></div>
    <div class="score-title">{{ data.score_label }}</div>
  </div>

  <div class="stats-row">
    <div class="stat-chip">
      <span class="num">{{ stats.total_turns }}</span>
      <span class="lbl">Total Convos</span>
    </div>
    <div class="stat-chip">
      <span class="num">{{ stats.total_concepts }}</span>
      <span class="lbl">Concepts</span>
    </div>
  </div>

  <div class="panel">
    <div class="panel-label"><span class="dot"></span> The Roast Begins</div>
    <p class="opening-text">{{ data.opening }}</p>
  </div>

  <div class="panel">
    <div class="panel-label" style="color: var(--gold);"><span class="dot" style="background: var(--gold)"></span> Hall of Shame</div>
    {% for r in data.roasts %}
    <div class="roast-item">
      <div class="roast-count">{{ r.count }}<span class="roast-count-x">times</span></div>
      <div>
        <div class="roast-concept">{{ r.concept }}</div>
        <div class="roast-line">{{ r.line }}</div>
      </div>
    </div>
    {% endfor %}
  </div>

  <div class="verdict-panel">
    <div class="verdict-label">🏆 The Verdict</div>
    <p class="verdict-text">{{ data.verdict }}</p>
  </div>

  <div class="roast-footer">
    <div class="footer-logo">Deep<span class="accent">Roast</span> by DeepReflect</div>
    <div class="footer-date">{{ generated_at }}</div>
    <div class="footer-tag">"Knowledge is knowing a tomato is a fruit. Wisdom is not asking your AI about it for the 8th time."</div>
  </div>
</div>

<div class="export-bar" id="export-bar">
  <div class="export-tip" id="export-tip">Saved! Show it off 🔥</div>
  <button class="export-btn" id="export-btn" type="button">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
    Save as PNG
  </button>
</div>

<script>
(function(){
  const btn = document.getElementById('export-btn');
  const tip = document.getElementById('export-tip');
  const bar = document.getElementById('export-bar');
  btn.addEventListener('click', async function() {
    if (typeof html2canvas !== 'function') { alert('Library not loaded yet.'); return; }
    const orig = btn.innerHTML; btn.disabled = true; btn.textContent = 'Rendering…'; bar.style.display = 'none';
    try {
      if (document.fonts && document.fonts.ready) await document.fonts.ready;
      const canvas = await html2canvas(document.getElementById('report-page'), { backgroundColor: '#0d0d0d', scale: 2, useCORS: true, logging: false });
      const link = document.createElement('a'); link.download = 'deepreflect-roast.png'; link.href = canvas.toDataURL('image/png'); link.click();
      bar.style.display = ''; tip.classList.add('show'); setTimeout(() => tip.classList.remove('show'), 3000);
    } catch(e) { bar.style.display = ''; alert('Export failed: ' + e.message); }
    finally { btn.disabled = false; btn.innerHTML = orig; }
  });
})();
</script>
</body>
</html>
""")


async def generate_roast_html(
    session: Session,
    llm: LLMClient,
    out_dir: Path | None = None,
) -> Path:
    stats = get_stats(session)
    concepts = get_concepts(session, min_ask_count=2)[:10]

    roast_data = await _generate_roast_data(concepts, stats, llm)

    html = _ROAST_TEMPLATE.render(
        data=roast_data,
        stats=stats,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
    )

    if out_dir is None:
        out_dir = Path.home() / ".deepreflect" / "data" / "summaries"
    out_dir.mkdir(parents=True, exist_ok=True)

    filename = f"roast_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    out_path = out_dir / filename
    out_path.write_text(html, encoding="utf-8")
    return out_path


