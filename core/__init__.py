# -*- coding: utf-8 -*-
"""
Core module for Blender Render Pipeline
CUDA対応、PyPy最適化済みコアモジュール
"""

__version__ = "1.0.0"
__author__ = "Masahiro"

# UTF-8エンコーディング強制設定
import sys
import os
if sys.platform.startswith('win'):
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# PyPy最適化のための設定
import sys

PYPY_AVAILABLE = hasattr(sys, 'pypy_version_info')
if PYPY_AVAILABLE:
    try:
        import __pypy__
    except ImportError:
        PYPY_AVAILABLE = False

# 主要コンポーネントのインポート
from .blender_engine import BlenderEngine
from .cuda_accelerator import CUDAAccelerator
from .settings_manager import SettingsManager
from .file_manager import FileManager

__all__ = [
    'BlenderEngine',
    'CUDAAccelerator', 
    'SettingsManager',
    'FileManager',
    'PYPY_AVAILABLE'
]
