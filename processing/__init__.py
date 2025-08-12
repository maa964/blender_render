# -*- coding: utf-8 -*-
"""
Processing module for Blender Render Pipeline
Numba・Cython最適化済み処理モジュール
"""

__version__ = "1.0.0"

# Numba/CUDA可用性チェック
try:
    import numba
    from numba import cuda
    NUMBA_AVAILABLE = True
    CUDA_AVAILABLE = cuda.is_available()
except ImportError:
    NUMBA_AVAILABLE = False
    CUDA_AVAILABLE = False

# Cython可用性チェック
try:
    import pyximport
    pyximport.install()
    CYTHON_AVAILABLE = True
except ImportError:
    CYTHON_AVAILABLE = False

# 処理モジュールのインポート
from .denoise_numba import DenoiseProcessor
from .upscale_numba import UpscaleProcessor
from .video_encoder import VideoEncoder

# Cythonモジュールの条件付きインポート
if CYTHON_AVAILABLE:
    try:
        from .interpolation_cython import InterpolationProcessor
    except ImportError:
        # Cythonモジュールが未ビルドの場合はPython版を使用
        from .interpolation_python import InterpolationProcessor
else:
    from .interpolation_python import InterpolationProcessor

__all__ = [
    'DenoiseProcessor',
    'UpscaleProcessor', 
    'InterpolationProcessor',
    'VideoEncoder',
    'NUMBA_AVAILABLE',
    'CUDA_AVAILABLE',
    'CYTHON_AVAILABLE'
]
