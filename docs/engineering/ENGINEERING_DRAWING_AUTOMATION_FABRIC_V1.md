# Engineering Drawing Automation Fabric — V1

## State

Implementation status: **CONTRACT VALIDATOR IMPLEMENTED IN THIS BRANCH**.
Native geometry generation, simulation adapters, and engineering-code certification are **NOT IMPLEMENTED BY THIS CHANGE**.

## Purpose

Provide a strict job contract before VAIXLNS asks a CAD/BIM/analysis adapter to generate complex engineering drawings. Keep user intent, units, coordinate frame, constraints, code references, backend version, requested deliverables and verification status explicit and machine-auditable.

The engineering orchestrator must not treat a rendered drawing as proof that geometry, calculations, constructability, accessibility, tolerances, or local-code compliance are correct.

## Pipeline contract

```text
INTENT
  -> DISCIPLINE + JURISDICTION
  -> UNITS + COORDINATE FRAME
  -> CONSTRAINT GRAPH
  -> STANDARDS SELECTION (CONFIRMED)
  -> CAD/BIM BACKEND CAPABILITY CHECK
  -> PARAMETRIC MODEL
  -> 2D/3D VIEW GENERATION
  -> ANALYSIS / SIMULATION
  -> INDEPENDENT CHECK
  -> EVIDENCE BUNDLE
  -> HUMAN RELEASE AUTHORIZATION
```

The first implemented component is a fail-closed job-admission validator. It rejects malformed job contracts, duplicate identities, implicit units, untraceable standard references, and malformed evidence fields. A structurally valid request can still be **ineligible for release** until mandatory constraints have item-level evidence, standards have been confirmed or explicitly justified as not applicable, the CAD/BIM adapter capability is verified, required simulation passes with an evidence reference, an independent checker passes with an evidence reference, and configured human approval has a traceable approval reference.

## Deliverables and adapters

The contract can request SVG/DXF/DWG 2D outputs, STEP/IGES/STL/GLB 3D outputs, IFC/RVT BIM models, and PDF/JSON reports. Declaring a format does not install or implement the native CAD adapter. The adapter must advertise its exact engine version and capability contract.

Suggested backend boundaries:
- FreeCAD / Open CASCADE for parametric or boundary-representation geometry.
- Autodesk Automation APIs for supported Revit, AutoCAD, Inventor, Fusion, and related batch workflows.
- IFC for neutral BIM data exchange.
- A separate discipline solver for structural, thermal, fluid, electrical or other engineering analysis.

No backend may be selected solely from a language model's preference; admission must check adapter availability and capability/version.

## Standards and codes

The profile registry is **REFERENCE_ONLY** and suggests candidate standards:
- ISO 128-1 and ISO 128-3 for technical drawing representation and views/sections.
- ISO 129-1 for presentation of dimensions/tolerances.
- ISO 1101 and ISO 22081 for ISO geometrical product specifications.
- ASME Y14.5 where a project explicitly chooses the ASME dimensioning/tolerancing system.
- ISO 19650 and a selected IFC release for BIM information management/exchange.
- For Saudi building projects, candidates include SBC 201-2024 and SBC 301-2024, but applicability must be verified for the actual occupancy, authority, discipline and project.

The engine must **suggest, not silently select** a code. Editions and applicability are checked at job admission because standards and local rules can change.

## Release invariant

No automatic release where any of these conditions holds:
1. Required constraint lacks item-level verification evidence.
2. Governing standard/edition is unresolved.
3. Required simulation/analysis has not passed.
4. Required independent verification has not passed.
5. Required human approval has not been granted.

This validator is a contract and workflow safety gate. It does not independently calculate building/code compliance, certify a design, or replace a licensed engineer's responsibilities.

## Run

```bash
python tools/validate_engineering_drawing_job.py path/to/job.json
python tools/validate_engineering_drawing_job.py path/to/job.json --require-release
python -m unittest discover -s tests -p "test_engineering_drawing_job.py" -v
```

Exit codes: 0 = structurally valid (or release-eligible with --require-release); 2 = invalid job; 3 = valid job blocked from release.
