# Changelog

## Version 1.0.0 - 2026-02-05

### Added
- Rust + PyO3 (`abi3`) implementation of spatial verification core.
- Pure Python reference implementation for equivalence checks.
- CI workflow that builds wheels and tests installed wheel artifacts.

### Changed
- Stable wrapper API now calls Rust extension backend while preserving
  `get_affine_inliers_cpp` and `get_best_affine_inliers_cpp` behavior.
- Packaging migrated to `pyproject.toml` + `maturin`.

### Removed
- Legacy C/C++/CMake/OpenCV build pipeline and related scripts.
