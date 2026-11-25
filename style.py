"""Vzhľad aplikácie – vlastné CSS (tmavý lesný motív s jantárovým akcentom)."""

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,800&family=Inter:wght@400;500;600&display=swap');

:root{
  --bg:#0E1712; --panel:#15241B; --panel2:#1B2E23; --line:#2A4234;
  --ink:#EDE6D6; --muted:#A3AE9F; --amber:#E9A23B; --amber2:#F4C36B;
  --moss:#6FA77A; --sky:#6FA3C7; --rust:#D9734A;
}
html, body, [class*="css"], .stMarkdown, p, li, label, input, textarea{
  font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif !important;
}
.block-container{padding-top:1.6rem; max-width:1250px;}
header[data-testid="stHeader"]{background:transparent;}

/* ---------- HERO ---------- */
.hero{
  position:relative; overflow:hidden; border-radius:22px; padding:34px 38px 30px;
  background:
    radial-gradient(1200px 300px at 85% -40%, rgba(233,162,59,.35), transparent 60%),
    radial-gradient(700px 260px at -10% 120%, rgba(111,167,122,.30), transparent 60%),
    linear-gradient(135deg,#132A1E 0%,#0E1712 70%);
  border:1px solid var(--line); box-shadow:0 20px 60px rgba(0,0,0,.35);
}
.hero:after{ /* silueta lesa */
  content:""; position:absolute; left:0; right:0; bottom:-2px; height:70px; opacity:.22;
  background:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1200 70' preserveAspectRatio='none'><path fill='%236FA77A' d='M0 70V48l30-26 22 20 26-34 30 30 24-18 30 26 36-40 30 34 28-22 30 28 40-44 32 36 26-20 34 30 30-36 34 28 26-16 32 26 38-42 30 36 28-24 32 30 34-38 30 32 26-18 30 26 40-46 32 40 26-22 30 30 36-34 28 24 32-20 30 28 38-44 30 38 26-18 34 28V70z'/></svg>") repeat-x bottom/1200px 70px;
}
.hero .eyebrow{color:var(--amber2); font-weight:600; letter-spacing:.16em; font-size:.78rem; text-transform:uppercase;}
.hero .htitle{font-family:'Fraunces',Georgia,serif !important; font-weight:800; font-size:2.9rem; line-height:1.05;
  margin:.35rem 0 .5rem; color:var(--ink) !important; letter-spacing:-.01em; padding:0 !important;}

.hero .htitle .grad{background:linear-gradient(90deg,var(--amber2),var(--amber) 60%,var(--rust)); -webkit-background-clip:text; background-clip:text; color:transparent;}
.hero p{color:var(--muted); font-size:1.02rem; max-width:720px; margin:0 0 1rem;}
.badges{display:flex; gap:8px; flex-wrap:wrap; position:relative; z-index:1;}
.badge{font-size:.78rem; font-weight:600; padding:6px 12px; border-radius:999px;
  background:rgba(237,230,214,.06); border:1px solid var(--line); color:var(--ink);}
.badge b{color:var(--amber2);}

/* ---------- KPI ---------- */
.kpis{display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin:18px 0 6px;}
.kpi{background:linear-gradient(180deg,var(--panel2),var(--panel)); border:1px solid var(--line);
  border-radius:16px; padding:16px 18px;}
.kpi .v{font-family:'Fraunces',Georgia,serif; font-size:2rem; font-weight:800; color:var(--ink); line-height:1;}
.kpi .l{color:var(--muted); font-size:.82rem; margin-top:6px;}
.kpi .dot{vertical-align:middle; display:inline-block; width:8px; height:8px; border-radius:50%; margin-right:6px; background:var(--moss); box-shadow:0 0 10px var(--moss);}
.kpi .dot.off{background:var(--rust); box-shadow:0 0 10px var(--rust);}
@media (max-width:900px){.kpis{grid-template-columns:repeat(2,1fr);} .hero .htitle{font-size:2.1rem;}}

/* ---------- TABS ---------- */
.stTabs [data-baseweb="tab-list"]{gap:6px; border-bottom:1px solid var(--line);}
.stTabs [data-baseweb="tab"]{background:transparent; border-radius:10px 10px 0 0; padding:10px 18px; color:var(--muted); font-weight:600;}
.stTabs [aria-selected="true"]{color:var(--amber2) !important; background:var(--panel);}
.stTabs [data-baseweb="tab-highlight"]{background:var(--amber);}

/* ---------- CHAT ---------- */
[data-testid="stChatMessage"]{background:var(--panel); border:1px solid var(--line); border-radius:16px; padding:14px 16px;}
[data-testid="stChatInput"] textarea{font-size:1rem;}
[data-testid="stChatInput"]{border-radius:14px;}
.stButton>button{border-radius:999px; border:1px solid var(--line); background:var(--panel); color:var(--ink);
  font-weight:500; padding:.45rem 1rem; transition:all .15s ease;}
.stButton>button:hover{border-color:var(--amber); color:var(--amber2); transform:translateY(-1px);}
.src{display:flex; align-items:center; gap:10px; padding:8px 10px; border-radius:10px; background:rgba(237,230,214,.03);
  border:1px solid var(--line); margin:6px 0; font-size:.86rem;}
.src .tag{font-size:.7rem; font-weight:700; padding:3px 8px; border-radius:6px; letter-spacing:.04em;}
.src .tag.onto{background:rgba(233,162,59,.16); color:var(--amber2);}
.src .tag.pdf{background:rgba(111,163,199,.16); color:var(--sky);}
.src .name{flex:1; color:var(--ink);}
.src .bar{width:80px; height:6px; border-radius:6px; background:var(--line); overflow:hidden;}
.src .bar i{display:block; height:100%; background:linear-gradient(90deg,var(--moss),var(--amber));}
.src .sc{color:var(--muted); width:38px; text-align:right; font-variant-numeric:tabular-nums;}

/* ---------- KATALÓG ---------- */
.grid{display:grid; grid-template-columns:repeat(auto-fill,minmax(220px,1fr)); gap:14px;}
.card{position:relative; background:linear-gradient(180deg,var(--panel2),var(--panel)); border:1px solid var(--line);
  border-radius:16px; padding:16px; transition:transform .15s ease, border-color .15s ease;}
.card:hover{transform:translateY(-3px); border-color:var(--amber);}
.card .rank{position:absolute; top:12px; right:14px; color:var(--muted); font-size:.8rem; font-weight:600;}
.card .ty{color:var(--muted); font-size:.75rem; text-transform:uppercase; letter-spacing:.1em;}
.card .nm{font-family:'Fraunces',Georgia,serif; font-size:1.25rem; font-weight:600; color:var(--ink); margin:4px 0 10px;}
.card .pr{font-family:'Fraunces',Georgia,serif; font-size:1.7rem; font-weight:800; color:var(--amber2);}
.card .meta{color:var(--muted); font-size:.82rem; margin-top:6px;}
.pill{display:inline-block; font-size:.72rem; font-weight:700; padding:3px 9px; border-radius:999px; margin-top:10px;}
.pill.Lacne{background:rgba(111,167,122,.18); color:#9ED3A8;}
.pill.Stredna_Trieda{background:rgba(111,163,199,.18); color:#9CC8E6;}
.pill.Premiove{background:rgba(233,162,59,.18); color:var(--amber2);}
.pill.Luxusne{background:rgba(217,115,74,.20); color:#F2A07E;}
.card.best{border-color:var(--moss); box-shadow:0 0 0 1px var(--moss), 0 10px 30px rgba(111,167,122,.15);}
.card.best .rank{color:#9ED3A8;}

/* ---------- ONTOLÓGIA / PIPELINE ---------- */
.tree{display:grid; grid-template-columns:repeat(auto-fill,minmax(210px,1fr)); gap:12px;}
.node{background:var(--panel); border:1px solid var(--line); border-radius:14px; padding:14px;}
.node h4{margin:0 0 8px; color:var(--amber2); font-size:.95rem;}
.leaf{display:inline-block; margin:3px 4px 0 0; padding:3px 9px; border-radius:8px; background:rgba(237,230,214,.05);
  border:1px solid var(--line); font-size:.8rem; color:var(--ink);}
.range{display:flex; height:46px; border-radius:12px; overflow:hidden; border:1px solid var(--line); margin:8px 0 4px;}
.range div{display:flex; align-items:center; justify-content:center; font-size:.8rem; font-weight:700; color:#0E1712;}
.steps{display:grid; grid-template-columns:repeat(5,1fr); gap:12px; counter-reset:s;}
.step{background:var(--panel); border:1px solid var(--line); border-radius:14px; padding:16px; position:relative;}
.step:before{counter-increment:s; content:counter(s); position:absolute; top:-12px; left:14px; width:26px; height:26px;
  border-radius:50%; background:var(--amber); color:#0E1712; font-weight:800; display:flex; align-items:center; justify-content:center; font-size:.85rem;}
.step h5{margin:6px 0 6px; color:var(--ink); font-size:.98rem;}
.step p{margin:0; color:var(--muted); font-size:.84rem; line-height:1.45;}
@media (max-width:900px){.steps{grid-template-columns:1fr 1fr;}}
.section-title{font-family:'Fraunces',Georgia,serif; font-size:1.35rem; font-weight:600; margin:18px 0 10px; color:var(--ink);}

/* ---------- SIDEBAR ---------- */
[data-testid="stSidebar"]{background:linear-gradient(180deg,#112018,#0E1712); border-right:1px solid var(--line);}
.side-status{display:flex; align-items:center; gap:8px; padding:10px 12px; border-radius:12px; border:1px solid var(--line);
  background:var(--panel); font-weight:600; font-size:.9rem;}
.sdot{color:var(--moss); text-shadow:0 0 10px var(--moss); font-size:.9rem;}
.sdot.off{color:var(--rust); text-shadow:0 0 10px var(--rust);}
.side-doc{font-size:.8rem; color:var(--muted); padding:4px 0; border-bottom:1px dashed var(--line);}
</style>
"""
