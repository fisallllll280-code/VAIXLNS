# Ω-Arena v1 — Capability Promotion Pipeline

**Status:** SPECIFIED
**Authority:** project.genome::v1.0.0
**Owner:** VAIXLNS / VX

## 1. Principle
Arena results do not directly modify the canonical system. Promotion is a separate controlled pipeline.

## 2. Pipeline
ARENA RESULT → EVIDENCE PACKAGE → INDEPENDENT VALIDATION → CAPABILITY EXTRACTION → LINEAGE CHECK → SECURITY REVIEW → REGRESSION SUITE → REPLAY → GOVERNANCE ADMISSION → CAPABILITY REGISTRY → DEPLOYED EXPERIMENT → OBSERVATION → ADOPTED / QUARANTINED / REJECTED

## 3. What can be promoted
Promotable objects include provider adapter improvements; reusable prompts/policies; verified tool strategies; reasoning/verification patterns; capability compositions; test suites; recovery strategies; validated engineering templates.

A model brand itself is never promoted as canonical capability.

## 4. Lineage requirements
Every promoted capability records capability_id; source arena/matches; parent capability IDs; provider/adapter references; evidence IDs; verification IDs; test corpus/version; environment fingerprint; origin metadata; promotion decision; rollback/quarantine reference.

## 5. Rollback
Any adopted capability can be quarantined when new evidence invalidates its assumptions. Rollback restores the previous known-good capability reference without deleting lineage.

## 6. Canonical boundary
Promotion creates a candidate registry entry first. It does not rewrite project.genome. Canonical changes require the existing VAIXLNS authority process.

## 7. Seven-day output
At the end of the first tournament, VX produces: provider conformance matrix; capability leaderboard; task/domain breakdown; adversarial failure matrix; reproducibility report; recovery/repair report; evidence confidence report; promoted capability candidates; rejected/quarantined candidates; unresolved research questions.

The result is an engineering evidence package, not a marketing ranking.