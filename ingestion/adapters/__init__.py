"""
Adapter registry. Import all adapters here and register them by slug.
"""

from ingestion.adapters.homes_co_jp import HomesCoJpAdapter
from ingestion.adapters.athome_co_jp import AthomeCoJpAdapter
from ingestion.adapters.realestate_co_jp import RealEstateCoJpAdapter
from ingestion.adapters.suumo_jp import SuumoJpAdapter
from ingestion.adapters.eikohome_co_jp import EikohHomeAdapter
from ingestion.adapters.akiya_mart import AkiyaMartAdapter
from ingestion.adapters.koryoya import KoryoyaAdapter
from ingestion.adapters.heritage_homes import HeritageHomesAdapter
from ingestion.adapters.bukkenfan_jp import BukkenfanAdapter
from ingestion.adapters.all_akiyas import AllAkiyasAdapter

# ── USA adapters ─────────────────────────────────────────
from ingestion.adapters.usa import USA_ADAPTER_MAP

# ── New Zealand adapters ─────────────────────────────────
from ingestion.adapters.nz import NZ_ADAPTER_MAP

# ── Adapter registry: slug → adapter class ───────────────
# Priority order: curated sources first, then major portals, then aggregators.
ADAPTER_MAP: dict[str, type] = {
    # Curated / character properties
    "koryoya": KoryoyaAdapter,                  # Pre-1950 traditional kominka
    "heritage-homes": HeritageHomesAdapter,      # Kyoto machiya & kominka specialist
    "bukkenfan": BukkenfanAdapter,               # Design-conscious curated properties
    "eikohome": EikohHomeAdapter,                # Nara specialist, rural houses
    # Major Japanese portals
    "homes-co-jp": HomesCoJpAdapter,             # LIFULL HOME'S — nationwide
    "athome-co-jp": AthomeCoJpAdapter,           # at home — good rural coverage
    "suumo-jp": SuumoJpAdapter,                  # Suumo — largest portal (cautious)
    "realestate-co-jp": RealEstateCoJpAdapter,   # English portal
    # Aggregators
    "akiya-mart": AkiyaMartAdapter,              # English aggregator (680K listings, source URLs)
    "all-akiyas": AllAkiyasAdapter,              # AllAkiyas — fallback
}

# Merge USA adapters
ADAPTER_MAP.update(USA_ADAPTER_MAP)

# Import European adapters
from ingestion.adapters.europe import EUROPE_ADAPTER_MAP

# Merge into main registry
ADAPTER_MAP.update(EUROPE_ADAPTER_MAP)

# Merge NZ adapters
ADAPTER_MAP.update(NZ_ADAPTER_MAP)


def get_adapter(slug: str):
    """Get an adapter instance by source slug."""
    cls = ADAPTER_MAP.get(slug)
    if cls is None:
        raise ValueError(
            f"No adapter registered for source '{slug}'. "
            f"Available: {list(ADAPTER_MAP.keys())}"
        )
    return cls()
