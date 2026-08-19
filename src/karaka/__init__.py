"""JRE-014 Karaka (Significator) Engine — deterministic significator mapping.

JRE-014 assigns and ranks Naisargika (Natural), Sthira (Permanent),
Chara (Temporary), and Vishesha (Special) significators for classical
life categories.  It performs NO predictive interpretation.

Strict Boundaries:
- IN SCOPE: src/karaka/, config/karaka.toml
- OUT OF SCOPE: No predictive interpretation, no modification of
  JRE-002 through JRE-013.

Core Models:
- ``KarakaCategory``: ATMA, MANAS, PUTRA, DHANA, DARA, etc.
- ``KarakaType``: NAISARGIKA, STHIRA, CHARA, VISHESHA
- ``KarakaAssignment``: category + planet + type + rank + strength
- ``KarakaReport``: complete significator report

Service Interface:
- ``KarakaService(config: KarakaConfig)``
- ``calculate_karakas(planet_states, bala_report) -> KarakaReport``
"""

from .config import load_config
from .errors import (
    InvalidKarakaConfigError,
    InvalidKarakaRequestError,
    KarakaComputationError,
    KarakaError,
)
from .models import (
    CHARA_KARAKA_RANKS,
    KARAKA_VERSION,
    KarakaAssignment,
    KarakaCategory,
    KarakaConfig,
    KarakaReport,
    KarakaType,
    compute_chara_karakas,
    validate,
)
from .serialize import (
    karaka_config_from_dict,
    result_to_dict,
    result_to_json,
)
from .service import KarakaService

__version__ = KARAKA_VERSION

__all__ = [
    # service
    "KarakaService",
    # config
    "load_config",
    "validate",
    "KarakaConfig",
    # models
    "KarakaCategory",
    "KarakaType",
    "KarakaAssignment",
    "KarakaReport",
    "CHARA_KARAKA_RANKS",
    # constants
    "KARAKA_VERSION",
    # derivation helpers
    "compute_chara_karakas",
    # errors
    "KarakaError",
    "InvalidKarakaConfigError",
    "InvalidKarakaRequestError",
    "KarakaComputationError",
    # serialization
    "result_to_json",
    "result_to_dict",
    "karaka_config_from_dict",
]
