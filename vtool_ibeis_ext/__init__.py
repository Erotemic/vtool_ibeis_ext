"""Rust-backed spatial verification helpers."""

from __future__ import annotations

import importlib

__version__ = "1.0.0"
__author__ = "Jon Crall"
__author_email__ = "erotemic@gmail.com"
__url__ = "https://github.com/Erotemic/vtool_ibeis_ext"

__all__ = ["__version__", "_sver"]

try:
    _sver = importlib.import_module("._sver", __name__)
except Exception:
    try:
        _sver = importlib.import_module("_sver")
    except Exception:
        _sver = None
