"""
Pipeline orchestrator: runs all enrichment stages in sequence.

Usage:
    from ingestion.pipeline.orchestrate import run_full_pipeline
    run_full_pipeline()
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def run_full_pipeline(
    skip_translate: bool = False,
    skip_llm: bool = False,
    limit: int = 500,
) -> dict:
    """
    Run all pipeline stages in order:
      1. Normalize raw → properties
      2. Translate (LLM)
      3. Deduplicate
      4. Hazard enrichment
      5. Lifestyle tagging
      6. Quality scoring
      7. What-to-Know generation

    Returns dict of counts per stage.
    """
    results = {}

    # Stage 1: Normalize
    logger.info("═══ Stage 1: Normalize ═══")
    from ingestion.pipeline.normalize import normalize_all
    results["normalized"] = normalize_all(limit=limit)

    # Stage 2: Translate
    if not skip_translate:
        logger.info("═══ Stage 2: Translate ═══")
        from ingestion.pipeline.translate import translate_all
        results["translated"] = translate_all(limit=limit)
    else:
        logger.info("═══ Stage 2: Translate (skipped) ═══")
        results["translated"] = 0

    # Stage 3: Deduplicate
    logger.info("═══ Stage 3: Deduplicate ═══")
    from ingestion.pipeline.dedupe import compute_fingerprints, find_duplicates
    results["fingerprinted"] = compute_fingerprints()
    dupes = find_duplicates()
    results["duplicate_clusters"] = len(dupes)

    # Stage 4: Hazard enrichment
    logger.info("═══ Stage 4: Hazard Enrichment ═══")
    from ingestion.pipeline.hazard import enrich_hazard_all
    results["hazard_enriched"] = enrich_hazard_all(limit=limit)

    # Stage 5: Lifestyle tagging
    logger.info("═══ Stage 5: Lifestyle Tagging ═══")
    from ingestion.pipeline.lifestyle import tag_lifestyle_all
    results["lifestyle_tagged"] = tag_lifestyle_all(limit=limit)

    # Stage 6: Quality scoring
    logger.info("═══ Stage 6: Quality Scoring ═══")
    from ingestion.pipeline.quality import score_quality_all
    results["quality_scored"] = score_quality_all(limit=limit)

    # Stage 7: What-to-Know
    if not skip_llm:
        logger.info("═══ Stage 7: What-to-Know ═══")
        from ingestion.pipeline.quality import generate_what_to_know_all
        results["what_to_know"] = generate_what_to_know_all(limit=min(limit, 50))
    else:
        logger.info("═══ Stage 7: What-to-Know (skipped) ═══")
        results["what_to_know"] = 0

    logger.info("═══ Pipeline complete ═══")
    return results
