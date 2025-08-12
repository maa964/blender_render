# -*- coding: utf-8 -*-
"""
Real-ESRGAN Wrapper Module  
Real-ESRGAN ラッパーモジュール
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class RealESRGANWrapper:
    """Real-ESRGAN ラッパークラス"""
    
    def __init__(self, realesrgan_path: Optional[str] = None):
        self.realesrgan_path = realesrgan_path or self._find_realesrgan()
        self.available = self._check_availability()
        
        if self.available:
            logger.info(f"Real-ESRGAN利用可能: {self.realesrgan_path}")
        else:
            logger.warning("Real-ESRGAN未対応")
    
    def _find_realesrgan(self) -> str:
        """Real-ESRGAN パス自動検出"""
        candidates = [
            "realesrgan-ncnn-vulkan",
            "realesrgan-ncnn-vulkan.exe",
            "realesrgan-ncnn-vulkan/realesrgan-ncnn-vulkan.exe"
        ]
        
        for path in candidates:
            if Path(path).exists():
                return path
        
        return ""
    
    def _check_availability(self) -> bool:
        """利用可能性チェック"""
        return bool(self.realesrgan_path and Path(self.realesrgan_path).exists())
    
    def upscale_image(self, input_path: str, output_path: str, 
                     scale: int = 2, model: str = "realesrgan-x4plus-anime",
                     use_gpu: bool = True) -> bool:
        """画像アップスケール"""
        if not self.available:
            logger.error("Real-ESRGAN未対応")
            return False
        
        try:
            cmd = [self.realesrgan_path, "-i", input_path, "-o", output_path, 
                   "-n", model, "-s", str(scale)]
            
            if not use_gpu:
                cmd.extend(["-g", "-1"])  # CPU mode
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Real-ESRGANエラー: {e}")
            return False
