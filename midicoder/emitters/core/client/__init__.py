"""Core Client Emitter Package (P2-002-D).

Package này chứa frontend client emitters cho API communication:
- Angular: HttpClient services với Pagination, Filtering, Caching, Error handling
- React: RTK Query hooks với tương tự features

Exports:
    Angular: AngularClientEmitter
    React: ReactClientEmitter
"""

from midicoder.emitters.core.client.angular import AngularClientEmitter
from midicoder.emitters.core.client.react import ReactClientEmitter

__all__ = [
    "AngularClientEmitter",
    "ReactClientEmitter",
]
