"""Jadro RAG: načítanie PDF, delenie na úseky, embeddingy cez Ollama,
vyhľadávanie podobných úsekov a generovanie odpovede lokálnym LLM."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

import numpy as np
import ollama
import yaml
from pypdf import PdfReader

from ontology import Ontologia

BASE = Path(__file__).resolve().parent


def load_config(path: str | Path = BASE / "config.yaml") -> dict:
    with open(path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    for k in ("pdf_dir", "ontology_file", "index_dir"):
        cfg[k] = str(BASE / cfg[k])
    return cfg


# ---------------- jazyk úseku (viacjazyčné manuály) ----------------
STOP = {
    "sk": {"a", "je", "sa", "na", "v", "pre", "alebo", "ktorý", "ako", "podľa", "zákona", "pri", "do", "od", "sú", "nie", "s", "z", "aby", "môže", "poľovníckeho"},
    "en": {"the", "and", "of", "to", "is", "in", "for", "with", "be", "on", "this", "that", "are", "or", "not", "you", "your", "can"},
    "de": {"der", "die", "das", "und", "ist", "nicht", "mit", "sie", "den", "zu", "auf", "für", "werden", "eine", "des", "im"},
    "fr": {"le", "la", "les", "et", "des", "est", "pour", "une", "dans", "vous", "avec", "pas", "sur", "du"},
    "it": {"il", "di", "che", "per", "con", "non", "una", "della", "sono", "lo", "gli", "del", "le"},
    "es": {"el", "los", "las", "que", "por", "con", "para", "una", "del", "se", "no", "es"},
    "nl": {"de", "het", "een", "van", "en", "niet", "met", "voor", "op", "zijn", "te"},
}


def detect_lang(text: str) -> str:
    if len(re.findall(r"[А-Яа-я]", text)) > 0.2 * max(1, len(re.findall(r"\w", text))):
        return "ru"
    words = re.findall(r"[a-záäčďéíĺľňóôŕšťúýžàâçèêëîïöüßñ]+", text.lower())
    if not words:
        return "?"
    scores = {lang: sum(w in s for w in words) for lang, s in STOP.items()}
    if re.search(r"[ľĺŕôťď]", text.lower()):
        scores["sk"] += 5
    best = max(scores, key=scores.get)
    return best if scores[best] >= 2 else "?"


# ---------------- PDF -> úseky ----------------
def chunk_text(text: str, size: int, overlap: int) -> list[str]:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text).strip()
    out, i = [], 0
    while i < len(text):
        piece = text[i:i + size]
        if i + size < len(text):  # zarovnať na koniec vety, ak sa dá
            cut = max(piece.rfind(". "), piece.rfind("\n"))
            if cut > size * 0.6:
                piece = piece[:cut + 1]
        out.append(piece.strip())
        if i + len(piece) >= len(text):
            break
        i += max(1, len(piece) - overlap)
    return [c for c in out if len(c) > 80]


def load_pdf_chunks(cfg: dict, log=print) -> list[dict]:
    chunks = []
    keep = set(cfg.get("keep_languages") or [])
    for pdf in sorted(Path(cfg["pdf_dir"]).glob("*.pdf")):
        reader = PdfReader(str(pdf))
        kept = skipped = 0
        for pno, page in enumerate(reader.pages, 1):
            try:
                txt = page.extract_text() or ""
            except Exception:
                continue
            for c in chunk_text(txt, cfg["chunk_size"], cfg["chunk_overlap"]):
                lang = detect_lang(c)
                if keep and lang not in keep:
                    skipped += 1
                    continue
                chunks.append({"text": c, "source": pdf.name, "page": pno, "lang": lang})
                kept += 1
        log(f"  {pdf.name}: {len(reader.pages)} strán, {kept} úsekov (vynechaných iné jazyky: {skipped})")
    return chunks


# ---------------- Ollama ----------------
def client(cfg: dict) -> ollama.Client:
    return ollama.Client(host=cfg.get("ollama_host", "http://localhost:11434"))


def embed(cfg: dict, texts: list[str], batch: int = 32) -> np.ndarray:
    cl, vecs = client(cfg), []
    for i in range(0, len(texts), batch):
        res = cl.embed(model=cfg["embed_model"], input=texts[i:i + batch])
        vecs.extend(res["embeddings"])
    v = np.array(vecs, dtype=np.float32)
    return v / (np.linalg.norm(v, axis=1, keepdims=True) + 1e-10)


# ---------------- index ----------------
def build_index(cfg: dict, log=print) -> int:
    log("Načítavam ontológiu…")
    onto = Ontologia(cfg["ontology_file"])
    chunks = [{"text": f, "source": "ontológia (OWL)", "page": None, "lang": "sk"} for f in onto.fakty()]
    log(f"  ontológia: {len(chunks)} faktov")
    log("Načítavam PDF…")
    chunks += load_pdf_chunks(cfg, log)
    log(f"Počítam embeddingy pre {len(chunks)} úsekov modelom {cfg['embed_model']} (môže trvať pár minút)…")
    vecs = embed(cfg, [c["text"] for c in chunks])
    os.makedirs(cfg["index_dir"], exist_ok=True)
    np.save(Path(cfg["index_dir"]) / "embeddings.npy", vecs)
    with open(Path(cfg["index_dir"]) / "chunks.json", "w", encoding="utf-8") as f:
        json.dump({"embed_model": cfg["embed_model"], "chunks": chunks}, f, ensure_ascii=False)
    log("Index uložený.")
    return len(chunks)


class RAG:
    SYSTEM = (
        "Si asistent e-shopu s poľovníckymi potrebami. Odpovedaj VŽDY po slovensky, stručne a vecne. "
        "Používaj iba informácie z KATALÓGU E-SHOPU a z KONTEXTU nižšie. Ceny a produkty ber výhradne z katalógu. "
        "Ak odpoveď v podkladoch nie je, povedz, že ju nevieš. Pri informáciách z dokumentov uveď zdroj v tvare [názov súboru, s. X]."
    )

    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.onto = Ontologia(cfg["ontology_file"])
        idx = Path(cfg["index_dir"])
        with open(idx / "chunks.json", encoding="utf-8") as f:
            data = json.load(f)
        self.chunks = data["chunks"]
        self.vecs = np.load(idx / "embeddings.npy")

    def retrieve(self, query: str, k: int | None = None) -> list[dict]:
        k = k or self.cfg["top_k"]
        q = embed(self.cfg, [query])[0]
        sims = self.vecs @ q
        top = np.argsort(-sims)[:k]
        return [{**self.chunks[i], "score": float(sims[i])} for i in top]

    def messages(self, query: str, hits: list[dict], history: list[dict] | None = None) -> list[dict]:
        ctx = "\n\n".join(
            f"[{h['source']}{', s. ' + str(h['page']) if h['page'] else ''}]\n{h['text']}" for h in hits)
        msgs = [{"role": "system", "content": self.SYSTEM + "\n\n" + self.onto.suhrn()}]
        msgs += (history or [])[-6:]
        msgs.append({"role": "user", "content": f"KONTEXT:\n{ctx}\n\nOTÁZKA: {query}"})
        return msgs

    def answer(self, query: str, history: list[dict] | None = None, stream: bool = True):
        hits = self.retrieve(query)
        msgs = self.messages(query, hits, history)
        resp = client(self.cfg).chat(model=self.cfg["llm_model"], messages=msgs, stream=stream,
                                     options={"temperature": self.cfg.get("temperature", 0.2)})
        if stream:
            return (part["message"]["content"] for part in resp), hits
        return resp["message"]["content"], hits
