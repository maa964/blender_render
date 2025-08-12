# -*- coding: utf-8 -*-
"""
Video Encoder Module
PyPy最適化対応動画エンコーダーモジュール
"""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
import logging
from glob import glob

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

import numpy as np

logger = logging.getLogger(__name__)

class VideoEncoder:
    """PyPy最適化動画エンコーダー"""
    
    def __init__(self, use_cuda: bool = True):
        self.use_cuda = use_cuda
        self.ffmpeg_path = self._find_ffmpeg()
        self.temp_dir = None
        
        # サポートされるコーデック
        self.supported_codecs = {
            'prores_ks': {
                'name': 'Apple ProRes 4444',
                'extension': '.mov',
                'args': ['-c:v', 'prores_ks', '-profile:v', '4', '-pix_fmt', 'yuva444p10le'],
                'supports_alpha': True,
                'quality': 'lossless'
            },
            'qtrle': {
                'name': 'QuickTime RLE',
                'extension': '.mov',
                'args': ['-c:v', 'qtrle', '-pix_fmt', 'rgba'],
                'supports_alpha': True,
                'quality': 'lossless'
            },
            'h264': {
                'name': 'H.264',
                'extension': '.mp4',
                'args': ['-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18'],
                'supports_alpha': False,
                'quality': 'high'
            },
            'h265': {
                'name': 'H.265/HEVC',
                'extension': '.mp4',
                'args': ['-c:v', 'libx265', '-pix_fmt', 'yuv420p', '-crf', '20'],
                'supports_alpha': False,
                'quality': 'high'
            },
            'vp9': {
                'name': 'VP9',
                'extension': '.webm',
                'args': ['-c:v', 'libvpx-vp9', '-pix_fmt', 'yuva420p', '-crf', '20'],
                'supports_alpha': True,
                'quality': 'high'
            },
            'av1': {
                'name': 'AV1',
                'extension': '.mp4',
                'args': ['-c:v', 'libaom-av1', '-pix_fmt', 'yuv420p', '-crf', '25'],
                'supports_alpha': False,
                'quality': 'high'
            }
        }
        
        logger.info(f"動画エンコーダー初期化 (CUDA: {self.use_cuda})")
        self._validate_ffmpeg()
    
    def _find_ffmpeg(self) -> str:
        """FFmpegパスを自動検出"""
        possible_paths = [
            'ffmpeg',  # PATH内
            'ffmpeg.exe',
            r'C:\ffmpeg\bin\ffmpeg.exe',
            r'C:\Program Files\ffmpeg\bin\ffmpeg.exe',
            '/usr/bin/ffmpeg',
            '/usr/local/bin/ffmpeg',
            '/opt/ffmpeg/bin/ffmpeg'
        ]
        
        for path in possible_paths:
            try:
                result = subprocess.run([path, '-version'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    logger.info(f"FFmpeg検出: {path}")
                    return path
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        
        raise FileNotFoundError("FFmpegが見つかりません。インストールしてPATHに追加してください。")
    
    def _validate_ffmpeg(self) -> None:
        """FFmpeg機能検証"""
        try:
            result = subprocess.run([self.ffmpeg_path, '-codecs'], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                codecs_output = result.stdout
                
                # CUDA対応チェック
                if self.use_cuda:
                    if 'nvenc' in codecs_output:
                        logger.info("NVIDIA NVENC サポート検出")
                    else:
                        logger.warning("NVIDIA NVENC未対応")
                        self.use_cuda = False
                
                # 各コーデックの利用可能性チェック
                for codec_name, codec_info in self.supported_codecs.items():
                    codec_lib = codec_info['args'][1]
                    if codec_lib in codecs_output:
                        logger.info(f"{codec_info['name']} サポート確認")
                    else:
                        logger.warning(f"{codec_info['name']} 未対応")
            
        except Exception as e:
            logger.warning(f"FFmpeg検証エラー: {e}")
    
    def encode_image_sequence(self,
                            input_pattern: str,
                            output_path: str,
                            framerate: int = 30,
                            codec: str = 'prores_ks',
                            **kwargs) -> bool:
        """画像シーケンスから動画エンコード"""
        
        if codec not in self.supported_codecs:
            raise ValueError(f"未対応のコーデック: {codec}")
        
        codec_info = self.supported_codecs[codec]
        
        # 出力ファイル名の拡張子を修正
        output_path = Path(output_path)
        if output_path.suffix != codec_info['extension']:
            output_path = output_path.with_suffix(codec_info['extension'])
        
        try:
            # FFmpegコマンド構築
            cmd = [
                self.ffmpeg_path,
                '-y',  # 出力ファイル上書き
                '-framerate', str(framerate),
                '-i', input_pattern,
            ]
            
            # CUDA加速設定
            if self.use_cuda and codec in ['h264', 'h265']:
                cmd.extend(['-hwaccel', 'cuda'])
                if codec == 'h264':
                    cmd.extend(['-c:v', 'h264_nvenc'])
                elif codec == 'h265':
                    cmd.extend(['-c:v', 'hevc_nvenc'])
            else:
                cmd.extend(codec_info['args'])
            
            # 追加オプション
            if 'duration' in kwargs:
                cmd.extend(['-t', str(kwargs['duration'])])
            
            if 'start_time' in kwargs:
                cmd.extend(['-ss', str(kwargs['start_time'])])
            
            # 品質設定
            if 'crf' in kwargs and codec in ['h264', 'h265', 'vp9', 'av1']:
                # CRF値を置き換え
                for i, arg in enumerate(cmd):
                    if arg == '-crf' and i + 1 < len(cmd):
                        cmd[i + 1] = str(kwargs['crf'])
                        break
            
            # ビットレート設定
            if 'bitrate' in kwargs:
                cmd.extend(['-b:v', kwargs['bitrate']])
            
            # 解像度設定
            if 'width' in kwargs and 'height' in kwargs:
                cmd.extend(['-s', f"{kwargs['width']}x{kwargs['height']}"])
            
            # フィルター設定
            filters = []
            if 'scale' in kwargs:
                filters.append(f"scale={kwargs['scale']}")
            if 'fps' in kwargs and kwargs['fps'] != framerate:
                filters.append(f"fps={kwargs['fps']}")
            if 'denoise' in kwargs and kwargs['denoise']:
                filters.append("hqdn3d")
            
            if filters:
                cmd.extend(['-vf', ','.join(filters)])
            
            # 出力パス
            cmd.append(str(output_path))
            
            logger.info(f"エンコード開始: {' '.join(cmd)}")
            
            # エンコード実行
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            
            # 進捗監視
            self._monitor_encoding_progress(process, output_path)
            
            return_code = process.wait()
            
            if return_code == 0:
                logger.info(f"エンコード完了: {output_path}")
                return True
            else:
                logger.error(f"エンコード失敗 (終了コード: {return_code})")
                return False
                
        except Exception as e:
            logger.error(f"エンコードエラー: {e}")
            return False
    
    def _monitor_encoding_progress(self, process: subprocess.Popen, output_path: Path) -> None:
        """エンコード進捗監視"""
        while process.poll() is None:
            try:
                line = process.stdout.readline()
                if line:
                    line = line.strip()
                    
                    # FFmpegの進捗情報を解析
                    if 'frame=' in line and 'time=' in line:
                        logger.info(f"エンコード進捗: {line}")
                    elif 'error' in line.lower() or 'warning' in line.lower():
                        logger.warning(f"FFmpeg: {line}")
                        
            except Exception:
                break
    
    def encode_frames_list(self,
                          frames: List[np.ndarray],
                          output_path: str,
                          framerate: int = 30,
                          codec: str = 'prores_ks',
                          **kwargs) -> bool:
        """フレームリストから動画エンコード"""
        
        if not frames:
            logger.error("エンコードするフレームがありません")
            return False
        
        # 一時ディレクトリ作成
        with tempfile.TemporaryDirectory() as temp_dir:
            self.temp_dir = temp_dir
            
            # フレームを一時ファイルとして保存
            try:
                frame_pattern = self._save_frames_to_temp(frames, temp_dir)
                
                # 画像シーケンスとしてエンコード
                return self.encode_image_sequence(
                    frame_pattern, output_path, framerate, codec, **kwargs
                )
                
            except Exception as e:
                logger.error(f"フレーム保存エラー: {e}")
                return False
            finally:
                self.temp_dir = None
    
    def _save_frames_to_temp(self, frames: List[np.ndarray], temp_dir: str) -> str:
        """フレームを一時ファイルに保存"""
        frame_pattern = os.path.join(temp_dir, 'frame_%08d.png')
        
        for i, frame in enumerate(frames):
            frame_path = os.path.join(temp_dir, f'frame_{i+1:08d}.png')
            
            if PIL_AVAILABLE:
                # PILで保存（アルファチャンネル対応）
                if len(frame.shape) == 3 and frame.shape[2] == 4:
                    # RGBA
                    Image.fromarray(frame, 'RGBA').save(frame_path)
                elif len(frame.shape) == 3 and frame.shape[2] == 3:
                    # RGB
                    Image.fromarray(frame, 'RGB').save(frame_path)
                else:
                    # グレースケール
                    Image.fromarray(frame, 'L').save(frame_path)
            
            elif CV2_AVAILABLE:
                # OpenCVで保存
                if len(frame.shape) == 3:
                    # BGRに変換
                    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    cv2.imwrite(frame_path, frame_bgr)
                else:
                    cv2.imwrite(frame_path, frame)
            
            else:
                raise ImportError("PIL または OpenCV が必要です")
        
        logger.info(f"フレーム保存完了: {len(frames)}枚")
        return frame_pattern
    
    def concatenate_videos(self,
                          input_paths: List[str],
                          output_path: str,
                          **kwargs) -> bool:
        """複数動画の連結"""
        
        if not input_paths:
            logger.error("連結する動画がありません")
            return False
        
        # 連結リストファイル作成
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            for path in input_paths:
                if os.path.exists(path):
                    f.write(f"file '{os.path.abspath(path)}'\n")
                else:
                    logger.warning(f"ファイルが見つかりません: {path}")
            
            concat_list_path = f.name
        
        try:
            cmd = [
                self.ffmpeg_path,
                '-y',
                '-f', 'concat',
                '-safe', '0',
                '-i', concat_list_path,
                '-c', 'copy',  # ストリームコピー（高速）
                output_path
            ]
            
            logger.info(f"動画連結開始: {len(input_paths)}個のファイル")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            
            if result.returncode == 0:
                logger.info(f"動画連結完了: {output_path}")
                return True
            else:
                logger.error(f"動画連結失敗: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"動画連結エラー: {e}")
            return False
        finally:
            # 一時ファイル削除
            try:
                os.remove(concat_list_path)
            except:
                pass
    
    def extract_frames(self,
                      video_path: str,
                      output_dir: str,
                      start_time: Optional[float] = None,
                      duration: Optional[float] = None,
                      fps: Optional[int] = None) -> List[str]:
        """動画からフレーム抽出"""
        
        if not os.path.exists(video_path):
            logger.error(f"動画ファイルが見つかりません: {video_path}")
            return []
        
        os.makedirs(output_dir, exist_ok=True)
        
        cmd = [
            self.ffmpeg_path,
            '-i', video_path
        ]
        
        # 開始時間設定
        if start_time is not None:
            cmd.extend(['-ss', str(start_time)])
        
        # 継続時間設定
        if duration is not None:
            cmd.extend(['-t', str(duration)])
        
        # FPS設定
        if fps is not None:
            cmd.extend(['-vf', f'fps={fps}'])
        
        # 出力設定
        output_pattern = os.path.join(output_dir, 'frame_%08d.png')
        cmd.extend(['-y', output_pattern])
        
        try:
            logger.info(f"フレーム抽出開始: {video_path}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            
            if result.returncode == 0:
                # 抽出されたフレームファイルのリストを取得
                extracted_frames = sorted(glob(os.path.join(output_dir, 'frame_*.png')))
                logger.info(f"フレーム抽出完了: {len(extracted_frames)}枚")
                return extracted_frames
            else:
                logger.error(f"フレーム抽出失敗: {result.stderr}")
                return []
                
        except Exception as e:
            logger.error(f"フレーム抽出エラー: {e}")
            return []
    
    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """動画情報取得"""
        
        if not os.path.exists(video_path):
            return {'error': 'ファイルが見つかりません'}
        
        cmd = [
            self.ffmpeg_path,
            '-i', video_path,
            '-f', 'null',
            '-'
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            
            # FFmpegの出力から情報を抽出
            output = result.stderr
            info = {
                'file_path': video_path,
                'file_size': os.path.getsize(video_path),
                'duration': None,
                'width': None,
                'height': None,
                'fps': None,
                'codec': None,
                'bitrate': None
            }
            
            # 解像度とFPS抽出
            import re
            
            # 解像度パターン
            resolution_match = re.search(r'(\d+)x(\d+)', output)
            if resolution_match:
                info['width'] = int(resolution_match.group(1))
                info['height'] = int(resolution_match.group(2))
            
            # FPSパターン
            fps_match = re.search(r'(\d+(?:\.\d+)?)\s*fps', output)
            if fps_match:
                info['fps'] = float(fps_match.group(1))
            
            # 継続時間パターン
            duration_match = re.search(r'Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)', output)
            if duration_match:
                hours = int(duration_match.group(1))
                minutes = int(duration_match.group(2))
                seconds = float(duration_match.group(3))
                info['duration'] = hours * 3600 + minutes * 60 + seconds
            
            # コーデック情報
            codec_match = re.search(r'Video:\s*(\w+)', output)
            if codec_match:
                info['codec'] = codec_match.group(1)
            
            # ビットレート情報
            bitrate_match = re.search(r'bitrate:\s*(\d+)\s*kb/s', output)
            if bitrate_match:
                info['bitrate'] = int(bitrate_match.group(1))
            
            return info
            
        except Exception as e:
            return {'error': f'情報取得エラー: {e}'}
    
    def create_preview(self,
                      video_path: str,
                      output_path: str,
                      thumbnail_count: int = 9,
                      columns: int = 3) -> bool:
        """動画プレビュー（サムネイル格子）作成"""
        
        video_info = self.get_video_info(video_path)
        if 'error' in video_info:
            logger.error(f"動画情報取得失敗: {video_info['error']}")
            return False
        
        duration = video_info.get('duration')
        if not duration:
            logger.error("動画の継続時間を取得できません")
            return False
        
        # サムネイル時間間隔計算
        time_interval = duration / (thumbnail_count + 1)
        
        cmd = [
            self.ffmpeg_path,
            '-i', video_path,
            '-vf', f'select=not(mod(n\\,{int(time_interval * video_info.get("fps", 30))})),scale=320:240,tile={columns}x{thumbnail_count//columns + 1}',
            '-frames:v', '1',
            '-y',
            output_path
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            
            if result.returncode == 0:
                logger.info(f"プレビュー作成完了: {output_path}")
                return True
            else:
                logger.error(f"プレビュー作成失敗: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"プレビュー作成エラー: {e}")
            return False
    
    def optimize_for_web(self,
                        input_path: str,
                        output_path: str,
                        target_size_mb: Optional[float] = None) -> bool:
        """Web最適化エンコード"""
        
        video_info = self.get_video_info(input_path)
        if 'error' in video_info:
            return False
        
        cmd = [
            self.ffmpeg_path,
            '-i', input_path,
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '23',
            '-pix_fmt', 'yuv420p',
            '-movflags', '+faststart',  # Web最適化
            '-y',
            output_path
        ]
        
        # ターゲットサイズが指定されている場合はビットレート計算
        if target_size_mb and video_info.get('duration'):
            target_bitrate = int((target_size_mb * 8 * 1024) / video_info['duration'])
            cmd.extend(['-b:v', f'{target_bitrate}k'])
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            
            if result.returncode == 0:
                logger.info(f"Web最適化完了: {output_path}")
                return True
            else:
                logger.error(f"Web最適化失敗: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Web最適化エラー: {e}")
            return False
    
    def __del__(self):
        """デストラクタ"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except:
                pass
