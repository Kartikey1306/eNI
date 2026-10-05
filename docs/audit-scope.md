# Security audit — scope, threat model, checklist (eNI + eIPC)

**Status:** Draft for review — formalizes
[#38](https://github.com/embeddedos-org/eNI/issues/38) (proposal:
`docs/security-audit-proposal.md`).
**Date:** 2026-10-05

## Objectives

1. Find vulnerabilities an attacker could use to read or alter neural
   signals, or to drive stimulation outputs without authorization.
2. Verify the eIPC transport eNI depends on: authentication, capability
   enforcement, encryption/integrity, replay protection.
3. Produce a ranked finding list with reproductions, so fixes are
   unambiguous.

## In scope

### eNI
- Neural-signal ingestion path: ADC drivers, signal conditioning, sample
  framing.
- `tools/quantize_model.py` and the model-format parsers (a malicious or
  malformed model file is attacker input).
- Firmware update / bootloader interface: signature verification, rollback
  protection, version binding.
- Host link (USB/BLE/UART): pairing, authentication, session encryption.
- Configuration/calibration interfaces; debug interfaces (JTAG/SWD
  production disablement).

### eIPC (as used by eNI)
- Capability model and enforcement (`security/` tree).
- Message encryption/integrity, keyring lifecycle, replay protection.
- The eNI↔eIPC interface itself — compositional flaws live here.

## Out of scope

- Host-side application code (out of the org's firmware boundary).
- Physical tamper resistance of the enclosure (noted, not tested).
- Availability/DoS beyond the stimulation-safety path.

## Threat model

**Assets:** raw neural signals (biometric identifiers), model weights,
calibration sets, stimulation-output control, device identity keys.

**Attackers:**
- *Remote (host link):* unauthenticated or low-privilege host software.
- *Proximity (BLE):* eavesdropper / active MITM during pairing.
- *Supply chain:* malicious model file, tampered firmware image.
- *Local (debug):* JTAG/SWD on a production unit.

**Assumptions:** the attacker does not have the signing keys; the hardware
provides the documented flash/RAM protections. Everything else is untrusted
until verified.

## Checklist per component

- [ ] **Input validation:** every parser (model formats, TLV frames, host
  protocol) rejects truncated, overlong, and type-confused inputs; fuzz
  corpus exists.
- [ ] **Bounds:** no unchecked indexing into sample buffers; ring-buffer
  wrap is tested at the boundary.
- [ ] **Stimulation gating:** no code path reaches DAC/current-source
  control without an authenticated, capability-checked command; default is
  off.
- [ ] **Update path:** signature verified before any flash write; version
  monotonicity enforced; rollback to a vulnerable version impossible.
- [ ] **Crypto:** no custom primitives; nonces never repeat; keys
  zeroized after use; no timing side-channels in compare paths.
- [ ] **eIPC capabilities:** a compromised peer cannot escalate beyond its
  granted capabilities; revoked capabilities stop working within one
  message round-trip.
- [ ] **Logging:** no raw neural data or key material in logs/telemetry.

## Scheduling

The audit itself is not started by this doc — it needs org staffing (see
the proposal). This scope is the concrete basis for that decision.
