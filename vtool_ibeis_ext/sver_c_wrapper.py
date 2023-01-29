#!/usr/bin/env python
"""
wraps c implementations slower parts of spatial verification

CommandLine:
    python -m vtool_ibeis_ext.sver_c_wrapper --rebuild-sver
    python -m vtool_ibeis_ext.sver_c_wrapper --rebuild-sver
    xdoctest -m vtool_ibeis_ext.sver_c_wrapper

Example:
    >>> import numpy as np
    >>> kpts1 = np.array([[ 3.2e+01,  2.7e+01,  1.7e+01,  5.0e+00,  2.1e+01,  6.2e+00],
    >>>                   [ 1.3e+02,  2.3e+01,  2.0e+01,  2.7e+00,  2.1e+01,  6.3e+00],
    >>>                   [ 2.3e+02,  2.4e+01,  1.7e+01, -9.2e+00,  1.6e+01,  4.7e-01],
    >>>                   [ 3.0e+01,  1.3e+02,  1.6e+01, -9.2e+00,  1.8e+01,  5.6e+00],
    >>>                   [ 1.3e+02,  1.4e+02,  1.9e+01, -1.6e-01,  2.1e+01,  1.1e-01],
    >>>                   [ 2.3e+02,  1.3e+02,  1.9e+01, -1.1e+00,  2.0e+01,  4.8e-02],
    >>>                   [ 3.5e+01,  2.2e+02,  1.8e+01, -3.0e+00,  2.0e+01,  1.8e-01],
    >>>                   [ 1.4e+02,  2.3e+02,  1.8e+01, -2.4e+00,  2.0e+01,  6.0e+00],
    >>>                   [ 2.3e+02,  2.3e+02,  2.3e+01,  1.3e+00,  1.9e+01,  4.4e-01]], dtype=np.float64)
    >>> kpts2 = np.array([[3.4e+01, 2.8e+01, 2.0e+01, 1.6e+00, 1.7e+01, 1.8e-02],
    >>>                   [1.3e+02, 2.7e+01, 2.1e+01, 4.4e+00, 2.0e+01, 6.3e+00],
    >>>                   [2.3e+02, 2.6e+01, 2.0e+01, 3.8e+00, 2.0e+01, 7.3e-03],
    >>>                   [3.2e+01, 1.3e+02, 2.3e+01, 1.1e+00, 2.2e+01, 6.0e+00],
    >>>                   [1.2e+02, 1.3e+02, 1.9e+01, 1.6e+00, 2.3e+01, 6.2e+00],
    >>>                   [2.3e+02, 1.4e+02, 1.8e+01, 4.5e+00, 1.6e+01, 2.7e-01],
    >>>                   [3.3e+01, 2.3e+02, 2.0e+01, 2.0e+00, 1.9e+01, 1.7e-01],
    >>>                   [1.3e+02, 2.3e+02, 2.1e+01, 4.0e+00, 2.1e+01, 1.1e-01],
    >>>                   [2.3e+02, 2.3e+02, 1.6e+01, 2.5e+00, 2.2e+01, 6.2e+00]], dtype=np.float64)
    >>> fm = np.array([[0, 0],[1, 1],[2, 2],[3, 3],[4, 4],[5, 5],[6, 6],[7, 7],[8, 8]], dtype=np.int64)
    >>> fs = np.array([1., 1., 1., 1., 1., 1., 1., 1., 1.], dtype=np.float64)
    >>> xy_thresh_sqrd = 100
    >>> scale_thresh_sqrd = 100
    >>> ori_thresh = 100
    >>> from vtool_ibeis_ext.sver_c_wrapper import *
    >>> out_inliers, out_errors, out_mats = get_affine_inliers_cpp(kpts1, kpts2, fm, fs, xy_thresh_sqrd, scale_thresh_sqrd, ori_thresh)
    >>> out_inliers, out_errors, out_mats = get_best_affine_inliers_cpp(kpts1, kpts2, fm, fs, xy_thresh_sqrd, scale_thresh_sqrd, ori_thresh)
"""
import ctypes as C
import numpy as np
import ubelt as ub
from os.path import dirname, join


if ub.WIN32:
    lib_ext = '.dll'
elif ub.DARWIN:
    lib_ext = '.dylib'
elif ub.LINUX:
    lib_ext = '.so'
else:
    lib_ext = '.so'

c_double_p = C.POINTER(C.c_double)

# copied/adapted from _pyhesaff.py
kpts_dtype = np.float64
# this is because size_t is 32 bit on mingw even on 64 bit machines
fm_dtype = np.int32 if ub.WIN32 else np.int64
fs_dtype = np.float64
FLAGS_RW = 'aligned, c_contiguous, writeable'
FLAGS_RO = 'aligned, c_contiguous'

