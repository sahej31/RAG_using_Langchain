"""Build RAG indexes from data/docs using local Ollama-based embeddings.

Usage:
    python -m app.rag.indexer
"""

from app.rag.pipelines import RAGPipelines


def main():
    pipelines = RAGPipelines()
    pipelines.build_indexes()
    print("Indexes built successfully.")


if __name__ == "__main__":
    main()
