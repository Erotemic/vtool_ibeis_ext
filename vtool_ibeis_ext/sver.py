"""Modernized spatial verification API."""

from __future__ import annotations

from typing import List, Tuple

import numpy as np

from . import sver_c_wrapper

ArrayF64 = np.ndarray
ArrayI64 = np.ndarray


def get_affine_inliers(
    kpts1: ArrayF64,
    kpts2: ArrayF64,
    fm: ArrayI64,
    fs: ArrayF64,
    xy_thresh_sqrd: float,
    scale_thresh_sqrd: float,
    ori_thresh: float,
) -> Tuple[List[np.ndarray], List[Tuple[np.ndarray, np.ndarray, np.ndarray]], np.ndarray]:
    """Alias for the stable wrapper implementation."""
    return sver_c_wrapper.get_affine_inliers_cpp(
        kpts1,
        kpts2,
        fm,
        fs,
        xy_thresh_sqrd,
        scale_thresh_sqrd,
        ori_thresh,
    )


def get_best_affine_inliers(
    kpts1: ArrayF64,
    kpts2: ArrayF64,
    fm: ArrayI64,
    fs: ArrayF64,
    xy_thresh_sqrd: float,
    scale_thresh_sqrd: float,
    ori_thresh: float,
) -> Tuple[np.ndarray, Tuple[np.ndarray, np.ndarray, np.ndarray], np.ndarray]:
    """Alias for the stable wrapper implementation."""
    return sver_c_wrapper.get_best_affine_inliers_cpp(
        kpts1,
        kpts2,
        fm,
        fs,
        xy_thresh_sqrd,
        scale_thresh_sqrd,
        ori_thresh,
    )
