"""Prediction Engine — Deep predictive modules for JRE."""

try:
    from jrs.prediction_engine.aspects import AspectMatrixEngine
    from jrs.prediction_engine.deep_dasha import DeepVimshottariEngine
    from jrs.prediction_engine.parivartana import ParivartanaEngine
except ImportError:
    from .aspects import AspectMatrixEngine
    from .deep_dasha import DeepVimshottariEngine
    from .parivartana import ParivartanaEngine

__all__ = [
    "ParivartanaEngine",
    "AspectMatrixEngine",
    "DeepVimshottariEngine",
]
