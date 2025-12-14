import os
import time
from typing import Literal, List, Dict, Any

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_community.vectorstores import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.chat_models import ChatOllama
from langchain_community.embeddings import OllamaEmbeddings
from langchain.schema import Document

from app.core.config import settings


PipelineId = Literal["bm25", "vector", "hybrid"]


class RAGPipelines:
    """Collection of RAG pipelines backed by local, free models via Ollama."""

    def __init__(self):
        # Local LLM & embeddings via Ollama (no API keys)
        self.llm = ChatOllama(
            model=settings.ollama_model,
            temperature=0.1,
        )
        self.embeddings = OllamaEmbeddings(model=settings.ollama_embedding_model)

        self._bm25_retriever = None
        self._vector_store = None

    # ---------- Document loading / chunking ----------

    def _load_documents(self) -> List[Document]:
        if not os.path.isdir(settings.docs_dir):
            raise RuntimeError(f"Docs directory not found: {settings.docs_dir}")

        loader = DirectoryLoader(
            settings.docs_dir,
            glob="**/*.txt",
            loader_cls=TextLoader,
            show_progress=True,
        )
        docs = loader.load()
        if not docs:
            raise RuntimeError(
                f"No documents found in {settings.docs_dir}. "
                "Add .txt files then run the indexer."
            )

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=200,
        )
        chunks = splitter.split_documents(docs)
        return chunks

    # ---------- Retrievers ----------

    def _ensure_bm25(self):
        if self._bm25_retriever is not None:
            return
        chunks = self._load_documents()
        self._bm25_retriever = BM25Retriever.from_documents(chunks)
        self._bm25_retriever.k = 5

    def _ensure_vector_store(self):
        if self._vector_store is not None:
            return
        if not os.path.isdir(settings.vector_store_dir):
            raise RuntimeError(
                f"Vector store directory not found at {settings.vector_store_dir}. "
                "Run the indexer first: python -m app.rag.indexer"
            )
        self._vector_store = Chroma(
            collection_name="oss_rag_docs",
            embedding_function=self.embeddings,
            persist_directory=settings.vector_store_dir,
        )

    # ---------- Public: build indexes ----------

    def build_indexes(self):
        chunks = self._load_documents()

        # BM25
        self._bm25_retriever = BM25Retriever.from_documents(chunks)
        self._bm25_retriever.k = 5

        # Vector store
        os.makedirs(settings.vector_store_dir, exist_ok=True)
        self._vector_store = Chroma.from_documents(
            chunks,
            embedding=self.embeddings,
            collection_name="oss_rag_docs",
            persist_directory=settings.vector_store_dir,
        )
        self._vector_store.persist()

    # ---------- Retrieval wrappers ----------

    def _retrieve_bm25(self, query: str) -> List[Document]:
        self._ensure_bm25()
        return self._bm25_retriever.get_relevant_documents(query)

    def _retrieve_vector(self, query: str) -> List[Document]:
        self._ensure_vector_store()
        return self._vector_store.similarity_search(query, k=5)

    def _retrieve_hybrid(self, query: str) -> List[Document]:
        bm25_docs = self._retrieve_bm25(query)
        vec_docs = self._retrieve_vector(query)
        # Simple hybrid: merge + deduplicate by page_content
        seen = set()
        merged: List[Document] = []
        for d in bm25_docs + vec_docs:
            key = d.page_content.strip()
            if key not in seen:
                seen.add(key)
                merged.append(d)
        return merged[:8]

    # ---------- Answer generation ----------

    def answer(self, question: str, pipeline_id: PipelineId) -> Dict[str, Any]:
        start = time.time()
        if pipeline_id == "bm25":
            docs = self._retrieve_bm25(question)
        elif pipeline_id == "vector":
            docs = self._retrieve_vector(question)
        elif pipeline_id == "hybrid":
            docs = self._retrieve_hybrid(question)
        else:
            raise ValueError(f"Unknown pipeline_id: {pipeline_id}")

        context_text = "\n\n".join(d.page_content for d in docs)

        prompt = f"""You are a helpful assistant that answers questions strictly
based on the provided context. If the context is insufficient, say that you don't know
and suggest what additional information would be needed. Do not invent facts.

Context:
{context_text}

Question: {question}

Answer: """

        response = self.llm.invoke(prompt)
        latency_ms = (time.time() - start) * 1000.0

        return {
            "answer": response.content,
            "context": [d.page_content for d in docs],
            "latency_ms": latency_ms,
            "pipeline_id": pipeline_id,
        }


_pipelines_instance: RAGPipelines | None = None


def get_pipelines() -> RAGPipelines:
    global _pipelines_instance
    if _pipelines_instance is None:
        _pipelines_instance = RAGPipelines()
    return _pipelines_instance
