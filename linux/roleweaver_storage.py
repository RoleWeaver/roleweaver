"""Compatibility import for packaged atomic storage."""

import os as _bootstrap_os
import sys as _bootstrap_sys

_bootstrap_root = _bootstrap_os.path.dirname(__file__)
for _bootstrap_src in (
    _bootstrap_os.path.join(_bootstrap_root, "src"),
    _bootstrap_os.path.join(_bootstrap_root, "..", "src"),
):
    _bootstrap_src = _bootstrap_os.path.abspath(_bootstrap_src)
    if _bootstrap_os.path.isdir(_bootstrap_src) and _bootstrap_src not in _bootstrap_sys.path:
        _bootstrap_sys.path.insert(0, _bootstrap_src)
        break

from roleweaver.storage import atomic as _implementation  # noqa: E402

_bootstrap_sys.modules[__name__] = _implementation
