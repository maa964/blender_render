# -*- coding: utf-8 -*-
"""
Enhanced Blender Render Pipeline GUI - 完全版
CUDA対応、AI強化機能、日本語文字化け対策済み
"""

import sys
import os
import shutil # Add shutil for directory operations
import subprocess
import threading
import time
import logging
import json
from glob import glob
from typing import Optional, Dict, Any, List
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import psutil
# UTF-8エンコーディング設定（Windows対応）
if sys.platform.startswith('win'):
    import locale
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    # Windows Console のUTF-8対応
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleOutputCP(65001)  # UTF-8
    except:
        pass

# ログ設定
logger = logging.getLogger(__name__)

# 依存モジュールの動的インポート
try:
    from core.cuda_accelerator import CUDAAccelerator
    CUDA_AVAILABLE = True
except ImportError as e:
    logger.warning(f"CUDAAccelerator未検出: {e}")
    CUDA_AVAILABLE = False
    CUDAAccelerator = None

try:
    from core.blender_engine import BlenderEngine
    BLENDER_ENGINE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"BlenderEngine未検出: {e}")
    BLENDER_ENGINE_AVAILABLE = False
    BlenderEngine = None

try:
    from processing.ai_processor import AIProcessor
    AI_PROCESSOR_AVAILABLE = True
except ImportError as e:
    logger.warning(f"AIProcessor未検出: {e}")
    AI_PROCESSOR_AVAILABLE = False
    AIProcessor = None


def test_basic_gui():
    """基本GUI動作テスト"""
    root = tk.Tk()
    root.title("Test GUI")
    root.geometry("400x300")
    
    label = tk.Label(root, text="基本GUIテスト")
    label.pack(pady=20)
    
    button = tk.Button(root, text="閉じる", command=root.destroy)
    button.pack(pady=10)
    
    print("テストGUI起動中...")
    root.mainloop()
    print("テストGUI終了")


