# -*- coding: utf-8 -*-
"""
Settings Manager Module
PyPy最適化対応設定管理モジュール
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional, Union
import logging

# UTF-8エンコーディング設定
if sys.platform.startswith('win'):
    os.environ['PYTHONIOENCODING'] = 'utf-8'

logger = logging.getLogger(__name__)

class SettingsManager:
    """設定管理クラス"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        self.default_settings_file = self.config_dir / "default_settings.json"
        self.user_settings_file = self.config_dir / "user_settings.json"
        
        # デフォルト設定
        self.default_settings = {
            # ファイル設定
            "blend_file": "",
            "output_dir": "",
            
            # レンダリング設定
            "frame_start": 1,
            "frame_end": 250,
            "resolution_x": 1920,
            "resolution_y": 1080,
            "resolution_percentage": 100,
            "samples": 128,
            "render_engine": "CYCLES",
            "use_gpu": True,
            "use_denoising": True,
            "tile_x": 256,
            "tile_y": 256,
            
            # AI処理設定
            "denoise_method": "OIDN",
            "denoise_strength": 1.0,
            "enable_upscale": False,
            "upscale_factor": 2,
            "upscale_model": "realesrgan-x4plus-anime",
            "enable_interpolation": False,
            "interpolation_method": "optical_flow",
            "interpolation_factor": 2,
            
            # 出力設定
            "output_format": "PNG",
            "output_codec": "prores_ks",
            "output_framerate": 30,
            "output_quality": "high",
            "output_bitrate": "",
            
            # システム設定
            "use_cuda": True,
            "max_memory_usage": 0.8,
            "cpu_threads": os.cpu_count() or 4,
            "gpu_device_id": 0,
            "temp_dir": "",
            
            # ツールパス設定
            "blender_path": "",
            "ffmpeg_path": "",
            "oidn_path": "",
            "realesrgan_path": "",
            "rife_path": "",
            "fastdvdnet_path": "",
            
            # UI設定
            "window_width": 1200,
            "window_height": 800,
            "log_level": "INFO",
            "auto_save_settings": True,
            "show_advanced_options": False,
            
            # 実験的機能
            "experimental_features": False,
            "debug_mode": False
        }
        
        self.current_settings = self.default_settings.copy()
        self._initialize_settings()
        
        logger.info("設定管理モジュール初期化完了")
    
    def _initialize_settings(self):
        """設定初期化"""
        # デフォルト設定ファイル作成
        self._save_default_settings()
        
        # ユーザー設定読み込み
        self.load_user_settings()
    
    def _save_default_settings(self):
        """デフォルト設定保存"""
        try:
            with open(self.default_settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.default_settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"デフォルト設定保存エラー: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """設定値取得"""
        return self.current_settings.get(key, default)
    
    def set(self, key: str, value: Any) -> bool:
        """設定値設定"""
        try:
            self.current_settings[key] = value
            
            # 自動保存が有効な場合
            if self.get("auto_save_settings", True):
                self.save_user_settings()
            
            return True
        except Exception as e:
            logger.error(f"設定値設定エラー ({key}): {e}")
            return False
    
    def update(self, settings_dict: Dict[str, Any]) -> bool:
        """複数設定値一括更新"""
        try:
            self.current_settings.update(settings_dict)
            
            if self.get("auto_save_settings", True):
                self.save_user_settings()
            
            logger.info(f"設定一括更新完了: {len(settings_dict)}項目")
            return True
        except Exception as e:
            logger.error(f"設定一括更新エラー: {e}")
            return False
    
    def load_user_settings(self) -> bool:
        """ユーザー設定読み込み"""
        try:
            if self.user_settings_file.exists():
                with open(self.user_settings_file, 'r', encoding='utf-8') as f:
                    user_settings = json.load(f)
                
                # デフォルト設定にユーザー設定をマージ
                self.current_settings.update(user_settings)
                
                logger.info("ユーザー設定読み込み完了")
                return True
            else:
                logger.info("ユーザー設定ファイルが存在しません。デフォルト設定を使用")
                return False
                
        except Exception as e:
            logger.error(f"ユーザー設定読み込みエラー: {e}")
            return False
    
    def save_user_settings(self) -> bool:
        """ユーザー設定保存"""
        try:
            # デフォルト設定と異なる項目のみ保存
            user_settings = {}
            for key, value in self.current_settings.items():
                if key not in self.default_settings or self.default_settings[key] != value:
                    user_settings[key] = value
            
            with open(self.user_settings_file, 'w', encoding='utf-8') as f:
                json.dump(user_settings, f, ensure_ascii=False, indent=2)
            
            logger.info(f"ユーザー設定保存完了: {len(user_settings)}項目")
            return True
            
        except Exception as e:
            logger.error(f"ユーザー設定保存エラー: {e}")
            return False
    
    def load_settings_from_file(self, file_path: Union[str, Path]) -> bool:
        """ファイルから設定読み込み"""
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                logger.error(f"設定ファイルが存在しません: {file_path}")
                return False
            
            with open(file_path, 'r', encoding='utf-8') as f:
                loaded_settings = json.load(f)
            
            # 現在の設定に上書き
            self.current_settings.update(loaded_settings)
            
            logger.info(f"設定ファイル読み込み完了: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"設定ファイル読み込みエラー: {e}")
            return False
    
    def save_settings_to_file(self, file_path: Union[str, Path]) -> bool:
        """設定をファイルに保存"""
        try:
            file_path = Path(file_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.current_settings, f, ensure_ascii=False, indent=2)
            
            logger.info(f"設定ファイル保存完了: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"設定ファイル保存エラー: {e}")
            return False
    
    def reset_to_defaults(self) -> bool:
        """デフォルト設定にリセット"""
        try:
            self.current_settings = self.default_settings.copy()
            
            # ユーザー設定ファイル削除
            if self.user_settings_file.exists():
                self.user_settings_file.unlink()
            
            logger.info("設定をデフォルトにリセットしました")
            return True
            
        except Exception as e:
            logger.error(f"設定リセットエラー: {e}")
            return False
    
    def validate_settings(self) -> Dict[str, str]:
        """設定値検証"""
        errors = {}
        
        # フレーム範囲検証
        frame_start = self.get("frame_start", 1)
        frame_end = self.get("frame_end", 250)
        
        if frame_start < 1:
            errors["frame_start"] = "フレーム開始は1以上である必要があります"
        
        if frame_end < frame_start:
            errors["frame_end"] = "フレーム終了は開始フレーム以上である必要があります"
        
        # 解像度検証
        res_x = self.get("resolution_x", 1920)
        res_y = self.get("resolution_y", 1080)
        
        if res_x < 1 or res_x > 16384:
            errors["resolution_x"] = "解像度Xは1-16384の範囲である必要があります"
        
        if res_y < 1 or res_y > 16384:
            errors["resolution_y"] = "解像度Yは1-16384の範囲である必要があります"
        
        # サンプル数検証
        samples = self.get("samples", 128)
        if samples < 1 or samples > 10000:
            errors["samples"] = "サンプル数は1-10000の範囲である必要があります"
        
        # ファイルパス検証
        blend_file = self.get("blend_file", "")
        if blend_file and not os.path.exists(blend_file):
            errors["blend_file"] = "Blendファイルが存在しません"
        
        output_dir = self.get("output_dir", "")
        if output_dir and not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir, exist_ok=True)
            except:
                errors["output_dir"] = "出力ディレクトリの作成に失敗しました"
        
        # ツールパス検証
        tool_paths = {
            "blender_path": "Blender",
            "ffmpeg_path": "FFmpeg",
            "oidn_path": "OIDN",
            "realesrgan_path": "Real-ESRGAN",
            "rife_path": "RIFE"
        }
        
        for key, name in tool_paths.items():
            path = self.get(key, "")
            if path and not os.path.exists(path):
                errors[key] = f"{name}のパスが正しくありません: {path}"
        
        return errors
    
    def get_render_settings(self) -> Dict[str, Any]:
        """レンダリング用設定取得"""
        return {
            "frame_start": self.get("frame_start"),
            "frame_end": self.get("frame_end"),
            "resolution_x": self.get("resolution_x"),
            "resolution_y": self.get("resolution_y"),
            "resolution_percentage": self.get("resolution_percentage"),
            "samples": self.get("samples"),
            "render_engine": self.get("render_engine"),
            "use_gpu": self.get("use_gpu"),
            "use_denoising": self.get("use_denoising"),
            "tile_x": self.get("tile_x"),
            "tile_y": self.get("tile_y"),
        }
    
    def get_ai_settings(self) -> Dict[str, Any]:
        """AI処理用設定取得"""
        return {
            "denoise_method": self.get("denoise_method"),
            "denoise_strength": self.get("denoise_strength"),
            "enable_upscale": self.get("enable_upscale"),
            "upscale_factor": self.get("upscale_factor"),
            "upscale_model": self.get("upscale_model"),
            "enable_interpolation": self.get("enable_interpolation"),
            "interpolation_method": self.get("interpolation_method"),
            "interpolation_factor": self.get("interpolation_factor"),
        }
    
    def get_output_settings(self) -> Dict[str, Any]:
        """出力用設定取得"""
        return {
            "output_format": self.get("output_format"),
            "output_codec": self.get("output_codec"),
            "output_framerate": self.get("output_framerate"),
            "output_quality": self.get("output_quality"),
            "output_bitrate": self.get("output_bitrate"),
        }
    
    def get_system_settings(self) -> Dict[str, Any]:
        """システム用設定取得"""
        return {
            "use_cuda": self.get("use_cuda"),
            "max_memory_usage": self.get("max_memory_usage"),
            "cpu_threads": self.get("cpu_threads"),
            "gpu_device_id": self.get("gpu_device_id"),
            "temp_dir": self.get("temp_dir"),
        }
    
    def auto_detect_tool_paths(self) -> Dict[str, str]:
        """ツールパス自動検出"""
        detected_paths = {}
        
        # Blender検出
        blender_candidates = [
            r"C:\Program Files\Blender Foundation\Blender 4.5\blender.exe",
            r"C:\Program Files\Blender Foundation\Blender 4.4\blender.exe",
            r"C:\Program Files\Blender Foundation\Blender 4.3\blender.exe",
            "/usr/bin/blender",
            "/usr/local/bin/blender",
            "/Applications/Blender.app/Contents/MacOS/Blender"
        ]
        
        for path in blender_candidates:
            if os.path.exists(path):
                detected_paths["blender_path"] = path
                break
        
        # FFmpeg検出
        try:
            import subprocess
            result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                detected_paths["ffmpeg_path"] = "ffmpeg"
        except:
            # Windowsの場合の候補
            ffmpeg_candidates = [
                r"C:\ffmpeg\bin\ffmpeg.exe",
                r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"
            ]
            for path in ffmpeg_candidates:
                if os.path.exists(path):
                    detected_paths["ffmpeg_path"] = path
                    break
        
        # 他のツールパス検出も同様に実装可能
        
        # 検出された設定を更新
        if detected_paths:
            self.update(detected_paths)
            logger.info(f"ツールパス自動検出完了: {list(detected_paths.keys())}")
        
        return detected_paths
    
    def export_settings(self, file_path: Union[str, Path], include_sensitive: bool = False) -> bool:
        """設定エクスポート"""
        try:
            export_settings = self.current_settings.copy()
            
            # 機密情報除外
            if not include_sensitive:
                sensitive_keys = ["temp_dir", "debug_mode"]
                for key in sensitive_keys:
                    export_settings.pop(key, None)
            
            # メタデータ追加
            export_data = {
                "metadata": {
                    "version": "1.0.0",
                    "exported_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "include_sensitive": include_sensitive
                },
                "settings": export_settings
            }
            
            file_path = Path(file_path)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"設定エクスポート完了: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"設定エクスポートエラー: {e}")
            return False
    
    def import_settings(self, file_path: Union[str, Path]) -> bool:
        """設定インポート"""
        try:
            file_path = Path(file_path)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # メタデータ確認
            if "metadata" in import_data and "settings" in import_data:
                settings_to_import = import_data["settings"]
                metadata = import_data["metadata"]
                logger.info(f"設定インポート - バージョン: {metadata.get('version', 'Unknown')}")
            else:
                # 旧形式
                settings_to_import = import_data
            
            # 既存設定に統合
            self.current_settings.update(settings_to_import)
            
            # 設定検証
            errors = self.validate_settings()
            if errors:
                logger.warning(f"インポート後の設定に問題があります: {errors}")
            
            logger.info(f"設定インポート完了: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"設定インポートエラー: {e}")
            return False
    
    def __str__(self) -> str:
        """文字列表現"""
        return f"SettingsManager(項目数: {len(self.current_settings)})"
    
    def __repr__(self) -> str:
        """詳細文字列表現"""
        return f"SettingsManager(config_dir='{self.config_dir}', settings_count={len(self.current_settings)})"


# シングルトンパターン
_settings_manager_instance = None

def get_settings_manager() -> SettingsManager:
    """設定管理シングルトンインスタンス取得"""
    global _settings_manager_instance
    if _settings_manager_instance is None:
        _settings_manager_instance = SettingsManager()
    return _settings_manager_instance
