# Development

## Contribution source of truth

[CONTRIBUTING](https://github.com/embeddedos-org/eNI/blob/master/CONTRIBUTING.md)

Before proposing a change, also review the [README](https://github.com/embeddedos-org/eNI/blob/master/README.md). Keep changes scoped, add tests appropriate to the affected behavior, and follow the repository's current automation and review requirements.

## Build and dependency inputs found

`CMakeLists.txt`, `Dockerfile`, `bindings/cpp/CMakeLists.txt`, `bindings/rust/Cargo.toml`, `cli/CMakeLists.txt`, `common/CMakeLists.txt`, `common/tinyml/CMakeLists.txt`, `docker/docker-compose.yml`, `framework/CMakeLists.txt`, `gui/package.json`, `integrations/CMakeLists.txt`, `integrations/eipc_streaming/CMakeLists.txt`, and 10 more.

## Tests found in the default-branch tree

`sdk/python/tests/test_bindings.py`, `tests/CMakeLists.txt`, `tests/__init__.py`, `tests/functional/__init__.py`, `tests/functional/test_functional_e2e.py`, `tests/functional/test_gps_client.py`, `tests/integration/test_calibration_session.c`, `tests/integration/test_full_pipeline.c`, `tests/mocks/mock_neural_input.c`, `tests/mocks/mock_neural_input.h`, `tests/mocks/mock_provider.c`, `tests/mocks/mock_provider.h`, and 48 more.

## Documented test commands

These commands are reproduced from the inspected root README or contributing guide:

```bash
cmake -B build -DCMAKE_BUILD_TYPE=Release
```

```bash
cmake --build build --parallel
```

```bash
cmake -B build -DENI_BUILD_TESTS=ON
```

```bash
ctest --test-dir build --output-on-failure
```

```bash
cmake --build build
```

```bash
cmake -B build -DENI_PROFILE=assistive-device
```

```bash
cmake --build build --config Release
```

```bash
ctest --test-dir build --output-on-failure -C Release
```

## Verification baseline

This inventory comes from `master` at [`fb59b4d5944b`](https://github.com/embeddedos-org/eNI/commit/fb59b4d5944bd6725fb050266eb4df6d1ae01ea5) and found 60 test-related paths among 375 files. Re-check the source tree when that commit is no longer current.
