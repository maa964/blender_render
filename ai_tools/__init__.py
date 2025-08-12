# -*- coding: utf-8 -*-
"""
AI Tools module for Blender Render Pipeline
外部AI ツールのラッパー
"""

__version__ = "1.0.0"

from .oidn_wrapper import OIDNWrapper
from .realesrgan_wrapper import RealESRGANWrapper
from .rife_wrapper import RIFEWrapper
from .fastdvdnet_wrapper import FastDVDnetWrapper

__all__ = [
    'OIDNWrapper',
    'RealESRGANWrapper',
    'RIFEWrapper', 
    'FastDVDnetWrapper'
]
