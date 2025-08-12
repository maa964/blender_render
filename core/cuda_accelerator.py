# -*- coding: utf-8 -*-
"""
CUDA Accelerator Module
CUDA機能の検出、管理、GPU負荷分散を行うモジュール
"""

import os
import sys
import logging
from typing import Optional, List, Dict, Any, Tuple
import psutil

# UTF-8エンコーディング設定
if sys.platform.startswith('win'):
    os.environ['PYTHONIOENCODING'] = 'utf-8'

logger = logging.getLogger(__name__)

class CUDAAccelerator:
    """CUDA加速管理クラス"""
    
    def __init__(self):
        self.cuda_available = False
        self.device_count = 0
        self.devices: List[Dict[str, Any]] = []
        self.current_device = 0
        self.memory_threshold = 0.8  # 80%まで使用可能
        self.torch_available = False
        self.cupy_available = False
        self.numba_cuda_available = False
        
        self._initialize_cuda()
    
    def _initialize_cuda(self) -> None:
        """CUDA環境の初期化と検出"""
        try:
            # PyTorch CUDA検出
            import torch
            self.torch_available = True
            if torch.cuda.is_available():
                self.cuda_available = True
                self.device_count = torch.cuda.device_count()
                self._detect_devices_torch()
                logger.info(f"PyTorch CUDA検出: {self.device_count}台のGPU")
            else:
                logger.warning("PyTorch: CUDA未対応")
        except ImportError:
            logger.warning("PyTorch未インストール")
        
        try:
            # CuPy検出
            import cupy
            self.cupy_available = True
            if not self.cuda_available:
                self.cuda_available = True
                self.device_count = cupy.cuda.runtime.getDeviceCount()
                self._detect_devices_cupy()
                logger.info(f"CuPy CUDA検出: {self.device_count}台のGPU")
        except ImportError:
            logger.warning("CuPy未インストール")
        except Exception as e:
            logger.warning(f"CuPy初期化エラー: {e}")
        
        try:
            # Numba CUDA検出
            from numba import cuda
            self.numba_cuda_available = cuda.is_available()
            if self.numba_cuda_available and not self.cuda_available:
                self.cuda_available = True
                self.device_count = len(cuda.gpus)
                self._detect_devices_numba()
                logger.info(f"Numba CUDA検出: {self.device_count}台のGPU")
        except ImportError:
            logger.warning("Numba CUDA未インストール")
        except Exception as e:
            logger.warning(f"Numba CUDA初期化エラー: {e}")
        
        if not self.cuda_available:
            logger.info("CUDA未対応 - CPU使用モードで動作")
    
    def _detect_devices_torch(self) -> None:
        """PyTorchを使用してGPUデバイスを検出"""
        try:
            import torch
            for i in range(self.device_count):
                device_props = torch.cuda.get_device_properties(i)
                memory_total = device_props.total_memory
                memory_free = memory_total - torch.cuda.memory_allocated(i)
                
                device_info = {
                    'id': i,
                    'name': device_props.name,
                    'compute_capability': f"{device_props.major}.{device_props.minor}",
                    'memory_total': memory_total,
                    'memory_free': memory_free,
                    'memory_used': torch.cuda.memory_allocated(i),
                    'temperature': self._get_gpu_temperature(i),
                    'utilization': self._get_gpu_utilization(i)
                }
                self.devices.append(device_info)
        except Exception as e:
            logger.error(f"PyTorchデバイス検出エラー: {e}")
    
    def _detect_devices_cupy(self) -> None:
        """CuPyを使用してGPUデバイスを検出"""
        try:
            import cupy
            for i in range(self.device_count):
                with cupy.cuda.Device(i):
                    mempool = cupy.get_default_memory_pool()
                    memory_info = cupy.cuda.runtime.memGetInfo()
                    
                    device_info = {
                        'id': i,
                        'name': cupy.cuda.runtime.getDeviceProperties(i)['name'].decode('utf-8'),
                        'compute_capability': f"{cupy.cuda.runtime.getDeviceProperties(i)['major']}.{cupy.cuda.runtime.getDeviceProperties(i)['minor']}",
                        'memory_total': memory_info[1],
                        'memory_free': memory_info[0],
                        'memory_used': memory_info[1] - memory_info[0],
                        'temperature': self._get_gpu_temperature(i),
                        'utilization': self._get_gpu_utilization(i)
                    }
                    self.devices.append(device_info)
        except Exception as e:
            logger.error(f"CuPyデバイス検出エラー: {e}")
    
    def _detect_devices_numba(self) -> None:
        """Numbaを使用してGPUデバイスを検出"""
        try:
            from numba import cuda
            for i, gpu in enumerate(cuda.gpus):
                device_info = {
                    'id': i,
                    'name': gpu.name.decode('utf-8'),
                    'compute_capability': f"{gpu.compute_capability[0]}.{gpu.compute_capability[1]}",
                    'memory_total': gpu.total_memory,
                    'memory_free': gpu.total_memory,  # Numbaでは詳細メモリ情報取得困難
                    'memory_used': 0,
                    'temperature': self._get_gpu_temperature(i),
                    'utilization': self._get_gpu_utilization(i)
                }
                self.devices.append(device_info)
        except Exception as e:
            logger.error(f"Numbaデバイス検出エラー: {e}")
    
    def _get_gpu_temperature(self, device_id: int) -> Optional[float]:
        """GPU温度を取得（nvidia-smi経由）"""
        try:
            import subprocess
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=temperature.gpu', '--format=csv,noheader,nounits', f'--id={device_id}'],
                capture_output=True, text=True, encoding='utf-8'
            )
            if result.returncode == 0:
                return float(result.stdout.strip())
        except Exception:
            pass
        return None
    
    def _get_gpu_utilization(self, device_id: int) -> Optional[float]:
        """GPU使用率を取得（nvidia-smi経由）"""
        try:
            import subprocess
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=utilization.gpu', '--format=csv,noheader,nounits', f'--id={device_id}'],
                capture_output=True, text=True, encoding='utf-8'
            )
            if result.returncode == 0:
                return float(result.stdout.strip())
        except Exception:
            pass
        return None
    
    def get_best_device(self) -> int:
        """最適なGPUデバイスを選択"""
        if not self.cuda_available or not self.devices:
            return -1  # CPU使用
        
        # メモリ使用量と温度を考慮して最適デバイスを選択
        best_device = 0
        best_score = float('-inf')
        
        for device in self.devices:
            memory_usage_ratio = device['memory_used'] / device['memory_total']
            memory_score = (1.0 - memory_usage_ratio) * 100
            
            temp_score = 0
            if device['temperature'] is not None:
                # 温度が低いほど高スコア（85℃を上限として正規化）
                temp_score = max(0, (85 - device['temperature']) / 85 * 100)
            
            util_score = 0
            if device['utilization'] is not None:
                # 使用率が低いほど高スコア
                util_score = (100 - device['utilization'])
            
            # 総合スコア計算（メモリ重視）
            total_score = memory_score * 0.6 + temp_score * 0.2 + util_score * 0.2
            
            if total_score > best_score:
                best_score = total_score
                best_device = device['id']
        
        self.current_device = best_device
        logger.info(f"最適デバイス選択: GPU {best_device} (スコア: {best_score:.1f})")
        return best_device
    
    def check_memory_available(self, required_memory: int, device_id: Optional[int] = None) -> bool:
        """指定メモリ量が利用可能かチェック"""
        if not self.cuda_available:
            return True  # CPU使用時は常にTrue
        
        target_device = device_id if device_id is not None else self.current_device
        
        if target_device >= len(self.devices):
            return False
        
        device = self.devices[target_device]
        available_memory = device['memory_free'] * self.memory_threshold
        
        return required_memory <= available_memory
    
    def get_optimal_batch_size(self, base_batch_size: int, memory_per_item: int, device_id: Optional[int] = None) -> int:
        """メモリ容量に基づいて最適なバッチサイズを計算"""
        if not self.cuda_available:
            return base_batch_size
        
        target_device = device_id if device_id is not None else self.current_device
        
        if target_device >= len(self.devices):
            return base_batch_size
        
        device = self.devices[target_device]
        available_memory = device['memory_free'] * self.memory_threshold
        
        max_batch_size = int(available_memory // memory_per_item)
        optimal_batch_size = min(base_batch_size, max_batch_size)
        
        return max(1, optimal_batch_size)  # 最低1は保証
    
    def set_device(self, device_id: int) -> bool:
        """使用デバイスを設定"""
        if not self.cuda_available or device_id >= len(self.devices):
            return False
        
        try:
            if self.torch_available:
                import torch
                torch.cuda.set_device(device_id)
            
            if self.cupy_available:
                import cupy
                cupy.cuda.Device(device_id).use()
            
            self.current_device = device_id
            logger.info(f"デバイス設定: GPU {device_id}")
            return True
            
        except Exception as e:
            logger.error(f"デバイス設定エラー: {e}")
            return False
    
    def clear_cache(self, device_id: Optional[int] = None) -> None:
        """GPU メモリキャッシュをクリア"""
        target_device = device_id if device_id is not None else self.current_device
        
        try:
            if self.torch_available:
                import torch
                if device_id is not None:
                    with torch.cuda.device(device_id):
                        torch.cuda.empty_cache()
                else:
                    torch.cuda.empty_cache()
            
            if self.cupy_available:
                import cupy
                if device_id is not None:
                    with cupy.cuda.Device(device_id):
                        cupy.get_default_memory_pool().free_all_blocks()
                else:
                    cupy.get_default_memory_pool().free_all_blocks()
            
            logger.info(f"GPU {target_device} メモリキャッシュクリア完了")
            
        except Exception as e:
            logger.error(f"メモリキャッシュクリアエラー: {e}")
    
    def get_device_info(self, device_id: Optional[int] = None) -> Dict[str, Any]:
        """デバイス情報を取得"""
        if not self.cuda_available:
            return {
                'cuda_available': False,
                'device_type': 'CPU',
                'device_count': 0
            }
        
        target_device = device_id if device_id is not None else self.current_device
        
        if target_device >= len(self.devices):
            return {'error': 'Invalid device ID'}
        
        device = self.devices[target_device].copy()
        device.update({
            'cuda_available': True,
            'device_type': 'CUDA',
            'device_count': self.device_count,
            'current_device': self.current_device,
            'torch_available': self.torch_available,
            'cupy_available': self.cupy_available,
            'numba_cuda_available': self.numba_cuda_available
        })
        
        return device
    
    def monitor_gpu_usage(self) -> List[Dict[str, Any]]:
        """GPU使用状況をリアルタイム監視"""
        if not self.cuda_available:
            return []
        
        usage_info = []
        
        for i, device in enumerate(self.devices):
            current_info = {
                'device_id': i,
                'name': device['name'],
                'temperature': self._get_gpu_temperature(i),
                'utilization': self._get_gpu_utilization(i),
                'memory_info': self._get_current_memory_info(i)
            }
            usage_info.append(current_info)
        
        return usage_info
    
    def _get_current_memory_info(self, device_id: int) -> Dict[str, int]:
        """現在のメモリ情報を取得"""
        try:
            if self.torch_available:
                import torch
                with torch.cuda.device(device_id):
                    memory_allocated = torch.cuda.memory_allocated(device_id)
                    memory_cached = torch.cuda.memory_reserved(device_id)
                    memory_total = torch.cuda.get_device_properties(device_id).total_memory
                    memory_free = memory_total - memory_allocated
                    
                    return {
                        'total': memory_total,
                        'allocated': memory_allocated,
                        'cached': memory_cached,
                        'free': memory_free
                    }
            
            elif self.cupy_available:
                import cupy
                with cupy.cuda.Device(device_id):
                    memory_info = cupy.cuda.runtime.memGetInfo()
                    return {
                        'total': memory_info[1],
                        'free': memory_info[0],
                        'allocated': memory_info[1] - memory_info[0],
                        'cached': 0
                    }
        except Exception as e:
            logger.error(f"メモリ情報取得エラー: {e}")
        
        return {'total': 0, 'free': 0, 'allocated': 0, 'cached': 0}
    
    def is_compatible_for_processing(self, processing_type: str) -> bool:
        """処理タイプに対するCUDA互換性をチェック"""
        if not self.cuda_available:
            return False
        
        compatibility_map = {
            'denoise': self.torch_available or self.cupy_available,
            'upscale': self.torch_available,
            'interpolation': self.torch_available,
            'video_encode': True,  # FFmpegのCUDA対応
            'general': self.cuda_available
        }
        
        return compatibility_map.get(processing_type, False)
    
    def get_cuda_command_args(self, processing_type: str) -> List[str]:
        """処理タイプに応じたCUDAコマンド引数を生成"""
        if not self.cuda_available:
            return []
        
        args = []
        
        if processing_type == 'oidn':
            args.extend(['--device', 'cuda'])
        elif processing_type == 'realesrgan':
            args.extend(['-g', str(self.current_device)])
        elif processing_type == 'rife':
            args.extend(['-g', str(self.current_device)])
        elif processing_type == 'ffmpeg':
            args.extend(['-hwaccel', 'cuda', '-hwaccel_device', str(self.current_device)])
        
        return args

# シングルトンパターンでインスタンス管理
_cuda_accelerator_instance = None

def get_cuda_accelerator() -> CUDAAccelerator:
    """CUDA加速器のシングルトンインスタンスを取得"""
    global _cuda_accelerator_instance
    if _cuda_accelerator_instance is None:
        _cuda_accelerator_instance = CUDAAccelerator()
    return _cuda_accelerator_instance
