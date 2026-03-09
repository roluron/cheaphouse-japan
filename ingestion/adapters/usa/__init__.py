"""
USA adapter registry.
"""

from ingestion.adapters.usa.cheap_old_houses import CheapOldHousesAdapter
from ingestion.adapters.usa.redfin_us import RedfinUSAdapter
from ingestion.adapters.usa.realtor_com import RealtorComAdapter
from ingestion.adapters.usa.landwatch_us import LandWatchUSAdapter
from ingestion.adapters.usa.auction_com import AuctionComAdapter

USA_ADAPTER_MAP: dict[str, type] = {
    "cheap-old-houses-us": CheapOldHousesAdapter,  # Easy — curated, perfect fit
    "redfin-us": RedfinUSAdapter,                    # Easy — CSV download!
    "realtor-com": RealtorComAdapter,                # Medium — JSON in script tags
    "landwatch-us": LandWatchUSAdapter,              # Medium — rural specialist
    "auction-com": AuctionComAdapter,                # Medium — foreclosures
}
