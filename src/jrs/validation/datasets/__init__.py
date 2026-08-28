"""JRS-089: Historical Reference Dataset Package.

Provides the initial 12-chart reference cohort with verified AA-rated
birth data sourced from Astro-Databank (astro.com) and independently
verifiable ground-truth historical events.

Usage::

    from jrs.validation.datasets import REFERENCE_COHORT_12, DatasetLoader

    loader = DatasetLoader()
    cohort = loader.get_reference_cohort()
    loader.export_cohort_to_json(Path("cohort.json"))
"""

from .loader import DatasetLoader
from .reference_cohort import REFERENCE_COHORT_12

__all__ = ["DatasetLoader", "REFERENCE_COHORT_12"]
