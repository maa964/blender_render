# -*- coding: utf-8 -*-
"""
File Manager Module
PyPy最適化対応ファイル管理モジュール
"""

import os
import sys
import shutil
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple
import logging
import hashlib
import time

# UTF-8エンコーディング設定
if sys.platform.startswith('win'):
    os.environ['PYTHONIOENCODING'] = 'utf-8'

logger = logging.getLogger(__name__)

class FileManager:
    """ファイル管理クラス"""
    
    def __init__(self, temp_dir: Optional[str] = None):
        self.temp_dir = Path(temp_dir) if temp_dir else Path(tempfile.gettempdir()) / "blender_render_pipeline"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # 管理対象ファイル
        self.managed_files: List[Path] = []
        self.managed_dirs: List[Path] = []
        
        logger.info(f"ファイル管理モジュール初期化完了: {self.temp_dir}")
    
    def create_temp_file(self, suffix: str = "", prefix: str = "blender_", content: Optional[str] = None) -> Path:
        """一時ファイル作成"""
        try:
            # 一意なファイル名生成
            timestamp = int(time.time() * 1000)
            temp_file = self.temp_dir / f"{prefix}{timestamp}{suffix}"
            
            # ファイル作成
            with open(temp_file, 'w', encoding='utf-8') as f:
                if content:
                    f.write(content)
            
            self.managed_files.append(temp_file)
            logger.debug(f"一時ファイル作成: {temp_file}")
            
            return temp_file
            
        except Exception as e:
            logger.error(f"一時ファイル作成エラー: {e}")
            raise
    
    def create_temp_dir(self, prefix: str = "render_") -> Path:
        """一時ディレクトリ作成"""
        try:
            timestamp = int(time.time() * 1000)
            temp_dir = self.temp_dir / f"{prefix}{timestamp}"
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            self.managed_dirs.append(temp_dir)
            logger.debug(f"一時ディレクトリ作成: {temp_dir}")
            
            return temp_dir
            
        except Exception as e:
            logger.error(f"一時ディレクトリ作成エラー: {e}")
            raise
    
    def safe_copy(self, src: Union[str, Path], dst: Union[str, Path], 
                  preserve_metadata: bool = True, backup: bool = False) -> bool:
        """安全なファイルコピー"""
        try:
            src_path = Path(src)
            dst_path = Path(dst)
            
            if not src_path.exists():
                logger.error(f"コピー元ファイルが存在しません: {src_path}")
                return False
            
            # バックアップ作成
            if backup and dst_path.exists():
                backup_path = dst_path.with_suffix(dst_path.suffix + ".backup")
                shutil.copy2(dst_path, backup_path)
                logger.debug(f"バックアップ作成: {backup_path}")
            
            # ディレクトリ作成
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            
            # コピー実行
            if preserve_metadata:
                shutil.copy2(src_path, dst_path)
            else:
                shutil.copy(src_path, dst_path)
            
            logger.debug(f"ファイルコピー完了: {src_path} -> {dst_path}")
            return True
            
        except Exception as e:
            logger.error(f"ファイルコピーエラー: {e}")
            return False
    
    def safe_move(self, src: Union[str, Path], dst: Union[str, Path], backup: bool = False) -> bool:
        """安全なファイル移動"""
        try:
            src_path = Path(src)
            dst_path = Path(dst)
            
            if not src_path.exists():
                logger.error(f"移動元ファイルが存在しません: {src_path}")
                return False
            
            # バックアップ作成
            if backup and dst_path.exists():
                backup_path = dst_path.with_suffix(dst_path.suffix + ".backup")
                shutil.move(dst_path, backup_path)
                logger.debug(f"バックアップ作成: {backup_path}")
            
            # ディレクトリ作成
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 移動実行
            shutil.move(src_path, dst_path)
            
            logger.debug(f"ファイル移動完了: {src_path} -> {dst_path}")
            return True
            
        except Exception as e:
            logger.error(f"ファイル移動エラー: {e}")
            return False
    
    def safe_delete(self, path: Union[str, Path], backup: bool = False) -> bool:
        """安全なファイル削除"""
        try:
            target_path = Path(path)
            
            if not target_path.exists():
                logger.warning(f"削除対象ファイルが存在しません: {target_path}")
                return True
            
            # バックアップ作成
            if backup:
                backup_path = target_path.with_suffix(target_path.suffix + ".deleted")
                shutil.move(target_path, backup_path)
                logger.debug(f"削除バックアップ作成: {backup_path}")
            else:
                # 完全削除
                if target_path.is_dir():
                    shutil.rmtree(target_path)
                else:
                    target_path.unlink()
            
            logger.debug(f"ファイル削除完了: {target_path}")
            return True
            
        except Exception as e:
            logger.error(f"ファイル削除エラー: {e}")
            return False
    
    def get_file_info(self, path: Union[str, Path]) -> Dict[str, Any]:
        """ファイル情報取得"""
        try:
            file_path = Path(path)
            
            if not file_path.exists():
                return {"error": "ファイルが存在しません"}
            
            stat_info = file_path.stat()
            
            info = {
                "path": str(file_path),
                "name": file_path.name,
                "size": stat_info.st_size,
                "size_mb": stat_info.st_size / (1024 * 1024),
                "created": time.ctime(stat_info.st_ctime),
                "modified": time.ctime(stat_info.st_mtime),
                "accessed": time.ctime(stat_info.st_atime),
                "is_file": file_path.is_file(),
                "is_dir": file_path.is_dir(),
                "extension": file_path.suffix,
                "parent": str(file_path.parent)
            }
            
            # ファイルハッシュ計算（小さなファイルのみ）
            if file_path.is_file() and stat_info.st_size < 10 * 1024 * 1024:  # 10MB未満
                info["md5"] = self.calculate_file_hash(file_path)
            
            return info
            
        except Exception as e:
            logger.error(f"ファイル情報取得エラー: {e}")
            return {"error": str(e)}
    
    def calculate_file_hash(self, path: Union[str, Path], algorithm: str = "md5") -> str:
        """ファイルハッシュ計算"""
        try:
            file_path = Path(path)
            
            if algorithm == "md5":
                hasher = hashlib.md5()
            elif algorithm == "sha256":
                hasher = hashlib.sha256()
            else:
                raise ValueError(f"未対応のハッシュアルゴリズム: {algorithm}")
            
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            
            return hasher.hexdigest()
            
        except Exception as e:
            logger.error(f"ファイルハッシュ計算エラー: {e}")
            return ""
    
    def find_files(self, directory: Union[str, Path], pattern: str = "*", 
                   recursive: bool = True, include_dirs: bool = False) -> List[Path]:
        """ファイル検索"""
        try:
            search_dir = Path(directory)
            
            if not search_dir.exists():
                logger.error(f"検索ディレクトリが存在しません: {search_dir}")
                return []
            
            if recursive:
                glob_pattern = f"**/{pattern}"
                files = list(search_dir.glob(glob_pattern))
            else:
                files = list(search_dir.glob(pattern))
            
            # フィルタリング
            if not include_dirs:
                files = [f for f in files if f.is_file()]
            
            return sorted(files)
            
        except Exception as e:
            logger.error(f"ファイル検索エラー: {e}")
            return []
    
    def get_directory_size(self, directory: Union[str, Path]) -> Tuple[int, int]:
        """ディレクトリサイズ取得（バイト数、ファイル数）"""
        try:
            dir_path = Path(directory)
            
            if not dir_path.exists() or not dir_path.is_dir():
                return 0, 0
            
            total_size = 0
            file_count = 0
            
            for file_path in dir_path.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
                    file_count += 1
            
            return total_size, file_count
            
        except Exception as e:
            logger.error(f"ディレクトリサイズ取得エラー: {e}")
            return 0, 0
    
    def cleanup_temp_files(self, older_than_hours: int = 24) -> int:
        """一時ファイルクリーンアップ"""
        cleaned_count = 0
        current_time = time.time()
        cutoff_time = current_time - (older_than_hours * 3600)
        
        try:
            # 管理ファイルのクリーンアップ
            for file_path in self.managed_files[:]:  # コピーでイテレート
                try:
                    if file_path.exists():
                        if file_path.stat().st_mtime < cutoff_time:
                            file_path.unlink()
                            self.managed_files.remove(file_path)
                            cleaned_count += 1
                    else:
                        self.managed_files.remove(file_path)
                except Exception as e:
                    logger.warning(f"一時ファイル削除エラー: {file_path}, {e}")
            
            # 管理ディレクトリのクリーンアップ
            for dir_path in self.managed_dirs[:]:
                try:
                    if dir_path.exists():
                        if dir_path.stat().st_mtime < cutoff_time:
                            shutil.rmtree(dir_path)
                            self.managed_dirs.remove(dir_path)
                            cleaned_count += 1
                    else:
                        self.managed_dirs.remove(dir_path)
                except Exception as e:
                    logger.warning(f"一時ディレクトリ削除エラー: {dir_path}, {e}")
            
            # temp_dir内の古いファイルもクリーンアップ
            for file_path in self.temp_dir.rglob("*"):
                try:
                    if (file_path.is_file() and 
                        file_path.stat().st_mtime < cutoff_time and
                        file_path not in self.managed_files):
                        file_path.unlink()
                        cleaned_count += 1
                except Exception as e:
                    logger.warning(f"古いファイル削除エラー: {file_path}, {e}")
            
            logger.info(f"一時ファイルクリーンアップ完了: {cleaned_count}個削除")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"一時ファイルクリーンアップエラー: {e}")
            return cleaned_count
    
    def create_file_sequence(self, directory: Union[str, Path], 
                           base_name: str, extension: str, 
                           start_frame: int, end_frame: int,
                           padding: int = 8) -> List[Path]:
        """ファイルシーケンス作成"""
        try:
            target_dir = Path(directory)
            target_dir.mkdir(parents=True, exist_ok=True)
            
            sequence_files = []
            
            for frame_num in range(start_frame, end_frame + 1):
                frame_str = str(frame_num).zfill(padding)
                filename = f"{base_name}_{frame_str}.{extension}"
                file_path = target_dir / filename
                
                # 空ファイル作成
                file_path.touch()
                sequence_files.append(file_path)
            
            logger.info(f"ファイルシーケンス作成完了: {len(sequence_files)}個")
            return sequence_files
            
        except Exception as e:
            logger.error(f"ファイルシーケンス作成エラー: {e}")
            return []
    
    def validate_file_sequence(self, directory: Union[str, Path], 
                             pattern: str) -> Dict[str, Any]:
        """ファイルシーケンス検証"""
        try:
            target_dir = Path(directory)
            
            if not target_dir.exists():
                return {"valid": False, "error": "ディレクトリが存在しません"}
            
            # パターンマッチング
            files = sorted(target_dir.glob(pattern))
            
            if not files:
                return {"valid": False, "error": "マッチするファイルがありません"}
            
            # フレーム番号抽出と連続性チェック
            frame_numbers = []
            for file_path in files:
                # ファイル名から数字抽出（簡易版）
                import re
                numbers = re.findall(r'\d+', file_path.stem)
                if numbers:
                    frame_numbers.append(int(numbers[-1]))  # 最後の数字をフレーム番号とみなす
            
            if not frame_numbers:
                return {"valid": False, "error": "フレーム番号を抽出できません"}
            
            frame_numbers.sort()
            missing_frames = []
            
            # 連続性チェック
            for i in range(frame_numbers[0], frame_numbers[-1] + 1):
                if i not in frame_numbers:
                    missing_frames.append(i)
            
            # ファイルサイズチェック
            file_sizes = [f.stat().st_size for f in files]
            avg_size = sum(file_sizes) / len(file_sizes)
            small_files = [f for f, size in zip(files, file_sizes) if size < avg_size * 0.1]
            
            result = {
                "valid": len(missing_frames) == 0 and len(small_files) == 0,
                "file_count": len(files),
                "frame_range": (frame_numbers[0], frame_numbers[-1]) if frame_numbers else (0, 0),
                "missing_frames": missing_frames,
                "small_files": [str(f) for f in small_files],
                "total_size": sum(file_sizes),
                "average_size": avg_size
            }
            
            return result
            
        except Exception as e:
            logger.error(f"ファイルシーケンス検証エラー: {e}")
            return {"valid": False, "error": str(e)}
    
    def compress_directory(self, source_dir: Union[str, Path], 
                          output_file: Union[str, Path],
                          compression: str = "zip") -> bool:
        """ディレクトリ圧縮"""
        try:
            source_path = Path(source_dir)
            output_path = Path(output_file)
            
            if not source_path.exists():
                logger.error(f"圧縮元ディレクトリが存在しません: {source_path}")
                return False
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            if compression == "zip":
                import zipfile
                with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for file_path in source_path.rglob("*"):
                        if file_path.is_file():
                            arcname = file_path.relative_to(source_path)
                            zipf.write(file_path, arcname)
            
            elif compression == "tar":
                import tarfile
                with tarfile.open(output_path, 'w:gz') as tarf:
                    tarf.add(source_path, arcname=source_path.name)
            
            else:
                logger.error(f"未対応の圧縮形式: {compression}")
                return False
            
            logger.info(f"ディレクトリ圧縮完了: {source_path} -> {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"ディレクトリ圧縮エラー: {e}")
            return False
    
    def extract_archive(self, archive_file: Union[str, Path], 
                       output_dir: Union[str, Path]) -> bool:
        """アーカイブ展開"""
        try:
            archive_path = Path(archive_file)
            output_path = Path(output_dir)
            
            if not archive_path.exists():
                logger.error(f"アーカイブファイルが存在しません: {archive_path}")
                return False
            
            output_path.mkdir(parents=True, exist_ok=True)
            
            if archive_path.suffix.lower() == '.zip':
                import zipfile
                with zipfile.ZipFile(archive_path, 'r') as zipf:
                    zipf.extractall(output_path)
            
            elif archive_path.suffix.lower() in ['.tar', '.tar.gz', '.tgz']:
                import tarfile
                with tarfile.open(archive_path, 'r:*') as tarf:
                    tarf.extractall(output_path)
            
            else:
                logger.error(f"未対応のアーカイブ形式: {archive_path.suffix}")
                return False
            
            logger.info(f"アーカイブ展開完了: {archive_path} -> {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"アーカイブ展開エラー: {e}")
            return False
    
    def get_disk_usage(self, path: Union[str, Path]) -> Dict[str, int]:
        """ディスク使用量取得"""
        try:
            target_path = Path(path)
            usage = shutil.disk_usage(target_path)
            
            return {
                "total": usage.total,
                "used": usage.used,
                "free": usage.free,
                "used_percent": (usage.used / usage.total) * 100
            }
            
        except Exception as e:
            logger.error(f"ディスク使用量取得エラー: {e}")
            return {"total": 0, "used": 0, "free": 0, "used_percent": 0}
    
    def __del__(self):
        """デストラクタ - 一時ファイルクリーンアップ"""
        try:
            self.cleanup_temp_files(older_than_hours=0)  # 全て削除
        except:
            pass


# シングルトンパターン
_file_manager_instance = None

def get_file_manager() -> FileManager:
    """ファイル管理シングルトンインスタンス取得"""
    global _file_manager_instance
    if _file_manager_instance is None:
        _file_manager_instance = FileManager()
    return _file_manager_instance
