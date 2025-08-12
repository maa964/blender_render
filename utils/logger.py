# -*- coding: utf-8 -*-
"""
Logger Utility Module
ログシステムユーティリティ
"""

import logging
import sys
import os
from pathlib import Path

def setup_logger(name: str = "blender_render_pipeline", 
                level: str = "INFO",
                log_file: str = "render_pipeline.log") -> logging.Logger:
    """ログシステムセットアップ"""
    
    # UTF-8エンコーディング設定
    if sys.platform.startswith('win'):
        os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    # ログレベル設定
    log_levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    
    logger = logging.getLogger(name)
    logger.setLevel(log_levels.get(level.upper(), logging.INFO))
    
    # 既存ハンドラクリア
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # フォーマッタ作成
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # コンソールハンドラ
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # ファイルハンドラ
    try:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.error(f"ログファイル作成エラー: {e}")
    
    return logger

def get_logger(name: str = "blender_render_pipeline") -> logging.Logger:
    """ログインスタンス取得"""
    return logging.getLogger(name)
