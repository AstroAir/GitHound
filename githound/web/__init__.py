"""Web interface package for GitHound."""

from .api import app
from .models import SearchRequest, SearchResponse

__all__ = ["app", "SearchRequest", "SearchResponse"]
