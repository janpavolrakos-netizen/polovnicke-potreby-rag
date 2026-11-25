"""Streamlit aplikácia – RAG asistent e-shopu Poľovnícke potreby.
Spustenie:  streamlit run app.py
"""
import json
from html import escape
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from ontology import Ontologia, label
from rag_core import RAG, build_index, client, load_config
from style import CSS

st.set_page_config(page_title="Poľovnícke potreby · RAG", page_icon="🦌", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)
cfg = load_config()
onto = Ontologia(cfg["ontology_file"])
pdfs = sorted(Path(cfg["pdf_dir"]).glob("*.pdf"))
idx_file = Path(cfg["index_dir"]) / "chunks.json"
CAT_COLORS = {"Lacne": "#6FA77A", "Stredna_Trieda": "#6FA3C7", "Premiove": "#E9A23B", "Luxusne": "#D9734A"}


def ollama_status():
    try:
        return True, [m["model"] for m in client(cfg).list()["models"]]
    except Exception:
        return False, []


def index_size() -> int:
    try:
        return len(json.loads(idx_file.read_text(encoding="utf-8"))["chunks"])
    except Exception:
        return 0


ok, models = ollama_status()

# ---------------- bočný panel ----------------
with st.sidebar:
    st.markdown("### ⚙️ Nastavenia")
    st.markdown(f"<div class='side-status'><span class='sdot{'' if ok else ' off'}'>●</span>"
                f"{'Ollama beží lokálne' if ok else 'Ollama nebeží'}</div>", unsafe_allow_html=True)
    if not ok:
        st.caption("Spusti aplikáciu Ollama alebo v termináli `ollama serve`.")
    st.write("")
    llm_opts = sorted({cfg["llm_model"], *[m.split(":")[0] for m in models if "embed" not in m and "bge" not in m]})
    cfg["llm_model"] = st.selectbox("Jazykový model (LLM)", llm_opts, index=llm_opts.index(cfg["llm_model"]))
    cfg["top_k"] = st.slider("Počet úsekov z dokumentov (top-k)", 1, 10, cfg["top_k"])
    st.caption(f"Embedding model: `{cfg['embed_model']}`")

    with st.expander(f"📄 Dokumenty ({len(pdfs)})"):
        for p in pdfs:
            st.markdown(f"<div class='side-doc'>{escape(p.name)}</div>", unsafe_allow_html=True)
        up = st.file_uploader("Pridať PDF", type="pdf", accept_multiple_files=True)
        if up:
            for f in up:
                (Path(cfg["pdf_dir"]) / f.name).write_bytes(f.getbuffer())
            st.info("Uložené – klikni na Prebudovať index.")
    if st.button("🔄 Prebudovať index", disabled=not ok, width="stretch"):
        with st.status("Indexujem ontológiu a PDF…", expanded=True) as s:
            n = build_index(cfg, log=st.write)
            s.update(label=f"Hotovo – {n} úsekov", state="complete")
        st.cache_resource.clear()
    if st.button("🗑️ Nová konverzácia", width="stretch"):
        st.session_state.msgs = []

# ---------------- hero + KPI ----------------
n_chunks = index_size()
st.markdown(f"""
<div class="hero">
  <div class="eyebrow">Lokálny RAG · ontológia + dokumenty</div>
  <div class="htitle">Poľovnícke potreby <span class="grad">AI asistent</span></div>
  <p>Pýtaj sa na produkty e-shopu, ceny, návody k optike a zbraniam aj na poľovnícku legislatívu.
     Odpovede sa skladajú z ontológie (OWL) a PDF dokumentov – všetko beží na tomto počítači.</p>
  <div class="badges">
    <span class="badge">🔒 <b>100 %</b> offline</span>
    <span class="badge">🧠 Ontológia <b>OWL</b></span>
    <span class="badge">📄 <b>{len(pdfs)}</b> PDF</span>
    <span class="badge">🦙 <b>{escape(cfg['llm_model'])}</b> cez Ollama</span>
  </div>
</div>
<div class="kpis">
  <div class="kpi"><div class="v">{len(onto.produkty)}</div><div class="l">produktov v ontológii</div></div>
  <div class="kpi"><div class="v">{len(pdfs)}</div><div class="l">PDF dokumentov</div></div>
  <div class="kpi"><div class="v">{n_chunks or '–'}</div><div class="l">úsekov vo vektorovom indexe</div></div>
  <div class="kpi"><div class="v"><span class="dot{'' if ok else ' off'}"></span>{'online' if ok else 'offline'}</div>
       <div class="l">stav lokálneho modelu</div></div>
</div>
""", unsafe_allow_html=True)


