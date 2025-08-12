# -*- coding: utf-8 -*-
"""
最小限CLIレンダリングシステム
GUI要素を完全に排除し、直接的な機能テスト用
"""

import os
import sys
import subprocess
import time
import tempfile
import argparse
import json
from pathlib import Path

# Blenderパス設定
BLENDER_PATHS = [
    r"C:\Program Files\Blender Foundation\Blender 4.5\blender.exe",
    r"C:\Program Files\Blender Foundation\Blender 4.4\blender.exe",
    r"C:\Program Files\Blender Foundation\Blender 4.3\blender.exe",
    r"C:\Program Files\Blender Foundation\Blender 4.2\blender.exe",
    r"C:\Program Files\Blender Foundation\Blender 4.1\blender.exe",
    r"C:\Program Files\Blender Foundation\Blender 4.0\blender.exe",
]

def find_blender():
    """Blenderパスを検出"""
    for path in BLENDER_PATHS:
        if os.path.exists(path):
            print(f"✅ Blender検出: {path}")
            return path
    
    print("❌ Blenderが見つかりません")
    return None

def create_test_script(frame_start, frame_end, output_path, samples=32, use_gpu=True):
    """テスト用Blenderスクリプト生成"""
    script_content = f'''
import bpy
import sys

print("=== CLI TEST SCRIPT START ===")

try:
    scene = bpy.context.scene
    
    # フレーム範囲設定
    scene.frame_start = {frame_start}
    scene.frame_end = {frame_end}
    print(f"フレーム設定: {{scene.frame_start}} - {{scene.frame_end}}")
    
    # 解像度設定
    scene.render.resolution_x = 640
    scene.render.resolution_y = 480
    scene.render.resolution_percentage = 100
    print(f"解像度: {{scene.render.resolution_x}}x{{scene.render.resolution_y}}")
    
    # Cyclesエンジン設定
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = {samples}
    print(f"サンプル数: {{scene.cycles.samples}}")
    
    # GPU設定
    if {str(use_gpu).lower()}:
        preferences = bpy.context.preferences
        cycles_preferences = preferences.addons["cycles"].preferences
        cycles_preferences.refresh_devices()
        
        print("GPU デバイス検索...")
        gpu_found = False
        
        # 全デバイス無効化
        for device in cycles_preferences.devices:
            device.use = False
        
        # GPU有効化
        for device in cycles_preferences.devices:
            print(f"デバイス: {{device.name}} ({{device.type}})")
            if device.type in ['OPTIX', 'CUDA', 'OPENCL', 'HIP']:
                device.use = True
                gpu_found = True
                print(f"  -> GPU有効: {{device.name}}")
        
        if gpu_found:
            scene.cycles.device = 'GPU'
            print("GPU レンダリングモード")
        else:
            scene.cycles.device = 'CPU'
            print("GPU未検出: CPUモード")
    else:
        scene.cycles.device = 'CPU'
        print("CPU レンダリングモード")
    
    # 出力設定
    scene.render.image_settings.file_format = 'PNG'
    scene.render.filepath = r"{output_path}"
    print(f"出力: {{scene.render.filepath}}")
    
    # デフォルトオブジェクト確認/作成
    if not bpy.data.objects or len([obj for obj in bpy.data.objects if obj.type == 'MESH']) == 0:
        print("テストオブジェクト作成中...")
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        bpy.ops.object.shade_smooth()
    
    # カメラ確認/作成
    if not scene.camera:
        print("テストカメラ作成中...")
        bpy.ops.object.camera_add(location=(7, -7, 5))
        bpy.ops.object.constraint_add(type='TRACK_TO')
        scene.camera = bpy.context.object
    
    # ライト確認/作成
    if len([obj for obj in bpy.data.objects if obj.type == 'LIGHT']) == 0:
        print("テストライト作成中...")
        bpy.ops.object.light_add(type='SUN', location=(5, 5, 10))
    
    print("\\n=== レンダリング開始 ===")
    
    # レンダリング実行
    bpy.ops.render.render(animation=True)
    
    print("=== レンダリング完了 ===")

except Exception as e:
    print(f"ERROR: {{e}}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
'''
    
    # 一時ファイル作成
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        f.write(script_content)
        return f.name

