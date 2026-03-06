"""
Adapter registry. Import all adapters here and register them by slug.
"""

from ingestion.adapters.all_akiyas import AllAkiyasAdapter
from ingestion.adapters.cheap_houses_japan import CheapHousesJapanAdapter
from ingestion.adapters.old_houses_japan import OldHousesJapanAdapter

# ── Adapter registry: slug → adapter class ───────────────
# Add new adapters here as you build them.
ADAPTER_MAP: dict[str, type] = {
    "old-houses-japan": OldHousesJapanAdapter,
    "all-akiyas": AllAkiyasAdapter,
    "cheap-houses-japan": CheapHousesJapanAdapter,
}


def get_adapter(slug: str):
    """Get an adapter instance by source slug."""
    cls = ADAPTER_MAP.get(slug)
    if cls is None:
        raise ValueError(
            f"No adapter registered for source '{slug}'. "
            f"Available: {list(ADAPTER_MAP.keys())}"
        )
    return cls()
