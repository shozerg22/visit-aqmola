import os
try:
    from prometheus_client import Counter
except ImportError:
    Counter = None

ENABLED = os.getenv("METRICS_ENABLED", "1") == "1" and Counter is not None

if ENABLED:
    ADMIN_ACTIONS_TOTAL = Counter("admin_actions_total", "Admin/moderator protected actions performed")
else:
    ADMIN_ACTIONS_TOTAL = None
