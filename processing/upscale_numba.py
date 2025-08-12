# -*- coding: utf-8 -*-
"""
Upscale Processor with Numba Optimization
Numba最適化アップスケール処理モジュール
"""

import os
import sys
import numpy as np
from typing import Optional, Union, Tuple, List
import logging

# UTF-8エンコーディング設定
if sys.platform.startswith('win'):
    os.environ['PYTHONIOENCODING'] = 'utf-8'

try:
    import numba
    from numba import jit, prange
    NUMBA_AVAILABLE = True
except ImportError:
    NUMBA_AVAILABLE = False

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

logger = logging.getLogger(__name__)

class UpscaleProcessor:
    """Numba最適化アップスケールプロセッサ"""
    
    def __init__(self, use_cuda: bool = True):
        self.use_cuda = use_cuda
        logger.info("Numba最適化アップスケールプロセッサ初期化")
    
    def upscale_image(self, image: np.ndarray, factor: int = 2, method: str = 'bicubic') -> np.ndarray:
        """画像アップスケール"""
        if method == 'bicubic' and CV2_AVAILABLE:
            return self._opencv_upscale(image, factor)
        elif method == 'numba_bilinear':
            return self._numba_bilinear_upscale(image, factor)
        else:
            return self._simple_upscale(image, factor)
    
    def _opencv_upscale(self, image: np.ndarray, factor: int) -> np.ndarray:
        """OpenCV バイキューブアップスケール"""
        height, width = image.shape[:2]
        new_height, new_width = height * factor, width * factor
        return cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
    
    @staticmethod
    @jit(nopython=True, parallel=True)
    def _numba_bilinear_upscale(image: np.ndarray, factor: int) -> np.ndarray:
        """Numba最適化バイリニアアップスケール"""
        height, width = image.shape[:2]
        new_height, new_width = height * factor, width * factor
        
        if len(image.shape) == 3:
            channels = image.shape[2]
            result = np.zeros((new_height, new_width, channels), dtype=image.dtype)
            
            for c in prange(channels):
                for y in prange(new_height):
                    for x in prange(new_width):
                        orig_y = y / factor
                        orig_x = x / factor
                        
                        y1 = int(orig_y)
                        x1 = int(orig_x)
                        y2 = min(y1 + 1, height - 1)
                        x2 = min(x1 + 1, width - 1)
                        
                        dy = orig_y - y1
                        dx = orig_x - x1
                        
                        val = (image[y1, x1, c] * (1 - dx) * (1 - dy) +
                               image[y1, x2, c] * dx * (1 - dy) +
                               image[y2, x1, c] * (1 - dx) * dy +
                               image[y2, x2, c] * dx * dy)
                        
                        result[y, x, c] = val
        else:
            result = np.zeros((new_height, new_width), dtype=image.dtype)
            for y in prange(new_height):
                for x in prange(new_width):
                    orig_y = y / factor
                    orig_x = x / factor
                    
                    y1 = int(orig_y)
                    x1 = int(orig_x)
                    y2 = min(y1 + 1, height - 1)
                    x2 = min(x1 + 1, width - 1)
                    
                    dy = orig_y - y1
                    dx = orig_x - x1
                    
                    val = (image[y1, x1] * (1 - dx) * (1 - dy) +
                           image[y1, x2] * dx * (1 - dy) +
                           image[y2, x1] * (1 - dx) * dy +
                           image[y2, x2] * dx * dy)
                    
                    result[y, x] = val
        
        return result
    
    def _simple_upscale(self, image: np.ndarray, factor: int) -> np.ndarray:
        """簡易アップスケール（最近傍法）"""
        return np.repeat(np.repeat(image, factor, axis=0), factor, axis=1)
    
    def upscale_file(self, input_path: str, output_path: str, factor: int = 2) -> bool:
        """ファイルアップスケール"""
        try:
            if PIL_AVAILABLE:
                image = np.array(Image.open(input_path))
                upscaled = self.upscale_image(image, factor)
                Image.fromarray(upscaled).save(output_path)
                return True
            return False
        except Exception as e:
            logger.error(f"アップスケールエラー: {e}")
            return False
