# Blender Render Pipeline Makefile
# CUDA対応、Numba最適化、Cython高速化のビルドとテスト自動化

PYTHON := python
PIP := pip
PROJECT_NAME := blender-render-pipeline
VENV_DIR := .venv
CUDA_AVAILABLE := $(shell python -c "import torch; print('cuda' if torch.cuda.is_available() else 'cpu')" 2>/dev/null || echo "cpu")

# カラー出力
BLUE := \033[34m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
NC := \033[0m # No Color

.PHONY: help install install-dev build-cython clean test test-cuda lint format setup-env run run-gui check-cuda info

# デフォルトターゲット
help:
	@echo "$(BLUE)Blender Render Pipeline - Make Commands$(NC)"
	@echo ""
	@echo "$(GREEN)セットアップ:$(NC)"
	@echo "  setup-env     - 仮想環境作成と依存関係インストール"
	@echo "  install       - 依存関係をインストール"
	@echo "  install-dev   - 開発用依存関係をインストール"
	@echo ""
	@echo "$(GREEN)ビルド:$(NC)"
	@echo "  build-cython  - Cythonモジュールをビルド"
	@echo "  build-all     - 全ての最適化モジュールをビルド"
	@echo ""
	@echo "$(GREEN)実行:$(NC)"
	@echo "  run          - GUIアプリケーション起動"
	@echo "  run-gui      - Tkinter GUI起動"
	@echo ""
	@echo "$(GREEN)テスト・品質:$(NC)"
	@echo "  test         - 基本テスト実行"
	@echo "  test-cuda    - CUDAテスト実行"
	@echo "  test-all     - 全テスト実行"
	@echo "  lint         - コード品質チェック"
	@echo "  format       - コードフォーマット"
	@echo ""
	@echo "$(GREEN)ユーティリティ:$(NC)"
	@echo "  check-cuda   - CUDA環境チェック"
	@echo "  info         - システム情報表示"
	@echo "  clean        - ビルドファイル削除"
	@echo ""
	@echo "$(YELLOW)現在のCUDA状態: $(CUDA_AVAILABLE)$(NC)"

# システム情報表示
info:
	@echo "$(BLUE)=== システム情報 ===$(NC)"
	@echo "Python版本: $(shell $(PYTHON) --version)"
	@echo "Pip版本: $(shell $(PIP) --version)"
	@echo "CUDA利用可能: $(CUDA_AVAILABLE)"
	@echo "プロジェクト名: $(PROJECT_NAME)"
	@echo "仮想環境: $(VENV_DIR)"
	@echo ""
	@echo "$(BLUE)=== GPU情報 ===$(NC)"
	@$(PYTHON) -c "import torch; print(f'PyTorch CUDA: {torch.cuda.is_available()}'); print(f'GPU数: {torch.cuda.device_count()}') if torch.cuda.is_available() else print('CUDA未対応')" 2>/dev/null || echo "PyTorch未インストール"

# CUDA環境チェック
check-cuda:
	@echo "$(BLUE)=== CUDA環境チェック ===$(NC)"
	@$(PYTHON) -c "\
import sys; \
try: \
    import torch; \
    print(f'✓ PyTorch: {torch.__version__}'); \
    print(f'✓ CUDA利用可能: {torch.cuda.is_available()}'); \
    if torch.cuda.is_available(): \
        print(f'✓ GPU数: {torch.cuda.device_count()}'); \
        for i in range(torch.cuda.device_count()): \
            print(f'  GPU {i}: {torch.cuda.get_device_name(i)}'); \
    else: print('⚠ CUDA未対応 - CPU使用'); \
except ImportError: \
    print('✗ PyTorch未インストール'); \
try: \
    import cupy; \
    print(f'✓ CuPy: {cupy.__version__}'); \
except ImportError: \
    print('⚠ CuPy未インストール'); \
try: \
    import numba.cuda; \
    print(f'✓ Numba CUDA: 利用可能'); \
except ImportError: \
    print('⚠ Numba CUDA未インストール'); \
"

# 仮想環境セットアップ
setup-env:
	@echo "$(GREEN)仮想環境をセットアップしています...$(NC)"
	$(PYTHON) -m venv $(VENV_DIR)
	@echo "$(GREEN)依存関係をインストールしています...$(NC)"
	$(VENV_DIR)/Scripts/python -m pip install --upgrade pip
	$(VENV_DIR)/Scripts/pip install -e .[dev,cython,gui]
	@echo "$(GREEN)セットアップ完了!$(NC)"
	@echo "$(YELLOW)仮想環境を有効化してください: $(VENV_DIR)\\Scripts\\activate$(NC)"

# 依存関係インストール
install:
	@echo "$(GREEN)基本依存関係をインストールしています...$(NC)"
	$(PIP) install --upgrade pip
	$(PIP) install -e .[gui]

# 開発用依存関係インストール
install-dev:
	@echo "$(GREEN)開発用依存関係をインストールしています...$(NC)"
	$(PIP) install --upgrade pip
	$(PIP) install -e .[dev,cython,gui]

# Cythonモジュールビルド
build-cython:
	@echo "$(GREEN)Cythonモジュールをビルドしています...$(NC)"
	$(PYTHON) setup_cython.py build_ext --inplace
	@echo "$(GREEN)Cythonビルド完了$(NC)"

# 全最適化モジュールビルド
build-all: build-cython
	@echo "$(GREEN)全最適化モジュールをビルドしています...$(NC)"
	@echo "$(GREEN)ビルド完了$(NC)"

# アプリケーション実行
run:
	@echo "$(GREEN)Blender Render Pipeline GUIを起動しています...$(NC)"
	$(PYTHON) main_gui.py

run-gui: run

# テスト実行
test:
	@echo "$(GREEN)基本テストを実行しています...$(NC)"
	$(PYTHON) -m pytest tests/ -v --tb=short -m "not cuda and not slow"

# CUDAテスト実行
test-cuda:
	@echo "$(GREEN)CUDAテストを実行しています...$(NC)"
	$(PYTHON) -m pytest tests/ -v --tb=short -m "cuda"

# 全テスト実行
test-all:
	@echo "$(GREEN)全テストを実行しています...$(NC)"
	$(PYTHON) -m pytest tests/ -v --tb=short --cov=core --cov=processing --cov=gui --cov=utils --cov=ai_tools

# コード品質チェック
lint:
	@echo "$(GREEN)コード品質をチェックしています...$(NC)"
	$(PYTHON) -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	$(PYTHON) -m flake8 . --count --exit-zero --max-complexity=10 --max-line-length=88 --statistics
	$(PYTHON) -m mypy core/ processing/ gui/ utils/ ai_tools/ --ignore-missing-imports

# コードフォーマット
format:
	@echo "$(GREEN)コードをフォーマットしています...$(NC)"
	$(PYTHON) -m black .
	$(PYTHON) -m isort .

# クリーンアップ
clean:
	@echo "$(GREEN)ビルドファイルを削除しています...$(NC)"
	$(PYTHON) -c "import shutil; import os; [shutil.rmtree(d, ignore_errors=True) for d in ['build', 'dist', '*.egg-info', '__pycache__']]"
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.so" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} +
	@echo "$(GREEN)クリーンアップ完了$(NC)"

# Cythonセットアップファイル生成
setup_cython.py:
	@echo "$(GREEN)Cythonセットアップファイルを生成しています...$(NC)"
	@echo "from setuptools import setup" > setup_cython.py
	@echo "from Cython.Build import cythonize" >> setup_cython.py
	@echo "import numpy" >> setup_cython.py
	@echo "" >> setup_cython.py
	@echo "setup(" >> setup_cython.py
	@echo "    ext_modules=cythonize([" >> setup_cython.py
	@echo "        'processing/interpolation_cython.py'," >> setup_cython.py
	@echo "    ])," >> setup_cython.py
	@echo "    include_dirs=[numpy.get_include()]," >> setup_cython.py
	@echo ")" >> setup_cython.py

# 必要ならsetup_cython.pyを生成してからビルド
build-cython: setup_cython.py
	@echo "$(GREEN)Cythonモジュールをビルドしています...$(NC)"
	$(PYTHON) setup_cython.py build_ext --inplace
	@echo "$(GREEN)Cythonビルド完了$(NC)"
