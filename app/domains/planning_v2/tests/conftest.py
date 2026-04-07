"""
conftest.py — 让 planning_v2 tests 目录独立于 __init__.py 的副作用。

step08_daily_constraints 在模块级使用 astral.LocationInfo 但未做 guard，
导致 __init__.py 无法正常导入。CP1 测试只需要 Step 1-4，
这里通过 sys.modules mock 规避 step08 的导入错误。
"""

import sys
from unittest.mock import MagicMock


def _patch_astral_if_missing():
    try:
        from astral import LocationInfo  # noqa: F401
    except ImportError:
        # astral 未安装，注入 mock 让 step08 能正常加载
        mock_astral = MagicMock()
        mock_astral.LocationInfo = MagicMock(return_value=MagicMock())
        sys.modules["astral"] = mock_astral
        sys.modules["astral.sun"] = MagicMock()


_patch_astral_if_missing()
