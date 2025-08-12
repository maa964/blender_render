# -*- coding: utf-8 -*-
"""
Path Validator Utility
パス検証ユーティリティ
"""

import os
from pathlib import Path
from typing import Union, List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class PathValidator:
    """パス検証クラス"""
    
    @staticmethod
    def validate_file_path(path: Union[str, Path], extensions: List[str] = None) -> Dict[str, Any]:
        """ファイルパス検証"""
        try:
            file_path = Path(path)
            
            result = {
                "valid": True,
                "exists": file_path.exists(),
                "is_file": file_path.is_file() if file_path.exists() else False,
                "extension": file_path.suffix.lower(),
                "size": file_path.stat().st_size if file_path.exists() else 0,
                "errors": []
            }
            
            if not file_path.exists():
                result["valid"] = False
                result["errors"].append("ファイルが存在しません")
            
            if not file_path.is_file() and file_path.exists():
                result["valid"] = False
                result["errors"].append("ファイルではありません")
            
            if extensions and result["extension"] not in [ext.lower() for ext in extensions]:
                result["valid"] = False
                result["errors"].append(f"対応していない拡張子です（対応: {extensions}）")
            
            return result
            
        except Exception as e:
            return {
                "valid": False,
                "exists": False,
                "is_file": False,
                "extension": "",
                "size": 0,
                "errors": [f"パス検証エラー: {e}"]
            }
    
    @staticmethod
    def validate_directory_path(path: Union[str, Path], create_if_missing: bool = False) -> Dict[str, Any]:
        """ディレクトリパス検証"""
        try:
            dir_path = Path(path)
            
            result = {
                "valid": True,
                "exists": dir_path.exists(),
                "is_dir": dir_path.is_dir() if dir_path.exists() else False,
                "writable": False,
                "errors": []
            }
            
            if not dir_path.exists():
                if create_if_missing:
                    try:
                        dir_path.mkdir(parents=True, exist_ok=True)
                        result["exists"] = True
                        result["is_dir"] = True
                    except Exception as e:
                        result["valid"] = False
                        result["errors"].append(f"ディレクトリ作成失敗: {e}")
                else:
                    result["valid"] = False
                    result["errors"].append("ディレクトリが存在しません")
            
            if dir_path.exists() and not dir_path.is_dir():
                result["valid"] = False
                result["errors"].append("ディレクトリではありません")
            
            # 書き込み権限チェック
            if result["is_dir"]:
                try:
                    test_file = dir_path / ".write_test"
                    test_file.touch()
                    test_file.unlink()
                    result["writable"] = True
                except:
                    result["writable"] = False
                    result["errors"].append("書き込み権限がありません")
            
            return result
            
        except Exception as e:
            return {
                "valid": False,
                "exists": False,
                "is_dir": False,
                "writable": False,
                "errors": [f"ディレクトリ検証エラー: {e}"]
            }
