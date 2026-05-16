"""依赖兼容性补丁.

basicsr 1.4.2 在新版 torchvision (>=0.17) 上会因为
`torchvision.transforms.functional_tensor` 模块被移除而无法导入.

本模块在 import basicsr / gfpgan / realesrgan 之前打补丁, 把
`functional_tensor` 重定向到现存的 `functional` 模块.

调用方法: 在 cli.py 最顶部 `from . import compat  # noqa`
"""
from __future__ import annotations

import sys
import types


def _patch_torchvision_functional_tensor() -> None:
    """为 basicsr 提供缺失的 torchvision.transforms.functional_tensor."""
    try:
        import torchvision.transforms.functional_tensor  # noqa: F401
        return  # 旧版 torchvision, 无需打补丁
    except ModuleNotFoundError:
        pass

    try:
        import torchvision.transforms.functional as _functional
    except Exception:
        # torchvision 还没装, 让后续 import 自然失败
        return

    fake = types.ModuleType("torchvision.transforms.functional_tensor")
    # basicsr 实际只用到 rgb_to_grayscale
    if hasattr(_functional, "rgb_to_grayscale"):
        fake.rgb_to_grayscale = _functional.rgb_to_grayscale
    sys.modules["torchvision.transforms.functional_tensor"] = fake


_patch_torchvision_functional_tensor()
