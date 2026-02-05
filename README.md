# vtool_ibeis_ext

Rust-backed spatial verification helpers with stable Python wrappers.

## Install

```bash
pip install vtool_ibeis_ext
```

## Usage

```python
import numpy as np
from vtool_ibeis_ext import sver_c_wrapper

kpts1 = np.zeros((10, 6), dtype=np.float64)
kpts2 = np.zeros((10, 6), dtype=np.float64)
fm = np.array([[0, 0], [1, 1]], dtype=np.int64)
fs = np.ones((2,), dtype=np.float64)

inliers, errors, mats = sver_c_wrapper.get_affine_inliers_cpp(
    kpts1, kpts2, fm, fs, xy_thresh_sqrd=10.0, scale_thresh_sqrd=10.0, ori_thresh=1.0
)
```

## Development

Build locally with maturin:

```bash
maturin develop
pytest
```
