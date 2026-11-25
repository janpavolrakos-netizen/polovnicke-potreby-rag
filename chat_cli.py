"""Konzolová verzia chatu (ako v pôvodnom videu easy-local-rag)."""
from rag_core import RAG, load_config

if __name__ == "__main__":
    rag = RAG(load_config())
    history = []
    print("RAG – Poľovnícke potreby. Napíš otázku (koniec = 'quit').")
    while True:
        q = input("\nTy: ").strip()
        if q.lower() in {"quit", "exit", "koniec"}:
            break
        gen, hits = rag.answer(q, history)
        print("\nAsistent: ", end="")
        ans = ""
        for t in gen:
            print(t, end="", flush=True)
            ans += t
        print("\n\nZdroje: " + "; ".join(f"{h['source']}" + (f" s.{h['page']}" if h['page'] else "") for h in hits))
        history += [{"role": "user", "content": q}, {"role": "assistant", "content": ans}]
