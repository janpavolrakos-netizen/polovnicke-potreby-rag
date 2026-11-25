# Poľovnícke potreby – lokálny RAG asistent

Lokálny RAG (Retrieval-Augmented Generation) podľa videa *Easy 100% Local RAG (Ollama)*,
rozšírený o napojenie na ontológiu z WebProtégé a Streamlit aplikáciu.

## Čo to robí
- **Ontológia** `data/ontology/polovnicke-potreby.owl` – produkty e-shopu, výrobcovia, typy, ceny, cenové kategórie.
- **9 PDF** v `data/pdf/` – návody (Sako, Beretta, Swarovski, Zeiss, Pulsar, Leica) a predpisy (zákon 274/2009, 190/2003, vyhláška 344/2009).
- **Ollama** – lokálny LLM `llama3.2` + embedding model `bge-m3`. Nič neodchádza na internet.
- **Streamlit apka** – chat so zdrojmi, katalóg e-shopu, prehľad ontológie, nahratie ďalších PDF.

## Spustenie (macOS)
1. Nainštaluj **Ollama**: https://ollama.com/download (spusti ju).
2. Dvojklik na **`start.command`** (prvýkrát: pravý klik → Otvoriť).
   Skript sám stiahne modely, vytvorí Python prostredie, zaindexuje dáta a otvorí apku v prehliadači.

### Ručne (terminál)
```bash
ollama pull llama3.2
ollama pull bge-m3
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python ingest.py          # vytvorí index (ontológia + PDF)
streamlit run app.py      # web apka  (alebo: python chat_cli.py – konzola)
```

## Súbory
| súbor | úloha |
|---|---|
| `ontology.py` | načíta OWL (rdflib), vytiahne produkty a cenové kategórie (vrátane rozsahov cien z `owl:equivalentClass`) |
| `rag_core.py` | PDF → úseky, filter jazykov, embeddingy (Ollama), kosínusové vyhľadávanie, prompt, odpoveď |
| `ingest.py` | zostaví vektorový index do `index/` |
| `app.py` | Streamlit aplikácia |
| `chat_cli.py` | konzolový chat (ako v pôvodnom videu) |
| `config.yaml` | modely, top-k, veľkosť úsekov, jazyky |

## Ukážkové otázky
- Aký je najlacnejší model v e-shope? → Morakniv Companion (20 €)
- Ktorá guľovnica je najlacnejšia? → Sako 85 (2200 €)
- Ako sa zapína termovízia Helion?
- Kto môže vykonávať poľovníctvo podľa zákona 274/2009?

## Zdroje PDF
| súbor | zdroj |
|---|---|
| 02_Sako_85_Classic.pdf | https://media.sako.global/image/upload/v1683879422/85_Classic_wzb8di.pdf |
| 03_Beretta_brokovnica_manual.pdf | https://www.beretta.com/content/dam/beretta-usa/user-manuals/Side_By_Side_Manual.pdf |
| 04_Swarovski_Z8i_navod.pdf | https://admin2.optics-trade.eu/media/instructions/Instructions_Swarovski_Z8i_OpticsTrade.pdf |
| 05_Zeiss_Victory_SF_navod.pdf | https://www.juelich-bonn.com/pdf/Victory-SF_Handbuch.pdf |
| 06_Pulsar_Helion2_XP50_PRO_manual.pdf | https://cdn.shopify.com/s/files/1/0584/7302/1645/files/HELION_2_XP50_PRO_manual_EN_RU.pdf |
| 07_Leica_Rangemaster_CRF_navod.pdf | https://cdn.shopify.com/s/files/1/1120/4516/files/pm-108993-Leica-CRF-R_CRF-Pro_Instructions_en_2.0.pdf |
| 09_Zakon_274-2009_o_polovnictve.pdf | https://static.slov-lex.sk/pdf/SK/ZZ/2009/274/ZZ_2009_274_20260601.pdf |
| 10_Zakon_190-2003_o_strelnych_zbraniach.pdf | https://static.slov-lex.sk/pdf/SK/ZZ/2003/190/ZZ_2003_190_20221115.pdf |
| 11_Vyhlaska_344-2009_k_zakonu_o_polovnictve.pdf | https://static.slov-lex.sk/pdf/SK/ZZ/2009/344/ZZ_2009_344_20250401.pdf |

PDF sú verejne dostupné dokumenty výrobcov a slovenské právne predpisy, použité na študijné účely.
