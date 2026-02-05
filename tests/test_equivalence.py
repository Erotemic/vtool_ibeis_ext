import numpy as np

from vtool_ibeis_ext import _reference, _sver, sver_c_wrapper


def _example_inputs():
    kpts1 = np.array(
        [
            [3.2e01, 2.7e01, 1.7e01, 5.0e00, 2.1e01, 6.2e00],
            [1.3e02, 2.3e01, 2.0e01, 2.7e00, 2.1e01, 6.3e00],
            [2.3e02, 2.4e01, 1.7e01, -9.2e00, 1.6e01, 4.7e-01],
            [3.0e01, 1.3e02, 1.6e01, -9.2e00, 1.8e01, 5.6e00],
            [1.3e02, 1.4e02, 1.9e01, -1.6e-01, 2.1e01, 1.1e-01],
            [2.3e02, 1.3e02, 1.9e01, -1.1e00, 2.0e01, 4.8e-02],
            [3.5e01, 2.2e02, 1.8e01, -3.0e00, 2.0e01, 1.8e-01],
            [1.4e02, 2.3e02, 1.8e01, -2.4e00, 2.0e01, 6.0e00],
            [2.3e02, 2.3e02, 2.3e01, 1.3e00, 1.9e01, 4.4e-01],
        ],
        dtype=np.float64,
    )
    kpts2 = np.array(
        [
            [3.4e01, 2.8e01, 2.0e01, 1.6e00, 1.7e01, 1.8e-02],
            [1.3e02, 2.7e01, 2.1e01, 4.4e00, 2.0e01, 6.3e00],
            [2.3e02, 2.6e01, 2.0e01, 3.8e00, 2.0e01, 7.3e-03],
            [3.2e01, 1.3e02, 2.3e01, 1.1e00, 2.2e01, 6.0e00],
            [1.2e02, 1.3e02, 1.9e01, 1.6e00, 2.3e01, 6.2e00],
            [2.3e02, 1.4e02, 1.8e01, 4.5e00, 1.6e01, 2.7e-01],
            [3.3e01, 2.3e02, 2.0e01, 2.0e00, 1.9e01, 1.7e-01],
            [1.3e02, 2.3e02, 2.1e01, 4.0e00, 2.1e01, 1.1e-01],
            [2.3e02, 2.3e02, 1.6e01, 2.5e00, 2.2e01, 6.2e00],
        ],
        dtype=np.float64,
    )
    fm = np.array(
        [[0, 0], [1, 1], [2, 2], [3, 3], [4, 4], [5, 5], [6, 6], [7, 7], [8, 8]],
        dtype=np.int64,
    )
    fs = np.ones((9,), dtype=np.float64)
    return kpts1, kpts2, fm, fs


def _assert_wrapper_matches_reference(result, expected):
    out_inliers, out_errors, out_mats = result
    exp_inliers, exp_errors, exp_mats = expected
    assert len(out_inliers) == len(exp_inliers)
    for left, right in zip(out_inliers, exp_inliers):
        assert np.array_equal(left, right)
    assert len(out_errors) == len(exp_errors)
    for left, right in zip(out_errors, exp_errors):
        for l_arr, r_arr in zip(left, right):
            assert np.allclose(l_arr, r_arr)
    assert np.allclose(out_mats, exp_mats)


def test_example_equivalence():
    kpts1, kpts2, fm, fs = _example_inputs()
    params = dict(xy_thresh_sqrd=100.0, scale_thresh_sqrd=100.0, ori_thresh=100.0)

    rust_out = sver_c_wrapper.get_affine_inliers_cpp(kpts1, kpts2, fm, fs, **params)
    ref_out = _reference.get_affine_inliers_cpp(kpts1, kpts2, fm, fs, **params)
    _assert_wrapper_matches_reference(rust_out, ref_out)

    rust_best = sver_c_wrapper.get_best_affine_inliers_cpp(kpts1, kpts2, fm, fs, **params)
    ref_best = _reference.get_best_affine_inliers_cpp(kpts1, kpts2, fm, fs, **params)
    assert np.array_equal(rust_best[0], ref_best[0])
    for l_arr, r_arr in zip(rust_best[1], ref_best[1]):
        assert np.allclose(l_arr, r_arr)
    assert np.allclose(rust_best[2], ref_best[2])


def test_random_equivalence():
    rng = np.random.default_rng(0)
    kpts1 = rng.normal(size=(12, 6))
    kpts2 = rng.normal(size=(12, 6))
    fm = rng.integers(0, 12, size=(15, 2), dtype=np.int64)
    fs = rng.random(size=(15,)).astype(np.float64)
    params = dict(xy_thresh_sqrd=5.0, scale_thresh_sqrd=10.0, ori_thresh=2.0)

    rust_raw = _sver.get_affine_inliers(kpts1, kpts2, fm, fs, **params)
    py_raw = _reference.get_affine_inliers_raw(kpts1, kpts2, fm, fs, **params)
    for left, right in zip(rust_raw, py_raw):
        if left.dtype == bool:
            assert np.array_equal(left, right)
        else:
            assert np.allclose(left, right)

    rust_best_raw = _sver.get_best_affine_inliers(kpts1, kpts2, fm, fs, **params)
    py_best_raw = _reference.get_best_affine_inliers_raw(kpts1, kpts2, fm, fs, **params)
    for left, right in zip(rust_best_raw, py_best_raw):
        if left.dtype == bool:
            assert np.array_equal(left, right)
        else:
            assert np.allclose(left, right)

    rust_out = sver_c_wrapper.get_affine_inliers_cpp(kpts1, kpts2, fm, fs, **params)
    ref_out = _reference.get_affine_inliers_cpp(kpts1, kpts2, fm, fs, **params)
    _assert_wrapper_matches_reference(rust_out, ref_out)