@st.cache_resource
def get_rag(_key: str):
    return RAG(cfg)


def render_sources(hits):
    html = ""
    for h in hits:
        is_onto = h["page"] is None
        name = escape(h["source"]) + ("" if is_onto else f" · s. {h['page']}")
        pct = max(0, min(100, int(h["score"] * 100)))
        html += (f"<div class='src'><span class='tag {'onto' if is_onto else 'pdf'}'>{'ONTOLÓGIA' if is_onto else 'PDF'}</span>"
                 f"<span class='name'>{name}</span><span class='bar'><i style='width:{pct}%'></i></span>"
                 f"<span class='sc'>{h['score']:.2f}</span></div>")
    with st.expander(f"Zdroje odpovede ({len(hits)})"):
        st.markdown(html, unsafe_allow_html=True)


tab_chat, tab_kat, tab_onto, tab_how = st.tabs(["💬  Chat", "🛒  Katalóg e-shopu", "🧠  Ontológia", "⚙️  Ako to funguje"])

# ---------------- CHAT ----------------
with tab_chat:
    st.session_state.setdefault("msgs", [])
    QUICK = {"💰 Najlacnejší model": "Aký je najlacnejší model v e-shope?",
             "🎯 Najlacnejšia guľovnica": "Ktorá guľovnica je najlacnejšia?",
             "💎 Luxusné produkty": "Ktoré produkty sú luxusné?",
             "🔋 Batéria Helion": "Ako sa nabíja batéria termovízie Helion?",
             "📜 Zbrojný preukaz": "Aké skupiny zbrojného preukazu existujú?"}
    cols = st.columns(len(QUICK))
    for c, (lbl, q) in zip(cols, QUICK.items()):
        if c.button(lbl, width="stretch", help=q):
            st.session_state.pending = q

    if not n_chunks:
        st.warning("Index ešte neexistuje. Spusti `python ingest.py` alebo klikni vľavo na **Prebudovať index**.")
    else:
        rag = get_rag(cfg["embed_model"] + str(n_chunks))
        rag.cfg = cfg
        for m in st.session_state.msgs:
            with st.chat_message(m["role"], avatar="🧑" if m["role"] == "user" else "🦌"):
                st.markdown(m["content"])
                if m.get("hits"):
                    render_sources(m["hits"])

        q = st.chat_input("Opýtaj sa na poľovnícke potreby…")
        q = q or st.session_state.pop("pending", None)
        if q:
            if not ok:
                st.error("Ollama nebeží – spusti ju a skús znova.")
            else:
                with st.chat_message("user", avatar="🧑"):
                    st.markdown(q)
                history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.msgs]
                with st.chat_message("assistant", avatar="🦌"):
                    with st.spinner("Hľadám v ontológii a dokumentoch…"):
                        gen, hits = rag.answer(q, history)
                    ans = st.write_stream(gen)
                    render_sources(hits)
                st.session_state.msgs += [{"role": "user", "content": q},
                                          {"role": "assistant", "content": ans, "hits": hits}]

# ---------------- KATALÓG ----------------
with tab_kat:
    st.markdown("<div class='section-title'>Produkty z ontológie · zoradené od najlacnejšieho</div>", unsafe_allow_html=True)
    cards = ""
    for i, p in enumerate(onto.produkty, 1):
        k = p.kategoria or p.kategoria_odvodena
        cards += (f"<div class='card{' best' if i == 1 else ''}'><div class='rank'>{'★ najlacnejší' if i == 1 else '#' + str(i)}</div>"
                  f"<div class='ty'>{escape(label(p.typ))}</div><div class='nm'>{escape(p.nazov)}</div>"
                  f"<div class='pr'>{f'{p.cena:,}'.replace(',', ' ')} €</div>"
                  f"<div class='meta'>{escape(label(p.vyrobca))} · {escape(label(p.krajina))}</div>"
                  f"<span class='pill {k}'>{escape(label(k))}</span></div>")
    st.markdown(f"<div class='grid'>{cards}</div>", unsafe_allow_html=True)

    st.markdown("<div class='section-title'>Cenová mapa</div>", unsafe_allow_html=True)
    df = pd.DataFrame([{"Produkt": p.nazov, "Cena": p.cena, "Kategória": label(p.kategoria or p.kategoria_odvodena),
                        "k": p.kategoria or p.kategoria_odvodena} for p in onto.produkty])
    chart = (alt.Chart(df).mark_bar(cornerRadiusEnd=6, height=22).encode(
        x=alt.X("Cena:Q", title="Cena (€)", axis=alt.Axis(grid=True, gridColor="#2A4234", labelColor="#A3AE9F", titleColor="#A3AE9F")),
        y=alt.Y("Produkt:N", sort=None, title=None, axis=alt.Axis(labelColor="#EDE6D6", labelFontSize=12)),
        color=alt.Color("Kategória:N", scale=alt.Scale(domain=[label(k) for k in CAT_COLORS], range=list(CAT_COLORS.values())),
                        legend=alt.Legend(orient="bottom", labelColor="#EDE6D6", titleColor="#A3AE9F")),
        tooltip=["Produkt", "Cena", "Kategória"]).properties(height=360)
        .configure_view(strokeWidth=0).configure(background="transparent"))
    st.altair_chart(chart, width="stretch")

