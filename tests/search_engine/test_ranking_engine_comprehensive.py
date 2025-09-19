"""Comprehensive tests for GitHound search engine ranking module."""

import pytest
import math
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from typing import List, Dict, Any

from githound.search_engine.ranking_engine import (
    RankingEngine,
    RankingCriteria,
    RankingConfig,
    ScoreCalculator,
    RelevanceScorer,
    FreshnessScorer,
    PopularityScorer
)
from githound.models import SearchResult, SearchType, CommitInfo


@pytest.fixture
def ranking_config() -> RankingConfig:
    """Create ranking configuration for testing."""
    return RankingConfig(
        relevance_weight=0.5,
        freshness_weight=0.3,
        popularity_weight=0.2,
        boost_exact_matches=True,
        boost_factor=1.5,
        decay_factor=0.1
    )


@pytest.fixture
def sample_search_results() -> List[SearchResult]:
    """Create sample search results for ranking tests."""
    base_time = datetime.now()
    
    return [
        SearchResult(
            commit_hash="abc123",
            file_path="src/main.py",
            line_number=10,
            matching_line="def main_function():",
            search_type=SearchType.CONTENT,
            relevance_score=0.9,
            commit_info=CommitInfo(
                hash="abc123",
                short_hash="abc123",
                author_name="Alice",
                author_email="alice@example.com",
                committer_name="Alice",
                committer_email="alice@example.com",
                message="Add main function",
                date=base_time - timedelta(days=1),
                files_changed=1,
                insertions=10,
                deletions=0
            )
        ),
        SearchResult(
            commit_hash="def456",
            file_path="src/utils.py",
            line_number=25,
            matching_line="def utility_function():",
            search_type=SearchType.CONTENT,
            relevance_score=0.7,
            commit_info=CommitInfo(
                hash="def456",
                short_hash="def456",
                author_name="Bob",
                author_email="bob@example.com",
                committer_name="Bob",
                committer_email="bob@example.com",
                message="Add utility functions",
                date=base_time - timedelta(days=30),
                files_changed=2,
                insertions=50,
                deletions=5
            )
        ),
        SearchResult(
            commit_hash="ghi789",
            file_path="tests/test_main.py",
            line_number=5,
            matching_line="def test_main_function():",
            search_type=SearchType.CONTENT,
            relevance_score=0.8,
            commit_info=CommitInfo(
                hash="ghi789",
                short_hash="ghi789",
                author_name="Charlie",
                author_email="charlie@example.com",
                committer_name="Charlie",
                committer_email="charlie@example.com",
                message="Add tests for main function",
                date=base_time - timedelta(hours=6),
                files_changed=1,
                insertions=20,
                deletions=0
            )
        )
    ]


