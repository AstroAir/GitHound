"""Pandas compatibility layer for optional pandas dependency."""

from typing import Any, Dict, List, Union, Optional
from collections import Counter, defaultdict
from datetime import datetime


class MockSeries:
    """Mock pandas Series for basic functionality."""
    
    def __init__(self, data: List[Any], index: Optional[List[Any]] = None) -> None:
        self.data = data
        self.index = index or list(range(len(data)))
    
    def value_counts(self) -> Dict[Any, int]:
        """Return value counts as a dictionary."""
        return dict(Counter(self.data))
    
    def head(self, n: int = 5) -> 'MockSeries':
        """Return first n elements."""
        return MockSeries(self.data[:n], self.index[:n])
    
    def mean(self) -> float:
        """Calculate mean of numeric data."""
        numeric_data = [x for x in self.data if isinstance(x, (int, float))]
        return sum(numeric_data) / len(numeric_data) if numeric_data else 0.0
    
    def median(self) -> float:
        """Calculate median of numeric data."""
        numeric_data = sorted([x for x in self.data if isinstance(x, (int, float))])
        n = len(numeric_data)
        if n == 0:
            return 0.0
        if n % 2 == 0:
            return (numeric_data[n//2 - 1] + numeric_data[n//2]) / 2
        return numeric_data[n//2]
    
    def std(self) -> float:
        """Calculate standard deviation."""
        numeric_data = [x for x in self.data if isinstance(x, (int, float))]
        if len(numeric_data) < 2:
            return 0.0
        mean_val = sum(numeric_data) / len(numeric_data)
        variance = sum((x - mean_val) ** 2 for x in numeric_data) / (len(numeric_data) - 1)
        return float(variance ** 0.5)
    
    def min(self) -> Any:
        """Return minimum value."""
        numeric_data = [x for x in self.data if isinstance(x, (int, float))]
        return min(numeric_data) if numeric_data else None
    
    def max(self) -> Any:
        """Return maximum value."""
        numeric_data = [x for x in self.data if isinstance(x, (int, float))]
        return max(numeric_data) if numeric_data else None
    
    def nunique(self) -> int:
        """Return number of unique values."""
        return len(set(self.data))
    
    def notna(self) -> 'MockSeries':
        """Return boolean series indicating non-null values."""
        return MockSeries([x is not None for x in self.data])
    
    def sum(self) -> Union[int, float]:
        """Sum of values."""
        return sum(1 for x in self.data if x)
    
    def dropna(self) -> 'MockSeries':
        """Drop null values."""
        filtered_data = [x for x in self.data if x is not None]
        return MockSeries(filtered_data)
    
    def any(self) -> bool:
        """Return True if any value is True."""
        return any(self.data)
    
    def to_dict(self) -> Dict[Any, Any]:
        """Convert to dictionary."""
        return dict(zip(self.index, self.data))


class MockDataFrame:
    """Mock pandas DataFrame for basic functionality."""
    
    def __init__(self, data: Optional[List[Dict[str, Any]]] = None) -> None:
        self.data = data or []
        self._columns = list(self.data[0].keys()) if self.data else []
    
    def __getitem__(self, key: str) -> MockSeries:
        """Get column as MockSeries."""
        column_data = [row.get(key) for row in self.data]
        return MockSeries(column_data)
    
    def __len__(self) -> int:
        """Return number of rows."""
        return len(self.data)
    
    def empty(self) -> bool:
        """Check if DataFrame is empty."""
        return len(self.data) == 0
    
    def groupby(self, by: Union[str, List[str]]) -> 'MockGroupBy':
        """Group by column(s)."""
        return MockGroupBy(self, by)


class MockGroupBy:
    """Mock pandas GroupBy for basic functionality."""
    
    def __init__(self, df: MockDataFrame, by: Union[str, List[str]]) -> None:
        self.df = df
        self.by = by if isinstance(by, list) else [by]
    
    def size(self) -> MockSeries:
        """Return size of each group."""
        groups: defaultdict[tuple, int] = defaultdict(int)
        for row in self.df.data:
            key = tuple(row.get(col) for col in self.by)
            groups[key] += 1
        return MockSeries(list(groups.values()), list(groups.keys()))
    
    def agg(self, agg_dict: Dict[str, str]) -> MockDataFrame:
        """Aggregate using dictionary."""
        # Simplified aggregation - just return the original data
        return self.df


def to_datetime(data: List[Any]) -> MockSeries:
    """Mock pandas to_datetime function."""
    converted: List[Optional[datetime]] = []
    for item in data:
        if isinstance(item, datetime):
            converted.append(item)
        elif item is None:
            converted.append(None)
        else:
            # Try to convert string to datetime
            try:
                converted.append(datetime.fromisoformat(str(item)))
            except:
                converted.append(None)
    return MockSeries(converted)


class MockPandas:
    """Mock pandas module."""
    
    DataFrame = MockDataFrame
    Series = MockSeries
    to_datetime = staticmethod(to_datetime)


# Create the mock pandas instance
mock_pd = MockPandas()
