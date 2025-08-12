# Import the tkinter module to fix "Tk" is not defined
import tkinter
from main_gui import BlenderRenderGUI
import os
import json
# -*- coding: utf-8 -*-
"""
Blender Render Pipeline GUI - Updated for Enhanced Architecture (続き)
"""

def main():
    """メイン関数"""
    root = tkinter.Tk()
    app = BlenderRenderGUI(root)
    
    def on_closing():
        if app.render_status['is_running']:
            app.cancel_render()
        
        # 設定自動保存
        try:
            app.save_settings()
        except Exception as e:
            app.log_message(f"設定保存エラー (終了時): {e}")

        
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    
    # アプリケーション情報表示
    app.log_message("=== Blender Render Pipeline v1.0 ===")
    app.log_message(f"Enhanced Mode: {app.enhanced_mode}")
    if app.enhanced_mode:
        app.log_message("Numba/CUDA最適化、AI処理統合が利用可能です")
        app.show_gpu_info()
    else:
        app.log_message("基本機能で動作中（拡張モジュール未検出）")
    root.mainloop()

if __name__ == "__main__":
    main()
