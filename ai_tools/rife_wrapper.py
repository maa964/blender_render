# -*- coding: utf-8 -*-
"""
RIFE Wrapper Module
RIFE フレーム補間ラッパーモジュール  
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class RIFEWrapper:
    """RIFE ラッパークラス"""
    
    def __init__(self, rife_path: Optional[str] = None):
        self.rife_path = rife_path or self._find_rife()
        self.available = self._check_availability()
        
        if self.available:
            logger.info(f"RIFE利用可能: {self.rife_path}")
        else:
            logger.warning("RIFE未対応")
    
    def _find_rife(self) -> str:
        """RIFE パス自動検出"""
        candidates = [
            "rife-ncnn-vulkan",
            "rife-ncnn-vulkan.exe", 
            "rife-ncnn-vulkan/rife-ncnn-vulkan.exe"
        ]
        
        for path in candidates:
            if Path(path).exists():
                return path
        
        return ""
    
    def _check_availability(self) -> bool:
        """利用可能性チェック"""
        return bool(self.rife_path and Path(self.rife_path).exists())
    
    def interpolate_frames(self, input_dir: str, output_dir: str, 
                          use_gpu: bool = True) -> bool:
        """フレーム補間"""
        if not self.available:
            logger.error("RIFE未対応")
            return False
        
        try:
            cmd = [self.rife_path, "-i", input_dir, "-o", output_dir]
            
            if use_gpu:
                cmd.extend(["-g", "0"])  # GPU 0
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"RIFEエラー: {e}")
            return False

class FastDVDnetWrapper:
    """FastDVDnet ラッパークラス"""
    
    def __init__(self, fastdvdnet_path: Optional[str] = None):
        self.fastdvdnet_path = fastdvdnet_path or "fastdvdnet/fastdvdnet.py"
        self.available = self._check_availability()
    
    def _check_availability(self) -> bool:
        """利用可能性チェック"""
        return Path(self.fastdvdnet_path).exists()
    
    def denoise_video(self, input_path: str, output_path: str) -> bool:
        """動画ノイズ除去"""
        if not self.available:
            return False
        
        try:
            cmd = ["python", self.fastdvdnet_path, "-i", input_path, "-o", output_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            return result.returncode == 0
        except:
            return False
