from __future__ import annotations

import os
from unittest import mock

from hiagentcontrol.backends.ohmy_backend import default_ohmy_bin


def test_default_ohmy_bin_hac_env_override() -> None:
    with mock.patch.dict(os.environ, {"HAC_OHMY_BIN": "/custom/oh-my-openagent"}, clear=False):
        assert default_ohmy_bin() == "/custom/oh-my-openagent"


def test_default_ohmy_bin_prefers_openagent_on_path() -> None:
    with mock.patch.dict(os.environ, {}, clear=False):
        os.environ.pop("HAC_OHMY_BIN", None)
        with mock.patch("hiagentcontrol.backends.ohmy_backend.shutil.which") as which:
            which.side_effect = lambda name: (
                "/usr/bin/oh-my-openagent" if name == "oh-my-openagent" else None
            )
            assert default_ohmy_bin() == "/usr/bin/oh-my-openagent"


def test_default_ohmy_bin_bunx_fallback() -> None:
    with mock.patch.dict(os.environ, {}, clear=False):
        os.environ.pop("HAC_OHMY_BIN", None)
        with mock.patch("hiagentcontrol.backends.ohmy_backend.shutil.which", return_value=None):
            assert default_ohmy_bin() == "bunx oh-my-openagent@latest"
