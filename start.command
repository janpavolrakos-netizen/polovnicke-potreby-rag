#!/bin/bash
# Spúšťač aplikácie (macOS: dvojklik). Pri prvom spustení všetko pripraví.
cd "$(dirname "$0")"
set -e

if ! command -v ollama >/dev/null 2>&1; then
  echo "❌ Ollama nie je nainštalovaná. Stiahni ju z https://ollama.com/download a spusti znova."
  read -p "Stlač Enter pre ukončenie…"; exit 1
fi
# spusti Ollama server, ak nebeží
if ! curl -s http://localhost:11434/api/tags >/dev/null; then
  echo "▶ Spúšťam Ollama…"; (ollama serve >/dev/null 2>&1 &); sleep 3
fi

LLM=$(grep '^llm_model:' config.yaml | awk '{print $2}')
EMB=$(grep '^embed_model:' config.yaml | awk '{print $2}')
for m in "$LLM" "$EMB"; do
  ollama list | grep -q "^$m" || { echo "⬇ Sťahujem model $m…"; ollama pull "$m"; }
done

if [ ! -d .venv ]; then
  echo "▶ Vytváram Python prostredie…"
  python3 -m venv .venv
  ./.venv/bin/pip install -q --upgrade pip
  ./.venv/bin/pip install -q -r requirements.txt
fi

if [ ! -f index/embeddings.npy ]; then
  echo "▶ Indexujem ontológiu a PDF (prvýkrát, pár minút)…"
  ./.venv/bin/python ingest.py
fi

echo "✅ Otváram aplikáciu v prehliadači…"
./.venv/bin/streamlit run app.py --server.headless false
