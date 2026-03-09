"""
New Zealand adapter registry.
"""

from ingestion.adapters.nz.trademe_nz import TradeMeNZAdapter
from ingestion.adapters.nz.realestate_co_nz import RealEstateCoNZAdapter
from ingestion.adapters.nz.homes_co_nz import HomesCoNZAdapter
from ingestion.adapters.nz.one_roof_nz import OneRoofNZAdapter
from ingestion.adapters.nz.harcourts_nz import HarcourtsNZAdapter

NZ_ADAPTER_MAP: dict[str, type] = {
    "trademe-nz": TradeMeNZAdapter,              # Easy — HAS OFFICIAL API
    "realestate-co-nz": RealEstateCoNZAdapter,    # Medium — #2 portal
    "homes-co-nz": HomesCoNZAdapter,              # Medium — valuations
    "oneroof-nz": OneRoofNZAdapter,               # Medium — NZ Herald
    "harcourts-nz": HarcourtsNZAdapter,           # Easy — major agency
}
