"""Napojenie na ontológiu Poľovnícke potreby (OWL z WebProtégé).

Z OWL súboru vytiahne produkty e-shopu (typ, výrobca, krajina, cena, cenová
kategória), hierarchiu typov a definície cenových kategórií. Výsledok sa použije
dvoma spôsobmi:
  1. ako štruktúrovaný katalóg (tabuľka v apke + presné fakty pre LLM),
  2. ako textové fakty, ktoré sa embedujú spolu s PDF (RAG).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from rdflib import BNode, Graph, Namespace, RDF, RDFS, OWL, XSD

NS = Namespace("http://www.semanticweb.org/janpavol/ontologies/2026/10/polovnicke-potreby#")

# Pekné slovenské názvy (IRI v ontológii sú bez diakritiky)
LABELS = {
    "Gulovnica": "Guľovnica", "Brokovnica": "Brokovnica", "Kombinovana_Zbran": "Kombinovaná zbraň",
    "Puskohlad": "Puškohľad", "Dalekohlad": "Ďalekohľad", "Termovizia": "Termovízia",
    "Dialkomer": "Diaľkomer", "Gulovy_Naboj": "Guľový náboj", "Brokovy_Naboj": "Brokový náboj",
    "Bunda": "Bunda", "Obuv": "Obuv", "Polovnicky_Noz": "Poľovnícky nôž", "Vabnicka": "Vábnička",
    "Zbrane": "Zbrane", "Optika": "Optika", "Strelivo": "Strelivo",
    "Oblecenie_A_Obuv": "Oblečenie a obuv", "Prislusenstvo": "Príslušenstvo",
    "Lacne": "Lacné", "Stredna_Trieda": "Stredná trieda", "Premiove": "Prémiové", "Luxusne": "Luxusné",
    "Bezna_Trieda": "Bežná trieda", "Exkluzivna_Trieda": "Exkluzívna trieda",
    "Harkila": "Härkila", "Finsko": "Fínsko", "Rakusko": "Rakúsko", "Dansko": "Dánsko",
    "Svedsko": "Švédsko",
}


def label(x: str) -> str:
    return LABELS.get(x, x.replace("_", " "))


def local(uri) -> str:
    return str(uri).split("#")[-1]


@dataclass
class Produkt:
    id: str
    nazov: str
    typ: str = ""
    skupina: str = ""
    vyrobca: str = ""
    krajina: str = ""
    cena: int | None = None
    kategoria: str = ""            # z ontológie (Spada_Do_Kategorie)
    kategoria_odvodena: str = ""   # vypočítaná z ceny podľa definícií v OWL
    strelivo: list[str] = field(default_factory=list)


class Ontologia:
    def __init__(self, path: str):
        self.g = Graph().parse(path)
        self.parent: dict[str, str] = {}   # pomenovaná trieda -> pomenovaný rodič
        for s, o in self.g.subject_objects(RDFS.subClassOf):
            if not isinstance(s, BNode) and not isinstance(o, BNode):
                self.parent[local(s)] = local(o)
        self.kategorie = self._cenove_kategorie()
        self.produkty = self._produkty()

    # ---------- pomocné ----------
    def _restrictions(self, cls):
        for r in self.g.objects(cls, RDFS.subClassOf):
            if (r, RDF.type, OWL.Restriction) not in self.g:
                continue
            prop = local(self.g.value(r, OWL.onProperty))
            for kind, pred in (("only", OWL.allValuesFrom), ("some", OWL.someValuesFrom), ("value", OWL.hasValue)):
                v = self.g.value(r, pred)
                if v is not None:
                    yield prop, kind, v

    def podtriedy(self, name: str) -> list[str]:
        return sorted(c for c, p in self.parent.items() if p == name)

    def _cenove_kategorie(self) -> dict[str, tuple[int | None, int | None]]:
        """Načíta rozsahy cien z owl:equivalentClass (minInclusive / maxExclusive)."""
        out = {}
        for top in self.podtriedy("Cenova_Kategoria"):
            for k in self.podtriedy(top):
                lo = hi = None
                for eq in self.g.objects(NS[k], OWL.equivalentClass):
                    for pred, val in self._facety(eq):
                        if pred == XSD.minInclusive:
                            lo = int(val)
                        elif pred == XSD.maxExclusive:
                            hi = int(val)
                out[k] = (lo, hi)
        return out

    def _facety(self, node, seen=None):
        """Prejde blank-node strom definície triedy a vráti facety (min/max)."""
        seen = seen if seen is not None else set()
        if node in seen or not isinstance(node, BNode):
            return
        seen.add(node)
        for p, o in self.g.predicate_objects(node):
            if p in (XSD.minInclusive, XSD.maxExclusive, XSD.maxInclusive, XSD.minExclusive):
                yield p, o
            elif isinstance(o, BNode):
                yield from self._facety(o, seen)

    def kategoria_podla_ceny(self, cena: int | None) -> str:
        if cena is None:
            return ""
        for k, (lo, hi) in self.kategorie.items():
            if (lo is None or cena >= lo) and (hi is None or cena < hi):
                return k
        return ""

    def _produkty(self) -> list[Produkt]:
        out = []
        for cls in self.podtriedy("Zname_Produkty"):
            p = Produkt(id=cls, nazov=cls.replace("_", " "))
            for prop, kind, v in self._restrictions(NS[cls]):
                if prop == "Je_Typu":
                    p.typ = local(v)
                elif prop == "Ma_Vyrobcu":
                    p.vyrobca = local(v)
                elif prop == "Spada_Do_Kategorie":
                    p.kategoria = local(v)
                elif prop == "Krajina_Povodu":
                    p.krajina = str(v)
                elif prop == "Cena":
                    p.cena = int(v)
                elif prop == "Pouziva_Strelivo":
                    p.strelivo.append(local(v))
            p.skupina = self.parent.get(p.typ, "")
            p.kategoria_odvodena = self.kategoria_podla_ceny(p.cena)
            out.append(p)
        return sorted(out, key=lambda x: (x.cena is None, x.cena))

    # ---------- výstupy ----------
    def tabulka(self) -> list[dict]:
        return [{
            "Produkt": p.nazov, "Typ": label(p.typ), "Skupina": label(p.skupina),
            "Výrobca": label(p.vyrobca), "Krajina": label(p.krajina), "Cena (€)": p.cena,
            "Cenová kategória": label(p.kategoria or p.kategoria_odvodena),
        } for p in self.produkty]

    def fakty(self) -> list[str]:
        """Textové fakty z ontológie – idú do vektorového indexu."""
        f = []
        for p in self.produkty:
            s = (f"Produkt {p.nazov} je typu {label(p.typ)} (skupina {label(p.skupina)}), "
                 f"výrobca {label(p.vyrobca)}, krajina pôvodu {label(p.krajina)}, "
                 f"cena v e-shope {p.cena} €, cenová kategória {label(p.kategoria or p.kategoria_odvodena)}.")
            if p.strelivo:
                s += " Používa strelivo: " + ", ".join(label(x) for x in p.strelivo) + "."
            f.append(s)
        for top in self.podtriedy("Typ_Potreby"):
            subs = self.podtriedy(top)
            if subs:
                f.append(f"Skupina poľovníckych potrieb {label(top)} zahŕňa: " + ", ".join(label(s) for s in subs) + ".")
        for k, (lo, hi) in self.kategorie.items():
            rng = f"od {lo} €" if lo is not None else ""
            rng += f" do {hi - 1} €" if hi is not None else ""
            f.append(f"Cenová kategória {label(k)} ({label(self.parent.get(k, ''))}) znamená cenu {rng.strip()}.")
        return f

    def suhrn(self) -> str:
        """Kompaktný prehľad e-shopu, ktorý LLM dostane vždy (presné ceny, min/max)."""
        lines = ["KATALÓG E-SHOPU (z ontológie, zoradené od najlacnejšieho):"]
        for i, p in enumerate(self.produkty, 1):
            lines.append(f"{i}. {p.nazov} – {label(p.typ)}, {label(p.vyrobca)} ({label(p.krajina)}), "
                         f"{p.cena} €, {label(p.kategoria or p.kategoria_odvodena)}")
        if self.produkty:
            lo, hi = self.produkty[0], self.produkty[-1]
            lines.append(f"Najlacnejší produkt v e-shope: {lo.nazov} ({lo.cena} €).")
            lines.append(f"Najdrahší produkt v e-shope: {hi.nazov} ({hi.cena} €).")
        by = {}
        for p in self.produkty:
            for key in (p.typ, p.skupina):
                by.setdefault(key, []).append(p)
        for key, ps in by.items():
            if len(ps) > 1:
                lines.append(f"Najlacnejší model v kategórii {label(key)}: {ps[0].nazov} ({ps[0].cena} €); "
                             f"najdrahší: {ps[-1].nazov} ({ps[-1].cena} €).")
        return "\n".join(lines)


if __name__ == "__main__":
    import yaml
    cfg = yaml.safe_load(open("config.yaml", encoding="utf-8"))
    o = Ontologia(cfg["ontology_file"])
    print(o.suhrn())
    print("\nCenové kategórie z OWL:", o.kategorie)
    print("\n".join(o.fakty()[:3]))
