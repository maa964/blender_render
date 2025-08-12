# -*- coding: utf-8 -*-
"""
OIDN Wrapper Module
Intel Open Image Denoise ラッパーモジュール
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class OIDNWrapper:
    """OIDN（Intel Open Image Denoise）ラッパークラス"""
    
    def __init__(self, oidn_path: Optional[str] = None):
        self.oidn_path = oidn_path or self._find_oidn()
        self.available = self._check_availability()
        
        if self.available:
            logger.info(f"OIDN利用可能: {self.oidn_path}")
        else:
            logger.warning("OIDN未対応")
    
    def _find_oidn(self) -> str:
        """OIDN パス自動検出"""
        candidates = [
            "oidnDenoise",
            "oidnDenoise.exe", 
            "C:/oidn/bin/oidnDenoise.exe",
            "/usr/local/bin/oidnDenoise",
            "/opt/oidn/bin/oidnDenoise"
        ]
        
        for path in candidates:
            if self._test_oidn_path(path):
                return path
        
        return ""
    
    def _test_oidn_path(self, path: str) -> bool:
        """OIDN パステスト"""
        try:
            result = subprocess.run([path, "--help"], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def _check_availability(self) -> bool:
        """OIDN利用可能性チェック"""
        return bool(self.oidn_path and Path(self.oidn_path).exists())
    
    def denoise_image(self, input_path: str, output_path: str, 
                     use_cuda: bool = False, **kwargs) -> bool:
        """画像ノイズ除去"""
        if not self.available:
            logger.error("OIDN未対応")
            return False
        
        try:
            cmd = [self.oidn_path, "--hdr", "-i", input_path, "-o", output_path]
            
            if use_cuda:
                cmd.extend(["--device", "cuda"])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                logger.debug(f"OIDN処理完了: {input_path} -> {output_path}")
                return True
            else:
                logger.error(f"OIDN処理失敗: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"OIDNエラー: {e}")
            return False