# ---------------- ONTOLÓGIA ----------------
with tab_onto:
    st.markdown("<div class='section-title'>Hierarchia typov potrieb (Typ_Potreby)</div>", unsafe_allow_html=True)
    nodes = "".join(
        f"<div class='node'><h4>{escape(label(top))}</h4>"
        + "".join(f"<span class='leaf'>{escape(label(s))}</span>" for s in onto.podtriedy(top)) + "</div>"
        for top in onto.podtriedy("Typ_Potreby"))
    st.markdown(f"<div class='tree'>{nodes}</div>", unsafe_allow_html=True)

    st.markdown("<div class='section-title'>Cenové kategórie (definované v OWL cez vlastnosť Cena)</div>", unsafe_allow_html=True)
    order = sorted(onto.kategorie.items(), key=lambda kv: kv[1][0] or 0)
    segs = "".join(f"<div style='flex:1;background:{CAT_COLORS.get(k, '#888')}'>{escape(label(k))} · "
                   f"{lo or 0}–{(str(hi - 1) + ' €') if hi else '∞'}</div>" for k, (lo, hi) in order)
    st.markdown(f"<div class='range'>{segs}</div>", unsafe_allow_html=True)
    st.caption("Kategória produktu sa odvodzuje z ceny podľa týchto definícií (ako by to urobil reasoner).")

    st.markdown("<div class='section-title'>Výrobcovia</div>", unsafe_allow_html=True)
    st.markdown("".join(f"<span class='leaf'>{escape(label(v))}</span>" for v in onto.podtriedy("Vyrobca")),
                unsafe_allow_html=True)
    with st.expander("Fakty z ontológie, ktoré idú do vektorového indexu"):
        st.code("\n".join(onto.fakty()), language=None)

# ---------------- AKO TO FUNGUJE ----------------
with tab_how:
    st.markdown("<div class='section-title'>Čo sa stane, keď položíš otázku</div>", unsafe_allow_html=True)
    st.markdown(f"""
<div class="steps">
 <div class="step"><h5>Embedding otázky</h5><p>Model <b>{escape(cfg['embed_model'])}</b> prevedie otázku na vektor. Je viacjazyčný – slovenská otázka nájde aj anglický návod.</p></div>
 <div class="step"><h5>Vyhľadanie</h5><p>Kosínusová podobnosť voči {n_chunks or '…'} úsekom z PDF a ontológie, vyberie sa top-{cfg['top_k']}.</p></div>
 <div class="step"><h5>Katalóg z ontológie</h5><p>Do promptu ide vždy celý katalóg e-shopu s presnými cenami a vopred vypočítaným min/max.</p></div>
 <div class="step"><h5>Generovanie</h5><p><b>{escape(cfg['llm_model'])}</b> cez Ollama odpovie po slovensky len z dodaných podkladov.</p></div>
 <div class="step"><h5>Zdroje</h5><p>Pod odpoveďou sú zdroje – ontológia alebo PDF so stranou a mierou podobnosti.</p></div>
</div>
""", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Prečo ontológia + RAG</div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    c1.markdown("**Ontológia** dáva štruktúrované a presné fakty: typy, výrobcov, ceny, kategórie. "
                "Vďaka nej model nehádá ceny a vie odpovedať na porovnania (najlacnejší, najdrahší).")
    c2.markdown("**PDF dokumenty** dávajú neštruktúrované znalosti: návody, technické údaje, zákony. "
                "Tie sa hľadajú sémanticky cez embeddingy.")
