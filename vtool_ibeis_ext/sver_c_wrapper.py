"""Stable wrapper for spatial verification affine inlier routines."""

from __future__ import annotations

from typing import List, Sequence, Tuple

import numpy as np

from . import _sver as _sver_mod


def _get_backend_module():
    if _sver_mod is None:
        raise ImportError(
            "vtool_ibeis_ext._sver is not available. Build/install the wheel "
            "before calling sver_c_wrapper functions."
        )
    return _sver_mod

ArrayF64 = np.ndarray
ArrayI64 = np.ndarray


def get_affine_inliers_cpp(
    kpts1: ArrayF64,
    kpts2: ArrayF64,
    fm: ArrayI64,
    fs: ArrayF64,
    xy_thresh_sqrd: float,
    scale_thresh_sqrd: float,
    ori_thresh: float,
) -> Tuple[List[np.ndarray], List[Tuple[np.ndarray, np.ndarray, np.ndarray]], np.ndarray]:
    """Return per-hypothesis inliers, errors, and affine matrices."""
    backend = _get_backend_module()
    inlier_flags, errors, mats = backend.get_affine_inliers(
        kpts1,
        kpts2,
        fm,
        fs,
        float(xy_thresh_sqrd),
        float(scale_thresh_sqrd),
        float(ori_thresh),
    )
    out_inliers = [np.where(row)[0] for row in inlier_flags]
    out_errors = [tuple(err_triplet) for err_triplet in errors]
    return out_inliers, out_errors, mats


def get_best_affine_inliers_cpp(
    kpts1: ArrayF64,
    kpts2: ArrayF64,
    fm: ArrayI64,
    fs: ArrayF64,
    xy_thresh_sqrd: float,
    scale_thresh_sqrd: float,
    ori_thresh: float,
) -> Tuple[np.ndarray, Tuple[np.ndarray, np.ndarray, np.ndarray], np.ndarray]:
    """Return the best hypothesis inliers, errors, and affine matrix."""
    backend = _get_backend_module()
    inlier_flags, errors, mat = backend.get_best_affine_inliers(
        kpts1,
        kpts2,
        fm,
        fs,
        float(xy_thresh_sqrd),
        float(scale_thresh_sqrd),
        float(ori_thresh),
    )
    out_inliers = np.where(inlier_flags)[0]
    out_errors = tuple(errors)
    return out_inliers, out_errors, mat
