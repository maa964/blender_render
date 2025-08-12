# セットアップガイド

## 🚀 クイックスタート

### 1. 依存関係のインストール

**Windows:**
```bash
pip install Flask Flask-CORS Pillow psutil
```

**または requirements.txt を使用:**
```bash
pip install -r requirements.txt
```

### 2. アプリケーションの起動

**方法1: Pythonスクリプトを直接実行**
```bash
python main.py
```

**方法2: バッチファイルを使用 (Windows)**
```bash
start.bat
```

**方法3: シェルスクリプトを使用 (Linux/Mac)**
```bash
chmod +x start.sh
./start.sh
```

### 3. Webアプリケーションへのアクセス

アプリケーションが起動すると、自動的にブラウザが開き、以下のURLでWebインターフェースにアクセスできます：

```
http://127.0.0.1:5000
```

## 🔧 事前準備

### 必要なツール

1. **Blender** (3.0以降推奨)
   - 公式サイトからダウンロード: https://www.blender.org/download/

2. **Intel Open Image Denoise (OIDN)**
   - ダウンロード: https://openimagedenoise.github.io/
   - `C:/oidn/` に展開することを推奨

3. **Real-ESRGAN** (アップスケール用)
   - GitHub: https://github.com/xinntao/Real-ESRGAN/releases
   - プロジェクトフォルダに展開

4. **RIFE** (フレーム補間用)
   - GitHub: https://github.com/megvii-research/ECCV2022-RIFE/releases
   - プロジェクトフォルダに展開

5. **FFmpeg** (動画エンコード用)
   - 公式サイト: https://ffmpeg.org/download.html
   - システムPATHに追加

## 📁 プロジェクト構造

```
blender-render-pipeline/
├── main.py                 # メインアプリケーション
├── requirements.txt        # Python依存関係
├── start.bat              # Windows起動スクリプト
├── start.sh               # Linux/Mac起動スクリプト
├── dist/                  # 自動生成されるWebファイル
│   └── index.html         # Webインターフェース
├── realesrgan-ncnn-vulkan/ # Real-ESRGANツール
├── rife-ncnn-vulkan/      # RIFEツール
└── fastdvdnet/            # FastDVDnetツール
```

## 🎯 使用方法

### 基本的なワークフロー

1. **Webブラウザでアプリケーションを開く**
2. **基本設定を入力:**
   - Blender実行ファイルのパス
   - レンダリングするBlendファイル
   - 出力ディレクトリ
   - フレーム範囲と解像度

3. **AI強化設定を選択:**
   - ノイズ除去方式 (OIDN推奨)
   - CUDA加速の有効化
   - アップスケールとフレーム補間の設定

4. **レンダリング開始ボタンをクリック**

5. **進捗をリアルタイムで監視**

### 設定例

**高品質レンダリング:**
- 解像度: 1920x1080
- サンプル数: 256
- ノイズ除去: OIDN
- アップスケール: 有効
- フレーム補間: 有効

**高速レンダリング:**
- 解像度: 1280x720
- サンプル数: 64
- ノイズ除去: FastDVDnet
- アップスケール: 無効
- フレーム補間: 無効

## 🔍 トラブルシューティング

### よくある問題

**1. Blenderが見つからない**
- Blenderの実行ファイルパスが正しいか確認
- パスにスペースが含まれる場合は引用符で囲む

**2. CUDA関連エラー**
- NVIDIAドライバーが最新か確認
- CUDA設定を無効にして再試行

**3. ツールが見つからない**
- OIDN、Real-ESRGAN、RIFEのパスが正しいか確認
- 実行権限があるか確認

**4. メモリ不足エラー**
- 解像度やサンプル数を下げる
- 他のアプリケーションを終了

### ログの確認

アプリケーションはコンソールに詳細なログを出力します：
```bash
python main.py
```

## 🚀 パフォーマンス最適化

### ハードウェア推奨仕様

**最小構成:**
- CPU: 4コア以上
- RAM: 8GB以上
- GPU: CUDA対応 (推奨)

**推奨構成:**
- CPU: 8コア以上
- RAM: 16GB以上
- GPU: RTX 3060以上
- SSD: 高速ストレージ

### 最適化のヒント

1. **SSDを使用** - 一時ファイルの読み書きが高速化
2. **CUDA有効化** - GPU加速で大幅な高速化
3. **適切なサンプル数** - 品質と速度のバランス
4. **バッチサイズ調整** - メモリ使用量の最適化

## 📞 サポート

問題が発生した場合：

1. **ログを確認** - コンソール出力をチェック
2. **設定を見直し** - パスや権限を確認
3. **Issue報告** - GitHubでIssueを作成

---

**Happy Rendering! 🎬✨**
```
```

添付されたPythonスクリプトを現代的なWebアプリケーションに変換しました！

## 🎯 主な変更点

### ✨ **Web化の実現**
- **Flask Webサーバー**：既存のPython機能をAPIエンドポイントとして提供
- **React Webインターフェース**：モダンなUIでTkinterを置き換え
- **自動ブラウザ起動**：`main.py`実行時に自動でWebアプリが開く

### 🔄 **既存機能の保持**
- **全てのレンダリング機能**：Blender、ノイズ除去、アップスケール、フレーム補間
- **リアルタイム進捗**：WebSocket風のポーリングで進捗を表示
- **プレビュー機能**：処理済み画像をBase64でWebに表示

### 🚀 **使用方法**

1. **依存関係をインストール**：
   ```bash
   pip install Flask Flask-CORS Pillow psutil