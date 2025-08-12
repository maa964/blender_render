# -*- coding: utf-8 -*-
"""
GPU Detector Utility
GPU検出ユーティリティ
"""

import os
import sys
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class GPUDetector:
    """GPU検出クラス"""
    
    def __init__(self):
        self.gpu_info = self._detect_gpus()
    
    def _detect_gpus(self) -> Dict[str, Any]:
        """GPU検出"""
        info = {
            "cuda_available": False,
            "gpu_count": 0,
            "gpus": []
        }
        
        try:
            import torch
            if torch.cuda.is_available():
                info["cuda_available"] = True
                info["gpu_count"] = torch.cuda.device_count()
                
                for i in range(info["gpu_count"]):
                    gpu_props = torch.cuda.get_device_properties(i)
                    gpu_info = {
                        "id": i,
                        "name": gpu_props.name,
                        "memory_total": gpu_props.total_memory,
                        "compute_capability": f"{gpu_props.major}.{gpu_props.minor}"
                    }
                    info["gpus"].append(gpu_info)
        
        except ImportError:
            logger.warning("PyTorch未インストール - GPU検出不可")
        except Exception as e:
            logger.error(f"GPU検出エラー: {e}")
        
        return info
    
    def get_gpu_info(self) -> Dict[str, Any]:
        """GPU情報取得"""
        return self.gpu_info
    
    def is_cuda_available(self) -> bool:
        """CUDA利用可能性チェック"""
        return self.gpu_info["cuda_available"]
    
    def get_gpu_count(self) -> int:
        """GPU数取得"""
        return self.gpu_info["gpu_count"]
