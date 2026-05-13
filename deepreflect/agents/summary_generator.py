"""Generate shareable, cinematic HTML summary pages — 年度总结 style."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from jinja2 import Template
from sqlmodel import Session

from deepreflect.memory.db import get_concepts, get_stats, get_turns

_TEMPLATE = Template(r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DeepReflect — {{ period_label }} Summary</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800;900&family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600&display=swap" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
:root {
  --teal: #2dd4bf; --indigo: #818cf8; --amber: #fbbf24;
  --rose: #fb7185; --green: #4ade80; --purple: #c084fc;
  --bg: #050a0e; --card: #0a1118; --surface: #0f1923;
  --border: #1a2d3d; --text: #e2e8f0; --muted: #94a3b8;
  --faint: #475569; --veryfaint: #1e293b;
}
body {
  background: var(--bg); color: var(--text);
  font-family: 'DM Sans', system-ui, sans-serif;
  min-height: 100vh; display: flex; flex-direction: column;
  align-items: center; padding: 48px 20px 140px;
  -webkit-font-smoothing: antialiased;
}
.page { width: 440px; max-width: 100%; }

/* GLOWING HERO */
.hero {
  background: linear-gradient(180deg, #091824 0%, #050a0e 100%);
  border: 1px solid var(--border); border-radius: 28px;
  padding: 56px 32px 48px; text-align: center;
  position: relative; overflow: hidden; margin-bottom: 14px;
}
.hero-glow {
  position: absolute; top: -100px; left: 50%;
  transform: translateX(-50%);
  width: 360px; height: 360px;
  background: radial-gradient(circle, rgba(45,212,191,0.15) 0%, transparent 65%);
  pointer-events: none;
}
.hero-glow2 {
  position: absolute; bottom: -80px; right: -60px;
  width: 240px; height: 240px;
  background: radial-gradient(circle, rgba(129,140,248,0.1) 0%, transparent 65%);
  pointer-events: none;
}
.hero-logo { display: inline-flex; align-items: center; gap: 8px; margin-bottom: 24px; }
.hero-logo .icon {
  width: 30px; height: 30px; border-radius: 9px;
  background: linear-gradient(135deg, var(--teal), var(--indigo));
  display: flex; align-items: center; justify-content: center;
}
.hero-logo span { font-family: 'Outfit', sans-serif; font-size: 14px; font-weight: 700; letter-spacing: 0.08em; color: var(--muted); }
.period-chip {
  font-family: 'Outfit', sans-serif; font-size: 11px; font-weight: 700;
  letter-spacing: 0.15em; text-transform: uppercase; color: var(--teal);
  background: rgba(45,212,191,0.08); border: 1px solid rgba(45,212,191,0.2);
  padding: 5px 16px; border-radius: 100px; display: inline-block; margin-bottom: 20px;
}
.hero h1 {
  font-family: 'Outfit', sans-serif; font-size: 34px; font-weight: 900;
  line-height: 1.15; color: var(--text); position: relative;
}
.hero h1 .accent {
  background: linear-gradient(135deg, var(--teal), var(--indigo));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.hero .date-range { font-size: 13px; color: var(--faint); margin-top: 12px; }

/* HIGHLIGHT BANNER */
.highlight {
  background: linear-gradient(135deg, rgba(45,212,191,0.07), rgba(129,140,248,0.05));
  border: 1px solid rgba(45,212,191,0.15); border-radius: 22px;
  padding: 40px 28px; text-align: center; margin-bottom: 14px;
}
.big-num {
  font-family: 'Outfit', sans-serif; font-size: 80px; font-weight: 900; line-height: 1;
  background: linear-gradient(135deg, var(--teal), var(--indigo));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
  filter: drop-shadow(0 0 40px rgba(45,212,191,0.3));
}
.big-label { font-family: 'Outfit', sans-serif; font-size: 15px; font-weight: 600; color: var(--muted); margin-top: 8px; }
.big-sub { font-size: 12px; color: var(--faint); margin-top: 4px; }

/* STAT GRID */
.stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 14px; }
.stat-card {
  background: var(--card); border: 1px solid var(--border);
  border-radius: 20px; padding: 24px 18px; text-align: center;
  position: relative; overflow: hidden;
}
.stat-card::after {
  content: ''; position: absolute; top: 0; left: 0; right: 0;
  height: 2px; border-radius: 20px 20px 0 0;
}
.stat-card:nth-child(1)::after { background: linear-gradient(90deg, var(--teal), transparent); }
.stat-card:nth-child(2)::after { background: linear-gradient(90deg, var(--indigo), transparent); }
.stat-card:nth-child(3)::after { background: linear-gradient(90deg, var(--amber), transparent); }
.stat-card:nth-child(4)::after { background: linear-gradient(90deg, var(--rose), transparent); }
.stat-num { font-family: 'Outfit', sans-serif; font-size: 42px; font-weight: 900; line-height: 1; display: block; margin-bottom: 6px; }
.stat-card:nth-child(1) .stat-num { color: var(--teal); text-shadow: 0 0 30px rgba(45,212,191,.3); }
.stat-card:nth-child(2) .stat-num { color: var(--indigo); text-shadow: 0 0 30px rgba(129,140,248,.3); }
.stat-card:nth-child(3) .stat-num { color: var(--amber); text-shadow: 0 0 30px rgba(251,191,36,.3); }
.stat-card:nth-child(4) .stat-num { color: var(--rose); text-shadow: 0 0 30px rgba(251,113,133,.3); }
.stat-label { font-family: 'Outfit', sans-serif; font-size: 10px; font-weight: 600; letter-spacing: .1em; text-transform: uppercase; color: var(--faint); }

/* PANEL */
.panel { background: var(--card); border: 1px solid var(--border); border-radius: 22px; padding: 28px 24px; margin-bottom: 14px; }
.panel-label { font-family: 'Outfit', sans-serif; font-size: 10px; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; color: var(--faint); margin-bottom: 18px; display: flex; align-items: center; gap: 6px; }
.panel-label .dot { width: 6px; height: 6px; border-radius: 50%; background: var(--teal); }

/* SOURCES */
.chips { display: flex; flex-wrap: wrap; gap: 8px; }
.chip { font-size: 12px; font-weight: 500; padding: 6px 14px; border-radius: 10px; background: var(--surface); border: 1px solid var(--border); color: var(--muted); display: flex; align-items: center; gap: 6px; }
.chip .cnt { color: var(--teal); font-family: 'Outfit', sans-serif; font-weight: 700; }

/* CATEGORY BREAKDOWN */
.cat-row { display: flex; align-items: center; gap: 10px; padding: 10px 0; border-bottom: 1px solid rgba(26,45,61,.5); }
.cat-row:last-child { border-bottom: none; }
.cat-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.cat-name { font-size: 12px; font-weight: 600; color: var(--text); flex: 1; }
.cat-bar-wrap { width: 100px; }
.cat-bar { height: 4px; background: var(--veryfaint); border-radius: 99px; overflow: hidden; }
.cat-bar-fill { height: 100%; border-radius: 99px; }
.cat-count { font-family: 'Outfit', sans-serif; font-size: 11px; color: var(--faint); text-align: right; margin-top: 2px; }
.cat-python { color: #60a5fa; }
.cat-ml { color: #a78bfa; }
.cat-git { color: #fb923c; }
.cat-web { color: #34d399; }
.cat-data { color: #22d3ee; }
.cat-math { color: #fbbf24; }
.cat-general { color: #94a3b8; }
.cat-other { color: #94a3b8; }

/* TOP CONCEPTS */
.concept-item { display: flex; align-items: center; gap: 12px; padding: 14px 0; border-bottom: 1px solid rgba(26,45,61,.5); }
.concept-item:last-child { border-bottom: none; }
.rank { font-family: 'Outfit', sans-serif; font-size: 26px; font-weight: 900; width: 36px; text-align: center; flex-shrink: 0; }
.rank.r1 { color: var(--teal); filter: drop-shadow(0 0 10px rgba(45,212,191,.4)); }
.rank.r2 { color: var(--indigo); }
.rank.r3 { color: var(--amber); }
.rank.rn { color: var(--faint); font-size: 18px; }
.c-info { flex: 1; min-width: 0; }
.c-name { font-size: 14px; font-weight: 600; color: var(--text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.c-meta { font-size: 11px; color: var(--faint); margin-top: 3px; display: flex; align-items: center; gap: 6px; }
.c-tag { font-size: 10px; font-weight: 600; padding: 2px 8px; border-radius: 6px; text-transform: uppercase; letter-spacing: .04em; }
.weak-tag { background: rgba(251,113,133,.1); color: var(--rose); font-size: 10px; font-weight: 600; padding: 2px 7px; border-radius: 5px; }
.c-bar-wrap { width: 80px; flex-shrink: 0; }
.c-bar { height: 4px; background: var(--veryfaint); border-radius: 99px; overflow: hidden; }
.c-bar-fill { height: 100%; border-radius: 99px; background: linear-gradient(90deg, var(--teal), var(--indigo)); }
.c-count { font-family: 'Outfit', sans-serif; font-size: 10px; color: var(--faint); text-align: right; margin-top: 2px; }

/* ACTIVITY HEATMAP */
.heatmap-grid { display: flex; flex-wrap: wrap; gap: 3px; }
.heatmap-cell {
  width: 12px; height: 12px; border-radius: 3px;
  background: var(--veryfaint);
}
.heatmap-cell.l1 { background: rgba(45,212,191,.25); }
.heatmap-cell.l2 { background: rgba(45,212,191,.5); }
.heatmap-cell.l3 { background: rgba(45,212,191,.75); }
.heatmap-cell.l4 { background: var(--teal); box-shadow: 0 0 6px rgba(45,212,191,.4); }
.heatmap-legend { display: flex; align-items: center; gap: 4px; margin-top: 10px; }
.heatmap-legend span { font-size: 10px; color: var(--faint); }

/* #1 SPOTLIGHT */
.spotlight {
  background: linear-gradient(135deg, rgba(45,212,191,.06), rgba(129,140,248,.04));
  border: 1px solid rgba(45,212,191,.15); border-radius: 20px;
  padding: 32px 24px; text-align: center; margin-bottom: 14px;
}
.spotlight .top-name {
  font-family: 'Outfit', sans-serif; font-size: 26px; font-weight: 900;
  color: var(--teal); filter: drop-shadow(0 0 16px rgba(45,212,191,.3));
  margin-top: 4px;
}
.spotlight .top-sub { font-size: 12px; color: var(--faint); margin-top: 6px; }

/* FOOTER */
.report-footer { text-align: center; padding: 32px 24px; background: var(--card); border: 1px solid var(--border); border-radius: 20px; margin-bottom: 14px; }
.footer-brand { font-family: 'Outfit', sans-serif; font-size: 13px; font-weight: 700; color: var(--faint); letter-spacing: .08em; }
.footer-brand .accent { color: var(--teal); }
.footer-date { font-size: 11px; color: var(--veryfaint); margin-top: 6px; }
.footer-tag { font-size: 12px; color: var(--faint); margin-top: 12px; font-style: italic; }

/* EXPORT */
.export-bar { position: fixed; bottom: 28px; right: 28px; z-index: 9999; display: flex; flex-direction: column; align-items: flex-end; gap: 10px; }
.export-btn {
  background: linear-gradient(135deg, var(--teal), #14b8a6);
  border: none; border-radius: 14px; padding: 14px 24px;
  font-family: 'Outfit', sans-serif; font-weight: 700; font-size: 15px;
  color: #050a0e; cursor: pointer;
  box-shadow: 0 4px 24px -4px rgba(45,212,191,.4);
  transition: transform .15s, box-shadow .15s;
  display: flex; align-items: center; gap: 8px;
}
.export-btn:hover { transform: translateY(-2px); box-shadow: 0 8px 32px -4px rgba(45,212,191,.5); }
.export-btn[disabled] { opacity: .6; cursor: progress; }
.export-tip { background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 8px 14px; font-size: 13px; color: var(--muted); display: none; }
.export-tip.show { display: block; }
@media print { .export-bar { display: none; } }
</style>
</head>
<body>
<div class="page" id="report-page">

  <div class="hero">
    <div class="hero-glow"></div>
    <div class="hero-glow2"></div>
    <div class="hero-logo">
      <div class="icon">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5" stroke-linecap="round">
          <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
        </svg>
      </div>
      <span>DEEPREFLECT</span>
    </div>
    <div class="period-chip">{{ period_label }} Report</div>
    <h1>Your Learning<br><span class="accent">Journey</span></h1>
    <div class="date-range">{{ date_range }}</div>
  </div>

  <div class="highlight">
    <div class="big-num">{{ stats.total_turns }}</div>
    <div class="big-label">Total AI Conversations</div>
    <div class="big-sub">across all your tools and projects</div>
  </div>

  <div class="stats-grid">
    <div class="stat-card"><span class="stat-num">{{ stats.total_turns }}</span><span class="stat-label">Exchanges</span></div>
    <div class="stat-card"><span class="stat-num">{{ stats.weekly_turns }}</span><span class="stat-label">This Week</span></div>
    <div class="stat-card"><span class="stat-num">{{ stats.total_concepts }}</span><span class="stat-label">Concepts</span></div>
    <div class="stat-card"><span class="stat-num">{{ stats.total_flashcards }}</span><span class="stat-label">Flashcards</span></div>
  </div>

  {% if sources %}
  <div class="panel">
    <div class="panel-label"><span class="dot"></span> AI Tools Used</div>
    <div class="chips">
      {% for src, cnt in sources.items() %}
      <span class="chip">{{ src }} <span class="cnt">{{ cnt }}</span></span>
      {% endfor %}
    </div>
  </div>
  {% endif %}

  {% if category_counts %}
  <div class="panel">
    <div class="panel-label" style="color: var(--faint)"><span class="dot" style="background: var(--purple)"></span> Knowledge by Category</div>
    {% set max_cat = category_counts[0][1] %}
    {% for cat, cnt in category_counts %}
    <div class="cat-row">
      <div class="cat-dot" style="background: {{ cat_colors.get(cat, '#94a3b8') }}"></div>
      <div class="cat-name cat-{{ cat }}">{{ cat }}</div>
      <div class="cat-bar-wrap">
        <div class="cat-bar"><div class="cat-bar-fill" style="width: {{ (cnt / max_cat * 100)|int }}%; background: {{ cat_colors.get(cat, '#94a3b8') }}"></div></div>
        <div class="cat-count">{{ cnt }}×</div>
      </div>
    </div>
    {% endfor %}
  </div>
  {% endif %}

  {% if heatmap_cells %}
  <div class="panel">
    <div class="panel-label"><span class="dot" style="background: var(--green)"></span> Activity — Last 30 Days</div>
    <div class="heatmap-grid">
      {% for cell in heatmap_cells %}
      <div class="heatmap-cell {{ cell }}"></div>
      {% endfor %}
    </div>
    <div class="heatmap-legend">
      <span>Less</span>
      <div class="heatmap-cell"></div>
      <div class="heatmap-cell l1"></div>
      <div class="heatmap-cell l2"></div>
      <div class="heatmap-cell l3"></div>
      <div class="heatmap-cell l4"></div>
      <span>More</span>
    </div>
  </div>
  {% endif %}

  {% if concepts %}
  <div class="panel">
    <div class="panel-label"><span class="dot" style="background: var(--indigo)"></span> Top Topics</div>
    {% set max_c = concepts[0].ask_count %}
    {% for c in concepts %}
    <div class="concept-item">
      <span class="rank {% if loop.index == 1 %}r1{% elif loop.index == 2 %}r2{% elif loop.index == 3 %}r3{% else %}rn{% endif %}">{{ loop.index }}</span>
      <div class="c-info">
        <div class="c-name">{{ c.name }}</div>
        <div class="c-meta">
          <span class="c-tag cat-{{ c.category }}" style="background: rgba(148,163,184,.08)">{{ c.category }}</span>
          {% if c.weak_score >= 0.4 %}<span class="weak-tag">needs review</span>{% endif %}
        </div>
      </div>
      <div class="c-bar-wrap">
        <div class="c-bar"><div class="c-bar-fill" style="width: {{ (c.ask_count / max_c * 100)|int }}%"></div></div>
        <div class="c-count">{{ c.ask_count }}×</div>
      </div>
    </div>
    {% endfor %}
  </div>

  {% if concepts|length >= 1 %}
  <div class="spotlight">
    <div class="panel-label" style="justify-content: center; margin-bottom: 8px;"><span class="dot"></span> Your #1 Topic</div>
    <div class="top-name">{{ concepts[0].name }}</div>
    <div class="top-sub">Asked {{ concepts[0].ask_count }} times · {{ concepts[0].category }}</div>
  </div>
  {% endif %}
  {% endif %}

  <div class="report-footer">
    <div class="footer-brand">Deep<span class="accent">Reflect</span></div>
    <div class="footer-date">Generated {{ generated_at }}</div>
    <div class="footer-tag">Your AI usage, mapped into knowledge.</div>
  </div>
</div>

<div class="export-bar" id="export-bar">
  <div class="export-tip" id="export-tip">Saved! ✨</div>
  <button class="export-btn" id="export-btn" type="button">
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
    Save as PNG
  </button>
</div>

<script>
(function(){
  const btn = document.getElementById('export-btn');
  const tip = document.getElementById('export-tip');
  const bar = document.getElementById('export-bar');
  btn.addEventListener('click', async function(){
    if(typeof html2canvas !== 'function'){alert('Library not loaded yet.');return;}
    const orig = btn.innerHTML; btn.disabled = true; btn.textContent = 'Rendering…'; bar.style.display = 'none';
    try {
      if(document.fonts && document.fonts.ready) await document.fonts.ready;
      const el = document.getElementById('report-page');
      const canvas = await html2canvas(el, { backgroundColor: '#050a0e', scale: 2, useCORS: true, logging: false, windowWidth: 520 });
      const link = document.createElement('a');
      link.download = 'deepreflect-{{ period_label|lower }}-report.png';
      link.href = canvas.toDataURL('image/png'); link.click();
      bar.style.display = ''; tip.classList.add('show'); setTimeout(()=>tip.classList.remove('show'), 3000);
    } catch(e){ bar.style.display = ''; alert('Export failed: ' + e.message); }
    finally { btn.disabled = false; btn.innerHTML = orig; }
  });
})();
</script>
</body>
</html>
""")

