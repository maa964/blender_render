# -*- coding: utf-8 -*-
"""
Frame Interpolation Processor (Python fallback version)
フレーム補間処理モジュール（Python版フォールバック）
"""

import os
import sys
import numpy as np
from typing import Optional, List, Tuple, Dict, Any
import logging

# UTF-8エンコーディング設定
if sys.platform.startswith('win'):
    os.environ['PYTHONIOENCODING'] = 'utf-8'

logger = logging.getLogger(__name__)

# OpenCV チェック
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logger.warning("OpenCV未対応 - フレーム補間機能制限")

class InterpolationProcessor:
    """フレーム補間処理クラス（Python版）"""
    
    def __init__(self):
        self.method = 'linear'
        self.quality = 'medium'
        
    def interpolate_frames(self, frame1: np.ndarray, frame2: np.ndarray, 
                         factor: int = 2) -> List[np.ndarray]:
        """フレーム補間処理"""
        if not CV2_AVAILABLE:
            logger.warning("OpenCV未対応 - 線形補間使用")
            return self._linear_interpolation(frame1, frame2, factor)
        
        try:
            return self._optical_flow_interpolation(frame1, frame2, factor)
        except Exception as e:
            logger.warning(f"オプティカルフロー補間失敗: {e} - 線形補間使用")
            return self._linear_interpolation(frame1, frame2, factor)
    
    def _linear_interpolation(self, frame1: np.ndarray, frame2: np.ndarray, 
                            factor: int) -> List[np.ndarray]:
        """線形補間"""
        result = []
        for i in range(1, factor):
            alpha = i / factor
            interpolated = cv2.addWeighted(frame1, 1-alpha, frame2, alpha, 0) if CV2_AVAILABLE else \
                          ((1-alpha) * frame1 + alpha * frame2).astype(frame1.dtype)
            result.append(interpolated)
        return result
    
    def _optical_flow_interpolation(self, frame1: np.ndarray, frame2: np.ndarray, 
                                  factor: int) -> List[np.ndarray]:
        """オプティカルフロー補間"""
        if not CV2_AVAILABLE:
            return self._linear_interpolation(frame1, frame2, factor)
        
        gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
        
        # オプティカルフロー計算
        flow = cv2.calcOpticalFlowPyrLK(gray1, gray2, None, None)
        
        result = []
        for i in range(1, factor):
            t = i / factor
            # 簡略化した補間（実際のRIFEアルゴリズムはより複雑）
            interpolated = self._warp_frame(frame1, frame2, flow, t)
            result.append(interpolated)
        
        return result
    
    def _warp_frame(self, frame1: np.ndarray, frame2: np.ndarray, 
                   flow: Any, t: float) -> np.ndarray:
        """フレームワープ処理"""
        # 簡略化実装
        alpha = t
        return cv2.addWeighted(frame1, 1-alpha, frame2, alpha, 0)

def interpolate_sequence(frames: List[np.ndarray], factor: int = 2) -> List[np.ndarray]:
    """フレームシーケンス補間"""
    processor = InterpolationProcessor()
    result = []
    
    for i in range(len(frames) - 1):
        result.append(frames[i])
        interpolated = processor.interpolate_frames(frames[i], frames[i+1], factor)
        result.extend(interpolated)
    
    result.append(frames[-1])  # 最後のフレーム追加
    return result
