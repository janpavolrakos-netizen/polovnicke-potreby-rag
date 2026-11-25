"""Vytvorí vektorový index z ontológie + PDF (spusti raz, alebo po pridaní PDF)."""
from rag_core import build_index, load_config

if __name__ == "__main__":
    build_index(load_config())