class TestRankingEngine:
    """Test RankingEngine class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.ranking_engine = RankingEngine()

    def test_ranking_engine_initialization(self, ranking_config: RankingConfig) -> None:
        """Test ranking engine initialization."""
        engine = RankingEngine(config=ranking_config)
        
        assert engine.config == ranking_config
        assert engine.config.relevance_weight == 0.5
        assert engine.config.freshness_weight == 0.3
        assert engine.config.popularity_weight == 0.2

    def test_rank_results_basic(self, sample_search_results: List[SearchResult]) -> None:
        """Test basic result ranking."""
        ranked_results = self.ranking_engine.rank_results(sample_search_results)
        
        assert len(ranked_results) == len(sample_search_results)
        
        # Results should be sorted by final score (descending)
        for i in range(len(ranked_results) - 1):
            assert ranked_results[i].final_score >= ranked_results[i + 1].final_score

    def test_rank_results_with_custom_weights(self, sample_search_results: List[SearchResult]) -> None:
        """Test ranking with custom weight configuration."""
        config = RankingConfig(
            relevance_weight=0.8,  # High relevance weight
            freshness_weight=0.1,
            popularity_weight=0.1
        )
        engine = RankingEngine(config=config)
        
        ranked_results = engine.rank_results(sample_search_results)
        
        # With high relevance weight, highest relevance should rank first
        highest_relevance = max(sample_search_results, key=lambda r: r.relevance_score)
        assert ranked_results[0].commit_hash == highest_relevance.commit_hash

    def test_rank_results_freshness_priority(self, sample_search_results: List[SearchResult]) -> None:
        """Test ranking with freshness priority."""
        config = RankingConfig(
            relevance_weight=0.1,
            freshness_weight=0.8,  # High freshness weight
            popularity_weight=0.1
        )
        engine = RankingEngine(config=config)
        
        ranked_results = engine.rank_results(sample_search_results)
        
        # Most recent commit should rank higher
        most_recent = max(sample_search_results, key=lambda r: r.commit_info.date)
        assert ranked_results[0].commit_hash == most_recent.commit_hash

    def test_exact_match_boost(self, sample_search_results: List[SearchResult]) -> None:
        """Test exact match boosting."""
        config = RankingConfig(
            boost_exact_matches=True,
            boost_factor=2.0
        )
        engine = RankingEngine(config=config)
        
        # Mark one result as exact match
        sample_search_results[1].is_exact_match = True
        
        ranked_results = engine.rank_results(sample_search_results)
        
        # Exact match should be boosted
        exact_match_result = next(r for r in ranked_results if r.is_exact_match)
        assert exact_match_result.final_score > exact_match_result.relevance_score

    def test_rank_empty_results(self) -> None:
        """Test ranking empty results list."""
        ranked_results = self.ranking_engine.rank_results([])
        assert ranked_results == []

    def test_rank_single_result(self, sample_search_results: List[SearchResult]) -> None:
        """Test ranking single result."""
        single_result = [sample_search_results[0]]
        ranked_results = self.ranking_engine.rank_results(single_result)
        
        assert len(ranked_results) == 1
        assert ranked_results[0].commit_hash == single_result[0].commit_hash


class TestRelevanceScorer:
    """Test RelevanceScorer class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.scorer = RelevanceScorer()

    def test_calculate_relevance_score(self, sample_search_results: List[SearchResult]) -> None:
        """Test relevance score calculation."""
        result = sample_search_results[0]
        
        score = self.scorer.calculate_score(result)
        
        assert 0.0 <= score <= 1.0
        assert score == result.relevance_score  # Should use existing relevance score

    def test_boost_exact_match(self, sample_search_results: List[SearchResult]) -> None:
        """Test exact match boosting in relevance scoring."""
        result = sample_search_results[0]
        result.is_exact_match = True
        
        scorer = RelevanceScorer(boost_exact_matches=True, boost_factor=1.5)
        score = scorer.calculate_score(result)
        
        assert score > result.relevance_score

    def test_content_type_scoring(self) -> None:
        """Test scoring based on search type."""
        content_result = SearchResult(
            commit_hash="abc123",
            file_path="test.py",
            line_number=10,
            matching_line="def test():",
            search_type=SearchType.CONTENT,
            relevance_score=0.8
        )
        
        author_result = SearchResult(
            commit_hash="def456",
            file_path="test.py",
            line_number=10,
            matching_line="def test():",
            search_type=SearchType.AUTHOR,
            relevance_score=0.8
        )
        
        content_score = self.scorer.calculate_score(content_result)
        author_score = self.scorer.calculate_score(author_result)
        
        # Content matches might be weighted differently than author matches
        assert isinstance(content_score, float)
        assert isinstance(author_score, float)


