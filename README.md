# Enhanced Blender Render Pipeline

CUDA対応GPU加速レンダリングパイプライン with AI強化機能

## 概要

Enhanced Blender Render Pipelineは、Blenderレンダリングの自動化とAI強化処理を組み合わせた高度なレンダリングシステムです。CUDA対応GPU、AI画質向上、フレーム補間などの最新技術を統合し、プロフェッショナルレベルの映像制作を支援します。

## 主要機能

### 🚀 GPU加速レンダリング
- **CUDA対応**: NVIDIA GPU による高速レンダリング
- **マルチGPU対応**: 複数GPUでの負荷分散
- **メモリ最適化**: 効率的なVRAM使用

### 🎨 AI強化機能
- **アップスケール**: RealESRGAN, ESRGAN による画質向上
- **フレーム補間**: RIFE, FastDVDnet による滑らかな動画生成
- **ノイズ除去**: Intel OIDN, OptiX デノイズ

### 💻 直感的GUI
- **タブ式インターフェース**: 機能別の整理された設定画面
- **リアルタイム監視**: GPU使用率・メモリ使用量の表示
- **プレビュー機能**: レンダリング結果の即座確認

### ⚡ 高度な自動化
- **バッチ処理**: 複数シーンの一括レンダリング
- **後処理パイプライン**: レンダリング完了後の自動AI処理
- **動画生成**: 自動的なMP4出力

## システム要件

### 必須要件
- **OS**: Windows 10/11, macOS 10.15+, Ubuntu 18.04+
- **Python**: 3.8以上
- **Blender**: 4.3以上
- **RAM**: 8GB以上
- **ストレージ**: 5GB以上の空き容量

### 推奨要件（AI機能使用時）
- **GPU**: NVIDIA RTX 20シリーズ以上（8GB VRAM推奨）
- **RAM**: 16GB以上
- **CUDA**: 12.0以上
- **cuDNN**: 8.0以上

## インストール

### 1. リポジトリのクローン
```bash
git clone https://github.com/yourusername/blender-render-pipeline.git
cd blender-render-pipeline
```

### 2. 完全セットアップ（推奨）
```bash
make setup
```

### 3. 手動セットアップ
```bash
# 仮想環境作成
python -m venv .venv

# 仮想環境アクティベート
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# 依存関係インストール
pip install -r requirements.txt

# CUDA対応（GPU使用時）
make install-cuda

# AI機能（オプション）
make install-ai
```

## 使用方法

### 1. アプリケーション起動
```bash
make run
# または
python main_gui_enhanced.py
```

### 2. 基本設定
1. **Blendファイル選択**: レンダリング対象の.blendファイルを選択
2. **出力ディレクトリ**: レンダリング結果の保存先を指定
3. **フレーム範囲**: 開始・終了フレームを設定
4. **解像度**: 出力解像度を指定（1920x1080推奨）

### 3. レンダリング設定
- **エンジン**: CYCLES（GPU推奨）, EEVEE, Workbench
- **デバイス**: CPU, GPU, GPU+CPU
- **サンプル数**: 品質vs速度のバランス調整

### 4. AI強化設定（オプション）
- **アップスケール**: 2x, 4x, 8x倍率選択
- **フレーム補間**: 滑らかな動画生成
- **デノイズ**: ノイズ除去による品質向上

### 5. 実行開始
1. 設定確認後「レンダリング開始」ボタンクリック
2. 進行状況をリアルタイム監視
3. 完了後、出力フォルダで結果確認

## 設定ファイル

### render_settings.json
```json
{
  "blendFile": "path/to/scene.blend",
  "outputDir": "path/to/output",
  "frameStart": 1,
  "frameEnd": 250,
  "resolutionX": 1920,
  "resolutionY": 1080,
  "samples": 128,
  "renderEngine": "CYCLES",
  "renderDevice": "GPU",
  "enableUpscale": true,
  "upscaleMethod": "RealESRGAN",
  "upscaleFactor": 2
}
```

## トラブルシューティング

