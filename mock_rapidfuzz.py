"""
Mock rapidfuzz module for testing when rapidfuzz is not available.
This provides basic functionality to allow tests to run.
"""

class MockFuzz:
    """Mock fuzz module."""
    
    @staticmethod
    def ratio(s1: str, s2: str) -> float:
        """Mock ratio function - simple string comparison."""
        if s1 == s2:
            return 100.0
        elif s1.lower() == s2.lower():
            return 90.0
        elif s1 in s2 or s2 in s1:
            return 70.0
        else:
            return 0.0
    
    @staticmethod
    def partial_ratio(s1: str, s2: str) -> float:
        """Mock partial_ratio function."""
        if s1 in s2 or s2 in s1:
            return 80.0
        elif s1.lower() in s2.lower() or s2.lower() in s1.lower():
            return 60.0
        else:
            return 0.0

class MockProcess:
    """Mock process module."""
    
    @staticmethod
    def extract(query: str, choices: list, scorer=None, score_cutoff: float = 0, limit: int = None):
        """Mock extract function - returns simple matches."""
        results = []
        for choice in choices:
            if scorer:
                score = scorer(query, choice)
            else:
                score = MockFuzz.ratio(query, choice)
            
            if score >= score_cutoff:
                results.append((choice, score, len(results)))
        
        # Sort by score descending
        results.sort(key=lambda x: x[1], reverse=True)
        
        # Apply limit if specified
        if limit is not None:
            results = results[:limit]
        
        return results

# Create mock modules
fuzz = MockFuzz()
process = MockProcess()
