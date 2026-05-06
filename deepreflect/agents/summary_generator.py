"""Generate shareable, screenshot-friendly HTML summary pages."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from jinja2 import Template
from sqlmodel import Session

from deepreflect.memory.db import get_concepts, get_stats, get_turns

_TEMPLATE = Template(
    r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DeepReflect — {{ period_label }} Summary</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800;900&family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600&display=swap" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
<style>
  :root {
    --bg: #050a0e;
    --card-bg: #0a1118;
    --surface: #0f1923;
    --border: #1a2d3d;
    --teal: #2dd4bf;
    --teal-dim: #0d9488;
    --indigo: #818cf8;
    --amber: #fbbf24;
    --rose: #fb7185;
    --text: #e2e8f0;
    --text-2: #94a3b8;
    --text-3: #475569;
    --text-4: #1e293b;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'DM Sans', -apple-system, system-ui, sans-serif;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 40px 20px 120px;
    -webkit-font-smoothing: antialiased;
  }

  .page {
    width: 420px;
    position: relative;
  }

  /* --- HERO SECTION --- */
  .hero {
    text-align: center;
    padding: 48px 32px 40px;
    background: linear-gradient(180deg, #0f2027 0%, #0a1118 100%);
    border-radius: 28px;
    border: 1px solid var(--border);
    position: relative;
    overflow: hidden;
    margin-bottom: 16px;
  }
  .hero::before {
    content: '';
    position: absolute;
    top: -80px; left: 50%;
    transform: translateX(-50%);
    width: 300px; height: 300px;
    background: radial-gradient(circle, rgba(45,212,191,0.12) 0%, transparent 70%);
    pointer-events: none;
  }
  .hero::after {
    content: '';
    position: absolute;
    bottom: -60px; right: -40px;
    width: 200px; height: 200px;
    background: radial-gradient(circle, rgba(129,140,248,0.08) 0%, transparent 70%);
    pointer-events: none;
  }
  .hero-logo {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 20px;
    position: relative;
  }
  .hero-logo .icon {
    width: 28px; height: 28px;
    border-radius: 8px;
    background: linear-gradient(135deg, var(--teal), var(--indigo));
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .hero-logo .icon svg { width: 14px; height: 14px; }
  .hero-logo span {
    font-family: 'Outfit', sans-serif;
    font-size: 14px;
    font-weight: 700;
    letter-spacing: 0.08em;
    color: var(--text-2);
  }
  .hero-period {
    font-family: 'Outfit', sans-serif;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: var(--teal);
    background: rgba(45,212,191,0.1);
    border: 1px solid rgba(45,212,191,0.2);
    padding: 5px 14px;
    border-radius: 100px;
    display: inline-block;
    margin-bottom: 24px;
  }
  .hero h1 {
    font-family: 'Outfit', sans-serif;
    font-size: 32px;
    font-weight: 800;
    line-height: 1.15;
    color: var(--text);
    position: relative;
  }
  .hero .date-range {
    font-size: 14px;
    color: var(--text-3);
    margin-top: 10px;
  }

  /* --- STAT CARDS --- */
  .stats-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin-bottom: 16px;
  }
  .stat-card {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 24px 20px;
    text-align: center;
    position: relative;
    overflow: hidden;
  }
  .stat-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    border-radius: 20px 20px 0 0;
  }
  .stat-card:nth-child(1)::before { background: linear-gradient(90deg, var(--teal), transparent); }
  .stat-card:nth-child(2)::before { background: linear-gradient(90deg, var(--indigo), transparent); }
  .stat-card:nth-child(3)::before { background: linear-gradient(90deg, var(--amber), transparent); }
  .stat-card:nth-child(4)::before { background: linear-gradient(90deg, var(--rose), transparent); }
  .stat-num {
    font-family: 'Outfit', sans-serif;
    font-size: 40px;
    font-weight: 900;
    line-height: 1;
    display: block;
    margin-bottom: 6px;
  }
  .stat-card:nth-child(1) .stat-num { color: var(--teal); text-shadow: 0 0 30px rgba(45,212,191,0.3); }
  .stat-card:nth-child(2) .stat-num { color: var(--indigo); text-shadow: 0 0 30px rgba(129,140,248,0.3); }
  .stat-card:nth-child(3) .stat-num { color: var(--amber); text-shadow: 0 0 30px rgba(251,191,36,0.3); }
  .stat-card:nth-child(4) .stat-num { color: var(--rose); text-shadow: 0 0 30px rgba(251,113,133,0.3); }
  .stat-label {
    font-family: 'Outfit', sans-serif;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--text-3);
  }

  /* --- SECTION PANEL --- */
  .panel {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 28px 24px;
    margin-bottom: 16px;
    position: relative;
    overflow: hidden;
  }
  .panel-label {
    font-family: 'Outfit', sans-serif;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--text-3);
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .panel-label .dot {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: var(--teal);
  }

  /* --- SOURCES --- */
  .source-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }
  .source-chip {
    font-size: 12px;
    font-weight: 500;
    padding: 6px 14px;
    border-radius: 10px;
    background: var(--surface);
    border: 1px solid var(--border);
    color: var(--text-2);
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .source-chip .count {
    color: var(--teal);
    font-family: 'Outfit', sans-serif;
    font-weight: 700;
  }

  /* --- CONCEPTS RANKING --- */
  .concept-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 14px 0;
    border-bottom: 1px solid rgba(26,45,61,0.6);
  }
  .concept-item:last-child { border-bottom: none; }
  .concept-rank {
    font-family: 'Outfit', sans-serif;
    font-size: 24px;
    font-weight: 800;
    width: 32px;
    text-align: center;
    flex-shrink: 0;
  }
  .concept-rank.r1 { color: var(--teal); text-shadow: 0 0 20px rgba(45,212,191,0.3); }
  .concept-rank.r2 { color: var(--indigo); }
  .concept-rank.r3 { color: var(--amber); }
  .concept-rank.rn { color: var(--text-3); font-size: 18px; }
  .concept-info { flex: 1; min-width: 0; }
  .concept-name {
    font-size: 14px;
    font-weight: 600;
    color: var(--text);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .concept-meta {
    font-size: 11px;
    color: var(--text-3);
    margin-top: 2px;
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .concept-cat {
    font-size: 10px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 6px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }
  .cat-python  { background: rgba(96,165,250,0.12); color: #60a5fa; }
  .cat-ml      { background: rgba(167,139,250,0.12); color: #a78bfa; }
  .cat-git     { background: rgba(251,146,60,0.12);  color: #fb923c; }
  .cat-web     { background: rgba(52,211,153,0.12);  color: #34d399; }
  .cat-data    { background: rgba(34,211,238,0.12);  color: #22d3ee; }
  .cat-math    { background: rgba(251,191,36,0.12);  color: #fbbf24; }
  .cat-general { background: rgba(148,163,184,0.12); color: #94a3b8; }
  .cat-other   { background: rgba(148,163,184,0.12); color: #94a3b8; }
  .concept-bar-wrap {
    width: 80px;
    flex-shrink: 0;
  }
  .concept-bar {
    height: 4px;
    background: var(--text-4);
    border-radius: 99px;
    overflow: hidden;
  }
  .concept-bar-fill {
    height: 100%;
    border-radius: 99px;
    background: linear-gradient(90deg, var(--teal), var(--indigo));
  }
  .concept-count {
    font-family: 'Outfit', sans-serif;
    font-size: 10px;
    color: var(--text-3);
    text-align: right;
    margin-top: 2px;
  }
  .weak-badge {
    font-size: 9px;
    font-weight: 600;
    padding: 2px 6px;
    border-radius: 4px;
    background: rgba(251,113,133,0.12);
    color: var(--rose);
    white-space: nowrap;
  }

  /* --- FOOTER --- */
  .report-footer {
    text-align: center;
    padding: 32px 24px;
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 20px;
    margin-bottom: 16px;
  }
  .footer-brand {
    font-family: 'Outfit', sans-serif;
    font-size: 13px;
    font-weight: 700;
    color: var(--text-3);
    letter-spacing: 0.08em;
  }
  .footer-brand .accent { color: var(--teal); }
  .footer-date {
    font-size: 11px;
    color: var(--text-4);
    margin-top: 6px;
  }
  .footer-tagline {
    font-size: 12px;
    color: var(--text-3);
    margin-top: 12px;
    font-style: italic;
  }

  /* --- DIVIDER --- */
  .divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--border), transparent);
    margin: 4px 0;
  }

  /* --- HIGHLIGHT CARD --- */
  .highlight-card {
    text-align: center;
    padding: 36px 28px;
    background: linear-gradient(135deg, rgba(45,212,191,0.06), rgba(129,140,248,0.04));
    border: 1px solid rgba(45,212,191,0.15);
    border-radius: 20px;
    margin-bottom: 16px;
  }
  .highlight-card .big-num {
    font-family: 'Outfit', sans-serif;
    font-size: 72px;
    font-weight: 900;
    background: linear-gradient(135deg, var(--teal), var(--indigo));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1;
    filter: drop-shadow(0 0 40px rgba(45,212,191,0.25));
  }
  .highlight-card .big-label {
    font-family: 'Outfit', sans-serif;
    font-size: 14px;
    font-weight: 600;
    color: var(--text-2);
    margin-top: 8px;
  }
  .highlight-card .big-sub {
    font-size: 12px;
    color: var(--text-3);
    margin-top: 4px;
  }

  /* --- EXPORT UI --- */
  .export-bar {
    position: fixed;
    bottom: 28px;
    right: 28px;
    z-index: 9999;
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 10px;
  }
  .export-btn {
    background: linear-gradient(135deg, var(--teal), #14b8a6);
    border: none;
    border-radius: 14px;
    padding: 14px 24px;
    font-family: 'Outfit', sans-serif;
    font-weight: 700;
    font-size: 15px;
    color: #050a0e;
    cursor: pointer;
    box-shadow: 0 4px 24px -4px rgba(45,212,191,0.4);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .export-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 32px -4px rgba(45,212,191,0.5);
  }
  .export-btn:active { transform: translateY(0); }
  .export-btn[disabled] { opacity: 0.6; cursor: progress; }
  .export-tip {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 8px 14px;
    font-size: 13px;
    color: var(--text-2);
    box-shadow: 0 4px 16px rgba(0,0,0,0.3);
    display: none;
  }
  .export-tip.show { display: block; }

  /* noise */
  .noise {
    position: fixed;
    inset: 0;
    pointer-events: none;
    z-index: 9998;
    opacity: 0.02;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
    background-repeat: repeat;
  }

  @media print { .export-bar { display: none; } }
</style>
</head>
<body>
<div class="noise"></div>

<div class="page" id="report-page">

  <!-- HERO -->
  <div class="hero">
    <div class="hero-logo">
      <div class="icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
        </svg>
      </div>
      <span>DEEPREFLECT</span>
    </div>
    <div class="hero-period">{{ period_label }} Report</div>
    <h1>Your Learning<br>Journey</h1>
    <div class="date-range">{{ date_range }}</div>
  </div>

  <!-- HIGHLIGHT -->
  <div class="highlight-card">
    <div class="big-num">{{ stats.total_turns }}</div>
    <div class="big-label">Total AI Conversations</div>
    <div class="big-sub">across all your tools and projects</div>
  </div>

  <!-- STATS -->
  <div class="stats-row">
    <div class="stat-card">
      <span class="stat-num">{{ stats.total_turns }}</span>
      <span class="stat-label">Exchanges</span>
    </div>
    <div class="stat-card">
      <span class="stat-num">{{ stats.weekly_turns }}</span>
      <span class="stat-label">This Week</span>
    </div>
    <div class="stat-card">
      <span class="stat-num">{{ stats.total_concepts }}</span>
      <span class="stat-label">Concepts</span>
    </div>
    <div class="stat-card">
      <span class="stat-num">{{ stats.total_flashcards }}</span>
      <span class="stat-label">Flashcards</span>
    </div>
  </div>

  {% if sources %}
  <!-- SOURCES -->
  <div class="panel">
    <div class="panel-label">
      <span class="dot"></span>
      AI Tools You Used
    </div>
    <div class="source-chips">
      {% for src, cnt in sources.items() %}
      <span class="source-chip">{{ src }} <span class="count">{{ cnt }}</span></span>
      {% endfor %}
    </div>
  </div>
  {% endif %}

  {% if concepts %}
  <!-- TOP CONCEPTS -->
  <div class="panel">
    <div class="panel-label">
      <span class="dot" style="background: var(--indigo);"></span>
      Your Top Topics
    </div>
    {% set max_count = concepts[0].ask_count %}
    {% for c in concepts %}
    <div class="concept-item">
      <span class="concept-rank {% if loop.index == 1 %}r1{% elif loop.index == 2 %}r2{% elif loop.index == 3 %}r3{% else %}rn{% endif %}">
        {{ loop.index }}
      </span>
      <div class="concept-info">
        <div class="concept-name">{{ c.name }}</div>
        <div class="concept-meta">
          <span class="concept-cat cat-{{ c.category }}">{{ c.category }}</span>
          {% if c.weak_score >= 0.4 %}
          <span class="weak-badge">needs review</span>
          {% endif %}
        </div>
      </div>
      <div class="concept-bar-wrap">
        <div class="concept-bar">
          <div class="concept-bar-fill" style="width: {{ (c.ask_count / max_count * 100)|int }}%"></div>
        </div>
        <div class="concept-count">{{ c.ask_count }}×</div>
      </div>
    </div>
    {% endfor %}
  </div>

  {% if concepts|length >= 1 %}
  <!-- #1 TOPIC HIGHLIGHT -->
  <div class="highlight-card">
    <div class="big-num" style="font-size: 28px; -webkit-text-fill-color: var(--teal); filter: drop-shadow(0 0 20px rgba(45,212,191,0.3));">
      {{ concepts[0].name }}
    </div>
    <div class="big-label">Your #1 Topic</div>
    <div class="big-sub">Asked about {{ concepts[0].ask_count }} times this period</div>
  </div>
  {% endif %}
  {% endif %}

  <!-- FOOTER -->
  <div class="report-footer">
    <div class="footer-brand">Deep<span class="accent">Reflect</span></div>
    <div class="footer-date">Generated {{ generated_at }}</div>
    <div class="footer-tagline">Your AI usage, mapped into knowledge.</div>
  </div>

</div>

<!-- EXPORT BUTTON -->
<div class="export-bar" id="export-bar">
  <div class="export-tip" id="export-tip">Saved! Check your Downloads ✨</div>
  <button class="export-btn" id="export-btn" type="button">
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
      <rect x="3" y="3" width="18" height="18" rx="2"/>
      <circle cx="8.5" cy="8.5" r="1.5"/>
      <polyline points="21 15 16 10 5 21"/>
    </svg>
    Save as PNG
  </button>
</div>

<script>
(function () {
  const btn = document.getElementById('export-btn');
  const tip = document.getElementById('export-tip');
  const bar = document.getElementById('export-bar');

  async function exportPNG() {
    if (typeof html2canvas !== 'function') {
      alert('Image export library not loaded yet — try again in a moment.');
      return;
    }
    const origText = btn.innerHTML;
    btn.disabled = true;
    btn.textContent = 'Rendering…';
    bar.style.display = 'none';

    try {
      if (document.fonts && document.fonts.ready) await document.fonts.ready;
      const target = document.getElementById('report-page');
      const rect = target.getBoundingClientRect();
      const canvas = await html2canvas(target, {
        backgroundColor: '#050a0e',
        scale: 2,
        useCORS: true,
        logging: false,
        windowWidth: Math.max(480, rect.width + 60),
      });
      const link = document.createElement('a');
      link.download = 'deepreflect-{{ period_label|lower }}-report.png';
      link.href = canvas.toDataURL('image/png');
      link.click();

      bar.style.display = '';
      tip.classList.add('show');
      setTimeout(() => tip.classList.remove('show'), 3000);
    } catch (err) {
      console.error('Export failed:', err);
      bar.style.display = '';
      alert('Export failed: ' + (err && err.message ? err.message : err));
    } finally {
      btn.disabled = false;
      btn.innerHTML = origText;
    }
  }

  btn.addEventListener('click', exportPNG);
})();
</script>
</body>
</html>
"""
)