def run_render_test(blender_path, frame_start, frame_end, output_dir, samples=32, use_gpu=True):
    """レンダリングテスト実行"""
    print(f"\n🚀 レンダリングテスト開始")
    print(f"フレーム範囲: {frame_start} - {frame_end}")
    print(f"サンプル数: {samples}")
    print(f"GPU使用: {use_gpu}")
    print(f"出力先: {output_dir}")
    
    # 出力ディレクトリ作成
    os.makedirs(output_dir, exist_ok=True)
    
    # スクリプト生成
    output_path = os.path.join(output_dir, "test_").replace('\\', '/')
    script_path = create_test_script(frame_start, frame_end, output_path, samples, use_gpu)
    
    try:
        # Blenderコマンド実行
        cmd = [
            blender_path,
            '--background',
            '--python', script_path,
            '--',
            '--frame-start', str(frame_start),
            '--frame-end', str(frame_end)
        ]
        
        print(f"\n📋 実行コマンド:")
        print(' '.join(cmd))
        print(f"\n📜 ログ出力:")
        print("-" * 50)
        
        start_time = time.time()
        
        # プロセス実行
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        # リアルタイムログ出力
        frame_count = 0
        for line in process.stdout:
            line = line.strip()
            if line:
                print(line)
                
                # フレーム完了カウント
                if 'Fra:' in line or 'Frame' in line:
                    frame_count += 1
        
        process.wait()
        end_time = time.time()
        
        print("-" * 50)
        print(f"🏁 実行完了")
        print(f"所要時間: {end_time - start_time:.2f}秒")
        print(f"終了コード: {process.returncode}")
        
        # 結果ファイル確認
        output_files = []
        for i in range(frame_start, frame_end + 1):
            expected_file = os.path.join(output_dir, f"test_{i:04d}.png")
            if os.path.exists(expected_file):
                output_files.append(expected_file)
                file_size = os.path.getsize(expected_file)
                print(f"✅ {expected_file} ({file_size} bytes)")
            else:
                print(f"❌ {expected_file} (見つかりません)")
        
        expected_count = frame_end - frame_start + 1
        actual_count = len(output_files)
        
        print(f"\n📊 結果サマリー:")
        print(f"期待フレーム数: {expected_count}")
        print(f"実際フレーム数: {actual_count}")
        print(f"成功率: {actual_count/expected_count*100:.1f}%")
        
        if process.returncode == 0 and actual_count == expected_count:
            print("🎉 テスト成功!")
            return True
        else:
            print("❌ テスト失敗")
            return False
            
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False
    finally:
        # クリーンアップ
        if os.path.exists(script_path):
            os.remove(script_path)

def gpu_info_test():
    """GPU情報テスト"""
    print("\n🔍 GPU情報テスト")
    
    try:
        # nvidia-smi で NVIDIA GPU確認
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ NVIDIA GPUが検出されました")
            lines = result.stdout.split('\n')
            for line in lines:
                if 'GeForce' in line or 'RTX' in line or 'GTX' in line:
                    print(f"GPU: {line.strip()}")
        else:
            print("❌ nvidia-smi が利用できません")
    except FileNotFoundError:
        print("❌ nvidia-smi が見つかりません")
    
    # PyTorch GPU確認
    try:
        import torch
        if torch.cuda.is_available():
            device_count = torch.cuda.device_count()
            print(f"✅ PyTorch CUDA対応: {device_count}デバイス")
            for i in range(device_count):
                name = torch.cuda.get_device_name(i)
                print(f"  デバイス{i}: {name}")
        else:
            print("❌ PyTorch CUDA利用不可")
    except ImportError:
        print("⚠️  PyTorch未インストール")