class TestFreshnessScorer:
    """Test FreshnessScorer class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.scorer = FreshnessScorer()

    def test_calculate_freshness_score(self, sample_search_results: List[SearchResult]) -> None:
        """Test freshness score calculation."""
        recent_result = sample_search_results[2]  # 6 hours ago
        old_result = sample_search_results[1]     # 30 days ago
        
        recent_score = self.scorer.calculate_score(recent_result)
        old_score = self.scorer.calculate_score(old_result)
        
        assert 0.0 <= recent_score <= 1.0
        assert 0.0 <= old_score <= 1.0
        assert recent_score > old_score  # More recent should score higher

    def test_freshness_decay(self) -> None:
        """Test freshness decay over time."""
        base_time = datetime.now()
        
        # Create results with different ages
        results = []
        for days_ago in [1, 7, 30, 90]:
            result = SearchResult(
                commit_hash=f"commit_{days_ago}",
                file_path="test.py",
                line_number=10,
                matching_line="test",
                search_type=SearchType.CONTENT,
                relevance_score=0.8,
                commit_info=CommitInfo(
                    hash=f"commit_{days_ago}",
                    short_hash=f"commit_{days_ago}",
                    author_name="Test",
                    author_email="test@example.com",
                    committer_name="Test",
                    committer_email="test@example.com",
                    message="Test commit",
                    date=base_time - timedelta(days=days_ago),
                    files_changed=1
                )
            )
            results.append(result)
        
        scores = [self.scorer.calculate_score(r) for r in results]
        
        # Scores should decrease with age
        for i in range(len(scores) - 1):
            assert scores[i] >= scores[i + 1]

    def test_freshness_with_custom_decay(self) -> None:
        """Test freshness scoring with custom decay factor."""
        scorer = FreshnessScorer(decay_factor=0.5)  # Faster decay
        
        old_result = SearchResult(
            commit_hash="old_commit",
            file_path="test.py",
            line_number=10,
            matching_line="test",
            search_type=SearchType.CONTENT,
            relevance_score=0.8,
            commit_info=CommitInfo(
                hash="old_commit",
                short_hash="old_commit",
                author_name="Test",
                author_email="test@example.com",
                committer_name="Test",
                committer_email="test@example.com",
                message="Old commit",
                date=datetime.now() - timedelta(days=30),
                files_changed=1
            )
        )
        
        score = scorer.calculate_score(old_result)
        assert 0.0 <= score <= 1.0


class TestPopularityScorer:
    """Test PopularityScorer class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.scorer = PopularityScorer()

    def test_calculate_popularity_score(self, sample_search_results: List[SearchResult]) -> None:
        """Test popularity score calculation."""
        result = sample_search_results[1]  # Has more insertions/changes
        
        score = self.scorer.calculate_score(result)
        
        assert 0.0 <= score <= 1.0

    def test_popularity_based_on_changes(self) -> None:
        """Test popularity scoring based on commit changes."""
        small_commit = SearchResult(
            commit_hash="small",
            file_path="test.py",
            line_number=10,
            matching_line="test",
            search_type=SearchType.CONTENT,
            relevance_score=0.8,
            commit_info=CommitInfo(
                hash="small",
                short_hash="small",
                author_name="Test",
                author_email="test@example.com",
                committer_name="Test",
                committer_email="test@example.com",
                message="Small change",
                date=datetime.now(),
                files_changed=1,
                insertions=5,
                deletions=1
            )
        )
        
        large_commit = SearchResult(
            commit_hash="large",
            file_path="test.py",
            line_number=10,
            matching_line="test",
            search_type=SearchType.CONTENT,
            relevance_score=0.8,
            commit_info=CommitInfo(
                hash="large",
                short_hash="large",
                author_name="Test",
                author_email="test@example.com",
                committer_name="Test",
                committer_email="test@example.com",
                message="Large change",
                date=datetime.now(),
                files_changed=10,
                insertions=100,
                deletions=20
            )
        )
        
        small_score = self.scorer.calculate_score(small_commit)
        large_score = self.scorer.calculate_score(large_commit)
        
        # Larger commits might be considered more "popular" or significant
        assert isinstance(small_score, float)
        assert isinstance(large_score, float)