kpts_t = np.ctypeslib.ndpointer(dtype=kpts_dtype, ndim=2, flags=FLAGS_RO)
fm_t  = np.ctypeslib.ndpointer(dtype=fm_dtype, ndim=2, flags=FLAGS_RO)
fs_t  = np.ctypeslib.ndpointer(dtype=fs_dtype, ndim=1, flags=FLAGS_RO)


def inliers_t(ndim):
    return np.ctypeslib.ndpointer(dtype=bool, ndim=ndim, flags=FLAGS_RW)


def errs_t(ndim):
    return np.ctypeslib.ndpointer(dtype=np.float64, ndim=ndim, flags=FLAGS_RW)


def mats_t(ndim):
    return np.ctypeslib.ndpointer(dtype=np.float64, ndim=ndim, flags=FLAGS_RW)

dpath = dirname(__file__)


lib_fname_cand = list(ub.find_path(
    name='libsver' + lib_ext,
    path=[
        join(dpath, 'lib'),
        dpath
    ],
    exact=False)
)

if len(lib_fname_cand):
    if len(lib_fname_cand) > 1:
        print('multiple libsver candidates: {}'.format(lib_fname_cand))
    lib_fname = lib_fname_cand[0]
else:
    raise Exception('cannot find path')
    lib_fname = None


if __name__ != '__main__':
    try:
        c_sver = C.cdll[lib_fname]
    except Exception:
        print('Failed to open lib_fname = %r' % (lib_fname,))
        raise
    c_getaffineinliers = c_sver['get_affine_inliers']
    c_getaffineinliers.restype = C.c_int
    # for every affine hypothesis, for every keypoint pair (is
    #  it an inlier, the error triples, the hypothesis itself)
    c_getaffineinliers.argtypes = [kpts_t, C.c_size_t,
                                   kpts_t, C.c_size_t,
                                   fm_t, fs_t, C.c_size_t,
                                   C.c_double, C.c_double, C.c_double,
                                   inliers_t(2), errs_t(3), mats_t(3)]
    # for the best affine hypothesis, for every keypoint pair
    #  (is it an inlier, the error triples (transposed?), the
    #   hypothesis itself)
    c_getbestaffineinliers = c_sver['get_best_affine_inliers']
    c_getbestaffineinliers.restype = C.c_int
    c_getbestaffineinliers.argtypes = [kpts_t, C.c_size_t,
                                       kpts_t, C.c_size_t,
                                       fm_t, fs_t, C.c_size_t,
                                       C.c_double, C.c_double, C.c_double,
                                       inliers_t(1), errs_t(2), mats_t(2)]


def get_affine_inliers_cpp(kpts1, kpts2, fm, fs, xy_thresh_sqrd, scale_thresh_sqrd, ori_thresh):
    #np.ascontiguousarray(kpts1)
    num_matches = len(fm)
    fm = np.ascontiguousarray(fm, dtype=fm_dtype)
    out_inlier_flags = np.empty((num_matches, num_matches), bool)
    out_errors = np.empty((num_matches, 3, num_matches), np.float64)
    out_mats = np.empty((num_matches, 3, 3), np.float64)
    c_getaffineinliers(kpts1, kpts1.size,
                       kpts2, kpts2.size,
                       fm, fs, len(fm),
                       xy_thresh_sqrd, scale_thresh_sqrd, ori_thresh,
                       out_inlier_flags, out_errors, out_mats)
    out_inliers = [np.where(row)[0] for row in out_inlier_flags]
    out_errors = list(map(tuple, out_errors))
    return out_inliers, out_errors, out_mats


def get_best_affine_inliers_cpp(kpts1, kpts2, fm, fs, xy_thresh_sqrd,
                                scale_thresh_sqrd, ori_thresh):
    #np.ascontiguousarray(kpts1)
    fm = np.ascontiguousarray(fm, dtype=fm_dtype)
    out_inlier_flags = np.empty((len(fm),), bool)
    out_errors = np.empty((3, len(fm)), np.float64)
    out_mat = np.empty((3, 3), np.float64)
    c_getbestaffineinliers(kpts1, 6 * len(kpts1),
                           kpts2, 6 * len(kpts2),
                           fm, fs, len(fm),
                           xy_thresh_sqrd, scale_thresh_sqrd, ori_thresh,
                           out_inlier_flags, out_errors, out_mat)
    out_inliers = np.where(out_inlier_flags)[0]
    out_errors = tuple(out_errors)
    return out_inliers, out_errors, out_mat


def call_hello():
    lib = C.cdll['./sver.so']
    hello = lib['hello_world']
    hello()


if __name__ == '__main__':
    """
    CommandLine:
        xdoctest -m vtool_ibeis_ext.sver_c_wrapper
    """
    import xdoctest
    xdoctest.doctest_module(__file__)
