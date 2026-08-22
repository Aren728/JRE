"""JRE-027 Birth Signature error taxonomy.

``BirthSignatureError`` is the base; request validation raises
subclasses with descriptive names.
"""


class BirthSignatureError(Exception):
    """Base class for all JRE-027 Birth Signature layer errors."""


class InvalidSignatureRequestError(BirthSignatureError):
    """Raised when a BirthSignature computation request is malformed:
    missing required fields, wrong types, or out-of-range values."""


class SignatureComputationError(BirthSignatureError):
    """Raised when an internal computation error occurs during
    BirthSignature derivation."""
