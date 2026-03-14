"""
CarbonIQ - Vector Service
In-memory TF-IDF document similarity engine for PDD and methodology documents.
No external vector DB dependency — uses scikit-learn.
"""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from typing import List, Optional, Tuple


class VectorService:
    """In-memory document index using TF-IDF vectors."""

    def __init__(self):
        self.documents = {}       # id -> {"text": str, "title": str, "metadata": dict}
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words="english",
            ngram_range=(1, 2),
            min_df=1,
        )
        self._matrix = None
        self._doc_ids = []
        self._dirty = True

    def add_document(self, doc_id: str, title: str, text: str, metadata: dict = None):
        """Add or update a document in the index."""
        self.documents[doc_id] = {
            "text": text,
            "title": title,
            "metadata": metadata or {},
        }
        self._dirty = True

    def remove_document(self, doc_id: str) -> bool:
        """Remove a document from the index."""
        if doc_id in self.documents:
            del self.documents[doc_id]
            self._dirty = True
            return True
        return False

    def _rebuild_index(self):
        """Rebuild TF-IDF matrix from current documents."""
        if not self.documents:
            self._matrix = None
            self._doc_ids = []
            self._dirty = False
            return

        self._doc_ids = list(self.documents.keys())
        texts = [self.documents[did]["text"] for did in self._doc_ids]

        try:
            self._matrix = self.vectorizer.fit_transform(texts)
        except ValueError:
            # Handle edge case with very few/empty documents
            self._matrix = None

        self._dirty = False

    def search_similar(self, query: str, top_k: int = 5) -> List[dict]:
        """
        Find documents most similar to the query.
        Returns list of {doc_id, title, similarity, metadata}.
        """
        if self._dirty:
            self._rebuild_index()

        if self._matrix is None or len(self._doc_ids) == 0:
            return []

        try:
            query_vec = self.vectorizer.transform([query])
            similarities = cosine_similarity(query_vec, self._matrix).flatten()
        except Exception:
            return []

        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for idx in top_indices:
            if similarities[idx] > 0.01:  # Minimum relevance threshold
                doc_id = self._doc_ids[idx]
                doc = self.documents[doc_id]
                results.append({
                    "doc_id": doc_id,
                    "title": doc["title"],
                    "similarity": round(float(similarities[idx]), 4),
                    "content_summary": doc["text"][:200] + "..." if len(doc["text"]) > 200 else doc["text"],
                    "metadata": doc["metadata"],
                })

        return results

    def get_document(self, doc_id: str) -> Optional[dict]:
        """Retrieve a specific document."""
        return self.documents.get(doc_id)

    def get_stats(self) -> dict:
        """Get index statistics."""
        return {
            "total_documents": len(self.documents),
            "index_dirty": self._dirty,
            "vocabulary_size": len(self.vectorizer.vocabulary_) if hasattr(self.vectorizer, 'vocabulary_') and self.vectorizer.vocabulary_ else 0,
        }


# Singleton instance
vector_service = VectorService()
