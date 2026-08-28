"""JRS-088: Cryptographic Persistence Driver for Blind Validation.

Provides `PredictionPacketStore` for persisting FrozenPredictionPacket
objects with SHA-256 integrity verification. Any modification to a stored
packet is detected on load and raises CryptographicTamperError.

Source: JRS-088 Blind Historical Validation Runner Engine.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .models import (
    BirthProvenance,
    ChartSubject,
    CryptographicTamperError,
    DomainType,
    FrozenPredictionPacket,
    RoddenRating,
)


def _canonicalize_floats(obj: Any) -> Any:
    """Recursively canonicalize floats to 6-decimal string representations.

    This prevents floating-point serialization discrepancies from causing
    false SHA-256 hash mismatches across Python versions or platforms.
    """
    if isinstance(obj, float):
        # Round to 6 decimal places for canonical form
        return round(obj, 6)
    if isinstance(obj, dict):
        return {k: _canonicalize_floats(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_canonicalize_floats(v) for v in obj]
    return obj


def _compute_packet_hash(packet: FrozenPredictionPacket) -> str:
    """Compute SHA-256 hash of a FrozenPredictionPacket.

    Uses canonical JSON serialization with sorted keys and no whitespace
    to ensure deterministic hashing.
    """
    payload = packet.to_dict()
    payload = _canonicalize_floats(payload)
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _packet_to_storage_dict(packet: FrozenPredictionPacket) -> dict[str, Any]:
    """Serialize a packet for disk storage (includes hash)."""
    d = packet.to_dict()
    d = _canonicalize_floats(d)
    d["payload_hash"] = packet.payload_hash
    return d


def _storage_dict_to_packet(d: dict[str, Any]) -> FrozenPredictionPacket:
    """Reconstruct a FrozenPredictionPacket from a storage dict."""
    subject_dict = d["subject"]
    provenance_dict = subject_dict.get("provenance", {})

    provenance = BirthProvenance(
        source=provenance_dict.get("source", "unknown"),
        rodden_rating=RoddenRating(provenance_dict.get("rodden_rating", "C")),
        birth_time_confidence_minutes=provenance_dict.get(
            "birth_time_confidence_minutes", 0,
        ),
    )

    subject = ChartSubject(
        chart_id=subject_dict["chart_id"],
        latitude=float(subject_dict["latitude"]),
        longitude=float(subject_dict["longitude"]),
        birth_timestamp=subject_dict["birth_timestamp"],
        timezone=subject_dict.get("timezone", "Asia/Kolkata"),
        provenance=provenance,
    )

    return FrozenPredictionPacket(
        subject=subject,
        target_timestamp=d["target_timestamp"],
        formation_strength=float(d.get("formation_strength", 0.0)),
        structural_relationship_score=float(d.get("structural_relationship_score", 0.0)),
        modification_impact=float(d.get("modification_impact", 0.0)),
        varga_confirmation_score=float(d.get("varga_confirmation_score", 0.0)),
        dasha_transit_activation=float(d.get("dasha_transit_activation", 0.0)),
        predicted_strength=float(d.get("predicted_strength", 0.0)),
        payload_hash=d.get("payload_hash", ""),
    )


class PredictionPacketStore:
    """Cryptographic persistence driver for FrozenPredictionPacket objects.

    Handles saving, loading, and verifying prediction packets with SHA-256
    integrity checks. Any tampering with the persisted packet is detected
    on load and raises CryptographicTamperError.

    Usage::

        store = PredictionPacketStore()
        path = store.save_packet(packet)
        verified = store.load_and_verify(path)
    """

    def save_packet(
        self,
        packet: FrozenPredictionPacket,
        destination_path: Path | None = None,
    ) -> Path:
        """Serialize and persist a prediction packet with its integrity hash.

        The packet is written as canonical JSON with the payload_hash included.

        Args:
            packet: The sealed FrozenPredictionPacket to persist.
            destination_path: Optional explicit path. If None, a path is
                generated from the packet's chart_id and target_timestamp.

        Returns:
            The Path where the packet was written.
        """
        if destination_path is None:
            safe_ts = packet.target_timestamp.replace(":", "-").replace("T", "_")
            filename = f"{packet.subject.chart_id}_{safe_ts}.json"
            destination_path = Path("blind_packets") / filename

        destination_path.parent.mkdir(parents=True, exist_ok=True)

        storage_dict = _packet_to_storage_dict(packet)
        canonical = json.dumps(storage_dict, sort_keys=True, indent=2)
        destination_path.write_text(canonical, encoding="utf-8")
        return destination_path

    def load_and_verify(self, packet_path: Path) -> FrozenPredictionPacket:
        """Load a persisted packet and verify its SHA-256 integrity.

        Reads the JSON file, reconstructs the FrozenPredictionPacket,
        re-computes the payload SHA-256 digest, and compares it against
        the stored hash.

        Args:
            packet_path: Path to the persisted JSON file.

        Returns:
            Verified FrozenPredictionPacket.

        Raises:
            CryptographicTamperError: If the re-computed hash does not
                match the stored hash, indicating tampering.
            FileNotFoundError: If the packet file does not exist.
            json.JSONDecodeError: If the file is not valid JSON.
        """
        raw = packet_path.read_text(encoding="utf-8")
        storage_dict = json.loads(raw)

        # Extract and remove the hash from the stored dict so we can
        # recompute it from the exact payload content (including any
        # extra fields that would indicate tampering).
        stored_hash = storage_dict.pop("payload_hash", None)
        if stored_hash is None:
            raise CryptographicTamperError(
                "No payload_hash found in stored packet.",
                expected_hash="",
                actual_hash="",
            )

        # Recompute hash from the raw canonical payload (after removing
        # the hash key itself). This catches injected extra fields.
        canonical_payload = _canonicalize_floats(storage_dict)
        canonical_str = json.dumps(
            canonical_payload, sort_keys=True, separators=(",", ":"),
        )
        computed_hash = hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()

        if computed_hash != stored_hash:
            raise CryptographicTamperError(
                f"SHA-256 hash mismatch for packet '{storage_dict.get("subject", {}).get("chart_id", "unknown")}'. "
                f"Expected {stored_hash[:16]}..., got {computed_hash[:16]}... "
                f"The prediction packet has been tampered with.",
                expected_hash=stored_hash,
                actual_hash=computed_hash,
            )

        # Reconstruct packet from verified storage dict
        packet = _storage_dict_to_packet(storage_dict)
        return FrozenPredictionPacket(
            subject=packet.subject,
            target_timestamp=packet.target_timestamp,
            formation_strength=packet.formation_strength,
            structural_relationship_score=packet.structural_relationship_score,
            modification_impact=packet.modification_impact,
            varga_confirmation_score=packet.varga_confirmation_score,
            dasha_transit_activation=packet.dasha_transit_activation,
            predicted_strength=packet.predicted_strength,
            payload_hash=stored_hash,
        )
