use numpy::{PyArray1, PyArray2, PyArray3, PyReadonlyArray1, PyReadonlyArray2};
use pyo3::prelude::*;

#[derive(Clone, Copy, Debug)]
struct Mat3 {
    data: [[f64; 3]; 3],
}

impl Mat3 {
    fn mul(&self, other: &Mat3) -> Mat3 {
        let mut out = [[0.0_f64; 3]; 3];
        for r in 0..3 {
            for c in 0..3 {
                out[r][c] = self.data[r][0] * other.data[0][c]
                    + self.data[r][1] * other.data[1][c]
                    + self.data[r][2] * other.data[2][c];
            }
        }
        Mat3 { data: out }
    }
}

fn ensure_0to_tau(x: f64) -> f64 {
    let tau = std::f64::consts::TAU;
    let mut v = x % tau;
    if v < 0.0 {
        v += tau;
    }
    v
}

fn inv_v_mat(kpt: &[f64; 6]) -> Mat3 {
    let x = kpt[0];
    let y = kpt[1];
    let a = kpt[2];
    let c = kpt[3];
    let d = kpt[4];
    let theta = kpt[5];
    let ct = theta.cos();
    let st = theta.sin();
    Mat3 {
        data: [
            [a * ct, a * (-st), x],
            [c * ct + d * st, c * (-st) + d * ct, y],
            [0.0, 0.0, 1.0],
        ],
    }
}

fn inv_affine(mat: &Mat3) -> Mat3 {
    let a = mat.data[0][0];
    let b = mat.data[0][1];
    let x = mat.data[0][2];
    let c = mat.data[1][0];
    let d = mat.data[1][1];
    let y = mat.data[1][2];
    let det = a * d - b * c;
    Mat3 {
        data: [
            [d / det, -b / det, (b * y - d * x) / det],
            [-c / det, a / det, (c * x - a * y) / det],
            [0.0, 0.0, 1.0],
        ],
    }
}

fn xy_distance(kpt1: &Mat3, kpt2: &Mat3) -> f64 {
    let dx = kpt2.data[0][2] - kpt1.data[0][2];
    let dy = kpt2.data[1][2] - kpt1.data[1][2];
    dx * dx + dy * dy
}

fn det_distance(kpt1: &Mat3, kpt2: &Mat3) -> f64 {
    let a1 = kpt1.data[0][0];
    let b1 = kpt1.data[0][1];
    let c1 = kpt1.data[1][0];
    let d1 = kpt1.data[1][1];
    let a2 = kpt2.data[0][0];
    let b2 = kpt2.data[0][1];
    let c2 = kpt2.data[1][0];
    let d2 = kpt2.data[1][1];
    let det1 = a1 * d1 - b1 * c1;
    let det2 = a2 * d2 - b2 * c2;
    let mut dist = det1 / det2;
    if dist < 1.0 {
        dist = 1.0 / dist;
    }
    dist
}

fn ori_distance(kpt1: &Mat3, kpt2: &Mat3) -> f64 {
    let a1 = kpt1.data[0][0];
    let b1 = kpt1.data[0][1];
    let a2 = kpt2.data[0][0];
    let b2 = kpt2.data[0][1];
    let ori1 = ensure_0to_tau(-b1.atan2(a1));
    let ori2 = ensure_0to_tau(-b2.atan2(a2));
    let mut delta = (ori1 - ori2).abs();
    delta = ensure_0to_tau(delta);
    let tau = std::f64::consts::TAU;
    delta.min(tau - delta)
}

fn extract_kpt(view: &numpy::ndarray::ArrayView2<'_, f64>, idx: usize) -> [f64; 6] {
    let row = view.row(idx);
    [row[0], row[1], row[2], row[3], row[4], row[5]]
}

#[pyfunction]
fn get_affine_inliers(
    py: Python<'_>,
    kpts1: PyReadonlyArray2<f64>,
    kpts2: PyReadonlyArray2<f64>,
    fm: PyReadonlyArray2<i64>,
    _fs: PyReadonlyArray1<f64>,
    xy_thresh_sqrd: f64,
    scale_thresh_sqrd: f64,
    ori_thresh: f64,
) -> PyResult<(Py<PyArray2<bool>>, Py<PyArray3<f64>>, Py<PyArray3<f64>>)> {
    let fm_view = fm.as_array();
    let num_matches = fm_view.shape()[0];

    let kpts1_view = kpts1.as_array();
    let kpts2_view = kpts2.as_array();

    let mut invvr1_list = Vec::with_capacity(num_matches);
    let mut invvr2_list = Vec::with_capacity(num_matches);
    for i in 0..num_matches {
        let idx1 = fm_view[[i, 0]] as usize;
        let idx2 = fm_view[[i, 1]] as usize;
        let kpt1 = extract_kpt(&kpts1_view, idx1);
        let kpt2 = extract_kpt(&kpts2_view, idx2);
        invvr1_list.push(inv_v_mat(&kpt1));
        invvr2_list.push(inv_v_mat(&kpt2));
    }

    let out_inliers = PyArray2::<bool>::zeros(py, [num_matches, num_matches], false);
    let out_errors = PyArray3::<f64>::zeros(py, [num_matches, 3, num_matches], false);
    let out_mats = PyArray3::<f64>::zeros(py, [num_matches, 3, 3], false);

    let mut inliers_view = unsafe { out_inliers.as_array_mut() };
    let mut errors_view = unsafe { out_errors.as_array_mut() };
    let mut mats_view = unsafe { out_mats.as_array_mut() };

    let mut aff_list = Vec::with_capacity(num_matches);
    for i in 0..num_matches {
        let aff = invvr2_list[i].mul(&inv_affine(&invvr1_list[i]));
        for r in 0..3 {
            for c in 0..3 {
                mats_view[[i, r, c]] = aff.data[r][c];
            }
        }
        aff_list.push(aff);
    }

    for i in 0..num_matches {
        let aff = &aff_list[i];
        for j in 0..num_matches {
            let invvr1_mt = aff.mul(&invvr1_list[j]);
            let xy_err = xy_distance(&invvr1_mt, &invvr2_list[j]);
            let ori_err = ori_distance(&invvr1_mt, &invvr2_list[j]);
            let scale_err = det_distance(&invvr1_mt, &invvr2_list[j]);
            errors_view[[i, 0, j]] = xy_err;
            errors_view[[i, 1, j]] = ori_err;
            errors_view[[i, 2, j]] = scale_err;
            inliers_view[[i, j]] =
                xy_err < xy_thresh_sqrd && scale_err < scale_thresh_sqrd && ori_err < ori_thresh;
        }
    }

    Ok((
        out_inliers.to_owned(),
        out_errors.to_owned(),
        out_mats.to_owned(),
    ))
}

