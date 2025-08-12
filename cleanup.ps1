# CLIテストシステム用クリーンアップ
# PowerShell -ExecutionPolicy Bypass -File cleanup.ps1

Write-Host "🧹 CLIテストシステム用クリーンアップ開始..." -ForegroundColor Green

$basePath = "D:\cursorproject\blender_render"
Set-Location $basePath

# 削除対象ファイル
$filesToDelete = @(
    "main.py", "main copy.py", "main_gui.py", "main_gui_enhanced.py", "main_gui_updated.py",
    "cleanup.bat", "components.json", "next-env.d.ts", "next.config.mjs", 
    "package-lock.json", "package.json", "pnpm-lock.yaml", "postcss.config.mjs",
    "tsconfig.json", "blender-render-app(1).zip", "Makefile", "poetry.lock",
    "pyproject.toml", "requirements.txt", "render_pipeline.log", "SETUP.md",
    "start.bat", "start.sh", "VSTインストーラー.zip"
)

# 削除対象ディレクトリ
$dirsToDelete = @(
    ".next", "ai_tools", "app", "blender-render-app", "blender-render-app(1)",
    "components", "config", "core", "dist", "fastdvdnet", "gui", "hooks",
    "lib", "node_modules", "processing", "public", "realesrgan-ncnn-vulkan",
    "rife-ncnn-vulkan", "styles", "tests", "utils", "__pycache__"
)

$deletedFiles = 0
$deletedDirs = 0

# ファイル削除
foreach ($file in $filesToDelete) {
    if (Test-Path $file) {
        Remove-Item $file -Force
        Write-Host "✅ ファイル削除: $file" -ForegroundColor Yellow
        $deletedFiles++
    }
}

# ディレクトリ削除
foreach ($dir in $dirsToDelete) {
    if (Test-Path $dir) {
        Remove-Item $dir -Recurse -Force
        Write-Host "✅ ディレクトリ削除: $dir" -ForegroundColor Yellow  
        $deletedDirs++
    }
}

Write-Host "`n📊 クリーンアップ完了:" -ForegroundColor Green
Write-Host "削除ファイル数: $deletedFiles" -ForegroundColor Cyan
Write-Host "削除ディレクトリ数: $deletedDirs" -ForegroundColor Cyan

Write-Host "`n📁 残存ファイル/ディレクトリ:" -ForegroundColor Green
Get-ChildItem | Select-Object Name, @{Name="Type";Expression={if($_.PSIsContainer){"DIR"}else{"FILE"}}} | Format-Table -AutoSize

Write-Host "🎯 CLIテストシステムの準備完了!" -ForegroundColor Green
Write-Host "実行方法: python cli_render_test.py" -ForegroundColor Cyan
