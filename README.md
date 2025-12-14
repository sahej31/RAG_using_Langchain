# OSS RAG Lab 

This is a **open-source RAG project** built with:

- 🧠 **LLM:** [Ollama](https://ollama.com/) running an open-source model (default: `llama3`)
- 🔎 **Retrieval:** BM25 + vector store (Chroma)
- 📦 **Orchestration:** LangChain (no paid APIs, no keys)
- 🌐 **Backend:** FastAPI
- 💾 **DB:** SQLite + SQLAlchemy for feedback
- 🎛️ **UI:** Simple HTML/JS frontend (no build tools)

You get:

- Multiple RAG pipelines: `bm25`, `vector`, `hybrid`
- Feedback storage (👍 / 👎 per answer)
- Simple per-pipeline metrics
- Offline docs-based QA

Perfect to push directly to GitHub as a showcase of **LLM + RAG + full-stack** using only open-source tools.

---

## 1. Prerequisites

1. **Python** 3.10+
2. **Ollama** installed and running  
   Install guide: see the official website.

Then pull the models (all free and open-source):

```bash
ollama pull llama3
ollama pull nomic-embed-text
```

> You can switch to other models later in `app/core/config.py`.

---

## 2. Setup

```bash
cd oss-rag-lab

python -m venv .venv
source .venv/bin/activate        # On Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

No API keys needed. No .env needed unless you want to override defaults.

---

## 3. Prepare documents

Put your domain documents (txt/markdown/etc.) into:

- `data/docs/`

There are two tiny sample files already included so everything works out of the box.

Then build indexes (BM25 + vector store):

```bash
python -m app.rag.indexer
```

This will:

- Load and chunk docs from `data/docs/`
- Build:
  - a **BM25** retriever
  - a **Chroma** vector store using `OllamaEmbeddings`
- Persist the vector store into `data/vector_store/`

---

## 4. Run the API server

```bash
uvicorn app.main:app --reload
```

Open: **http://localhost:8000**

You can:

- Choose a pipeline (`hybrid`, `bm25`, `vector`)
- Ask a question based on your docs
- See:
  - Answer
  - Retrieved context chunks
- Give 👍 / 👎 feedback on the answer

Feedback is stored in **SQLite**: `local_rag.db`.

The **metrics** card on the page shows per-pipeline:

- total feedback count
- positive count
- positive rate

---

## 5. Offline evaluation (optional)

Example eval questions live in:

- `data/eval/qa.jsonl`

Run:

```bash
python -m app.eval.eval_runner
```

This will:

- Run all pipelines on the eval questions
- Compute a simple lexical-overlap score for each answer
- Write detailed results to:

```text
data/eval/results.json
```

You can extend this with more metrics or add an LLM-as-a-judge later.

---

## 6. Project structure

```text
oss-rag-lab/
  app/
    __init__.py
    main.py              # FastAPI app + routes
    core/
      __init__.py
      config.py          # Settings (models, paths, DB URL)
    models/
      __init__.py
      db.py              # SQLAlchemy models + engine
    rag/
      __init__.py
      pipelines.py       # RAG pipelines (bm25/vector/hybrid)
      indexer.py         # Build indexes from data/docs
    eval/
      __init__.py
      eval_runner.py     # Offline evaluation
    templates/
      index.html         # Simple frontend
    static/
      main.js            # Frontend logic
      styles.css         # Minimal styling
  data/
    docs/                # Your documents
    eval/
      qa.jsonl           # Sample eval QA pairs
      results.json       # (generated) eval results
  local_rag.db           # (generated) SQLite feedback DB
  requirements.txt
  README.md
  LICENSE
```

---

## 7. License

This project is under the **MIT License** (see `LICENSE`).  
You can freely modify, use, and publish it as your own project. Just update the copyright line.

---

## 8. Quick GitHub push

```bash
git init
git add .
git commit -m "Initial commit: OSS RAG Lab"
git branch -M main
git remote add origin <your-github-repo-url>
git push -u origin main
```

Then add a nice description + tags like: `rag`, `ollama`, `langchain`, `fastapi`, `ml`, `llm`.