_CAT_COLORS = {
    "python": "#60a5fa", "ml": "#a78bfa", "git": "#fb923c",
    "web": "#34d399", "data": "#22d3ee", "math": "#fbbf24",
    "general": "#94a3b8", "other": "#94a3b8",
}


def _period_bounds(period: str) -> tuple[datetime, datetime, str, str]:
    now = datetime.now(timezone.utc)
    if period == "daily":
        since = now.replace(hour=0, minute=0, second=0, microsecond=0)
        label, date_range = "Daily", now.strftime("%B %d, %Y")
    elif period == "weekly":
        since = now - timedelta(days=7)
        label = "Weekly"
        date_range = f"{since.strftime('%b %d')} – {now.strftime('%b %d, %Y')}"
    elif period == "monthly":
        since = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        label, date_range = "Monthly", now.strftime("%B %Y")
    elif period == "yearly":
        since = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        label, date_range = "Yearly", now.strftime("%Y")
    else:
        since = now - timedelta(days=7)
        label = "Weekly"
        date_range = f"{since.strftime('%b %d')} – {now.strftime('%b %d, %Y')}"
    return since, now, label, date_range


def _build_heatmap(turns: list, days: int = 30) -> list[str]:
    now = datetime.now(timezone.utc)
    counts: dict[str, int] = {}
    for t in turns:
        ts = t.timestamp
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        day_key = ts.strftime("%Y-%m-%d")
        counts[day_key] = counts.get(day_key, 0) + 1

    cells = []
    for i in range(days - 1, -1, -1):
        day = (now - timedelta(days=i)).strftime("%Y-%m-%d")
        c = counts.get(day, 0)
        if c == 0:
            cells.append("")
        elif c == 1:
            cells.append("l1")
        elif c <= 3:
            cells.append("l2")
        elif c <= 6:
            cells.append("l3")
        else:
            cells.append("l4")
    return cells


