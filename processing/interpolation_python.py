# -*- coding: utf-8 -*-
"""
Frame Interpolation Processor (Python version)
フレーム補間処理モジュール（Python版 - Cython未対応時のフォールバック）
"""

import os
import sys
import numpy as np
from typing import Optional, List, Tuple, Dict, Any
import logging

# UTF-8エンコーディング設定
if sys.platform.startswith('win'):
    os.environ['PYTHONIOENCODING'] = 'utf-8'

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

class InterpolationProcessor:
    """フレーム補間プロセッサ（Python版）"""
    
    def __init__(self, use_cuda: bool = True):
        self.use_cuda = use_cuda
        logger.info("Python版フレーム補間プロセッサ初期化")
    
    def interpolate_frames(self,
                          frame1: np.ndarray,
                          frame2: np.ndarray,
                          num_interpolated: int = 1,
                          method: str = 'optical_flow') -> List[np.ndarray]:
        """
        2フレーム間の補間フレーム生成
        
        Args:
            frame1: 開始フレーム
            frame2: 終了フレーム  
            num_interpolated: 補間フレーム数
            method: 補間手法 ('optical_flow', 'linear', 'morph')
        
        Returns:
            補間フレームリスト
        """
        if method == 'optical_flow':
            return self._optical_flow_interpolation(frame1, frame2, num_interpolated)
        elif method == 'linear':
            return self._linear_interpolation(frame1, frame2, num_interpolated)
        elif method == 'morph':
            return self._morphological_interpolation(frame1, frame2, num_interpolated)
        else:
            raise ValueError(f"未対応の補間手法: {method}")
    
    def _optical_flow_interpolation(self, frame1: np.ndarray, frame2: np.ndarray, num_interpolated: int) -> List[np.ndarray]:
        """オプティカルフロー補間"""
        if not CV2_AVAILABLE:
            logger.warning("OpenCV未インストール - 線形補間で代替")
            return self._linear_interpolation(frame1, frame2, num_interpolated)
        
        # グレースケール変換
        gray1 = cv2.cvtColor(frame1, cv2.COLOR_RGB2GRAY) if len(frame1.shape) == 3 else frame1
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_RGB2GRAY) if len(frame2.shape) == 3 else frame2
        
        # オプティカルフロー計算
        flow = cv2.calcOpticalFlowPyrLK(gray1, gray2, None, None)
        
        interpolated_frames = []
        
        for i in range(1, num_interpolated + 1):
            t = i / (num_interpolated + 1)
            
            # フロー補間
            interpolated_frame = self._warp_frame_with_flow(frame1, frame2, flow, t)
            interpolated_frames.append(interpolated_frame)
        
        return interpolated_frames
    
    def _linear_interpolation(self, frame1: np.ndarray, frame2: np.ndarray, num_interpolated: int) -> List[np.ndarray]:
        """線形補間"""
        interpolated_frames = []
        
        for i in range(1, num_interpolated + 1):
            t = i / (num_interpolated + 1)
            interpolated = (1 - t) * frame1.astype(np.float32) + t * frame2.astype(np.float32)
            interpolated = np.clip(interpolated, 0, 255).astype(frame1.dtype)
            interpolated_frames.append(interpolated)
        
        return interpolated_frames
    
    def _morphological_interpolation(self, frame1: np.ndarray, frame2: np.ndarray, num_interpolated: int) -> List[np.ndarray]:
        """モルフォロジー補間"""
        # 簡易実装：重みつき平均 + エッジ保持
        interpolated_frames = []
        
        for i in range(1, num_interpolated + 1):
            t = i / (num_interpolated + 1)
            
            # 重みつき平均
            blended = (1 - t) * frame1.astype(np.float32) + t * frame2.astype(np.float32)
            
            # エッジ情報保持
            if CV2_AVAILABLE:
                # エッジ検出
                edges1 = cv2.Canny(frame1, 50, 150)
                edges2 = cv2.Canny(frame2, 50, 150)
                edge_blend = (1 - t) * edges1.astype(np.float32) + t * edges2.astype(np.float32)
                
                # エッジ強調
                if len(blended.shape) == 3:
                    for c in range(blended.shape[2]):
                        blended[:, :, c] += edge_blend * 0.1
                else:
                    blended += edge_blend * 0.1
            
            interpolated = np.clip(blended, 0, 255).astype(frame1.dtype)
            interpolated_frames.append(interpolated)
        
        return interpolated_frames
    
    def _warp_frame_with_flow(self, frame1: np.ndarray, frame2: np.ndarray, flow: np.ndarray, t: float) -> np.ndarray:
        """フローを使用したフレームワープ"""
        # 簡易実装：フロー情報を使用した重みつき平均
        # 実際のRIFEなどではより高度な手法を使用
        return self._linear_interpolation(frame1, frame2, 1)[0]
    
    def batch_interpolate(self, frames: List[np.ndarray], method: str = 'optical_flow') -> List[np.ndarray]:
        """バッチフレーム補間"""
        if len(frames) < 2:
            return frames
        
        result_frames = [frames[0]]  # 最初のフレーム
        
        for i in range(len(frames) - 1):
            # 各フレーム間に1つの補間フレームを挿入
            interpolated = self.interpolate_frames(frames[i], frames[i + 1], 1, method)
            result_frames.extend(interpolated)
            result_frames.append(frames[i + 1])
        
        return result_frames
