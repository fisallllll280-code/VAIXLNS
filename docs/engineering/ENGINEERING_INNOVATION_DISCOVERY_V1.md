# ENGINEERING INNOVATION DISCOVERY — deep source loop v1

**Authority:** VAIXLNS  
**Research / synthesis boundary:** NEXENT  
**Execution / replay boundary:** VX  
**State:** Implemented as a curated-source discovery runner and scheduled workflow proposal; external changes remain review candidates, not canonical innovations.

## 1. The problem being solved

The project already has a source-derived Innovation Master Index. Its entries include Architecture Self-Discovery Engine, Capability Genome, Architecture Search Space, Architecture Laboratory, Architecture Recombination, Counterfactual Architecture, Formal Proof Orchestrator, Replay Determinism Verifier, Failure Genome and Self-Healing Architecture. The index itself says that an entry is not evidence of implementation.

The engineering discovery loop should not add another top-level agent for every tool. It should discover external capabilities, classify them, identify whether they fill a real gap, generate a bounded candidate integration, and return evidence to the existing VAIXLNS authority.

## 2. Research architecture

\`\`\`text
VAIXLNS / NEXENT OWNED INDEX
        │
        ├── existing innovation IDs, capabilities, gaps, lineage
        │
        ▼
CURATED UPSTREAM SOURCE REGISTRY
        │
        ├── release notes / tags
        ├── recent commits / source activity
        ├── default branch / license metadata
        └── official project links
        │
        ▼
EVIDENCE NORMALIZER
        │
        ├── source identity + URL
        ├── observation timestamp
        ├── response/source hash
        └── previous successful snapshot
        │
        ▼
DELTA + ENGINEERING SIGNALS
        │
        ├── NEW_RELEASE_SIGNAL
        ├── SOURCE_ACTIVITY_CHANGED
        ├── SOURCE_POLICY_OR_BRANCH_CHANGE
        ├── NO_CHANGE_OBSERVED
        └── SOURCE_FETCH_FAILED
        │
        ▼
ENGINEERING REVIEW / GAP MATCH
        │
        ├── duplicate / compatible extension / conflict / new candidate
        ├── license and dependency closure
        ├── platform and reproducibility check
        └── reference problem + tolerances
        │
        ▼
SANDBOX → BENCHMARK → COUNTEREXAMPLE → REPLAY → INDEPENDENT VERIFY
        │
        ▼
VAIXLNS ADMISSION GATE → approved canonical adoption
\`\`\`

### Why this is a deep engineering loop

A release tag alone is not an innovation proof. A commit alone is not a feature proof. A mesh generated without quality checks is not a valid finite-element input. A solver that exits with code zero is not necessarily numerically correct. A rendered image is not a verified physical design. The pipeline keeps these claims separate and preserves links to upstream source evidence.

## 3. Implemented discovery surface

### Source registry

\`registry/engineering/ENGINEERING_INNOVATION_SOURCES_V1.json\` contains 15 curated upstream sources across eight domains:

- CAD and geometric kernels
- Meshing and finite elements
- CFD and multiphysics
- Multidisciplinary optimization
- Electronics design automation
- Model-based system simulation
- Engineering visualization
- Aerospace conceptual design

The upstream identity is provider-aware. The two OpenFOAM source streams are recorded separately: OpenFOAM Foundation and the Keysight/OpenCFD GitLab project. Gmsh is recorded on its actual upstream host, not on an assumed GitHub mirror. KiCad is called out as a GitHub mirror whose description says GitHub pull requests are not accepted.

### Collector

\`tools/engineering_innovation_discovery.py\` uses GET-only public APIs for repository metadata, the latest three releases and the latest five commits. It generates JSON evidence plus a Markdown review report. It compares the result against the latest prior successful report when available.

The collector has source-host allowlists, response-size limits, bounded timeouts, limited stored text, and per-source failure isolation. The GitLab.com token is never forwarded to the separate Gmsh host. Tokens, private endpoint URLs and raw API responses are not written to the report.

### Unit tests

\`tests/test_engineering_innovation_discovery.py\` covers manifest allowlisting, duplicate identity, release/commit/license delta classification, one-source failure without losing other sources, evidence links, engineering keyword triage, and cross-host token isolation.

### Schedule

\`.github/workflows/engineering-innovation-discovery.yml\` runs daily at 04:17 UTC (07:17 in Saudi Arabia), and can also be dispatched manually. It restores the prior successful report from the main branch when one exists, runs offline tests, queries upstream APIs, and stores JSON/Markdown as a 90-day GitHub Actions artifact.

No source change is automatically merged, no package is automatically installed, and no solver is automatically executed by the scheduled discovery run. The first task is to identify and prioritize candidates. Engineering execution begins only after a separate bounded benchmark job is configured.

## 4. Candidate capability map

| Domain | Candidate upstream | Why it matters to the system | Minimum proof before adoption |
|---|---|---|---|
| CAD kernel | [Open CASCADE Technology](https://github.com/Open-Cascade-SAS/OCCT) | Solid/surface geometry, data exchange and shape healing | STEP round-trip, boolean/topology edge cases, shape-validity and deterministic hash tests |
| Scripted parametric CAD | [CadQuery](https://github.com/CadQuery/cadquery) | Reproducible, parameter-driven 3D models from code | Parameter bounds, CAD-kernel validity, STEP/STL export and regression fixtures |
| CAD application | [FreeCAD](https://github.com/FreeCAD/FreeCAD) | Python-enabled parametric modeling and engineering workbenches | Headless document build, constraint checks, geometry validation and version pinning |
| Mesh generation | [Gmsh](https://gmsh.info/) | Geometry-to-mesh transition for FEA/CFD | Element quality, mesh convergence, boundary-label preservation and invalid-geometry tests |
| CFD | [OpenFOAM Foundation](https://github.com/OpenFOAM/OpenFOAM-dev) | Fluid, thermal and related computational engineering | Canonical validation case, conservation residuals, mesh/time-step study and environment fingerprint |
| CFD | [OpenFOAM OpenCFD / Keysight](https://gitlab.com/openfoam/core/openfoam) | A distinct release and source stream | Same reference case tested separately; never assume parity with Foundation releases |
| Multiphysics | [Elmer FEM](https://github.com/ElmerCSC/elmerfem) | Coupled structural, thermal, fluid and electromagnetic workloads | Published reference problem, units, solver convergence and energy/error balance |
| Programmable FEM | [FEniCSx / DOLFINx](https://github.com/FEniCS/dolfinx) | Mathematical model building, variational forms and parallel FEM | Manufactured solution, expected convergence order and pinned dependencies |
| Optimization | [OpenMDAO](https://github.com/OpenMDAO/OpenMDAO) | Coupled design-space search and multidisciplinary optimization | Gradient checks, constraint feasibility, finite-difference comparison and repeatable optimum |
| Physical-system models | [OpenModelica](https://github.com/OpenModelica/OpenModelica) | Dynamic systems and co-simulation | Unit consistency, solver settings, step-size comparison and known response tests |
| Electronics | [KiCad source mirror](https://github.com/KiCad/kicad-source-mirror) | Schematic/PCB validation and manufacturing outputs | ERC/DRC, netlist comparison, BOM integrity and fabrication-file consistency |
| Multiphysics | [Kratos](https://github.com/KratosMultiphysics/Kratos) | Multi-domain numerical simulation | A small, pinned module set and validated reference cases before large installation |
| Aerospace concepts | [OpenVSP](https://github.com/OpenVSP/OpenVSP) | Parametric aircraft geometry and early design trade-offs | Geometry constraints and downstream analysis; conceptual outputs are not certification evidence |
| Electromagnetics | [openEMS](https://github.com/thliebig/openEMS) | RF, antenna and FDTD candidate analysis | Published antenna/RF reference case, mesh/time-step sensitivity and energy checks |
| Visualization | [Blender](https://github.com/blender/blender) | Inspection and communication of 3D engineering results | Visuals tied back to artifact hashes; rendering must not be treated as solver proof |

## 5. Initial outside-source findings (snapshot: 2026-10-09)

These are findings from official project pages reviewed for this research pass. The scheduled collector will keep monitoring repository metadata and release/source signals; it does not crawl every official webpage.

- **OpenMDAO:** the official documentation listed 3.45.1 as a release from September 10, 2026, and described multidisciplinary optimization with analytic derivatives, coupled systems and large design spaces. The useful integration question is whether a verified CAD/CAE adapter can expose differentiable or otherwise reliable design variables and constraints. Sources: [OpenMDAO current docs](https://openmdao.org/newdocs/versions/latest/index.html), [release documentation](https://openmdao.org/openmdao_docs/).
- **Gmsh:** its official manual identifies version 4.15.2, dated March 24, 2026, and documents automated 3D finite-element meshing and an API. The high-value problem is not “generate a mesh”; it is generating a mesh that passes quality, boundary-condition and convergence checks. Source: [Gmsh manual](https://gmsh.info/doc/texinfo/).
- **OpenFOAM Foundation:** version 14 was announced July 14, 2026, with changes including named units, field functions and solver developments. **OpenFOAM OpenCFD/Keysight** has its own separate v2606 release stream, announced in June 2026. The discovery agent must keep the variants distinct and use per-version reference cases. Sources: [Foundation release 14](https://openfoam.org/release/14/), [OpenCFD v2606](https://www.openfoam.com/news/main-news/openfoam-v2606).
- **Open CASCADE Technology:** its 8.0.1 release notes highlight modeling reliability, shape healing, periodic geometry, meshing and STEP export. This is a strong candidate for a geometry-validity and data-exchange test battery, not a reason to declare the current drawing agent kernel-verified. Source: [OCCT releases](https://github.com/Open-Cascade-SAS/OCCT/releases).
- **KiCad:** the official site lists a KiCad 10.0.7 release notice dated October 7, 2026, while the GitHub source mirror's release page may reflect a different publication state. This mismatch itself demonstrates why official release pages and mirrored source snapshots need separate provenance. Sources: [KiCad official site](https://www.kicad.org/), [KiCad source mirror releases](https://github.com/KiCad/kicad-source-mirror/releases).
- **Elmer FEM:** the official repository describes structural mechanics, fluid dynamics, heat transfer and electromagnetics, including work from desktop to HPC scales. Source: [Elmer FEM](https://github.com/ElmerCSC/elmerfem).
- **FEniCSx/DOLFINx:** the official repository describes a C++/Python finite-element environment for solving PDEs, with parallel-computing support and LGPL licensing. Source: [DOLFINx](https://github.com/FEniCS/dolfinx).
- **FreeCAD / CadQuery / OCCT:** the upstream docs together suggest a practical programmable CAD chain: build parametric geometry, use a CAD kernel to validate it, and preserve open exchange formats for downstream tools. Sources: [FreeCAD](https://github.com/FreeCAD/FreeCAD), [CadQuery](https://cadquery.readthedocs.io/), [OCCT](https://github.com/Open-Cascade-SAS/OCCT).

## 6. Highest-value integration order

1. **Geometry and drawing validation:** CadQuery + OCCT + FreeCAD, beginning with a pinned, small benchmark set and geometry-validity tests.
2. **Mesh and solver evidence:** Gmsh then DOLFINx/Elmer, with one canonical physical problem, explicit units, boundary conditions, convergence criteria and expected outputs.
3. **Optimization over verified analyses:** OpenMDAO only after a discipline adapter has stable contracts, meaningful gradients or a defined derivative-free strategy, and reliable failure signaling.
4. **Domain expansion:** keep both OpenFOAM streams, OpenModelica, KiCad, openEMS, OpenVSP and Kratos as separate capability candidates with separate reference suites.
5. **Visualization:** feed Blender from versioned engineering artifacts and simulation outputs, but keep visual results separate from numerical verification.

This ordering minimizes the risk of building a broad “agent that uses everything” before any one engineering chain is reproducible.

## 7. Required output from every discovery run

Each run should produce:

- Source identity, upstream URL, provider and observation timestamp.
- Release tag/date, release URL and bounded release notes.
- Recent commit SHAs, dates, subjects and links.
- License metadata as published by the source API, marked for manual verification.
- Prior-snapshot delta and a triage score with explicit disclaimer.
- Fetch failures as first-class records rather than silently skipped sources.
- A short review checklist mapping source evidence to the existing Innovation Master Index.

## 8. Admission contract

A source event becomes an engineering innovation candidate only after the reviewer records:
\`CandidateID + ExistingIndexMatches + CapabilityGap + SourceEvidence + LicenseReview + BenchmarkPlan + FailureCases + Owner + Lifecycle\`.

It can be marked implemented only after code or adapter tests exist. It can be marked verified only after a reproducible reference test passes with a pinned environment and retained evidence. Only the VAIXLNS admission authority may promote a candidate to canonical state; the research collector cannot approve its own findings.

## 9. Reproduce locally

\`\`\`bash
python -m py_compile tools/engineering_innovation_discovery.py
python -m unittest discover -s tests -p "test_engineering_innovation_discovery.py" -v
python tools/engineering_innovation_discovery.py --output-dir artifacts/engineering-discovery
\`\`\`

To compare against an earlier report, pass its JSON file via \`--baseline path/to/engineering-discovery-report.json\`.

The report is data for review. A successful HTTP API call proves access to the metadata endpoint at that time, not the correctness or safety of the upstream solver and not the readiness of the VAIXLNS integration.
