# -*- coding: utf-8 -*-
"""
Blender Engine - Enhanced Render Pipeline
Blenderエンジンの管理とレンダリング制御
"""

import os
import sys
import subprocess
import tempfile
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

# UTF-8エンコーディング設定
if sys.platform.startswith('win'):
    os.environ['PYTHONIOENCODING'] = 'utf-8'

logger = logging.getLogger(__name__)


class BlenderEngine:
    """Blenderエンジン管理クラス"""
    
    def __init__(self, blender_path: Optional[str] = None):
        self.blender_path = blender_path or self._find_blender()
        self.validate_blender()
        
    def _find_blender(self) -> str:
        """Blenderの実行パスを検出"""
        possible_paths = [
            r"C:\Program Files\Blender Foundation\Blender 4.5\blender.exe",
            r"C:\Program Files\Blender Foundation\Blender 4.4\blender.exe", 
            r"C:\Program Files\Blender Foundation\Blender 4.3\blender.exe",
            "blender"  # PATH環境変数
        ]
        
        for path in possible_paths:
            if path == "blender" or os.path.exists(path):
                return path
                
        raise FileNotFoundError("Blenderが見つかりません")
    
    def validate_blender(self) -> None:
        """Blenderの有効性検証"""
        try:
            result = subprocess.run(
                [self.blender_path, '--version'], 
                capture_output=True, text=True, timeout=30
            )
            if result.returncode != 0:
                raise RuntimeError("Blender実行エラー")
            logger.info("Blender検証完了")
        except Exception as e:
            raise RuntimeError(f"Blender検証失敗: {e}")
    
    def get_blend_info(self, blend_file: str) -> Dict[str, Any]:
        """Blendファイル情報取得"""
        info_script = '''
import bpy
import json

info = {
    "name": bpy.path.basename(bpy.data.filepath),
    "frame_start": bpy.context.scene.frame_start,
    "frame_end": bpy.context.scene.frame_end,
    "resolution_x": bpy.context.scene.render.resolution_x,
    "resolution_y": bpy.context.scene.render.resolution_y,
    "cameras": [obj.name for obj in bpy.data.objects if obj.type == 'CAMERA'],
    "lights": [obj.name for obj in bpy.data.objects if obj.type == 'LIGHT'],
    "meshes": len([obj for obj in bpy.data.objects if obj.type == 'MESH']),
    "materials": len(bpy.data.materials),
    "has_animation": any(obj.animation_data for obj in bpy.data.objects if obj.animation_data)
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
            
            for line in result.stdout.split('\n'):
                if line.startswith('BLEND_INFO:'):
                    return json.loads(line[11:])
            
            raise RuntimeError("ファイル情報取得失敗")
            
        finally:
            os.unlink(info_script_path)
    
    def render_frame_sequence(self, blend_file: str, output_path: str, 
                            frame_start: int, frame_end: int,
                            engine: str = "CYCLES", device: str = "GPU",
                            samples: int = 128, **kwargs) -> None:
        """フレームシーケンスレンダリング"""
        
        render_script = f'''
import bpy

# レンダリング設定
scene = bpy.context.scene
scene.render.engine = '{engine}'
scene.render.filepath = '{output_path}'
scene.frame_start = {frame_start}
scene.frame_end = {frame_end}

if '{engine}' == 'CYCLES':
    scene.cycles.samples = {samples}
    if '{device}' == 'GPU':
        bpy.context.preferences.addons['cycles'].preferences.compute_device_type = 'CUDA'
        scene.cycles.device = 'GPU'

# レンダリング実行
bpy.ops.render.render(animation=True)
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write(render_script)
            script_path = f.name
        
        try:
            cmd = [
                self.blender_path, '-b', blend_file, 
                '-P', script_path, '--'
            ]
            
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, encoding='utf-8'
            )
            
            return process
            
        finally:
            os.unlink(script_path)
    
    def optimize_for_render(self) -> None:
        """レンダリング最適化"""
        logger.info("Blenderエンジン最適化実行")
    
    def get_render_progress(self, output: str) -> Optional[int]:
        """レンダリング進捗解析"""
        if "Fra:" in output:
            try:
                frame_part = output.split("Fra:")[1].split()[0]
                return int(frame_part)
            except (ValueError, IndexError):
                pass
        return None
