"""
European adapter registry.
"""

from ingestion.adapters.europe.green_acres_fr import GreenAcresFrAdapter
from ingestion.adapters.europe.immobilier_notaires_fr import NotairesFrAdapter
from ingestion.adapters.europe.immobiliare_it import ImmobiliareItAdapter
from ingestion.adapters.europe.gate_away_com import GateAwayComAdapter
from ingestion.adapters.europe.italian_houses_for_sale import ItalianHousesForSaleAdapter
from ingestion.adapters.europe.one_euro_houses import OneEuroHousesAdapter
from ingestion.adapters.europe.idealista_pt import IdealistaPtAdapter
from ingestion.adapters.europe.imovirtual_com import ImovirtualComAdapter
from ingestion.adapters.europe.hemnet_se import HemnetSeAdapter
from ingestion.adapters.europe.blocket_se import BlocketSeAdapter

EUROPE_ADAPTER_MAP: dict[str, type] = {
    # France
    "green-acres-fr": GreenAcresFrAdapter,       # Easy — international portal
    "notaires-fr": NotairesFrAdapter,             # Medium — official notary DB
    # Italy
    "gate-away-it": GateAwayComAdapter,           # Easy — English portal for foreigners
    "italian-houses": ItalianHousesForSaleAdapter, # Easy — curated cheap houses
    "1euro-houses": OneEuroHousesAdapter,          # Easy — 1€ house program catalog
    "immobiliare-it": ImmobiliareItAdapter,       # Hard — Italy's #1 portal
    # Portugal
    "idealista-pt": IdealistaPtAdapter,            # Medium — HAS OFFICIAL API
    "imovirtual-pt": ImovirtualComAdapter,         # Medium — 2nd largest
    # Sweden
    "hemnet-se": HemnetSeAdapter,                  # Hard — 90% market share
    "blocket-se": BlocketSeAdapter,                # Medium — marketplace + unofficial API
}
