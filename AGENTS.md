# Repository Covenant

This project is distributed to customer Kylin Linux machines. Packaging and
runtime choices must prioritize low-glibc Linux ARM64 compatibility.

## Third-Party Runtime Dependencies

- Prefer packages with PyPI wheels for Linux `aarch64` using
  `manylinux2014_aarch64` / glibc 2.17, or a lower/equivalent compatibility
  baseline.
- Do not add runtime dependencies that only publish Linux `aarch64` wheels
  requiring newer baselines such as `manylinux_2_31` or `manylinux_2_39`
  unless the target Kylin release and packaging path are explicitly verified.
- Do not require customer machines to install system Qt, PySide, PyQt, or other
  desktop UI runtime packages for the distributed application.
- GUI dependencies must be bundled into the application package. The current
  GUI toolkit is Dear PyGui because it provides `manylinux2014_aarch64` wheels.
- Keep CLI/core PDF processing code independent from the GUI toolkit where
  practical, so future UI packaging changes do not affect document operations.

## Packaging

- Build Kylin RPMs with `scripts/build_kylin_rpm.sh`.
- Build standalone Linux binaries with `scripts/build_linux.sh`.
- Before changing packaging dependencies, verify wheel availability on the
  target architecture with the actual Kylin Python version and glibc baseline.