#[pyfunction]
fn get_best_affine_inliers(
    py: Python<'_>,
    kpts1: PyReadonlyArray2<f64>,
    kpts2: PyReadonlyArray2<f64>,
    fm: PyReadonlyArray2<i64>,
    fs: PyReadonlyArray1<f64>,
    xy_thresh_sqrd: f64,
    scale_thresh_sqrd: f64,
    ori_thresh: f64,
) -> PyResult<(Py<PyArray1<bool>>, Py<PyArray2<f64>>, Py<PyArray2<f64>>)> {
    let fm_view = fm.as_array();
    let num_matches = fm_view.shape()[0];

    let kpts1_view = kpts1.as_array();
    let kpts2_view = kpts2.as_array();

    let mut invvr1_list = Vec::with_capacity(num_matches);
    let mut invvr2_list = Vec::with_capacity(num_matches);
    for i in 0..num_matches {
        let idx1 = fm_view[[i, 0]] as usize;
        let idx2 = fm_view[[i, 1]] as usize;
        let kpt1 = extract_kpt(&kpts1_view, idx1);
        let kpt2 = extract_kpt(&kpts2_view, idx2);
        invvr1_list.push(inv_v_mat(&kpt1));
        invvr2_list.push(inv_v_mat(&kpt2));
    }

    let out_inliers = PyArray1::<bool>::zeros(py, [num_matches], false);
    let out_errors = PyArray2::<f64>::zeros(py, [3, num_matches], false);
    let out_mat = PyArray2::<f64>::zeros(py, [3, 3], false);

    let mut best_weight = f64::NEG_INFINITY;
    let mut best_inliers = vec![false; num_matches];
    let mut best_errors = vec![0.0_f64; num_matches * 3];
    let mut best_mat = Mat3 {
        data: [[0.0; 3]; 3],
    };

    let fs_view = fs.as_array();

    for i in 0..num_matches {
        let aff = invvr2_list[i].mul(&inv_affine(&invvr1_list[i]));
        let mut weight = 0.0_f64;
        let mut tmp_inliers = vec![false; num_matches];
        let mut tmp_errors = vec![0.0_f64; num_matches * 3];
        for j in 0..num_matches {
            let invvr1_mt = aff.mul(&invvr1_list[j]);
            let xy_err = xy_distance(&invvr1_mt, &invvr2_list[j]);
            let ori_err = ori_distance(&invvr1_mt, &invvr2_list[j]);
            let scale_err = det_distance(&invvr1_mt, &invvr2_list[j]);
            tmp_errors[(0 * num_matches) + j] = xy_err;
            tmp_errors[(1 * num_matches) + j] = ori_err;
            tmp_errors[(2 * num_matches) + j] = scale_err;
            let is_inlier =
                xy_err < xy_thresh_sqrd && scale_err < scale_thresh_sqrd && ori_err < ori_thresh;
            tmp_inliers[j] = is_inlier;
            if is_inlier {
                weight += fs_view[j];
            }
        }

        if weight >= best_weight {
            best_weight = weight;
            best_inliers = tmp_inliers;
            best_errors = tmp_errors;
            best_mat = aff;
        }
    }

    let mut inliers_view = unsafe { out_inliers.as_array_mut() };
    for (i, val) in best_inliers.iter().enumerate() {
        inliers_view[i] = *val;
    }

    let mut errors_view = unsafe { out_errors.as_array_mut() };
    for i in 0..3 {
        for j in 0..num_matches {
            errors_view[[i, j]] = best_errors[(i * num_matches) + j];
        }
    }

    let mut mat_view = unsafe { out_mat.as_array_mut() };
    for r in 0..3 {
        for c in 0..3 {
            mat_view[[r, c]] = best_mat.data[r][c];
        }
    }

    Ok((out_inliers.to_owned(), out_errors.to_owned(), out_mat.to_owned()))
}

#[pymodule]
fn _sver(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(get_affine_inliers, m)?)?;
    m.add_function(wrap_pyfunction!(get_best_affine_inliers, m)?)?;
    Ok(())
}
