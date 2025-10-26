"""Advanced indexing system for GitHound search engine.

This module provides incremental and inverted indexing capabilities
to significantly improve search performance.
"""

import hashlib
import json
import pickle
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from git import Repo


class InvertedIndex:
    """Inverted index for fast term-based search.

    The inverted index maps terms (words) to documents (commits/files) that contain them,
    enabling O(1) lookup instead of O(n) scanning.
    """

    def __init__(self) -> None:
        # Term -> {commit_hash: [locations]}
        self.index: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(
            lambda: defaultdict(list)
        )

        # Document frequency for each term (used in TF-IDF)
        self.doc_freq: dict[str, int] = defaultdict(int)

        # Total number of documents
        self.total_docs = 0

        # Metadata for each document
        self.doc_metadata: dict[str, dict[str, Any]] = {}

        # Index build timestamp
        self.build_time: datetime | None = None

        # Statistics
        self.stats = {
            "total_terms": 0,
            "total_postings": 0,
            "avg_postings_per_term": 0.0,
        }

    def add_document(
        self,
        doc_id: str,
        content: str,
        metadata: dict[str, Any] | None = None,
        field: str = "content",
    ) -> None:
        """Add a document to the index.

        Args:
            doc_id: Unique document identifier (e.g., commit hash)
            content: Text content to index
            metadata: Optional metadata about the document
            field: Field name (content, message, author, etc.)
        """
        # Tokenize content
        tokens = self._tokenize(content)

        # Track unique terms for this document
        doc_terms = set()

        # Add each token to the index
        for position, token in enumerate(tokens):
            self.index[token][doc_id].append(
                {
                    "position": position,
                    "field": field,
                }
            )
            doc_terms.add(token)

        # Update document frequency
        for term in doc_terms:
            self.doc_freq[term] += 1

        # Store metadata
        if metadata:
            self.doc_metadata[doc_id] = metadata

        self.total_docs += 1

    def search(self, query: str, limit: int = 100) -> list[tuple[str, float]]:
        """Search the index for documents matching the query.

        Returns:
            List of (doc_id, score) tuples sorted by relevance
        """
        query_tokens = self._tokenize(query)

        if not query_tokens:
            return []

        # Calculate TF-IDF scores for each document
        doc_scores: dict[str, float] = defaultdict(float)

        for token in query_tokens:
            if token not in self.index:
                continue

            # Calculate IDF (inverse document frequency)
            idf = self._calculate_idf(token)

            # Add TF-IDF score for each document containing this token
            for doc_id, locations in self.index[token].items():
                # TF (term frequency) is the number of times term appears
                tf = len(locations)

                # TF-IDF score
                doc_scores[doc_id] += tf * idf

        # Sort by score and return top results
        sorted_results = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)

        return sorted_results[:limit]

    def _tokenize(self, text: str) -> list[str]:
        """Tokenize text into searchable terms.

        Optimization: Simple but fast tokenization.
        For better results, could use nltk or spaCy.
        """
        # Convert to lowercase and split on non-alphanumeric
        import re

        text = text.lower()
        tokens = re.findall(r"\b\w+\b", text)

        # Filter out very short tokens and common stop words
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for"}
        tokens = [t for t in tokens if len(t) > 2 and t not in stop_words]

        return tokens

    def _calculate_idf(self, term: str) -> float:
        """Calculate IDF (inverse document frequency) for a term.

        IDF = log(total_docs / doc_freq)
        """
        import math

        if term not in self.doc_freq or self.total_docs == 0:
            return 0.0

        # Add 1 to avoid division by zero
        return math.log((self.total_docs + 1) / (self.doc_freq[term] + 1))

    def update_stats(self) -> None:
        """Update index statistics."""
        self.stats["total_terms"] = len(self.index)
        self.stats["total_postings"] = sum(len(postings) for postings in self.index.values())
        if self.stats["total_terms"] > 0:
            self.stats["avg_postings_per_term"] = (
                self.stats["total_postings"] / self.stats["total_terms"]
            )

    def save(self, path: Path) -> None:
        """Save index to disk."""
        path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "index": dict(self.index),
            "doc_freq": dict(self.doc_freq),
            "total_docs": self.total_docs,
            "doc_metadata": self.doc_metadata,
            "build_time": self.build_time.isoformat() if self.build_time else None,
            "stats": self.stats,
        }

        with open(path, "wb") as f:
            pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)

    def load(self, path: Path) -> bool:
        """Load index from disk.

        Returns:
            True if successful, False otherwise
        """
        if not path.exists():
            return False

        try:
            with open(path, "rb") as f:
                data = pickle.load(f)

            self.index = defaultdict(lambda: defaultdict(list), data["index"])
            self.doc_freq = defaultdict(int, data["doc_freq"])
            self.total_docs = data["total_docs"]
            self.doc_metadata = data["doc_metadata"]
            self.stats = data["stats"]

            if data["build_time"]:
                self.build_time = datetime.fromisoformat(data["build_time"])

            return True
        except Exception:
            return False


