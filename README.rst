vtool_ibeis_ext
==============

``vtool_ibeis_ext`` provides spatial verification helper functions backed by a
Rust extension module (PyO3 + abi3), while preserving the historical Python
wrapper API.

Stable API
----------

The following functions remain stable and importable from
``vtool_ibeis_ext.sver_c_wrapper``:

* ``get_affine_inliers_cpp``
* ``get_best_affine_inliers_cpp``

Install
-------

.. code-block:: bash

   pip install vtool_ibeis_ext

Development
-----------

.. code-block:: bash

   python -m pip install maturin pytest numpy
   python -m maturin build -o dist
   python -m pip install --force-reinstall dist/*.whl
   pytest -q tests
