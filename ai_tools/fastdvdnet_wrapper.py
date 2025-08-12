# -*- coding: utf-8 -*-
"""
FastDVDnet Wrapper Module
FastDVDnet ラッパーモジュール
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class FastDVDnetWrapper:
    """FastDVDnet ラッパークラス"""
    
    def __init__(self, fastdvdnet_path: Optional[str] = None):
        self.fastdvdnet_path = fastdvdnet_path or "fastdvdnet/fastdvdnet.py"
        self.available = self._check_availability()
        
        if self.available:
            logger.info(f"FastDVDnet利用可能: {self.fastdvdnet_path}")
        else:
            logger.warning("FastDVDnet未対応")
    
    def _check_availability(self) -> bool:
        """利用可能性チェック"""
        return Path(self.fastdvdnet_path).exists()
    
    def denoise_video(self, input_path: str, output_path: str, 
                     noise_level: float = 1.0) -> bool:
        """動画ノイズ除去"""
        if not self.available:
            logger.error("FastDVDnet未対応")
            return False
        
        try:
            cmd = ["python", self.fastdvdnet_path, 
                   "-i", input_path, "-o", output_path,
                   "--noise_level", str(noise_level)]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"FastDVDnetエラー: {e}")
            return False
    
    def denoise_image(self, input_path: str, output_path: str,
                     noise_level: float = 1.0) -> bool:
        """画像ノイズ除去"""
        if not self.available:
            return False
        
        try:
            cmd = ["python", self.fastdvdnet_path,
                   "-i", input_path, "-o", output_path,
                   "--noise_level", str(noise_level)]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"FastDVDnet画像処理エラー: {e}")
            return False
