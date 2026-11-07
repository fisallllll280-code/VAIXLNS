# VCEF — Computer Engineering & Innovation Index V1

Date: 2026-10-25  
State: **PROPOSED / RESEARCH INVENTORY**, not hardware or production implementation.

VCEF is a proposed engineering assembly under V, with VX execution adapters, VV verification and VAIXLNS governance. This additive index does not overwrite the canonical master index or promote research to canonical status.

## Eight engineering tracks

CE-01 Processor Architecture (RISC-V); CE-02 RTL/FPGA; CE-03 ASIC/Chiplets; CE-04 PCB/Electronics; CE-05 Firmware/RTOS; CE-06 System Emulation; CE-07 Hardware Security; CE-08 Performance/Emerging Computing.

## Initial tools

Verilator, cocotb, Yosys, QEMU and Renode form the proposed simulation/test baseline. gem5 supports architecture exploration; OpenROAD requires foundry/PDK and license review; KiCad supports PCB design; OpenOCD requires authorized hardware.

**No tool installation, RTL simulation, silicon fabrication, hardware measurements or hardware verification has been performed by this change.** The CI validates registry structure and research provenance only.

## Research and experiment queue

| ID | Innovation | Track | Priority | Experiment |
|---|---|---|---|---|
| CEI-001 | RISC-V domain-specific acceleration | CE-01 | P0 | RV32I baseline vs accelerator |
| CEI-002 | Open-source chiplets | CE-03 | P1 | Model interconnect overhead |
| CEI-003 | Photonic in-memory computing | CE-08 | P2 | Normalize published energy metrics |
| CEI-004 | Secure RISC-V root of trust | CE-07 | P1 | Emulated attestation contracts |
| CEI-005 | Chiplet memory isolation | CE-07 | P1 | Deny unauthorized transactions |
| CEI-006 | Reconfigurable RISC-V instructions | CE-02 | P1 | Correctness and fallback testing |
| CEI-007 | RISC-V soft-GPU and HBM | CE-08 | P2 | Model memory throughput |
| CEI-008 | Heterogeneous AI chiplets | CE-03 | P2 | Normalize dense/sparse workloads |

Exact source links, maturity labels, proposed toolchains and falsifiable hypotheses are in `registry/computer-engineering/VCEF_INNOVATION_INDEX_V1.json`.

## Admission stages

SOURCE → LICENSE → REPRODUCIBLE EXPERIMENT → SECURITY REVIEW → SANDBOX EVIDENCE → INDEPENDENT VERIFICATION → GOVERNANCE ADMISSION.

No research paper's results are claims about VAIXLNS performance. No external repository is silently copied, merged or deployed.

## Run the initial registry tests

```bash
python scripts/validate_vcef_innovation_index.py
python -m unittest discover -s tests -p 'test_vcef_innovation_index.py' -v
```

## Follow-up implementation

1. Create an RV32I reference design with fixed tool versions and licensed sources.
2. Add Verilator/cocotb execution CI with machine-readable receipts.
3. Add a QEMU firmware boot baseline and compare behavior.
4. Record runtime, coverage, reproducibility and SHA-256 digests.
5. Review evidence before connecting VX/VV production adapters.