def _build_category_counts(concepts) -> list[tuple[str, int]]:
    counts: dict[str, int] = {}
    for c in concepts:
        cat = c.category or "general"
        counts[cat] = counts.get(cat, 0) + c.ask_count
    return sorted(counts.items(), key=lambda x: x[1], reverse=True)


def generate_summary_html(
    session: Session,
    period: str = "weekly",
    out_dir: Path | None = None,
) -> Path:
    since, until, label, date_range = _period_bounds(period)

    stats = get_stats(session)
    concepts = get_concepts(session, min_ask_count=1)[:15]
    sources = stats.get("sources", {})
    all_turns = get_turns(session, limit=5000)
    heatmap_cells = _build_heatmap(all_turns, days=30)
    category_counts = _build_category_counts(concepts)

    html = _TEMPLATE.render(
        period_label=label,
        date_range=date_range,
        stats=stats,
        concepts=concepts,
        sources=sources,
        heatmap_cells=heatmap_cells,
        category_counts=category_counts,
        cat_colors=_CAT_COLORS,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
    )

    if out_dir is None:
        out_dir = Path.home() / ".deepreflect" / "data" / "summaries"
    out_dir.mkdir(parents=True, exist_ok=True)

    filename = f"summary_{period}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    out_path = out_dir / filename
    out_path.write_text(html, encoding="utf-8")
    return out_path