def create_test_blend_file(output_path):
    """テスト用Blendファイル作成"""
    blender_path = find_blender()
    if not blender_path:
        return False
    
    script = '''
import bpy

# シーンクリア
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# テストオブジェクト作成
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
cube = bpy.context.object
cube.name = "TestCube"

# マテリアル追加
mat = bpy.data.materials.new(name="TestMaterial")
mat.use_nodes = True
mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (0.8, 0.2, 0.2, 1.0)
cube.data.materials.append(mat)

# カメラ設定
bpy.ops.object.camera_add(location=(7, -7, 5))
camera = bpy.context.object
bpy.context.scene.camera = camera

# カメラをオブジェクトに向ける
bpy.ops.object.constraint_add(type='TRACK_TO')
camera.constraints["Track To"].target = cube

# ライト追加
bpy.ops.object.light_add(type='SUN', location=(5, 5, 10))
light = bpy.context.object
light.data.energy = 3

# アニメーション追加（回転）
cube.rotation_euler = (0, 0, 0)
cube.keyframe_insert(data_path="rotation_euler", frame=1)
cube.rotation_euler = (0, 0, 6.28)  # 360度
cube.keyframe_insert(data_path="rotation_euler", frame=30)

# フレーム設定
bpy.context.scene.frame_start = 1
bpy.context.scene.frame_end = 30

# レンダリング設定
bpy.context.scene.render.engine = 'CYCLES'
bpy.context.scene.cycles.samples = 64
bpy.context.scene.render.resolution_x = 1280
bpy.context.scene.render.resolution_y = 720

# ファイル保存
bpy.ops.wm.save_as_mainfile(filepath=r"{}")

print("テストBlendファイル作成完了")
'''.format(output_path.replace('\\', '\\\\'))
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        f.write(script)
        script_path = f.name
    
    try:
        cmd = [blender_path, '--background', '--python', script_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0 and os.path.exists(output_path):
            print(f"✅ テストBlendファイル作成: {output_path}")
            return True
        else:
            print(f"❌ テストBlendファイル作成失敗")
            print(result.stdout)
            print(result.stderr)
            return False
    finally:
        os.remove(script_path)

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='Blender CLI レンダリングテスト')
    parser.add_argument('--blend-file', help='Blendファイルパス（未指定時は自動生成）')
    parser.add_argument('--frame-start', type=int, default=1, help='開始フレーム')
    parser.add_argument('--frame-end', type=int, default=3, help='終了フレーム')
    parser.add_argument('--samples', type=int, default=32, help='サンプル数')
    parser.add_argument('--output-dir', default='./test_output', help='出力ディレクトリ')
    parser.add_argument('--gpu', action='store_true', default=True, help='GPU使用')
    parser.add_argument('--cpu', action='store_true', help='CPU使用（GPUを無効）')
    parser.add_argument('--gpu-info', action='store_true', help='GPU情報のみ表示')
    parser.add_argument('--create-test-file', help='テスト用Blendファイル作成')
    
    args = parser.parse_args()
    
    print("🎬 Blender CLI レンダリングテスト システム")
    print("=" * 50)
    
    # GPU情報テストのみ
    if args.gpu_info:
        gpu_info_test()
        return
    
    # テストファイル作成のみ
    if args.create_test_file:
        if create_test_blend_file(args.create_test_file):
            print(f"テストファイル作成完了: {args.create_test_file}")
        return
    
    # Blender検出
    blender_path = find_blender()
    if not blender_path:
        print("❌ Blenderが見つかりません。インストールを確認してください。")
        return
    
    # GPU設定
    use_gpu = args.gpu and not args.cpu
    
    # Blendファイル準備
    blend_file = args.blend_file
    if not blend_file:
        # 自動生成
        blend_file = os.path.join(args.output_dir, 'test_scene.blend')
        os.makedirs(args.output_dir, exist_ok=True)
        
        print(f"📁 テストBlendファイル自動生成中...")
        if not create_test_blend_file(blend_file):
            print("❌ テストファイル生成失敗")
            return
    
    if not os.path.exists(blend_file):
        print(f"❌ Blendファイルが見つかりません: {blend_file}")
        return
    
    print(f"📂 使用Blendファイル: {blend_file}")
    
    # GPU情報表示
    gpu_info_test()
    
    # レンダリングテスト実行
    success = run_render_test(
        blender_path=blender_path,
        frame_start=args.frame_start,
        frame_end=args.frame_end,
        output_dir=args.output_dir,
        samples=args.samples,
        use_gpu=use_gpu
    )
    
    if success:
        print("\n🎉 全テスト完了！")
    else:
        print("\n❌ テスト失敗")

if __name__ == "__main__":
    main()
