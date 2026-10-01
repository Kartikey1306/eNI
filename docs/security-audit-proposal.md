# Security Audit Proposal — eNI + eIPC (combined)

**Status:** Proposal — for org staffing decision.
**Date:** 2026-10-01

## Why

eNI is neural-interface firmware: it sits between human neural signals and a
host computer. A vulnerability here is not a data breach — it is a
safety-critical failure with direct human impact. No formal security audit of
eNI has ever been performed.

eIPC is the secure inter-process communication layer. eNI's host link almost
certainly depends on eIPC's transport, authentication, and encryption
primitives. Auditing them separately would miss the interface between them —
exactly where compositional vulnerabilities hide. Hence a **combined audit**.

## Scope

### eNI firmware attack surface
- Neural signal acquisition path (ADC drivers, signal conditioning)
- Stimulation output path (if present — any DAC/current-source control is
  safety-critical; unauthorized stimulation is the highest-severity finding
  class)
- Firmware update / bootloader interface (signed updates? rollback protection?)
- Host communication link (USB/BLE/UART — pairing, authentication, encryption)
- Configuration and calibration interfaces (clinical vs. developer modes)
- Debug interfaces (JTAG/SWD — production disablement)

### Neural-data privacy
- Signal data classification (raw neural signals are biometric identifiers)
- Data-at-rest encryption on device and host
- Data-in-transit encryption on the host link
- Retention, logging, and telemetry minimization
- Consent and data-subject controls (where applicable regulations apply)

### eIPC security primitives (as used by eNI)
- Authentication and capability model (`security/` tree)
- Encryption and integrity of IPC messages
- Keyring management and key lifecycle
- Replay protection
- Transport-agnosticism: audit the abstraction, then each transport eNI uses

### Out of scope (first pass)
- Host OS / driver security beyond the eNI link endpoint
- Physical hardware attacks (side-channel, fault injection) — note as
  follow-up if the firmware audit surfaces hardware-trust assumptions
- Supply-chain / build-system compromise (covered by SLSA/Scorecard work)

## Phases

1. **Threat modeling (2 weeks).** Data-flow diagrams for acquisition →
   processing → host link; STRIDE per trust boundary; stimulation-path
   hazard analysis. Output: threat model document, ranked finding backlog.
2. **Manual code review (3–4 weeks).** eNI firmware + eIPC `security/`
   subtree, guided by the threat model. Focus: memory safety in signal
   paths, auth bypasses, crypto misuse, integer issues in fixed-point DSP.
3. **Targeted testing (2 weeks).** Fuzz the host-link protocol parser and
   the eIPC message layer; fault-injection on update path (unsigned /
   rollback images must be rejected).
4. **Remediation support (2 weeks).** Fix verification, re-test of closed
   findings. Output: final report with residual-risk register.

## Acceptance criteria

- Threat model published in `docs/` of both repos.
- Zero unresolved **critical** findings (remote code execution, unauthorized
  stimulation, auth bypass on the host link, unsigned firmware acceptance).
- Zero unresolved **high** findings, or explicit risk acceptance signed by a
  maintainer for each.
- Fuzz harnesses for the host-link parser and eIPC message layer landed in
  CI and running (not one-off).
- Residual-risk register published; follow-up issues filed for mediums.

## Staffing notes

- Requires embedded-security expertise **and** familiarity with neural-
  interface safety considerations (stimulation hazards are domain-specific).
- eIPC's ISO 20243 O-TTPS documentation (in-repo) should be reviewed as
  part of phase 1 input.
- Estimated effort: 1 security engineer × 9–10 weeks, or a boutique audit
  firm fixed-scope engagement.

## References

- eNI `docs/compliance/` and `qms/` (existing — verify current before the
  audit; not rewritten by this proposal).
- eIPC `security/` subtree (auth, capability, encryption, integrity,
  keyring, replay).
- Tock 2.2 (MPU isolation, capability IPC) — a reference model for the
  eIPC/eNI isolation story.
