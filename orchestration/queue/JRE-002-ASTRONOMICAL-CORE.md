# JRE-002 — Astronomical Core

Status: REQUESTED
Priority: CRITICAL

## Objective

Create the deterministic astronomical calculation layer of JRE.

## Required Inputs

- Date
- Time
- Latitude
- Longitude
- Timezone
- Ayanamsa configuration

## Required Initial Outputs

For:

- Sun
- Moon
- Mars
- Mercury
- Jupiter
- Venus
- Saturn
- Rahu
- Ketu

calculate:

- Ecliptic longitude
- Latitude where applicable
- Apparent/required astronomical state
- Instantaneous speed where available
- Retrograde/direct state
- Timestamp used
- Ephemeris provider
- Calculation configuration

## Separation Requirement

The astronomical layer MUST NOT perform astrological interpretation.

It must not determine:

- Benefic/malefic status
- House meaning
- Yoga
- Dasha result
- Wealth
- Marriage
- Career
- Prediction

## Provider Architecture

Create an abstraction allowing multiple astronomical providers.

Initial provider:

- Swiss Ephemeris or equivalent validated ephemeris library

Future providers must be capable of being added without rewriting the core.

## Determinism

Identical:

- input timestamp
- coordinates
- timezone
- ephemeris version
- configuration

must produce identical astronomical output.

## Testing Requirements

Tests must include:

1. Valid birth timestamp.
2. Invalid timestamp.
3. Invalid coordinates.
4. Timezone handling.
5. Boundary conditions.
6. Retrograde planet.
7. Provider metadata.
8. Repeated calculation producing identical output.

## Validation

The validator must independently verify selected planetary positions against an external astronomical reference.

## Deliverables

- Specification refinement
- Python implementation
- Automated tests
- Provider abstraction
- Documentation
- Validation report

## Restrictions

Do not implement:
- predictions
- Jyotish interpretations
- Yogas
- Dasha
- Gochar interpretation

Those belong to later modules.