### よくある問題

#### CUDA not available
```bash
# CUDA インストール確認
make gpu-info

# または手動確認
nvidia-smi
python -c "import torch; print(torch.cuda.is_available())"
```

#### メモリ不足エラー
- タイルサイズを小さく設定
- バッチサイズを削減
- 解像度を下げて確認

#### Blender not found
- Blenderパスを環境変数PATHに追加
- または絶対パスで指定

### ログファイル
```
render_pipeline.log  # 詳細な実行ログ
```

## 開発・貢献

### 開発環境セットアップ
```bash
# 開発依存関係インストール
make install-dev

# コード品質チェック
make lint

# テスト実行
make test

# 型チェック
make typecheck
```

### 利用可能なMakeコマンド
```bash
make help              # ヘルプ表示
make setup             # 完全セットアップ
make run               # アプリケーション実行
make test              # テスト実行
make test-cuda         # CUDAテスト
make lint              # コード品質チェック
make format            # コードフォーマット
make gpu-info          # GPU情報表示
make clean             # 一時ファイル削除
```

## アーキテクチャ

### Numba/CUDA/PyPy 最適化構成
- **数値演算部分**: Numba JIT コンパイル + CUDA対応
- **ループ処理**: Cython による高速化
- **その他処理**: PyPy での実行

### ディレクトリ構造
```
blender-render-pipeline/
├── main_gui_enhanced.py          # メインGUIアプリケーション（完全版）
├── core/
│   ├── cuda_accelerator.py       # CUDA加速制御
│   ├── blender_engine.py         # Blenderエンジン管理
│   └── settings_manager.py       # 設定管理
├── processing/
│   ├── ai_processor.py           # AI処理エンジン
│   └── video_encoder.py          # 動画エンコード
├── gui/
│   ├── main_window.py            # メインウィンドウ
│   └── components/               # UIコンポーネント
├── utils/
│   ├── file_manager.py           # ファイル操作
│   └── logger.py                 # ログ管理
├── requirements.txt              # 依存関係
├── pyproject.toml               # プロジェクト設定
├── Makefile                     # ビルド自動化
└── README.md                    # このファイル
```

## パフォーマンス

### ベンチマーク結果（参考値）
- **CPU レンダリング**: Intel i7-12700K @ 100 samples/分
- **GPU レンダリング**: RTX 4080 @ 800 samples/分（8倍高速）
- **AI アップスケール**: 1080p→4K @ 2fps（RealESRGAN）
- **フレーム補間**: 30fps→60fps @ リアルタイム（RIFE）

### 最適化のポイント
- CUDA有効化で大幅な高速化
- タイルサイズの適切な設定
- VRAMに応じたバッチサイズ調整

## ライセンス

MIT License - 詳細は [LICENSE](LICENSE) ファイルを参照

## サポート

- **Issues**: GitHub Issues での問題報告
- **Wiki**: 詳細なドキュメント
- **Discussions**: 機能提案・質問

## 更新履歴

### v2.0.0 (2025-08-12) - Enhanced Release
- ✨ CUDA対応GPU加速の実装
- ✨ AI画質向上機能の追加
- ✨ タブ式GUI への刷新
- ✨ リアルタイム監視機能
- ✨ 設定の永続化
- ✨ 日本語文字化け対策
- ✨ Numba/Cython/PyPy最適化構成
- ✨ ファイル分割対応

### v1.5.0 (2025-07-01)
- フレーム補間機能追加
- バッチ処理対応
- パフォーマンス最適化

### v1.0.0 (2025-06-01)
- 初回リリース
- 基本レンダリング機能
- シンプルGUI

## クレジット

- **Blender Foundation**: Blender 3D creation suite
- **Intel**: Open Image Denoise (OIDN)
- **NVIDIA**: CUDA, OptiX
- **xinntao**: Real-ESRGAN
- **HolyWu**: RIFE-ncnn-vulkan

---

**Enhanced Blender Render Pipeline** - プロフェッショナル映像制作のための次世代レンダリングソリューション
