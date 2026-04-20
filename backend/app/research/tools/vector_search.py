import json
import logging
import os
from typing import Optional

from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# Global FAISS store reference
_faiss_store = None


def _get_embeddings(settings):
    """Return the configured embeddings provider, preferring Jina."""
    if settings.JINA_API_KEY:
        from langchain_community.embeddings import JinaEmbeddings

        logger.info("Using Jina embeddings for FAISS search")
        return JinaEmbeddings(
            model_name="jina-embeddings-v2-base-en",
            jina_api_key=settings.JINA_API_KEY,
        )

    if settings.GEMINI_API_KEY:
        from langchain_google_genai import GoogleGenerativeAIEmbeddings

        logger.info("Using Gemini embeddings for FAISS search")
        return GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=settings.GEMINI_API_KEY,
        )

    logger.warning("No embeddings API key configured. Set JINA_API_KEY or GEMINI_API_KEY.")
    return None


def get_faiss_store():
    """Get the FAISS store, loading it on first access."""
    global _faiss_store
    if _faiss_store is not None:
        return _faiss_store

    try:
        from langchain_community.vectorstores import FAISS
        from app.config import get_settings

        settings = get_settings()
        backend_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        index_path = os.path.join(backend_root, "data", "faiss_index")

        if not os.path.exists(index_path):
            logger.warning(f"FAISS index not found at {index_path}")
            return None

        embeddings = _get_embeddings(settings)
        if embeddings is None:
            return None

        _faiss_store = FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)
        logger.info("FAISS index loaded successfully")
        return _faiss_store

    except Exception as e:
        logger.error(f"Failed to load FAISS index: {e}")
        return None


@tool
def search_financial_documents(query: str) -> str:
    """
    Search through financial documents like earnings reports, company summaries, and SEC filings.
    Returns the most relevant document passages for the given query.
    Use this when you need detailed financial information from company reports and filings.
    
    Args:
        query: Search query (e.g., "Apple Q4 2024 revenue", "Tesla profit margins", "Microsoft cloud growth")
    """
    store = get_faiss_store()

    if store is None:
        return json.dumps({
            "documents": [],
            "query": query,
            "message": "Vector search unavailable — FAISS index not loaded",
        })

    try:
        results = store.similarity_search_with_score(query, k=3)

        documents = []
        for doc, score in results:
            # Lower score = more similar in FAISS (L2 distance)
            if score < 1.5:  # Relevance threshold
                normalized_score = round(float(1 / (1 + float(score))), 3)
                documents.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "relevance_score": normalized_score,  # Convert to 0-1 similarity
                })

        if not documents:
            return json.dumps({
                "documents": [],
                "query": query,
                "message": "No relevant documents found in the knowledge base",
            })

        return json.dumps({
            "documents": documents,
            "query": query,
            "total_results": len(documents),
        })

    except Exception as e:
        logger.error(f"Vector search failed: {e}")
        return json.dumps({
            "documents": [],
            "query": query,
            "message": f"Vector search error: {str(e)}",
        })
