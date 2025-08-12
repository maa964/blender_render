@echo off
echo Blender Render Pipeline を起動中...
echo.

REM 必要なPythonパッケージをインストール
echo 📦 依存関係をインストール中...
pip install -r requirements.txt

echo.
echo 🚀 アプリケーションを起動中...
python main.py

pause
