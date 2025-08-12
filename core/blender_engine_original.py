# -*- coding: utf-8 -*-
"""
修正済みBlender Render Engine - 完全版
フレーム数制限、GPU使用率、進捗監視の問題を修正
"""

import os
import sys
import subprocess
import threading
import time
import tempfile
from typing import Optional, Dict, Any, Callable
import logging
import re
import json

# UTF-8エンコーディング設定
if sys.platform.startswith('win'):
    os.environ['PYTHONIOENCODING'] = 'utf-8'

logger = logging.getLogger(__name__)

class BlenderRenderEngine:
    """修正済みBlenderレンダリングエンジンクラス"""
    
    def __init__(self, blender_path: Optional[str] = None):
        self.blender_path = blender_path or self._find_blender_path()
        self.process: Optional[subprocess.Popen] = None
        self.is_running = False
        self.progress_callback: Optional[Callable[[float, str], None]] = None
        self.log_callback: Optional[Callable[[str], None]] = None
        self.temp_script_path: Optional[str] = None
        
        # レンダリング統計
        self.stats = {
            'frames_rendered': 0,
            'total_frames': 0,
            'start_time': None,
            'end_time': None,
            'errors': [],
            'warnings': []
        }
        
        self._validate_blender_installation()
    
    def _find_blender_path(self) -> str:
        """Blenderインストールパスを自動検出"""
        possible_paths = [
            r"C:\Program Files\Blender Foundation\Blender 4.5\blender.exe",
            r"C:\Program Files\Blender Foundation\Blender 4.4\blender.exe", 
            r"C:\Program Files\Blender Foundation\Blender 4.3\blender.exe",
            r"C:\Program Files\Blender Foundation\Blender 4.2\blender.exe",
            r"C:\Program Files\Blender Foundation\Blender 4.1\blender.exe",
            r"C:\Program Files\Blender Foundation\Blender 4.0\blender.exe",
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                logger.info(f"Blender検出: {path}")
                return path
        
        raise FileNotFoundError("Blenderが見つかりません。")
    
    def _validate_blender_installation(self) -> None:
        """Blenderインストールの検証"""
        if not os.path.exists(self.blender_path):
            raise FileNotFoundError(f"Blender not found at: {self.blender_path}")
    
    def set_progress_callback(self, callback: Callable[[float, str], None]) -> None:
        """進捗コールバック設定"""
        self.progress_callback = callback
    
    def set_log_callback(self, callback: Callable[[str], None]) -> None:
        """ログコールバック設定"""
        self.log_callback = callback
    
    def _log(self, message: str) -> None:
        """ログ出力"""
        logger.info(message)
        if self.log_callback:
            self.log_callback(message)
    
    def _update_progress(self, progress: float, message: str) -> None:
        """進捗更新"""
        if self.progress_callback:
            self.progress_callback(progress, message)
    
    def create_render_script(self, settings: Dict[str, Any]) -> str:
        """修正済みレンダリング用Pythonスクリプト生成"""
        script_content = f'''
import bpy
import os
import sys

print("=== Blender Python script started ===")

try:
    # シーン設定
    scene = bpy.context.scene
    
    # フレーム範囲を明示的に設定（重要な修正）
    frame_start = {settings.get('frame_start', 1)}
    frame_end = {settings.get('frame_end', 10)}
    scene.frame_start = frame_start
    scene.frame_end = frame_end
    print(f"フレーム範囲設定: {{frame_start}} - {{frame_end}}")
    
    # 解像度設定
    scene.render.resolution_x = {settings.get('resolution_x', 1280)}
    scene.render.resolution_y = {settings.get('resolution_y', 720)}
    scene.render.resolution_percentage = {settings.get('resolution_percentage', 100)}
    print(f"解像度設定: {{scene.render.resolution_x}}x{{scene.render.resolution_y}}")
    
    # レンダリングエンジン設定
    target_engine = '{settings.get('render_engine', 'CYCLES')}'
    if target_engine != scene.render.engine:
        scene.render.engine = target_engine
        print(f"レンダリングエンジン変更: {{target_engine}}")
    
    # Cyclesエンジン設定
    if scene.render.engine == 'CYCLES':
        samples = {settings.get('samples', 64)}
        scene.cycles.samples = samples
        scene.cycles.use_denoising = {str(settings.get('use_denoising', True)).lower()}
        print(f"Cycles設定 - サンプル数: {{samples}}")
        
        # GPU設定の強化
        use_gpu = {str(settings.get('use_gpu', False)).lower()}
        if use_gpu:
            preferences = bpy.context.preferences
            cycles_preferences = preferences.addons["cycles"].preferences
            cycles_preferences.refresh_devices()
            
            print("=== GPU デバイス検出開始 ===")
            gpu_found = False
            
            # 全てのデバイスを無効化
            for device in cycles_preferences.devices:
                device.use = False
            
            # GPUデバイスを優先的に有効化
            for device in cycles_preferences.devices:
                print(f"デバイス発見: {{device.name}} ({{device.type}})")
                
                if device.type in ['OPTIX', 'CUDA', 'OPENCL', 'HIP']:
                    device.use = True
                    gpu_found = True
                    print(f"  -> GPU有効化: {{device.name}} ({{device.type}})")
            
            if gpu_found:
                scene.cycles.device = 'GPU'
                print("GPU レンダリングモード有効")
            else:
                scene.cycles.device = 'CPU'
                print("GPU未検出: CPUレンダリングモード")
        else:
            scene.cycles.device = 'CPU'
            print("CPU レンダリングモード")
        
        # 適応的サンプリング
        scene.cycles.use_adaptive_sampling = {str(settings.get('use_adaptive_sampling', True)).lower()}
        if scene.cycles.use_adaptive_sampling:
            scene.cycles.adaptive_threshold = {settings.get('adaptive_threshold', 0.01)}
            print(f"適応的サンプリング有効")
    
    # 出力設定
    scene.render.image_settings.file_format = '{settings.get('file_format', 'PNG')}'
    scene.render.image_settings.color_mode = '{settings.get('color_mode', 'RGBA')}'
    
    # 出力パス設定
    output_path = r"{settings.get('output_path', '').replace(chr(92), chr(92)+chr(92))}"
    scene.render.filepath = output_path
    print(f"出力パス: {{output_path}}")
    
    # 最終設定確認
    print("=== 最終レンダリング設定 ===")
    print(f"エンジン: {{scene.render.engine}}")
    print(f"フレーム範囲: {{scene.frame_start}} - {{scene.frame_end}} ({{scene.frame_end - scene.frame_start + 1}}フレーム)")
    print(f"解像度: {{scene.render.resolution_x}} x {{scene.render.resolution_y}}")
    print(f"出力パス: {{scene.render.filepath}}")
    
    if scene.render.engine == 'CYCLES':
        print(f"サンプル数: {{scene.cycles.samples}}")
        print(f"デバイス: {{scene.cycles.device}}")
    
    print("=== レンダリング開始 ===")
    
    # レンダリング実行
    bpy.ops.render.render(animation=True)
    
    print("=== レンダリング完了 ===")

except Exception as e:
    print(f"ERROR: レンダリングエラー: {{e}}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
'''
        
        # 一時スクリプトファイル作成
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write(script_content)
            self.temp_script_path = f.name
        
        return self.temp_script_path
    
    def render(self, blend_file: str, output_dir: str, settings: Dict[str, Any]) -> bool:
        """修正済みレンダリング実行"""
        if self.is_running:
            self._log("エラー: 既にレンダリングが実行中です")
            return False
        
        if not os.path.exists(blend_file):
            self._log(f"エラー: Blendファイルが見つかりません: {blend_file}")
            return False
        
        # 出力ディレクトリ作成
        os.makedirs(output_dir, exist_ok=True)
        
        # 設定のデフォルト値設定
        render_settings = {
            'frame_start': settings.get('frame_start', 1),
            'frame_end': settings.get('frame_end', 10),
            'resolution_x': settings.get('resolution_x', 1280),
            'resolution_y': settings.get('resolution_y', 720),
            'samples': settings.get('samples', 64),
            'use_gpu': settings.get('use_gpu', True),
            'render_engine': 'CYCLES',
            'output_path': os.path.join(output_dir, 'render_').replace('\\', '/'),
            **settings
        }
        
        # ログ出力
        self._log(f"レンダリング設定:")
        self._log(f"  フレーム範囲: {render_settings['frame_start']} - {render_settings['frame_end']}")
        self._log(f"  解像度: {render_settings['resolution_x']}x{render_settings['resolution_y']}")
        self._log(f"  サンプル数: {render_settings['samples']}")
        self._log(f"  GPU使用: {render_settings['use_gpu']}")
        
        try:
            # レンダリングスクリプト作成
            script_path = self.create_render_script(render_settings)
            
            # 統計初期化
            self.stats = {
                'frames_rendered': 0,
                'total_frames': render_settings['frame_end'] - render_settings['frame_start'] + 1,
                'start_time': time.time(),
                'end_time': None,
                'errors': [],
                'warnings': []
            }
            
            # Blenderコマンド構築（修正版）
            cmd = [
                self.blender_path,
                '-b',  # バックグラウンド
                blend_file,
                '-s', str(render_settings['frame_start']),  # 開始フレーム
                '-e', str(render_settings['frame_end']),    # 終了フレーム
                '-P', script_path,  # スクリプト実行（出力設定もここで）
                '-a'  # アニメーションレンダリング
            ]
            
            self._log(f"実行コマンド: {' '.join(cmd)}")
            
            # プロセス開始
            self.is_running = True
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                cwd=output_dir
            )
            
            # 進捗監視スレッド開始
            monitor_thread = threading.Thread(target=self._monitor_progress, args=(output_dir,))
            monitor_thread.daemon = True
            monitor_thread.start()
            
            # プロセス完了待ち
            return_code = self.process.wait()
            
            # 統計更新
            self.stats['end_time'] = time.time()
            render_time = self.stats['end_time'] - self.stats['start_time']
            
            if return_code == 0:
                self._log(f"レンダリング完了! 時間: {render_time:.2f}秒")
                self._log(f"レンダリング済みフレーム: {self.stats['frames_rendered']}/{self.stats['total_frames']}")
                self._update_progress(100.0, "レンダリング完了")
                return True
            else:
                self._log(f"レンダリング失敗 (終了コード: {return_code})")
                return False
                
        except Exception as e:
            self._log(f"レンダリングエラー: {e}")
            self.stats['errors'].append(str(e))
            return False
        finally:
            self.is_running = False
            self._cleanup_temp_files()
    
    def _monitor_progress(self, output_dir: str) -> None:
        """改良された進捗監視"""
        last_frame = 0
        frame_start_time = None
        
        while self.is_running and self.process and self.process.poll() is None:
            try:
                if self.process.stdout:
                    line = self.process.stdout.readline()
                    if line:
                        line = line.strip()
                        self._log(f"Blender: {line}")
                        
                        # フレーム進捗の解析（複数パターン対応）
                        frame_patterns = [
                            r"Fra:(\d+)",  # Cycles
                            r"Saved: '.*render_(\d+)\..*'",  # 保存完了
                            r"Rendering (\d+) / (\d+)",  # 一般的なパターン
                            r"Frame (\d+)"  # Eevee等
                        ]
                        
                        current_frame = None
                        for pattern in frame_patterns:
                            match = re.search(pattern, line)
                            if match:
                                current_frame = int(match.group(1))
                                break
                        
                        if current_frame is not None and current_frame >= last_frame:
                            last_frame = current_frame
                            frame_offset = current_frame - self.stats.get('frame_start', 1) + 1
                            self.stats['frames_rendered'] = max(self.stats['frames_rendered'], frame_offset)
                            
                            if self.stats['total_frames'] > 0:
                                progress = (self.stats['frames_rendered'] / self.stats['total_frames']) * 100.0
                                progress = min(progress, 99.0)  # 100%は完了時のみ
                                
                                # 残り時間推定
                                if frame_start_time and self.stats['frames_rendered'] > 1:
                                    elapsed = time.time() - frame_start_time
                                    avg_time_per_frame = elapsed / self.stats['frames_rendered']
                                    remaining_frames = self.stats['total_frames'] - self.stats['frames_rendered']
                                    eta_seconds = remaining_frames * avg_time_per_frame
                                    eta_minutes = eta_seconds / 60
                                    
                                    message = f"フレーム {current_frame} 完了 ({self.stats['frames_rendered']}/{self.stats['total_frames']}) - 残り約{eta_minutes:.1f}分"
                                else:
                                    message = f"フレーム {current_frame} 完了 ({self.stats['frames_rendered']}/{self.stats['total_frames']})"
                                
                                self._update_progress(progress, message)
                                
                                if frame_start_time is None:
                                    frame_start_time = time.time()
                        
                        # GPU使用状況の監視
                        if "CUDA" in line or "GPU" in line or "OPTIX" in line:
                            self._log(f"GPU情報: {line}")
                        
                        # エラー・警告の記録
                        if 'ERROR' in line or 'Error' in line:
                            self.stats['errors'].append(line)
                        elif 'WARNING' in line or 'Warning' in line:
                            self.stats['warnings'].append(line)
                
                time.sleep(0.1)
                
            except Exception as e:
                self._log(f"進捗監視エラー: {e}")
                break
    
    def cancel_render(self) -> bool:
        """レンダリングキャンセル"""
        if not self.is_running or not self.process:
            return False
        
        try:
            self.process.terminate()
            
            # プロセス終了待ち
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
            
            self.is_running = False
            self._log("レンダリングがキャンセルされました")
            return True
            
        except Exception as e:
            self._log(f"レンダリングキャンセルエラー: {e}")
            return False
        finally:
            self._cleanup_temp_files()
    
    def _cleanup_temp_files(self) -> None:
        """一時ファイルクリーンアップ"""
        if self.temp_script_path and os.path.exists(self.temp_script_path):
            try:
                os.remove(self.temp_script_path)
                self.temp_script_path = None
            except Exception as e:
                logger.warning(f"一時ファイル削除警告: {e}")
    
    def get_render_stats(self) -> Dict[str, Any]:
        """レンダリング統計取得"""
        stats = self.stats.copy()
        
        if stats['start_time'] and stats['end_time']:
            stats['total_time'] = stats['end_time'] - stats['start_time']
            if stats['frames_rendered'] > 0:
                stats['time_per_frame'] = stats['total_time'] / stats['frames_rendered']
            else:
                stats['time_per_frame'] = 0
        else:
            stats['total_time'] = 0
            stats['time_per_frame'] = 0
        
        stats['completion_rate'] = (stats['frames_rendered'] / stats['total_frames']) * 100 if stats['total_frames'] > 0 else 0
        
        return stats
    
    def validate_blend_file(self, blend_file: str) -> Dict[str, Any]:
        """Blendファイルの検証"""
        if not os.path.exists(blend_file):
            return {'valid': False, 'error': 'ファイルが存在しません'}
        
        try:
            # Blenderでファイル情報取得
            info_script = '''
import bpy
import json

info = {
    "scene_name": bpy.context.scene.name,
    "render_engine": bpy.context.scene.render.engine,
    "frame_start": bpy.context.scene.frame_start,
    "frame_end": bpy.context.scene.frame_end,
    "resolution_x": bpy.context.scene.render.resolution_x,
    "resolution_y": bpy.context.scene.render.resolution_y,
    "cameras": [obj.name for obj in bpy.data.objects if obj.type == 'CAMERA'],
    "lights": [obj.name for obj in bpy.data.objects if obj.type == 'LIGHT'],
    "meshes": len([obj for obj in bpy.data.objects if obj.type == 'MESH']),
    "materials": len(bpy.data.materials)
}

print("BLEND_INFO:" + json.dumps(info, ensure_ascii=False))
'''
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
                f.write(info_script)
                info_script_path = f.name
            
            try:
                cmd = [self.blender_path, '-b', blend_file, '-P', info_script_path]
                result = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=60,
                    encoding='utf-8', errors='replace'
                )
                
                # 出力からファイル情報を抽出
                for line in result.stdout.split('\n'):
                    if line.startswith('BLEND_INFO:'):
                        info_data = json.loads(line[11:])
                        info_data['valid'] = True
                        return info_data
                
                return {'valid': False, 'error': 'ファイル情報の取得に失敗'}
                
            finally:
                os.remove(info_script_path)
                
        except subprocess.TimeoutExpired:
            return {'valid': False, 'error': 'ファイル検証タイムアウト'}
        except Exception as e:
            return {'valid': False, 'error': f'検証エラー: {e}'}
    
    def estimate_render_time(self, blend_file: str, settings: Dict[str, Any]) -> Dict[str, float]:
        """レンダリング時間推定"""
        try:
            # 単一フレームでテストレンダリング
            test_settings = settings.copy()
            test_settings.update({
                'frame_start': settings.get('frame_start', 1),
                'frame_end': settings.get('frame_start', 1),  # 1フレームのみ
                'samples': min(settings.get('samples', 128), 32)  # サンプル数制限
            })
            
            # テスト用出力ディレクトリ
            with tempfile.TemporaryDirectory() as temp_dir:
                start_time = time.time()
                
                # テストレンダリング実行
                if self.render(blend_file, temp_dir, test_settings):
                    test_time = time.time() - start_time
                    
                    # 実際の設定での推定時間計算
                    sample_ratio = settings.get('samples', 128) / test_settings['samples']
                    frame_count = settings.get('frame_end', 250) - settings.get('frame_start', 1) + 1
                    
                    estimated_time_per_frame = test_time * sample_ratio
                    estimated_total_time = estimated_time_per_frame * frame_count
                    
                    return {
                        'test_time': test_time,
                        'estimated_time_per_frame': estimated_time_per_frame,
                        'estimated_total_time': estimated_total_time,
                        'estimated_hours': estimated_total_time / 3600
                    }
                else:
                    return {'error': 'テストレンダリング失敗'}
                    
        except Exception as e:
            return {'error': f'時間推定エラー: {e}'}
    
    def __del__(self):
        """デストラクタ"""
        if self.is_running:
            self.cancel_render()
        self._cleanup_temp_files()
