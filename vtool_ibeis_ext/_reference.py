"""Pure Python/Numpy reference implementation for spatial verification."""

from __future__ import annotations

from typing import List, Tuple

import numpy as np

ArrayF64 = np.ndarray
ArrayI64 = np.ndarray

TAU = 2.0 * np.pi


def _ensure_0to_tau(x: float) -> float:
    x = np.fmod(x, TAU)
    if x < 0:
        x += TAU
    return float(x)


def _inv_v_mat(kpt: ArrayF64) -> ArrayF64:
    x, y, a, c, d, theta = kpt
    ct = np.cos(theta)
    st = np.sin(theta)
    return np.array(
        [
            [a * ct, a * (-st), x],
            [c * ct + d * st, c * (-st) + d * ct, y],
            [0.0, 0.0, 1.0],
        ],
        dtype=np.float64,
    )


def _inv_affine(mat: ArrayF64) -> ArrayF64:
    a, b, x = mat[0]
    c, d, y = mat[1]
    det = a * d - b * c
    return np.array(
        [
            [d / det, -b / det, (b * y - d * x) / det],
            [-c / det, a / det, (c * x - a * y) / det],
            [0.0, 0.0, 1.0],
        ],
        dtype=np.float64,
    )


def _xy_distance(kpt1: ArrayF64, kpt2: ArrayF64) -> float:
    dx = kpt2[0, 2] - kpt1[0, 2]
    dy = kpt2[1, 2] - kpt1[1, 2]
    return float(dx * dx + dy * dy)


def _det_distance(kpt1: ArrayF64, kpt2: ArrayF64) -> float:
    a1, b1 = kpt1[0, 0], kpt1[0, 1]
    c1, d1 = kpt1[1, 0], kpt1[1, 1]
    a2, b2 = kpt2[0, 0], kpt2[0, 1]
    c2, d2 = kpt2[1, 0], kpt2[1, 1]
    det1 = a1 * d1 - b1 * c1
    det2 = a2 * d2 - b2 * c2
    dist = det1 / det2
    if dist < 1:
        dist = 1.0 / dist
    return float(dist)


def _ori_distance(kpt1: ArrayF64, kpt2: ArrayF64) -> float:
    a1, b1 = kpt1[0, 0], kpt1[0, 1]
    a2, b2 = kpt2[0, 0], kpt2[0, 1]
    ori1 = _ensure_0to_tau(-np.arctan2(b1, a1))
    ori2 = _ensure_0to_tau(-np.arctan2(b2, a2))
    delta = abs(ori1 - ori2)
    delta = _ensure_0to_tau(delta)
    return float(min(delta, TAU - delta))


def get_affine_inliers_raw(
    kpts1: ArrayF64,
    kpts2: ArrayF64,
    fm: ArrayI64,
    fs: ArrayF64,
    xy_thresh_sqrd: float,
    scale_thresh_sqrd: float,
    ori_thresh: float,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Reference implementation returning raw arrays."""
    num_matches = fm.shape[0]
    invvr1_list = []
    invvr2_list = []
    for i in range(num_matches):
        idx1 = fm[i, 0]
        idx2 = fm[i, 1]
        invvr1_list.append(_inv_v_mat(kpts1[idx1]))
        invvr2_list.append(_inv_v_mat(kpts2[idx2]))

    mats = np.empty((num_matches, 3, 3), dtype=np.float64)
    for i in range(num_matches):
        mats[i] = invvr2_list[i] @ _inv_affine(invvr1_list[i])

    inlier_flags = np.empty((num_matches, num_matches), dtype=bool)
    errors = np.empty((num_matches, 3, num_matches), dtype=np.float64)

    for i in range(num_matches):
        aff = mats[i]
        for j in range(num_matches):
            invvr1_mt = aff @ invvr1_list[j]
            xy_err = _xy_distance(invvr1_mt, invvr2_list[j])
            ori_err = _ori_distance(invvr1_mt, invvr2_list[j])
            scale_err = _det_distance(invvr1_mt, invvr2_list[j])
            errors[i, 0, j] = xy_err
            errors[i, 1, j] = ori_err
            errors[i, 2, j] = scale_err
            inlier_flags[i, j] = (
                xy_err < xy_thresh_sqrd
                and scale_err < scale_thresh_sqrd
                and ori_err < ori_thresh
            )

    _ = fs
    return inlier_flags, errors, mats


def get_best_affine_inliers_raw(
    kpts1: ArrayF64,
    kpts2: ArrayF64,
    fm: ArrayI64,
    fs: ArrayF64,
    xy_thresh_sqrd: float,
    scale_thresh_sqrd: float,
    ori_thresh: float,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Reference implementation returning raw arrays."""
    num_matches = fm.shape[0]
    invvr1_list = []
    invvr2_list = []
    for i in range(num_matches):
        idx1 = fm[i, 0]
        idx2 = fm[i, 1]
        invvr1_list.append(_inv_v_mat(kpts1[idx1]))
        invvr2_list.append(_inv_v_mat(kpts2[idx2]))

    best_weight = -np.inf
    best_inliers = np.empty((num_matches,), dtype=bool)
    best_errors = np.empty((3, num_matches), dtype=np.float64)
    best_mat = np.empty((3, 3), dtype=np.float64)

    for i in range(num_matches):
        aff = invvr2_list[i] @ _inv_affine(invvr1_list[i])
        tmp_inliers = np.empty((num_matches,), dtype=bool)
        tmp_errors = np.empty((3, num_matches), dtype=np.float64)
        weight = 0.0
        for j in range(num_matches):
            invvr1_mt = aff @ invvr1_list[j]
            xy_err = _xy_distance(invvr1_mt, invvr2_list[j])
            ori_err = _ori_distance(invvr1_mt, invvr2_list[j])
            scale_err = _det_distance(invvr1_mt, invvr2_list[j])
            tmp_errors[0, j] = xy_err
            tmp_errors[1, j] = ori_err
            tmp_errors[2, j] = scale_err
            is_inlier = (
                xy_err < xy_thresh_sqrd
                and scale_err < scale_thresh_sqrd
                and ori_err < ori_thresh
            )
            tmp_inliers[j] = is_inlier
            if is_inlier:
                weight += fs[j]

        if weight >= best_weight:
            best_weight = weight
            best_inliers = tmp_inliers
            best_errors = tmp_errors
            best_mat = aff

    return best_inliers, best_errors, best_mat


def get_affine_inliers_cpp(
    kpts1: ArrayF64,
    kpts2: ArrayF64,
    fm: ArrayI64,
    fs: ArrayF64,
    xy_thresh_sqrd: float,
    scale_thresh_sqrd: float,
    ori_thresh: float,
) -> Tuple[List[np.ndarray], List[Tuple[np.ndarray, np.ndarray, np.ndarray]], np.ndarray]:
    inlier_flags, errors, mats = get_affine_inliers_raw(
        kpts1,
        kpts2,
        fm,
        fs,
        xy_thresh_sqrd,
        scale_thresh_sqrd,
        ori_thresh,
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
    inlier_flags, errors, mat = get_best_affine_inliers_raw(
        kpts1,
        kpts2,
        fm,
        fs,
        xy_thresh_sqrd,
        scale_thresh_sqrd,
        ori_thresh,
    )
    out_inliers = np.where(inlier_flags)[0]
    out_errors = tuple(errors)
    return out_inliers, out_errors, mat
