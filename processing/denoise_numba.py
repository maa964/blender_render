# -*- coding: utf-8 -*-
"""
Denoise Processor with Numba Optimization
Numba/CUDA最適化対応ノイズ除去処理モジュール
"""

import os
import sys
import numpy as np
from typing import Optional, Union, Tuple, List, Dict, Any

# Numbaインポート（エラーハンドリング付き）
try:
    from numba import jit, prange
    from numba import cuda as numba_cuda
    NUMBA_AVAILABLE = True
    CUDA_AVAILABLE = True
except ImportError:
    # Numba未利用時のダミー関数
    def jit(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    
    class DummyCuda:
        @staticmethod
        def jit(*args, **kwargs):
            def decorator(func):
                return func
            return decorator
    
    numba_cuda = DummyCuda()
    prange = range
    NUMBA_AVAILABLE = False
    CUDA_AVAILABLE = False

# エイリアス設定
cuda = numba_cuda
import logging
from pathlib import Path

# UTF-8エンコーディング設定
if sys.platform.startswith('win'):
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# Numba/CUDA imports
try:
    import numba
    from numba import cuda, jit, prange
    NUMBA_AVAILABLE = True
    CUDA_AVAILABLE = cuda.is_available()
except ImportError:
    NUMBA_AVAILABLE = False
    CUDA_AVAILABLE = False

# 画像処理ライブラリ
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

class DenoiseProcessor:
    """Numba最適化ノイズ除去プロセッサ"""
    
    def __init__(self, use_cuda: bool = True):
        self.use_cuda = use_cuda and CUDA_AVAILABLE
        self.device_id = 0
        
        if self.use_cuda:
            logger.info(f"CUDA対応ノイズ除去プロセッサ初期化 (GPU: {cuda.get_current_device()})")
        else:
            logger.info("CPU対応ノイズ除去プロセッサ初期化")
    
    def denoise_image(self, 
                     image: np.ndarray, 
                     method: str = 'bilateral',
                     strength: float = 1.0,
                     **kwargs) -> np.ndarray:
        """
        画像ノイズ除去
        
        Args:
            image: 入力画像 (H, W, C) または (H, W)
            method: ノイズ除去手法 ('bilateral', 'gaussian', 'median', 'nlm', 'wavelet')
            strength: ノイズ除去強度 (0.0-2.0)
            **kwargs: 手法固有のパラメータ
        
        Returns:
            ノイズ除去済み画像
        """
        if not isinstance(image, np.ndarray):
            raise ValueError("入力画像はnumpy.ndarrayである必要があります")
        
        # 画像の前処理
        processed_image = self._preprocess_image(image)
        
        # 手法別ノイズ除去
        if method == 'bilateral':
            result = self._bilateral_denoise(processed_image, strength, **kwargs)
        elif method == 'gaussian':
            result = self._gaussian_denoise(processed_image, strength, **kwargs)
        elif method == 'median':
            result = self._median_denoise(processed_image, strength, **kwargs)
        elif method == 'nlm':
            result = self._nlm_denoise(processed_image, strength, **kwargs)
        elif method == 'wavelet':
            result = self._wavelet_denoise(processed_image, strength, **kwargs)
        elif method == 'numba_custom':
            result = self._numba_custom_denoise(processed_image, strength, **kwargs)
        else:
            raise ValueError(f"未対応のノイズ除去手法: {method}")
        
        # 後処理
        return self._postprocess_image(result, image.shape, image.dtype)
    
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """画像前処理"""
        # データ型をfloat32に統一
        if image.dtype != np.float32:
            if image.dtype == np.uint8:
                processed = image.astype(np.float32) / 255.0
            elif image.dtype == np.uint16:
                processed = image.astype(np.float32) / 65535.0
            else:
                processed = image.astype(np.float32)
        else:
            processed = image.copy()
        
        # 値の範囲を[0, 1]にクリップ
        processed = np.clip(processed, 0.0, 1.0)
        
        return processed
    
    def _postprocess_image(self, image: np.ndarray, original_shape: Tuple, original_dtype: np.dtype) -> np.ndarray:
        """画像後処理"""
        # 形状を元に戻す
        if image.shape != original_shape:
            image = image.reshape(original_shape)
        
        # データ型を元に戻す
        if original_dtype == np.uint8:
            result = (np.clip(image, 0.0, 1.0) * 255.0).astype(np.uint8)
        elif original_dtype == np.uint16:
            result = (np.clip(image, 0.0, 1.0) * 65535.0).astype(np.uint16)
        else:
            result = image.astype(original_dtype)
        
        return result
    
    def _bilateral_denoise(self, image: np.ndarray, strength: float, **kwargs) -> np.ndarray:
        """バイラテラルフィルタによるノイズ除去"""
        if not CV2_AVAILABLE:
            logger.warning("OpenCV未インストール - Gaussianフィルタで代替")
            return self._gaussian_denoise(image, strength, **kwargs)
        
        # パラメータ設定
        d = kwargs.get('diameter', int(9 * strength))
        sigma_color = kwargs.get('sigma_color', 75 * strength)
        sigma_space = kwargs.get('sigma_space', 75 * strength)
        
        # チャンネル別処理
        if len(image.shape) == 3:
            channels = []
            for c in range(image.shape[2]):
                channel = image[:, :, c]
                # float32を8bitに変換
                channel_8bit = (channel * 255).astype(np.uint8)
                denoised_8bit = cv2.bilateralFilter(channel_8bit, d, sigma_color, sigma_space)
                denoised = denoised_8bit.astype(np.float32) / 255.0
                channels.append(denoised)
            result = np.stack(channels, axis=2)
        else:
            # グレースケール処理
            image_8bit = (image * 255).astype(np.uint8)
            denoised_8bit = cv2.bilateralFilter(image_8bit, d, sigma_color, sigma_space)
            result = denoised_8bit.astype(np.float32) / 255.0
        
        return result
    
    def _gaussian_denoise(self, image: np.ndarray, strength: float, **kwargs) -> np.ndarray:
        """Gaussianフィルタによるノイズ除去"""
        if not CV2_AVAILABLE:
            return self._numba_gaussian_denoise(image, strength, **kwargs)
        
        # カーネルサイズとシグマ設定
        kernel_size = kwargs.get('kernel_size', int(5 + 4 * strength))
        if kernel_size % 2 == 0:
            kernel_size += 1
        
        sigma_x = kwargs.get('sigma_x', strength)
        sigma_y = kwargs.get('sigma_y', sigma_x)
        
        # OpenCVのGaussianBlur使用
        result = cv2.GaussianBlur(image, (kernel_size, kernel_size), sigma_x, sigmaY=sigma_y)
        
        return result
    
    def _median_denoise(self, image: np.ndarray, strength: float, **kwargs) -> np.ndarray:
        """メディアンフィルタによるノイズ除去"""
        if not CV2_AVAILABLE:
            return self._numba_median_denoise(image, strength, **kwargs)
        
        # カーネルサイズ設定
        kernel_size = kwargs.get('kernel_size', int(3 + 2 * strength))
        if kernel_size % 2 == 0:
            kernel_size += 1
        
        # チャンネル別処理
        if len(image.shape) == 3:
            channels = []
            for c in range(image.shape[2]):
                channel = image[:, :, c]
                # float32を8bitに変換
                channel_8bit = (channel * 255).astype(np.uint8)
                denoised_8bit = cv2.medianBlur(channel_8bit, kernel_size)
                denoised = denoised_8bit.astype(np.float32) / 255.0
                channels.append(denoised)
            result = np.stack(channels, axis=2)
        else:
            # グレースケール処理
            image_8bit = (image * 255).astype(np.uint8)
            denoised_8bit = cv2.medianBlur(image_8bit, kernel_size)
            result = denoised_8bit.astype(np.float32) / 255.0
        
        return result
    
    def _nlm_denoise(self, image: np.ndarray, strength: float, **kwargs) -> np.ndarray:
        """Non-Local Meansによるノイズ除去"""
        if not CV2_AVAILABLE:
            logger.warning("OpenCV未インストール - Gaussianフィルタで代替")
            return self._gaussian_denoise(image, strength, **kwargs)
        
        # パラメータ設定
        h = kwargs.get('h', 10 * strength)
        template_window_size = kwargs.get('template_window_size', 7)
        search_window_size = kwargs.get('search_window_size', 21)
        
        # カラー画像とグレースケール画像で処理を分ける
        if len(image.shape) == 3:
            # カラー画像
            image_8bit = (image * 255).astype(np.uint8)
            denoised_8bit = cv2.fastNlMeansDenoisingColored(
                image_8bit, None, h, h, template_window_size, search_window_size
            )
            result = denoised_8bit.astype(np.float32) / 255.0
        else:
            # グレースケール画像
            image_8bit = (image * 255).astype(np.uint8)
            denoised_8bit = cv2.fastNlMeansDenoising(
                image_8bit, None, h, template_window_size, search_window_size
            )
            result = denoised_8bit.astype(np.float32) / 255.0
        
        return result
    
    def _wavelet_denoise(self, image: np.ndarray, strength: float, **kwargs) -> np.ndarray:
        """ウェーブレット変換によるノイズ除去"""
        try:
            import pywt
        except ImportError:
            logger.warning("PyWavelets未インストール - Gaussianフィルタで代替")
            return self._gaussian_denoise(image, strength, **kwargs)
        
        # パラメータ設定
        wavelet = kwargs.get('wavelet', 'db4')
        sigma = kwargs.get('sigma', 0.1 * strength)
        
        # チャンネル別処理
        if len(image.shape) == 3:
            channels = []
            for c in range(image.shape[2]):
                channel = image[:, :, c]
                denoised_channel = self._wavelet_denoise_single_channel(channel, wavelet, sigma)
                channels.append(denoised_channel)
            result = np.stack(channels, axis=2)
        else:
            result = self._wavelet_denoise_single_channel(image, wavelet, sigma)
        
        return result
    
    def _wavelet_denoise_single_channel(self, channel: np.ndarray, wavelet: str, sigma: float) -> np.ndarray:
        """単一チャンネルのウェーブレットノイズ除去"""
        import pywt
        
        # ウェーブレット分解
        coeffs = pywt.wavedec2(channel, wavelet, levels=4)
        
        # 閾値設定
        threshold = sigma * np.sqrt(2 * np.log(channel.size))
        
        # 詳細係数に閾値適用
        coeffs_thresh = list(coeffs)
        for i in range(1, len(coeffs)):
            coeffs_thresh[i] = tuple([pywt.threshold(c, threshold, mode='soft') for c in coeffs[i]])
        
        # ウェーブレット再構成
        denoised = pywt.waverec2(coeffs_thresh, wavelet)
        
        return denoised
    
    @staticmethod
    @jit(nopython=True, parallel=True)
    def _numba_gaussian_kernel(size: int, sigma: float) -> np.ndarray:
        """Numba最適化Gaussianカーネル生成"""
        kernel = np.zeros((size, size), dtype=np.float32)
        center = size // 2
        sum_val = 0.0
        
        for i in prange(size):
            for j in prange(size):
                x = i - center
                y = j - center
                val = np.exp(-(x*x + y*y) / (2.0 * sigma * sigma))
                kernel[i, j] = val
                sum_val += val
        
        # 正規化
        for i in prange(size):
            for j in prange(size):
                kernel[i, j] /= sum_val
        
        return kernel
    
    def _numba_gaussian_denoise(self, image: np.ndarray, strength: float, **kwargs) -> np.ndarray:
        """Numba最適化Gaussianノイズ除去"""
        if not NUMBA_AVAILABLE:
            return image  # フォールバック
        
        kernel_size = kwargs.get('kernel_size', int(5 + 4 * strength))
        if kernel_size % 2 == 0:
            kernel_size += 1
        
        sigma = kwargs.get('sigma_x', strength)
        
        # Gaussianカーネル生成
        kernel = self._numba_gaussian_kernel(kernel_size, sigma)
        
        # 畳み込み処理
        if len(image.shape) == 3:
            result = np.zeros_like(image)
            for c in range(image.shape[2]):
                result[:, :, c] = self._numba_convolve2d(image[:, :, c], kernel)
        else:
            result = self._numba_convolve2d(image, kernel)
        
        return result
    
    @staticmethod
    @jit(nopython=True, parallel=True)
    def _numba_convolve2d(image: np.ndarray, kernel: np.ndarray) -> np.ndarray:
        """Numba最適化2D畳み込み"""
        h, w = image.shape
        kh, kw = kernel.shape
        pad_h, pad_w = kh // 2, kw // 2
        
        result = np.zeros_like(image)
        
        for i in prange(h):
            for j in prange(w):
                sum_val = 0.0
                for ki in range(kh):
                    for kj in range(kw):
                        ii = i + ki - pad_h
                        jj = j + kj - pad_w
                        
                        # 境界処理（ミラーパディング）
                        if ii < 0:
                            ii = -ii
                        elif ii >= h:
                            ii = 2 * h - ii - 2
                        
                        if jj < 0:
                            jj = -jj
                        elif jj >= w:
                            jj = 2 * w - jj - 2
                        
                        sum_val += image[ii, jj] * kernel[ki, kj]
                
                result[i, j] = sum_val
        
        return result
    
    def _numba_median_denoise(self, image: np.ndarray, strength: float, **kwargs) -> np.ndarray:
        """Numba最適化メディアンノイズ除去"""
        if not NUMBA_AVAILABLE:
            return image  # フォールバック
        
        kernel_size = kwargs.get('kernel_size', int(3 + 2 * strength))
        if kernel_size % 2 == 0:
            kernel_size += 1
        
        # チャンネル別処理
        if len(image.shape) == 3:
            result = np.zeros_like(image)
            for c in range(image.shape[2]):
                result[:, :, c] = self._numba_median_filter(image[:, :, c], kernel_size)
        else:
            result = self._numba_median_filter(image, kernel_size)
        
        return result
    
    @staticmethod
    @jit(nopython=True, parallel=True)
    def _numba_median_filter(image: np.ndarray, kernel_size: int) -> np.ndarray:
        """Numba最適化メディアンフィルタ"""
        h, w = image.shape
        pad_size = kernel_size // 2
        result = np.zeros_like(image)
        
        for i in prange(h):
            for j in prange(w):
                # 近傍値収集
                values = []
                for ki in range(kernel_size):
                    for kj in range(kernel_size):
                        ii = i + ki - pad_size
                        jj = j + kj - pad_size
                        
                        # 境界処理
                        if ii < 0:
                            ii = 0
                        elif ii >= h:
                            ii = h - 1
                        
                        if jj < 0:
                            jj = 0
                        elif jj >= w:
                            jj = w - 1
                        
                        values.append(image[ii, jj])
                
                # 中央値計算
                values.sort()
                median_idx = len(values) // 2
                result[i, j] = values[median_idx]
        
        return result
    
    def _numba_custom_denoise(self, image: np.ndarray, strength: float, **kwargs) -> np.ndarray:
        """Numba最適化カスタムノイズ除去"""
        if not NUMBA_AVAILABLE:
            return self._gaussian_denoise(image, strength, **kwargs)
        
        # エッジ保持平滑化フィルタ
        if self.use_cuda and CUDA_AVAILABLE:
            return self._cuda_edge_preserving_denoise(image, strength, **kwargs)
        else:
            return self._cpu_edge_preserving_denoise(image, strength, **kwargs)
    
    def _cpu_edge_preserving_denoise(self, image: np.ndarray, strength: float, **kwargs) -> np.ndarray:
        """CPU版エッジ保持ノイズ除去"""
        iterations = kwargs.get('iterations', int(3 * strength))
        lambda_param = kwargs.get('lambda_param', 0.1 * strength)
        
        if len(image.shape) == 3:
            result = np.zeros_like(image)
            for c in range(image.shape[2]):
                result[:, :, c] = self._anisotropic_diffusion(image[:, :, c], iterations, lambda_param)
        else:
            result = self._anisotropic_diffusion(image, iterations, lambda_param)
        
        return result
    
    @staticmethod
    @jit(nopython=True)
    def _anisotropic_diffusion(image: np.ndarray, iterations: int, lambda_param: float) -> np.ndarray:
        """異方性拡散フィルタ（Perona-Malik）"""
        h, w = image.shape
        result = image.copy()
        
        for _ in range(iterations):
            # 勾配計算
            grad_n = np.zeros((h-1, w))
            grad_s = np.zeros((h-1, w))
            grad_e = np.zeros((h, w-1))
            grad_w = np.zeros((h, w-1))
            
            # 北向き勾配
            for i in range(h-1):
                for j in range(w):
                    grad_n[i, j] = result[i, j] - result[i+1, j]
            
            # 南向き勾配
            for i in range(h-1):
                for j in range(w):
                    grad_s[i, j] = result[i+1, j] - result[i, j]
            
            # 東向き勾配
            for i in range(h):
                for j in range(w-1):
                    grad_e[i, j] = result[i, j+1] - result[i, j]
            
            # 西向き勾配
            for i in range(h):
                for j in range(w-1):
                    grad_w[i, j] = result[i, j] - result[i, j+1]
            
            # 拡散係数計算（エッジ検出）
            k = 0.1
            
            # 更新
            for i in range(1, h-1):
                for j in range(1, w-1):
                    # 拡散係数
                    cn = np.exp(-(grad_n[i-1, j] / k) ** 2)
                    cs = np.exp(-(grad_s[i, j] / k) ** 2)
                    ce = np.exp(-(grad_e[i, j] / k) ** 2)
                    cw = np.exp(-(grad_w[i, j-1] / k) ** 2)
                    
                    # 更新
                    result[i, j] += lambda_param * (
                        cn * grad_n[i-1, j] + cs * grad_s[i, j] + 
                        ce * grad_e[i, j] + cw * grad_w[i, j-1]
                    )
        
        return result
    
    def _cuda_edge_preserving_denoise(self, image: np.ndarray, strength: float, **kwargs) -> np.ndarray:
        """CUDA版エッジ保持ノイズ除去"""
        if not CUDA_AVAILABLE:
            return self._cpu_edge_preserving_denoise(image, strength, **kwargs)
        
        try:
            # GPU メモリ転送
            d_image = cuda.to_device(image.astype(np.float32))
            d_result = cuda.device_array_like(d_image)
            
            # CUDA カーネル実行
            threads_per_block = (16, 16)
            blocks_per_grid_x = (image.shape[1] + threads_per_block[1] - 1) // threads_per_block[1]
            blocks_per_grid_y = (image.shape[0] + threads_per_block[0] - 1) // threads_per_block[0]
            blocks_per_grid = (blocks_per_grid_x, blocks_per_grid_y)
            
            iterations = kwargs.get('iterations', int(3 * strength))
            lambda_param = kwargs.get('lambda_param', 0.1 * strength)
            
            if len(image.shape) == 3:
                # カラー画像
                for c in range(image.shape[2]):
                    self._cuda_anisotropic_diffusion_kernel[blocks_per_grid, threads_per_block](
                        d_image[:, :, c], d_result[:, :, c], iterations, lambda_param
                    )
            else:
                # グレースケール画像
                self._cuda_anisotropic_diffusion_kernel[blocks_per_grid, threads_per_block](
                    d_image, d_result, iterations, lambda_param
                )
            
            # 結果を CPU に戻す
            result = d_result.copy_to_host()
            
            return result
            
        except Exception as e:
            logger.warning(f"CUDA処理失敗、CPU処理に切り替え: {e}")
            return self._cpu_edge_preserving_denoise(image, strength, **kwargs)
    
    @staticmethod
    @cuda.jit
    def _cuda_anisotropic_diffusion_kernel(image, result, iterations, lambda_param):
        """CUDA異方性拡散カーネル"""
        i, j = cuda.grid(2)
        
        if i >= image.shape[0] or j >= image.shape[1]:
            return
        
        result[i, j] = image[i, j]
        
        # 境界をスキップ
        if i == 0 or i == image.shape[0] - 1 or j == 0 or j == image.shape[1] - 1:
            return
        
        k = 0.1
        
        for _ in range(iterations):
            # 勾配計算
            grad_n = result[i-1, j] - result[i, j]
            grad_s = result[i+1, j] - result[i, j]
            grad_e = result[i, j+1] - result[i, j]
            grad_w = result[i, j-1] - result[i, j]
            
            # 拡散係数
            cn = numba.exp(-(grad_n / k) ** 2)
            cs = numba.exp(-(grad_s / k) ** 2)
            ce = numba.exp(-(grad_e / k) ** 2)
            cw = numba.exp(-(grad_w / k) ** 2)
            
            # 更新
            result[i, j] += lambda_param * (cn * grad_n + cs * grad_s + ce * grad_e + cw * grad_w)
    
    def batch_denoise(self, 
                     images: List[np.ndarray], 
                     method: str = 'bilateral',
                     strength: float = 1.0,
                     **kwargs) -> List[np.ndarray]:
        """バッチノイズ除去処理"""
        results = []
        
        for i, image in enumerate(images):
            try:
                denoised = self.denoise_image(image, method, strength, **kwargs)
                results.append(denoised)
                logger.info(f"ノイズ除去完了: {i+1}/{len(images)}")
            except Exception as e:
                logger.error(f"ノイズ除去エラー (画像{i+1}): {e}")
                results.append(image)  # エラー時は元画像を返す
        
        return results
    
    def denoise_file(self, 
                    input_path: str, 
                    output_path: str,
                    method: str = 'bilateral',
                    strength: float = 1.0,
                    **kwargs) -> bool:
        """ファイルからファイルへのノイズ除去"""
        try:
            # 画像読み込み
            if PIL_AVAILABLE:
                image = np.array(Image.open(input_path))
            else:
                raise ImportError("PIL未インストール")
            
            # ノイズ除去処理
            denoised = self.denoise_image(image, method, strength, **kwargs)
            
            # 結果保存
            if PIL_AVAILABLE:
                Image.fromarray(denoised).save(output_path)
            else:
                raise ImportError("PIL未インストール")
            
            logger.info(f"ノイズ除去ファイル保存完了: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"ファイルノイズ除去エラー: {e}")
            return False