def _period_bounds(period: str) -> tuple[datetime, datetime, str, str]:
    now = datetime.now(timezone.utc)
    if period == "daily":
        since = now.replace(hour=0, minute=0, second=0, microsecond=0)
        label = "Daily"
        date_range = now.strftime("%B %d, %Y")
    elif period == "weekly":
        since = now - timedelta(days=7)
        label = "Weekly"
        date_range = f"{since.strftime('%b %d')} – {now.strftime('%b %d, %Y')}"
    elif period == "monthly":
        since = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        label = "Monthly"
        date_range = now.strftime("%B %Y")
    elif period == "yearly":
        since = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        label = "Yearly"
        date_range = now.strftime("%Y")
    else:
        since = now - timedelta(days=7)
        label = "Weekly"
        date_range = f"{since.strftime('%b %d')} – {now.strftime('%b %d, %Y')}"
    return since, now, label, date_range


def generate_summary_html(
    session: Session,
    period: str = "weekly",
    out_dir: Path | None = None,
) -> Path:
    since, until, label, date_range = _period_bounds(period)

    stats = get_stats(session)
    concepts = get_concepts(session, min_ask_count=1)[:15]
    sources = stats.get("sources", {})

    html = _TEMPLATE.render(
        period_label=label,
        date_range=date_range,
        stats=stats,
        concepts=concepts,
        sources=sources,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
    )

    if out_dir is None:
        out_dir = Path.home() / ".deepreflect" / "data" / "summaries"
    out_dir.mkdir(parents=True, exist_ok=True)

    filename = f"summary_{period}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    out_path = out_dir / filename
    out_path.write_text(html, encoding="utf-8")
    return out_path
