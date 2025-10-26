"""BM25 ranking algorithm for GitHound search engine.

BM25 is a probabilistic ranking function that provides better
relevance scoring than traditional TF-IDF.
"""

import math
from collections import defaultdict
from typing import Any

from ..models import SearchQuery, SearchResult


class BM25Ranker:
    """BM25 (Best Matching 25) ranking algorithm implementation.

    BM25 is considered the state-of-the-art probabilistic ranking function
    for text retrieval. It addresses limitations of TF-IDF by using
    saturation functions and document length normalization.

    Key improvements over TF-IDF:
    1. Term frequency saturation (diminishing returns for repeated terms)
    2. Document length normalization
    3. Better handling of short vs long documents
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        """Initialize BM25 ranker.

        Args:
            k1: Controls term frequency saturation (typical range: 1.2-2.0)
                Higher values = less saturation
            b: Controls document length normalization (typical range: 0.5-0.8)
               0 = no normalization, 1 = full normalization
        """
        self.k1 = k1
        self.b = b

        # Document statistics
        self.doc_freqs: dict[str, int] = defaultdict(int)  # Term -> doc frequency
        self.doc_lengths: dict[str, int] = {}  # Doc ID -> length
        self.avg_doc_length = 0.0
        self.num_docs = 0

        # Cache for IDF scores
        self._idf_cache: dict[str, float] = {}

    def index_documents(self, documents: list[dict[str, Any]]) -> None:
        """Index documents for BM25 scoring.

        Args:
            documents: List of dicts with 'id' and 'text' keys
        """
        total_length = 0

        for doc in documents:
            doc_id = doc["id"]
            text = doc["text"]

            # Tokenize
            tokens = self._tokenize(text)
            doc_length = len(tokens)

            # Store document length
            self.doc_lengths[doc_id] = doc_length
            total_length += doc_length

            # Track unique terms
            unique_terms = set(tokens)
            for term in unique_terms:
                self.doc_freqs[term] += 1

        self.num_docs = len(documents)
        self.avg_doc_length = total_length / self.num_docs if self.num_docs > 0 else 0

        # Clear IDF cache after re-indexing
        self._idf_cache.clear()

    def score(self, query: str, doc_id: str, doc_text: str) -> float:
        """Calculate BM25 score for a document given a query.

        Args:
            query: Search query
            doc_id: Document ID
            doc_text: Document text content

        Returns:
            BM25 score (higher is better)
        """
        query_tokens = self._tokenize(query)
        doc_tokens = self._tokenize(doc_text)

        # Count term frequencies in document
        term_freqs: dict[str, int] = defaultdict(int)
        for token in doc_tokens:
            term_freqs[token] += 1

        doc_length = self.doc_lengths.get(doc_id, len(doc_tokens))

        score = 0.0

        for term in query_tokens:
            if term not in term_freqs:
                continue

            # Term frequency in document
            tf = term_freqs[term]

            # IDF score
            idf = self._get_idf(term)

            # Document length normalization factor
            doc_len_norm = 1 - self.b + self.b * (doc_length / self.avg_doc_length)

            # BM25 formula
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * doc_len_norm

            score += idf * (numerator / denominator)

        return score

    def rank_results(self, results: list[SearchResult], query: SearchQuery) -> list[SearchResult]:
        """Rank search results using BM25.

        Args:
            results: List of search results
            query: Original search query

        Returns:
            Sorted list of results with updated relevance scores
        """
        if not results:
            return results

        # Index documents from results
        documents = []
        for result in results:
            # Combine multiple text fields for better matching
            text_parts = []

            if result.matching_line:
                text_parts.append(result.matching_line)

            if result.commit_info:
                text_parts.append(result.commit_info.message)
                text_parts.append(result.commit_info.author_name)

            doc_text = " ".join(text_parts)

            documents.append(
                {
                    "id": result.commit_hash,
                    "text": doc_text,
                }
            )

        # Index documents
        self.index_documents(documents)

        # Build query text from all query fields
        query_parts = []
        if query.content_pattern:
            query_parts.append(query.content_pattern)
        if query.message_pattern:
            query_parts.append(query.message_pattern)
        if query.author_pattern:
            query_parts.append(query.author_pattern)

        query_text = " ".join(query_parts)

        # Score each result
        for i, result in enumerate(results):
            doc_text = documents[i]["text"]
            bm25_score = self.score(query_text, result.commit_hash, doc_text)

            # Combine BM25 score with existing relevance score
            # Use weighted average (70% BM25, 30% existing)
            combined_score = 0.7 * bm25_score + 0.3 * result.relevance_score
            result.relevance_score = combined_score

        # Sort by relevance score
        results.sort(key=lambda r: r.relevance_score, reverse=True)

        return results

    def _get_idf(self, term: str) -> float:
        """Get IDF score for a term (with caching).

        IDF formula: log((N - df + 0.5) / (df + 0.5) + 1)
        where N = total documents, df = document frequency
        """
        if term in self._idf_cache:
            return self._idf_cache[term]

        df = self.doc_freqs.get(term, 0)

        # BM25 IDF formula (slightly different from standard IDF)
        idf = math.log((self.num_docs - df + 0.5) / (df + 0.5) + 1)

        self._idf_cache[term] = idf
        return idf

    def _tokenize(self, text: str) -> list[str]:
        """Tokenize text into terms."""
        import re

        # Convert to lowercase and extract alphanumeric tokens
        text = text.lower()
        tokens = re.findall(r"\b\w+\b", text)

        # Filter short tokens and stop words
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "from",
            "as",
            "is",
        }

        tokens = [t for t in tokens if len(t) > 2 and t not in stop_words]

        return tokens

    def get_stats(self) -> dict[str, Any]:
        """Get ranker statistics."""
        return {
            "num_docs": self.num_docs,
            "avg_doc_length": self.avg_doc_length,
            "num_unique_terms": len(self.doc_freqs),
            "k1": self.k1,
            "b": self.b,
        }
