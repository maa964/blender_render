@echo off
echo CLIテストシステム用クリーンアップ開始...

REM GUI関連ファイル削除
del /q "main.py" 2>nul
del /q "main copy.py" 2>nul
del /q "main_gui.py" 2>nul
del /q "main_gui_enhanced.py" 2>nul
del /q "main_gui_updated.py" 2>nul

REM Next.js/React関連削除
rmdir /s /q ".next" 2>nul
rmdir /s /q "app" 2>nul
rmdir /s /q "components" 2>nul
rmdir /s /q "hooks" 2>nul
rmdir /s /q "lib" 2>nul
rmdir /s /q "public" 2>nul
rmdir /s /q "styles" 2>nul
rmdir /s /q "node_modules" 2>nul
del /q "components.json" 2>nul
del /q "next-env.d.ts" 2>nul
del /q "next.config.mjs" 2>nul
del /q "package-lock.json" 2>nul
del /q "package.json" 2>nul
del /q "pnpm-lock.yaml" 2>nul
del /q "postcss.config.mjs" 2>nul
del /q "tsconfig.json" 2>nul

REM その他不要ファイル削除
rmdir /s /q "blender-render-app" 2>nul
rmdir /s /q "blender-render-app(1)" 2>nul
del /q "blender-render-app(1).zip" 2>nul
rmdir /s /q "ai_tools" 2>nul
rmdir /s /q "config" 2>nul
rmdir /s /q "core" 2>nul
rmdir /s /q "dist" 2>nul
rmdir /s /q "fastdvdnet" 2>nul
rmdir /s /q "gui" 2>nul
rmdir /s /q "processing" 2>nul
rmdir /s /q "realesrgan-ncnn-vulkan" 2>nul
rmdir /s /q "rife-ncnn-vulkan" 2>nul
rmdir /s /q "tests" 2>nul
rmdir /s /q "utils" 2>nul
del /q "Makefile" 2>nul
del /q "poetry.lock" 2>nul
del /q "pyproject.toml" 2>nul
del /q "requirements.txt" 2>nul
del /q "render_pipeline.log" 2>nul
del /q "SETUP.md" 2>nul
del /q "start.bat" 2>nul
del /q "start.sh" 2>nul
del /q "VSTインストーラー.zip" 2>nul

echo クリーンアップ完了
echo.
echo 残存ファイル:
dir /b
pause
