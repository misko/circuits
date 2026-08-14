#!/usr/bin/env python3
"""Run upstream easyeda2kicad with a configurable current browser User-Agent.

This is deliberately a compatibility shim, not a fork. It imports the already
installed upstream package, changes only the HTTP User-Agent created by
``EasyedaApi``, then delegates every argument and conversion byte to upstream's
normal ``main`` function.

EasyEDA currently rejects easyeda2kicad 1.0.1's pinned Chrome/120 string with
HTTP 403 but accepts Chrome/146. Override ``JLC_TWIN_USER_AGENT`` when that
policy changes again; the default is a measured compatibility value, not an
assertion about browser identity.
"""
from __future__ import annotations

import os
import sys

from easyeda2kicad.easyeda.easyeda_api import EasyedaApi


DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"
)
_original_init = EasyedaApi.__init__


def _compat_init(self, *args, **kwargs):
    _original_init(self, *args, **kwargs)
    self.headers["User-Agent"] = os.environ.get(
        "JLC_TWIN_USER_AGENT", DEFAULT_USER_AGENT
    )


EasyedaApi.__init__ = _compat_init

from easyeda2kicad.__main__ import main  # noqa: E402


if __name__ == "__main__":
    sys.exit(main())