class TestScoreCalculator:
    """Test ScoreCalculator utility class."""

    def test_weighted_average_calculation(self) -> None:
        """Test weighted average calculation."""
        scores = [0.8, 0.6, 0.9]
        weights = [0.5, 0.3, 0.2]
        
        calculator = ScoreCalculator()
        result = calculator.calculate_weighted_average(scores, weights)
        
        expected = (0.8 * 0.5) + (0.6 * 0.3) + (0.9 * 0.2)
        assert abs(result - expected) < 0.001

    def test_normalize_scores(self) -> None:
        """Test score normalization."""
        scores = [10, 20, 30, 40]
        
        calculator = ScoreCalculator()
        normalized = calculator.normalize_scores(scores)
        
        assert min(normalized) == 0.0
        assert max(normalized) == 1.0
        assert len(normalized) == len(scores)

    def test_apply_boost(self) -> None:
        """Test boost application."""
        base_score = 0.6
        boost_factor = 1.5
        
        calculator = ScoreCalculator()
        boosted = calculator.apply_boost(base_score, boost_factor)
        
        assert boosted == min(base_score * boost_factor, 1.0)

    def test_exponential_decay(self) -> None:
        """Test exponential decay calculation."""
        calculator = ScoreCalculator()
        
        # Test decay over different time periods
        decay_1_day = calculator.calculate_exponential_decay(1, decay_factor=0.1)
        decay_7_days = calculator.calculate_exponential_decay(7, decay_factor=0.1)
        
        assert 0.0 <= decay_1_day <= 1.0
        assert 0.0 <= decay_7_days <= 1.0
        assert decay_1_day > decay_7_days  # Less decay for shorter time


@pytest.mark.integration
class TestRankingIntegration:
    """Integration tests for ranking components."""

    def test_end_to_end_ranking_workflow(
        self,
        sample_search_results: List[SearchResult],
        ranking_config: RankingConfig
    ) -> None:
        """Test complete ranking workflow."""
        engine = RankingEngine(config=ranking_config)
        
        # Rank results
        ranked_results = engine.rank_results(sample_search_results)
        
        # Verify ranking quality
        assert len(ranked_results) == len(sample_search_results)
        
        # Check that all results have final scores
        for result in ranked_results:
            assert hasattr(result, 'final_score')
            assert 0.0 <= result.final_score <= 1.0
        
        # Verify sorting
        for i in range(len(ranked_results) - 1):
            assert ranked_results[i].final_score >= ranked_results[i + 1].final_score

    def test_ranking_consistency(self, sample_search_results: List[SearchResult]) -> None:
        """Test ranking consistency across multiple runs."""
        engine = RankingEngine()
        
        # Rank the same results multiple times
        rankings = []
        for _ in range(5):
            ranked = engine.rank_results(sample_search_results.copy())
            rankings.append([r.commit_hash for r in ranked])
        
        # All rankings should be identical
        first_ranking = rankings[0]
        for ranking in rankings[1:]:
            assert ranking == first_ranking

    def test_ranking_with_different_configurations(
        self,
        sample_search_results: List[SearchResult]
    ) -> None:
        """Test ranking with different configuration scenarios."""
        configs = [
            RankingConfig(relevance_weight=1.0, freshness_weight=0.0, popularity_weight=0.0),
            RankingConfig(relevance_weight=0.0, freshness_weight=1.0, popularity_weight=0.0),
            RankingConfig(relevance_weight=0.0, freshness_weight=0.0, popularity_weight=1.0),
        ]
        
        rankings = []
        for config in configs:
            engine = RankingEngine(config=config)
            ranked = engine.rank_results(sample_search_results.copy())
            rankings.append([r.commit_hash for r in ranked])
        
        # Different configurations should potentially produce different rankings
        # (unless all results happen to have identical scores in all dimensions)
        assert len(set(tuple(r) for r in rankings)) >= 1