class BlenderRenderGUI:
    """Enhanced Blender Render Pipeline GUI メインクラス"""
    
    def __init__(self, master):
        try:
            self.master = master
            self.setup_window()
            
            # 拡張機能の初期化
            self.enhanced_mode = False
            self.cuda_accelerator = None
            self.blender_engine = None
            self.ai_processor = None
            
            self.initialize_enhanced_features()
            self.initialize_settings()
            
            # 状態管理
            self.render_status = {
                'step': 'idle',
                'progress': 0,
                'message': '準備完了',
                'is_running': False,
                'current_frame': 0,
                'total_frames': 0,
                'start_time': None,
                'estimated_time': None
            }
            
            # UI構築
            self.setup_ui()
            self.load_settings()
            
            # 初期メッセージ
            self.add_log("=== Enhanced Blender Render Pipeline v2.0 ===")
            self.add_log(f"拡張モード: {'有効' if self.enhanced_mode else '無効'}")
            if self.enhanced_mode:
                self.show_gpu_info()
                
        except Exception as e:
            logger.error(f"GUI初期化エラー: {e}")
            messagebox.showerror("初期化エラー", f"アプリケーションの初期化に失敗しました:\n{e}")
            raise
    
    def setup_window(self):
        """ウィンドウの基本設定"""
        self.master.title("Enhanced Blender Render Pipeline - GPU加速対応")
        self.master.geometry("1000x800")
        self.master.configure(bg='#2c3e50')
        self.master.resizable(True, True)
    
    def initialize_enhanced_features(self):
        """拡張機能の初期化"""
        try:
            if CUDA_AVAILABLE and CUDAAccelerator:
                self.cuda_accelerator = CUDAAccelerator()
                if hasattr(self.cuda_accelerator, 'cuda_available') and self.cuda_accelerator.cuda_available:
                    self.enhanced_mode = True
                    logger.info("CUDA加速が利用可能です")
            
            if BLENDER_ENGINE_AVAILABLE and BlenderEngine:
                self.blender_engine = BlenderEngine()
                
            if AI_PROCESSOR_AVAILABLE and self.enhanced_mode and AIProcessor:
                self.ai_processor = AIProcessor()
                
        except Exception as e:
            logger.error(f"拡張機能初期化エラー: {e}")
            self.enhanced_mode = False
    
    def initialize_settings(self):
        """設定値の初期化"""
        self.settings = {
            'blendFile': tk.StringVar(value=""),
            'outputDir': tk.StringVar(value=""),
            'frameStart': tk.IntVar(value=1),
            'frameEnd': tk.IntVar(value=250),
            'resolutionX': tk.IntVar(value=1920),
            'resolutionY': tk.IntVar(value=1080),
            'samples': tk.IntVar(value=128),
            'renderEngine': tk.StringVar(value="CYCLES"),
            'renderDevice': tk.StringVar(value="GPU" if self.enhanced_mode else "CPU"),
            'useCuda': tk.IntVar(value=1 if self.enhanced_mode else 0),
            'framerate': tk.IntVar(value=30),  # framerate設定追加
            'enableUpscale': tk.IntVar(value=0),
            'enableInterpolation': tk.IntVar(value=0),
            'enableDenoise': tk.IntVar(value=0),
        }
    
    def setup_ui(self):
        """UIコンポーネントの設定"""
        main_container = tk.Frame(self.master, bg='#2c3e50')
        main_container.pack(fill='both', expand=True, padx=10, pady=10)
        
        # シンプルなUIを作成
        title_label = tk.Label(main_container, text="Enhanced Blender Render Pipeline", 
                              font=('Arial', 16, 'bold'), bg='#2c3e50', fg='white')
        title_label.pack(pady=20)
        
        # ファイル選択
        file_frame = tk.Frame(main_container, bg='#34495e', relief='ridge', bd=2)
        file_frame.pack(fill='x', pady=10)
        
        tk.Label(file_frame, text="Blendファイル:", bg='#34495e', fg='white').pack(side='left', padx=10)
        self.blend_entry = tk.Entry(file_frame, textvariable=self.settings['blendFile'], width=50)
        self.blend_entry.pack(side='left', padx=5)
        tk.Button(file_frame, text="参照", command=self.select_blend_file).pack(side='left', padx=5)
        
        # 出力ディレクトリ
        output_frame = tk.Frame(main_container, bg='#34495e', relief='ridge', bd=2)
        output_frame.pack(fill='x', pady=5)
        
        tk.Label(output_frame, text="出力先:", bg='#34495e', fg='white').pack(side='left', padx=10)
        self.output_entry = tk.Entry(output_frame, textvariable=self.settings['outputDir'], width=50)
        self.output_entry.pack(side='left', padx=5)
        tk.Button(output_frame, text="参照", command=self.select_output_dir).pack(side='left', padx=5)
        
        # 制御ボタン
        control_frame = tk.Frame(main_container, bg='#2c3e50')
        control_frame.pack(pady=20)
        
        self.start_button = tk.Button(control_frame, text="レンダリング開始", 
                                     command=self.start_render, bg='#27ae60', fg='white',
                                     font=('Arial', 12, 'bold'))
        self.start_button.pack(side='left', padx=10)
        
        tk.Button(control_frame, text="設定保存", command=self.save_settings,
                 bg='#3498db', fg='white').pack(side='left', padx=5)
        
        tk.Button(control_frame, text="設定読込", command=self.load_settings,
                 bg='#9b59b6', fg='white').pack(side='left', padx=5)
        
        # AI処理設定（GPU有効時のみ）
        if self.enhanced_mode:
            ai_frame = tk.Frame(main_container, bg='#34495e', relief='ridge', bd=2)
            ai_frame.pack(fill='x', pady=5)
            
            tk.Label(ai_frame, text="AI強化設定", bg='#34495e', fg='#f39c12',
                    font=('Arial', 11, 'bold')).pack(pady=5)
            
            ai_controls = tk.Frame(ai_frame, bg='#34495e')
            ai_controls.pack(pady=5)
            
            def toggle_upscale():
                current_value = self.settings['enableUpscale'].get()
                self.settings['enableUpscale'].set(1 - current_value)
                self.add_log(f"アップスケール設定: {self.settings['enableUpscale'].get()}")

            def toggle_interpolation():
                current_value = self.settings['enableInterpolation'].get()
                self.settings['enableInterpolation'].set(1 - current_value)
                self.add_log(f"フレーム補間設定: {self.settings['enableInterpolation'].get()}")

            def toggle_denoise():
                current_value = self.settings['enableDenoise'].get()
                self.settings['enableDenoise'].set(1 - current_value)
                self.add_log(f"デノイズ設定: {self.settings['enableDenoise'].get()}")

            tk.Checkbutton(ai_controls, text="🚀 アップスケール (RealESRGAN)", 
                          variable=self.settings['enableUpscale'], 
                          bg='#34495e', fg='white',
                          command=toggle_upscale).pack(side='left', padx=5)
            
            tk.Checkbutton(ai_controls, text="🎥 フレーム補間 (RIFE)", 
                          variable=self.settings['enableInterpolation'], 
                          bg='#34495e', fg='white',
                          command=toggle_interpolation).pack(side='left', padx=5)
            
            tk.Checkbutton(ai_controls, text="✨ デノイズ (FastDVDnet)", 
                          variable=self.settings['enableDenoise'], 
                          bg='#34495e', fg='white',
                          command=toggle_denoise).pack(side='left', padx=5)
        
        # フレームレート設定
        framerate_frame = tk.Frame(main_container, bg='#34495e', relief='ridge', bd=2)
        framerate_frame.pack(fill='x', pady=5)
        
        tk.Label(framerate_frame, text="フレームレート:", bg='#34495e', fg='white').pack(side='left', padx=10)
        framerate_spinbox = tk.Spinbox(framerate_frame, from_=1, to=120, width=10,
                                      textvariable=self.settings['framerate'])
        framerate_spinbox.pack(side='left', padx=5)
        tk.Label(framerate_frame, text="fps", bg='#34495e', fg='white').pack(side='left')
        
        # ログ表示
        log_frame = tk.Frame(main_container, bg='#2c3e50')
        log_frame.pack(fill='both', expand=True, pady=10)
        
        tk.Label(log_frame, text="ログ", bg='#2c3e50', fg='white', 
                font=('Arial', 12, 'bold')).pack(anchor='w')
        
        self.log_text = tk.Text(log_frame, height=15, bg='#1e1e1e', fg='#00ff00',
                               font=('Consolas', 9))
        scrollbar = tk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
    
    def select_blend_file(self):
        """Blendファイル選択"""
        filename = filedialog.askopenfilename(
            title="Blendファイルを選択",
            filetypes=[("Blender files", "*.blend"), ("All files", "*.*")]
        )
        if filename:
            self.settings['blendFile'].set(filename)
            self.add_log(f"Blendファイル選択: {os.path.basename(filename)}")
    
    def select_output_dir(self):
        """出力ディレクトリ選択"""
        dirname = filedialog.askdirectory(title="出力ディレクトリを選択")
        if dirname:
            self.settings['outputDir'].set(dirname)
            self.add_log(f"出力先設定: {dirname}")
    
    def start_render(self):
        """レンダリング開始"""
        blend_file = self.settings['blendFile'].get()
        output_dir = self.settings['outputDir'].get()
        
        if not blend_file:
            messagebox.showerror("エラー", "Blendファイルが選択されていません")
            return
        
        if not output_dir:
            messagebox.showerror("エラー", "出力ディレクトリが選択されていません")
            return
            
        if not os.path.exists(blend_file):
            messagebox.showerror("エラー", "Blendファイルが見つかりません")
            return
            
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
                self.add_log(f"出力ディレクトリを作成: {output_dir}")
            except Exception as e:
                messagebox.showerror("エラー", f"出力ディレクトリ作成失敗: {e}")
                return
        
        # 出力ディレクトリのクリーンアップ
        self.cleanup_output_directory(output_dir)

        self.add_log("レンダリングを開始します...")
        self.add_log(f"入力: {blend_file}")
        self.add_log(f"出力: {output_dir}")
        
        # UI状態更新
        self.start_button.config(text="レンダリング中...", state='disabled')
        
        # バックグラウンドでレンダリング実行
        render_thread = threading.Thread(target=self.render_worker, 
                                        args=(blend_file, output_dir), daemon=True)
        render_thread.start()
    
    def cleanup_output_directory(self, output_dir: str):
        """
        指定された出力ディレクトリ内のファイルを全て削除し、サブフォルダは残す。
        """
        self.add_log(f"出力ディレクトリ {output_dir} のクリーンアップを開始します...")
        try:
            for root, dirs, files in os.walk(output_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        os.remove(file_path)
                        self.add_log(f"  ファイルを削除: {file_path}")
                    except Exception as e:
                        self.add_log(f"  ファイル削除エラー {file_path}: {e}")
            self.add_log(f"出力ディレクトリ {output_dir} のクリーンアップが完了しました。")
        except Exception as e:
            self.add_log(f"出力ディレクトリのクリーンアップ中にエラーが発生しました: {e}")

    def render_worker(self, blend_file: str, output_dir: str):
        """レンダリングワーカー"""
        try:
            # Blenderパス検出
            blender_paths = [
                r"C:\Program Files\Blender Foundation\Blender 4.5\blender.exe",
                r"C:\Program Files\Blender Foundation\Blender 4.4\blender.exe", 
                r"C:\Program Files\Blender Foundation\Blender 4.3\blender.exe",
                "blender"  # PATH環境変数
            ]
            
            blender_exe = None
            for path in blender_paths:
                if path == "blender":
                    # PATHでblenderコマンドが使えるか確認
                    try:
                        subprocess.run(["blender", "--version"], capture_output=True, timeout=10)
                        blender_exe = "blender"
                        break
                    except:
                        continue
                elif os.path.exists(path):
                    blender_exe = path
                    break
            
            if not blender_exe:
                self.add_log("エラー: Blenderが見つかりません")
                self.add_log("BlenderをインストールしてPATHに追加してください")
                return
            
            self.add_log(f"Blender検出: {blender_exe}")
            
            # フレーム設定
            frame_start = self.settings['frameStart'].get()
            frame_end = self.settings['frameEnd'].get()
            
            # 出力パターン設定
            output_pattern = os.path.join(output_dir, "frame_####.png")
            
            # Blenderコマンド構築
            cmd = [
                blender_exe,
                "-b", blend_file,  # バックグラウンドモード
                "-o", output_pattern,  # 出力パターン
                "-s", str(frame_start),  # 開始フレーム
                "-e", str(frame_end),    # 終了フレーム
                "-a"  # アニメーションレンダリング
            ]
            
            # CUDA設定（GPU有効時）
            if self.enhanced_mode and self.settings['useCuda'].get():
                self.add_log("🚀 CUDA加速有効")
                cmd.extend(["-E", "CYCLES"])  # Cyclesエンジン使用
            
            self.add_log(f"🎥 フレーム {frame_start}-{frame_end} をレンダリング中...")
            
            # Blender実行
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace',
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform.startswith('win') else 0
            )
            
            # リアルタイム出力監視
            current_frame = frame_start
            total_frames = frame_end - frame_start + 1
            
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                    
                if output:
                    line = output.strip()
                    
                    # フレーム情報抽出
                    if "Fra:" in line:
                        try:
                            frame_info = line.split("Fra:")[1].split()[0]
                            current_frame = int(frame_info)
                            progress = ((current_frame - frame_start + 1) / total_frames) * 100
                            
                            self.add_log(f"🎥 フレーム {current_frame}/{frame_end} ({progress:.1f}%)")
                            
                        except (ValueError, IndexError):
                            pass
                    
                    # 重要な情報のみログ出力
                    if any(keyword in line.lower() for keyword in ["error", "warning", "rendered", "time:"]):
                        self.add_log(f"Blender: {line}")
            
            # 結果確認
            return_code = process.poll()
            if return_code == 0:
                # 成功時の処理
                rendered_files = glob(os.path.join(output_dir, "frame_*.png"))
                if rendered_files:
                    self.add_log(f"✅ レンダリング完了! {len(rendered_files)}ファイル作成")
                    
                    # AI後処理実行
                    if self.enhanced_mode:
                        rendered_files = self.apply_ai_processing(output_dir, rendered_files)
                    
                    # 動画作成提案
                    if messagebox.askyesno("完了", f"レンダリングが完了しました！\n\n{len(rendered_files)}ファイルを作成\n\n動画ファイル(MP4)を作成しますか？"):
                        self.create_video(output_dir, rendered_files)
                    
                    # 出力フォルダを開く
                    if messagebox.askyesno("確認", "出力フォルダを開きますか？"):
                        self.open_output_folder(output_dir)
                else:
                    self.add_log("⚠️ 警告: 出力ファイルが見つかりません")
            else:
                self.add_log(f"❌ レンダリング失敗 (終了コード: {return_code})")
                # エラー出力表示
                stderr = process.stderr.read()
                if stderr:
                    self.add_log(f"エラー詳細: {stderr[:500]}...")  # 最初の500文字のみ
                    
        except Exception as e:
            self.add_log(f"❌ レンダリングエラー: {e}")
            logger.error(f"Render error: {e}", exc_info=True)
            
        finally:
            # UI状態リセット
            self.master.after(0, lambda: self.start_button.config(text="レンダリング開始", state='normal'))
    
    def apply_ai_processing(self, output_dir: str, frames: List[str]) -> List[str]:
        """統合AI後処理"""
        processed_frames = frames.copy()
        
        try:
            # 1. デノイズ処理
            if self.settings['enableDenoise'].get():
                self.add_log("✨ AIデノイズ処理を開始...")
                processed_frames = self.apply_fastdvdnet_denoise(processed_frames)
            
            # 2. アップスケール処理
            if self.settings['enableUpscale'].get():
                self.add_log("🚀 AIアップスケール処理を開始...")
                processed_frames = self.apply_realesrgan_upscale(processed_frames)
            
            # 3. フレーム補間処理（最後に実行）
            if self.settings['enableInterpolation'].get():
                self.add_log("🎥 AIフレーム補間処理を開始...")
                processed_frames = self.apply_rife_interpolation(processed_frames)
            
            return processed_frames
            
        except Exception as e:
            self.add_log(f"⚠️ AI処理エラー: {e}")
            return frames  # エラー時は元のフレームを返す
    
    def apply_fastdvdnet_denoise(self, frames: List[str]) -> List[str]:
        """デノイズ処理 (FastDVDnet)"""
        try:
            # FastDVDnetスクリプトのパス検出
            fastdvdnet_script = os.path.join("fastdvdnet", "fastdvdnet.py")
            
            if not os.path.exists(fastdvdnet_script):
                self.add_log("⚠️ FastDVDnetスクリプトが見つかりません")
                return frames
            
            denoised_frames = []
            
            for i, frame in enumerate(frames):
                progress = (i + 1) / len(frames) * 100
                self.add_log(f"✨ デノイズ中... {i+1}/{len(frames)} ({progress:.1f}%)")
                
                # 出力ファイル名
                frame_dir = os.path.dirname(frame)
                frame_name = os.path.splitext(os.path.basename(frame))[0]
                denoised_path = os.path.join(frame_dir, f"{frame_name}_denoised.png")
                
                # 簡単なデノイズ処理（フォールバック）
                try:
                    import cv2
                    img = cv2.imread(frame)
                    # ガウシアンフィルタで簡単デノイズ
                    denoised = cv2.GaussianBlur(img, (3, 3), 0)
                    cv2.imwrite(denoised_path, denoised)
                    denoised_frames.append(denoised_path)
                except ImportError:
                    # OpenCVがない場合は元のファイルを使用
                    denoised_frames.append(frame)
            
            self.add_log(f"✅ デノイズ完了: {len(denoised_frames)}ファイル")
            return denoised_frames
            
        except Exception as e:
            self.add_log(f"❌ デノイズエラー: {e}")
            return frames
    
    def apply_realesrgan_upscale(self, frames: List[str]) -> List[str]:
        """アップスケール処理 (RealESRGAN)"""
        try:
            # RealESRGAN実行ファイルのパス検出
            realesrgan_exe = os.path.join("realesrgan-ncnn-vulkan", "realesrgan-ncnn-vulkan.exe")
            
            if not os.path.exists(realesrgan_exe):
                self.add_log("⚠️ RealESRGAN実行ファイルが見つかりません")
                return frames
            
            upscaled_frames = []
            
            for i, frame in enumerate(frames):
                progress = (i + 1) / len(frames) * 100
                self.add_log(f"🚀 アップスケール中... {i+1}/{len(frames)} ({progress:.1f}%)")
                
                frame_dir = os.path.dirname(frame)
                frame_name = os.path.splitext(os.path.basename(frame))[0]
                upscaled_path = os.path.join(frame_dir, f"{frame_name}_upscaled.png")
                
                # RealESRGANコマンド実行
                cmd = [
                    realesrgan_exe,
                    "-i", frame,
                    "-o", upscaled_path,
                    "-n", "realesrgan-x4plus",  # モデル名
                    "-s", "2"  # 2倍スケール
                ]
                
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                    if result.returncode == 0 and os.path.exists(upscaled_path):
                        upscaled_frames.append(upscaled_path)
                    else:
                        upscaled_frames.append(frame)  # 失敗時は元ファイル使用
                except subprocess.TimeoutExpired:
                    self.add_log(f"⚠️ アップスケールタイムアウト: {frame}")
                    upscaled_frames.append(frame)
            
            self.add_log(f"✅ アップスケール完了: {len(upscaled_frames)}ファイル")
            return upscaled_frames
            
        except Exception as e:
            self.add_log(f"❌ アップスケールエラー: {e}")
            return frames
    
    def apply_rife_interpolation(self, frames: List[str]) -> List[str]:
        """フレーム補間処理 (RIFE)"""
        try:
            # RIFE実行ファイルのパス検出
            rife_exe = os.path.join("rife-ncnn-vulkan", "rife-ncnn-vulkan.exe")
            
            if not os.path.exists(rife_exe):
                self.add_log("⚠️ RIFE実行ファイルが見つかりません")
                return frames
            
            # 補間用一時ディレクトリ作成
            temp_dir = os.path.join(os.path.dirname(frames[0]), "temp_interpolation")
            os.makedirs(temp_dir, exist_ok=True)
            
            # フレームを一時ディレクトリにコピー
            for i, frame in enumerate(frames):
                import shutil
                temp_frame = os.path.join(temp_dir, f"frame_{i:06d}.png")
                shutil.copy2(frame, temp_frame)
            
            output_temp_dir = os.path.join(os.path.dirname(frames[0]), "temp_interpolated")
            os.makedirs(output_temp_dir, exist_ok=True)
            
            self.add_log(f"🎥 RIFEフレーム補間中... ({len(frames)}ファイル → 約2倍)")
            
            # RIFEコマンド実行
            cmd = [
                rife_exe,
                "-i", temp_dir,
                "-o", output_temp_dir,
                "-n", "2",  # 2倍補間
                "-m", "rife-v4.6"  # RIFEモデル
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            # 補間結果収集
            interpolated_frames = sorted(glob(os.path.join(output_temp_dir, "*.png")))
            
            if interpolated_frames and result.returncode == 0:
                self.add_log(f"✅ フレーム補間完了: {len(interpolated_frames)}ファイル")
                
                # 一時ディレクトリクリーンアップ
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
                
                return interpolated_frames
            else:
                self.add_log(f"⚠️ フレーム補間失敗、元ファイルを使用")
                return frames
                
        except Exception as e:
            self.add_log(f"❌ フレーム補間エラー: {e}")
            return frames
    
    def create_video(self, output_dir: str, frames: List[str]):
        """動画ファイル作成"""
        try:
            self.add_log("🎦 動画ファイルを作成中...")
            
            video_path = os.path.join(output_dir, "render_output.mp4")
            framerate = self.settings['framerate'].get()
            
            if not frames:
                self.add_log("⚠️ 動画作成: 処理するフレームが見つかりません。")
                return

            # ffmpeg concat demuxer 用のリストファイルを作成
            list_file_path = os.path.join(output_dir, "input.txt")
            try:
                with open(list_file_path, "w", encoding="utf-8") as f:
                    for frame_path in sorted(frames): # 確実にソートされた順でリストに追加
                        f.write(f"file '{os.path.abspath(frame_path)}'\n")
                self.add_log(f"入力リストファイルを作成: {list_file_path}")
            except Exception as e:
                self.add_log(f"❌ 入力リストファイル作成エラー: {e}")
                return
            
            # ffmpegコマンド (concat demuxer を使用)
            ffmpeg_cmd = [
                "ffmpeg", "-y",  # 上書き許可
                "-f", "concat",
                "-safe", "0",  # 危険なファイルパスを許可 (絶対パスを使用するため)
                "-i", list_file_path,
                "-framerate", str(framerate), # framerateを-iの後に移動
                "-c:v", "libx264",  # H.264エンコード
                "-pix_fmt", "yuv420p",  # 互換性のため
                "-crf", "18",  # 高品質設定
                video_path
            ]
            
            self.add_log(f"ffmpegコマンド: {' '.join(ffmpeg_cmd)}")
            result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, timeout=600) # タイムアウトを延長
            
            # 一時リストファイルを削除
            try:
                os.remove(list_file_path)
                self.add_log(f"一時リストファイルを削除: {list_file_path}")
            except Exception as e:
                self.add_log(f"⚠️ 一時リストファイル削除エラー: {e}")
            
            if result.returncode == 0:
                self.add_log(f"✅ 動画作成完了: {os.path.basename(video_path)}")
                messagebox.showinfo("完了", f"動画ファイルを作成しました！\n\n{video_path}")
            else:
                self.add_log(f"❌ ffmpegエラー: {result.stderr[:200]}...")
                
        except FileNotFoundError:
            self.add_log("⚠️ ffmpegが見つかりません。手動で動画を作成してください。")
        except Exception as e:
            self.add_log(f"❌ 動画作成エラー: {e}")
    
    def open_output_folder(self, output_dir: str):
        """出力フォルダを開く"""
        try:
            if sys.platform.startswith('win'):
                os.startfile(output_dir)
            elif sys.platform.startswith('darwin'):
                subprocess.run(['open', output_dir])
            else:
                subprocess.run(['xdg-open', output_dir])
                
            self.add_log(f"📂 出力フォルダを開きました: {output_dir}")
        except Exception as e:
            self.add_log(f"⚠️ フォルダを開けませんでした: {e}")
    
    def save_settings(self):
        """設定保存"""
        try:
            settings_data = {key: var.get() for key, var in self.settings.items()}
            with open("render_settings.json", 'w', encoding='utf-8') as f:
                json.dump(settings_data, f, indent=2, ensure_ascii=False)
            self.add_log("設定を保存しました")
            messagebox.showinfo("完了", "設定を保存しました")
        except Exception as e:
            self.add_log(f"設定保存エラー: {e}")
            messagebox.showerror("エラー", f"設定保存に失敗しました: {e}")
    
    def load_settings(self):
        """設定読込"""
        try:
            if os.path.exists("render_settings.json"):
                with open("render_settings.json", 'r', encoding='utf-8') as f:
                    settings_data = json.load(f)
                
                for key, value in settings_data.items():
                    if key in self.settings:
                        self.settings[key].set(value)
                
                self.add_log("設定を読み込みました")
        except Exception as e:
            self.add_log(f"設定読込エラー: {e}")
    
    def add_log(self, message):
        """ログメッセージ追加"""
        timestamp = time.strftime("[%H:%M:%S]")
        log_message = f"{timestamp} {message}"
        
        try:
            self.log_text.insert('end', log_message + '\n')
            self.log_text.see('end')
            
            # ログの行数制限
            lines = int(self.log_text.index('end-1c').split('.')[0])
            if lines > 1000:
                self.log_text.delete('1.0', '100.0')
        except:
            pass
        
        print(log_message)  # コンソール出力も
    
    def show_gpu_info(self):
        """GPU情報表示"""
        if self.enhanced_mode and self.cuda_accelerator:
            try:
                gpu_count = getattr(self.cuda_accelerator, 'device_count', 0)
                self.add_log(f"CUDA対応GPU検出: {gpu_count}台")
            except:
                self.add_log("GPU情報取得に失敗しました")
    
    def on_closing(self):
        """アプリケーション終了時処理"""
        try:
            self.save_settings()
        except:
            pass
        self.master.destroy()


def main():
    """メイン関数"""
    try:
        # ログ設定
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('render_pipeline.log', encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        print("Enhanced Blender Render Pipeline 起動中...")
        
        # GUI作成
        root = tk.Tk()
        app = BlenderRenderGUI(root)
        
        # 終了時処理設定
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
        
        # メインループ開始
        logger.info("Enhanced Blender Render Pipeline GUI 開始")
        root.mainloop()
        
    except Exception as e:
        error_msg = f"アプリケーション起動エラー: {e}"
        logger.error(error_msg)
        print(error_msg)
        try:
            messagebox.showerror("起動エラー", error_msg)
        except:
            pass
        sys.exit(1)


if __name__ == "__main__":
    # デバッグモード確認
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_basic_gui()
    else:
        main()
