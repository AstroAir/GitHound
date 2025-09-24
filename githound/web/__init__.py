"""Web interface package for GitHound."""

from .main import app
from .models.api_models import SearchRequest, SearchResponse

__all__ = ["app", "SearchRequest", "SearchResponse"]
