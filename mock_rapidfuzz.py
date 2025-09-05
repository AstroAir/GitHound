"""Mock implementation of rapidfuzz for testing purposes."""

from typing import Any, Dict, List, Optional, Tuple, Union


class MockFuzz:
    """Mock implementation of rapidfuzz.fuzz module."""
    
    @staticmethod
    def ratio(s1: str, s2: str) -> float:
        """Mock ratio function that returns a simple similarity score."""
        if s1 == s2:
            return 100.0
        if not s1 or not s2:
            return 0.0
        # Simple mock implementation
        common_chars = set(s1.lower()) & set(s2.lower())
        return len(common_chars) / max(len(s1), len(s2)) * 100.0
    
    @staticmethod
    def partial_ratio(s1: str, s2: str) -> float:
        """Mock partial ratio function."""
        return MockFuzz.ratio(s1, s2)
    
    @staticmethod
    def token_sort_ratio(s1: str, s2: str) -> float:
        """Mock token sort ratio function."""
        return MockFuzz.ratio(s1, s2)
    
    @staticmethod
    def token_set_ratio(s1: str, s2: str) -> float:
        """Mock token set ratio function."""
        return MockFuzz.ratio(s1, s2)


class MockProcess:
    """Mock implementation of rapidfuzz.process module."""
    
    @staticmethod
    def extract(
        query: str, 
        choices: List[str], 
        limit: Optional[int] = None,
        score_cutoff: Optional[float] = None
    ) -> List[Tuple[str, float, int]]:
        """Mock extract function that returns simple matches."""
        results = []
        for i, choice in enumerate(choices):
            score = MockFuzz.ratio(query, choice)
            if score_cutoff is None or score >= score_cutoff:
                results.append((choice, score, i))
        
        # Sort by score descending
        results.sort(key=lambda x: x[1], reverse=True)
        
        if limit is not None:
            results = results[:limit]
        
        return results
    
    @staticmethod
    def extractOne(
        query: str, 
        choices: List[str], 
        score_cutoff: Optional[float] = None
    ) -> Optional[Tuple[str, float, int]]:
        """Mock extractOne function that returns the best match."""
        results = MockProcess.extract(query, choices, limit=1, score_cutoff=score_cutoff)
        return results[0] if results else None


# Create module-level instances
fuzz = MockFuzz()
process = MockProcess()