class IncrementalIndexer:
    """Incremental indexer that only indexes new commits.

    This dramatically improves performance by avoiding re-indexing
    of the entire repository on each search.
    """

    def __init__(self, repo_path: Path, cache_dir: Path | None = None) -> None:
        self.repo_path = repo_path
        self.cache_dir = cache_dir or (repo_path / ".githound" / "index")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Main inverted index
        self.content_index = InvertedIndex()
        self.message_index = InvertedIndex()
        self.author_index = InvertedIndex()

        # Track indexed commits
        self.indexed_commits: set[str] = set()

        # Track last index time
        self.last_index_time: datetime | None = None

    def get_index_path(self, index_type: str) -> Path:
        """Get the path for a specific index file."""
        repo_hash = hashlib.md5(str(self.repo_path).encode()).hexdigest()[:8]
        return self.cache_dir / f"{repo_hash}_{index_type}.idx"

    def load_indexes(self) -> bool:
        """Load existing indexes from disk.

        Returns:
            True if indexes were loaded successfully
        """
        success = True

        # Load content index
        if not self.content_index.load(self.get_index_path("content")):
            success = False

        # Load message index
        if not self.message_index.load(self.get_index_path("message")):
            success = False

        # Load author index
        if not self.author_index.load(self.get_index_path("author")):
            success = False

        # Load indexed commits list
        commits_path = self.get_index_path("commits")
        if commits_path.exists():
            try:
                with open(commits_path) as f:
                    data = json.load(f)
                    self.indexed_commits = set(data.get("commits", []))
                    if data.get("last_index_time"):
                        self.last_index_time = datetime.fromisoformat(data["last_index_time"])
            except Exception:
                success = False

        return success

    def save_indexes(self) -> None:
        """Save all indexes to disk."""
        # Save inverted indexes
        self.content_index.save(self.get_index_path("content"))
        self.message_index.save(self.get_index_path("message"))
        self.author_index.save(self.get_index_path("author"))

        # Save indexed commits list
        commits_path = self.get_index_path("commits")
        with open(commits_path, "w") as f:
            json.dump(
                {
                    "commits": list(self.indexed_commits),
                    "last_index_time": self.last_index_time.isoformat()
                    if self.last_index_time
                    else None,
                },
                f,
            )

    def build_incremental_index(
        self,
        repo: Repo,
        branch: str | None = None,
        progress_callback: Any | None = None,
        max_commits: int = 10000,
    ) -> dict[str, Any]:
        """Build or update indexes incrementally.

        Only indexes commits that haven't been indexed yet.

        Returns:
            Statistics about the indexing operation
        """
        start_time = time.time()

        # Try to load existing indexes
        self.load_indexes()

        branch = branch or repo.active_branch.name

        # Get all commits
        all_commits = list(repo.iter_commits(branch, max_count=max_commits))

        # Filter out already indexed commits
        new_commits = [c for c in all_commits if c.hexsha not in self.indexed_commits]

        if not new_commits:
            return {
                "indexed_commits": 0,
                "total_commits": len(all_commits),
                "time_seconds": time.time() - start_time,
                "status": "up_to_date",
            }

        # Index new commits
        indexed_count = 0
        for i, commit in enumerate(new_commits):
            # Index commit message
            self.message_index.add_document(
                doc_id=commit.hexsha,
                content=commit.message,
                metadata={
                    "author": commit.author.name,
                    "date": datetime.fromtimestamp(commit.committed_date).isoformat(),
                },
                field="message",
            )

            # Index author
            author_text = f"{commit.author.name} {commit.author.email}"
            self.author_index.add_document(
                doc_id=commit.hexsha,
                content=author_text,
                metadata={
                    "author": commit.author.name,
                    "email": commit.author.email,
                },
                field="author",
            )

            # Index file content (only for recent commits to avoid memory issues)
            if i < 1000:  # Only index content for most recent 1000 commits
                for parent in commit.parents:
                    try:
                        diffs = commit.diff(parent)
                        for diff in diffs:
                            if diff.b_blob is None or diff.b_path is None:
                                continue

                            # Skip large files
                            if diff.b_blob.size > 1024 * 1024:  # 1MB limit
                                continue

                            try:
                                content = diff.b_blob.data_stream.read().decode(
                                    "utf-8", errors="ignore"
                                )
                                self.content_index.add_document(
                                    doc_id=commit.hexsha,
                                    content=content,
                                    metadata={
                                        "file_path": diff.b_path,
                                        "commit": commit.hexsha,
                                    },
                                    field="content",
                                )
                            except Exception:
                                pass
                    except Exception:
                        pass

            # Mark as indexed
            self.indexed_commits.add(commit.hexsha)
            indexed_count += 1

            # Progress reporting
            if progress_callback and indexed_count % 100 == 0:
                progress = indexed_count / len(new_commits)
                progress_callback(f"Indexed {indexed_count}/{len(new_commits)} commits", progress)

        # Update statistics
        self.content_index.update_stats()
        self.message_index.update_stats()
        self.author_index.update_stats()

        # Update build time
        self.last_index_time = datetime.now()
        self.content_index.build_time = self.last_index_time
        self.message_index.build_time = self.last_index_time
        self.author_index.build_time = self.last_index_time

        # Save indexes
        self.save_indexes()

        return {
            "indexed_commits": indexed_count,
            "total_commits": len(all_commits),
            "time_seconds": time.time() - start_time,
            "status": "updated",
            "content_index_stats": self.content_index.stats,
            "message_index_stats": self.message_index.stats,
            "author_index_stats": self.author_index.stats,
        }

    def search_content(self, query: str, limit: int = 100) -> list[tuple[str, float]]:
        """Search content index."""
        return self.content_index.search(query, limit)

    def search_messages(self, query: str, limit: int = 100) -> list[tuple[str, float]]:
        """Search message index."""
        return self.message_index.search(query, limit)

    def search_authors(self, query: str, limit: int = 100) -> list[tuple[str, float]]:
        """Search author index."""
        return self.author_index.search(query, limit)

    def get_stats(self) -> dict[str, Any]:
        """Get comprehensive indexing statistics."""
        return {
            "total_indexed_commits": len(self.indexed_commits),
            "last_index_time": self.last_index_time.isoformat() if self.last_index_time else None,
            "content_index": self.content_index.stats,
            "message_index": self.message_index.stats,
            "author_index": self.author_index.stats,
        }
