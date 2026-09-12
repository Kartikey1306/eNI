# AGENTS.md — eNI

eNI (CMake project `ENI`, v0.3.0) is the neural-interface adapter of the
EmbeddedOS ecosystem, written in C: acquiring data from BCI hardware and
simulators through a provider model, running it through DSP, a neural decoder,
and an on-device neural-network inference engine, and driving a
stimulator/feedback path. It reads and writes neural data formats (EDF+, BDF+,
XDF, and a native ENI format) and includes session management and calibration.
(Provenance: `README.md` intro, `CMakeLists.txt` project version.)

## Layout (from `README.md` "What's inside")

- `providers/` — input providers: `eeg`, `lsl`, `neuralink`, `simulator`,
  `wireless`, `stimulator_sim`, `generic`, `template`
- `common/` — core signal path: `dsp`, `nn`, `feedback`, `tinyml`, `math`, `hal`
- `min/` — ENI-Min lightweight runtime
- `framework/` — ENI-Framework platform
- `platform/` — platform adapters: `linux`, `macos`, `windows`, `posix`, `eos`
- `cli/` — `eni` command-line tool
- `integrations/` — optional `ros2`, `oni` (ONI compliance), `eipc_streaming`
- `models/` — model assets and metadata
- `bindings/`, `sdk/` — language bindings (C++, Java, Python, Rust) and SDKs
  (Node.js, Python)
- `sim/` — simulation environment
- `gui/` — front-end (`package.json` + `src/`, `backend/`)
- `eni/`, `network/` — Python package and an IP-based geolocation helper used
  as a location fallback when GPS lock is lost
- `tests/` — unit, functional, performance, and simulation tests (C and Python)
- `docs/` — `ARCHITECTURE.md`, `BUILDING.md`, `GETTING_STARTED.md`,
  `PRODUCT_OVERVIEW.md`, `tutorials/`

## Build (from `README.md` "Build" and `CONTRIBUTING.md` "Development Setup")

Requires CMake ≥ 3.16 and a C compiler (GCC ≥ 11, Clang ≥ 14, or MSVC ≥ 2022).
`CMakePresets.json` defines the presets used by CI (`linux-debug`,
`linux-release`, `windows-debug`, `windows-release`, `macos-debug`,
`arm-cortex-m4`, `riscv32`, `native-asan`, `native-ubsan`). Tests are disabled
by default; enable with `ENI_BUILD_TESTS=ON`.

```bash
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel
```

Build manifests: `CMakeLists.txt`, `CMakePresets.json`,
`bindings/rust/Cargo.toml`, `gui/package.json`, `sdk/nodejs/package.json`,
`sdk/python/setup.py`, `Dockerfile`.

## Test (from `README.md` "Test")

```bash
cmake -B build -DENI_BUILD_TESTS=ON
cmake --build build --parallel
ctest --test-dir build --output-on-failure

# Python-driven suites
python run_all_tests.py
```

`run_all_tests.py` runs `pytest tests/unit tests/functional
tests/performance tests/simulation -v`. C tests are registered in
`tests/CMakeLists.txt` with labels `unit`, `integration`, and `stress`
(`ctest --test-dir build -L unit` selects unit tests; see `docs/BUILDING.md`
"Running Tests"). Profile verification per `CONTRIBUTING.md`
("How to Verify Locally"): at least one `-DENI_PROFILE=` build, e.g.
`cmake -B build-assistive -DENI_PROFILE=assistive-device`.

## Lint / format

Not defined: no lint or format command is documented in `README.md` or
`CONTRIBUTING.md`. (`cmake/static-analysis.cmake` provides opt-in
`ENI_ENABLE_CPPCHECK` / `ENI_ENABLE_CLANG_TIDY` / `ENI_ENABLE_SCAN_BUILD` /
`ENI_ENABLE_INFER` CMake options, but the repo documents no command to invoke
them; C style rules — C11, `-Wall -Wextra` clean — are in `CONTRIBUTING.md`
"Code Guidelines".)

## Contributing

See `CONTRIBUTING.md`: fork, create a feature branch (`git checkout -b
feat/my-feature`), run the build and tests locally, then submit a pull request.
Follow Conventional Commits; new features need unit tests in `tests/`; the PR
checklist requires zero-warning compiles on GCC, Clang, and MSVC, `#ifdef`
guards for all 3 OS targets, and no hardcoded filesystem paths. `CODEOWNERS`
requires at least one admin review on every PR.

## Security

See `SECURITY.md`. Report vulnerabilities to security@embeddedos.org — do NOT
open public issues for vulnerabilities. Response SLA: acknowledgment within
48 hours.
