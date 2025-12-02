import os
try:
    from prometheus_client import Counter
except ImportError:
    Counter = None

ENABLED = os.getenv("METRICS_ENABLED", "1") == "1" and Counter is not None

if ENABLED:
    RAG_SEARCH_TOTAL = Counter("rag_search_total", "Total RAG search requests")
    RAG_FALLBACK_TOTAL = Counter("rag_fallback_total", "RAG searches served via fallback mode")
    ADMIN_ACTIONS_TOTAL = Counter("admin_actions_total", "Admin/moderator protected actions performed")
else:
    RAG_SEARCH_TOTAL = None
    RAG_FALLBACK_TOTAL = None
    ADMIN_ACTIONS_TOTAL = None
