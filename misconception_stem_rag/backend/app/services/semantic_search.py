"""Semantic search service using ChromaDB and sentence-transformers.

This module provides semantic embedding and retrieval for PDF content,
enabling true RAG (Retrieval-Augmented Generation) for question generation.
"""

from __future__ import annotations

import logging
from typing import Any

import chromadb
from sentence_transformers import SentenceTransformer

from ..config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Initialize sentence-transformer model
# Using all-MiniLM-L6-v2: Fast, lightweight, good for semantic search
EMBEDDING_MODEL = None

def get_embedding_model():
    """Lazy load the embedding model to avoid loading on every import."""
    global EMBEDDING_MODEL
    if EMBEDDING_MODEL is None:
        logger.info("🔧 Loading sentence-transformer model: all-MiniLM-L6-v2")
        EMBEDDING_MODEL = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("✅ Embedding model loaded successfully")
    return EMBEDDING_MODEL


class SemanticSearchService:
    """Service for semantic embedding and retrieval using ChromaDB."""
    
    def __init__(self):
        """Initialize ChromaDB client and embedding model."""
        self.client = chromadb.PersistentClient(path=str(settings.chroma_db_path))
        self.embedding_model = get_embedding_model()
        logger.info(f"📦 ChromaDB initialized at: {settings.chroma_db_path}")
    
    def create_or_get_collection(self, collection_name: str):
        """
        Create or retrieve a ChromaDB collection.
        
        Args:
            collection_name: Name of the collection (e.g., 'pdf_content', 'misconceptions')
        
        Returns:
            ChromaDB collection object
        """
        try:
            collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}  # Use cosine similarity
            )
            logger.info(f"✅ Collection '{collection_name}' ready (count: {collection.count()})")
            return collection
        except Exception as e:
            logger.error(f"❌ Error creating collection '{collection_name}': {str(e)}")
            raise
    
    def embed_text(self, text: str | list[str]) -> list[list[float]]:
        """
        Generate embeddings for text using sentence-transformers.
        
        Args:
            text: Single text string or list of text strings
        
        Returns:
            List of embedding vectors
        """
        if isinstance(text, str):
            text = [text]
        
        try:
            embeddings = self.embedding_model.encode(text, convert_to_numpy=True)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"❌ Error generating embeddings: {str(e)}")
            raise
    
    def store_pdf_chunks(
        self,
        session_id: str,
        chunks: list[str],
        metadata_list: list[dict[str, Any]],
    ) -> int:
        """
        Store PDF chunks with embeddings in ChromaDB.
        
        Args:
            session_id: Unique session identifier
            chunks: List of text chunks from PDF
            metadata_list: List of metadata dicts for each chunk
                          Should include: page, topic, chunk_index, total_chunks
        
        Returns:
            Number of chunks stored
        """
        collection_name = f"pdf_session_{session_id}"
        collection = self.create_or_get_collection(collection_name)
        
        try:
            logger.info(f"🔄 Embedding {len(chunks)} PDF chunks...")
            embeddings = self.embed_text(chunks)
            
            # Generate unique IDs for each chunk
            ids = [f"{session_id}_chunk_{i}" for i in range(len(chunks))]
            
            # Store in ChromaDB
            collection.add(
                documents=chunks,
                embeddings=embeddings,
                metadatas=metadata_list,
                ids=ids
            )
            
            logger.info(f"✅ Stored {len(chunks)} chunks in ChromaDB collection '{collection_name}'")
            return len(chunks)
            
        except Exception as e:
            logger.error(f"❌ Error storing PDF chunks: {str(e)}")
            raise
    
    def semantic_search(
        self,
        session_id: str,
        query: str,
        n_results: int = 5,
        filter_metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Perform semantic search on stored PDF chunks.
        
        Args:
            session_id: Session identifier to search within
            query: Search query (e.g., topic name or question context)
            n_results: Number of results to retrieve (default: 5)
            filter_metadata: Optional metadata filters (e.g., {"page": 3})
        
        Returns:
            Dictionary with:
                - documents: List of retrieved text chunks
                - distances: Similarity scores (lower = more similar)
                - metadatas: Metadata for each chunk
                - ids: Chunk IDs
        """
        collection_name = f"pdf_session_{session_id}"
        
        try:
            collection = self.client.get_collection(collection_name)
        except Exception:
            logger.warning(f"⚠️ Collection '{collection_name}' not found. No embeddings stored yet.")
            return {
                "documents": [],
                "distances": [],
                "metadatas": [],
                "ids": []
            }
        
        try:
            logger.info(f"🔍 Semantic search: '{query}' in collection '{collection_name}'")
            
            # Generate query embedding
            query_embedding = self.embed_text(query)[0]
            
            # Search ChromaDB
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=min(n_results, collection.count()),
                where=filter_metadata  # Optional metadata filtering
            )
            
            # Extract first result (we only sent one query)
            retrieved = {
                "documents": results["documents"][0] if results["documents"] else [],
                "distances": results["distances"][0] if results["distances"] else [],
                "metadatas": results["metadatas"][0] if results["metadatas"] else [],
                "ids": results["ids"][0] if results["ids"] else []
            }
            
            logger.info(f"✅ Retrieved {len(retrieved['documents'])} relevant chunks")
            return retrieved
            
        except Exception as e:
            logger.error(f"❌ Error in semantic search: {str(e)}")
            raise
    
    def get_collection_stats(self, session_id: str) -> dict[str, Any]:
        """
        Get statistics about a PDF session collection.
        
        Args:
            session_id: Session identifier
        
        Returns:
            Dictionary with collection statistics
        """
        collection_name = f"pdf_session_{session_id}"
        
        try:
            collection = self.client.get_collection(collection_name)
            return {
                "collection_name": collection_name,
                "total_chunks": collection.count(),
                "exists": True
            }
        except Exception:
            return {
                "collection_name": collection_name,
                "total_chunks": 0,
                "exists": False
            }
    
    def delete_session_collection(self, session_id: str) -> bool:
        """
        Delete all embeddings for a session (cleanup).
        
        Args:
            session_id: Session identifier
        
        Returns:
            True if deleted, False if collection didn't exist
        """
        collection_name = f"pdf_session_{session_id}"
        
        try:
            self.client.delete_collection(collection_name)
            logger.info(f"🗑️ Deleted collection '{collection_name}'")
            return True
        except Exception:
            logger.warning(f"⚠️ Collection '{collection_name}' not found for deletion")
            return False


# Singleton instance
_semantic_search_service = None

def get_semantic_search_service() -> SemanticSearchService:
    """Get or create the singleton SemanticSearchService instance."""
    global _semantic_search_service
    if _semantic_search_service is None:
        _semantic_search_service = SemanticSearchService()
    return _semantic_search_service
