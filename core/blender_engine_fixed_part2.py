            # Blenderコマンド構築（修正版）
            cmd = [
                self.blender_path,
                '-b',  # バックグラウンド
                blend_file,
                '-s', str(render_settings['frame_start']),  # 開始フレーム
                '-e', str(render_settings['frame_end']),    # 終了フレーム
                '-P', script_path,  # スクリプト実行（出力設定もここで）
                '-a'  # アニメーションレンダリング
            ]
            
            self._log(f"実行コマンド: {' '.join(cmd)}")
            
            # プロセス開始
            self.is_running = True
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                cwd=output_dir
            )
            
            # 進捗監視スレッド開始
            monitor_thread = threading.Thread(target=self._monitor_progress, args=(output_dir,))
            monitor_thread.daemon = True
            monitor_thread.start()
            
            # プロセス完了待ち
            return_code = self.process.wait()
            
            # 統計更新
            self.stats['end_time'] = time.time()
            render_time = self.stats['end_time'] - self.stats['start_time']
            
            if return_code == 0:
                self._log(f"レンダリング完了! 時間: {render_time:.2f}秒")
                self._log(f"レンダリング済みフレーム: {self.stats['frames_rendered']}/{self.stats['total_frames']}")
                self._update_progress(100.0, "レンダリング完了")
                return True
            else:
                self._log(f"レンダリング失敗 (終了コード: {return_code})")
                return False
                
        except Exception as e:
            self._log(f"レンダリングエラー: {e}")
            self.stats['errors'].append(str(e))
            return False
        finally:
            self.is_running = False
            self._cleanup_temp_files()
    
    def _monitor_progress(self, output_dir: str) -> None:
        """改良された進捗監視"""
        last_frame = 0
        frame_start_time = None
        
        while self.is_running and self.process and self.process.poll() is None:
            try:
                if self.process.stdout:
                    line = self.process.stdout.readline()
                    if line:
                        line = line.strip()
                        self._log(f"Blender: {line}")
                        
                        # フレーム進捗の解析（複数パターン対応）
                        frame_patterns = [
                            r"Fra:(\d+)",  # Cycles
                            r"Saved: '.*render_(\d+)\..*'",  # 保存完了
                            r"Rendering (\d+) / (\d+)",  # 一般的なパターン
                            r"Frame (\d+)"  # Eevee等
                        ]
                        
                        current_frame = None
                        for pattern in frame_patterns:
                            match = re.search(pattern, line)
                            if match:
                                current_frame = int(match.group(1))
                                break
                        
                        if current_frame is not None and current_frame > last_frame:
                            last_frame = current_frame
                            self.stats['frames_rendered'] = current_frame - self.stats.get('frame_start', 1) + 1
                            
                            if self.stats['total_frames'] > 0:
                                progress = (self.stats['frames_rendered'] / self.stats['total_frames']) * 100.0
                                progress = min(progress, 99.0)  # 100%は完了時のみ
                                
                                # 残り時間推定
                                if frame_start_time and self.stats['frames_rendered'] > 1:
                                    elapsed = time.time() - frame_start_time
                                    avg_time_per_frame = elapsed / self.stats['frames_rendered']
                                    remaining_frames = self.stats['total_frames'] - self.stats['frames_rendered']
                                    eta_seconds = remaining_frames * avg_time_per_frame
                                    eta_minutes = eta_seconds / 60
                                    
                                    message = f"フレーム {current_frame} 完了 ({self.stats['frames_rendered']}/{self.stats['total_frames']}) - 残り約{eta_minutes:.1f}分"
                                else:
                                    message = f"フレーム {current_frame} 完了 ({self.stats['frames_rendered']}/{self.stats['total_frames']})"
                                
                                self._update_progress(progress, message)
                                
                                if frame_start_time is None:
                                    frame_start_time = time.time()
                        
                        # タイル進捗の解析（詳細進捗用）
                        tile_match = re.search(r"Rendered (\d+)/(\d+) Tiles", line)
                        if tile_match:
                            tiles_done = int(tile_match.group(1))
                            tiles_total = int(tile_match.group(2))
                            if tiles_total > 0:
                                tile_progress = (tiles_done / tiles_total) * 100.0
                                self._log(f"タイル進捗: {tiles_done}/{tiles_total} ({tile_progress:.1f}%)")
                        
                        # GPU使用状況の監視
                        if "CUDA" in line or "GPU" in line:
                            self._log(f"GPU情報: {line}")
                        
                        # エラー・警告の記録
                        if 'ERROR' in line or 'Error' in line:
                            self.stats['errors'].append(line)
                            self._log(f"エラー検出: {line}")
                        elif 'WARNING' in line or 'Warning' in line:
                            self.stats['warnings'].append(line)
                            self._log(f"警告検出: {line}")
                
                time.sleep(0.05)  # より高頻度な監視
                
            except Exception as e:
                self._log(f"進捗監視エラー: {e}")
                break
    
    def cancel_render(self) -> bool:
        """レンダリングキャンセル"""
        if not self.is_running or not self.process:
            return False
        
        try:
            self.process.terminate()
            
            # プロセス終了待ち
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
            
            self.is_running = False
            self._log("レンダリングがキャンセルされました")
            return True
            
        except Exception as e:
            self._log(f"レンダリングキャンセルエラー: {e}")
            return False
        finally:
            self._cleanup_temp_files()
    
    def _cleanup_temp_files(self) -> None:
        """一時ファイルクリーンアップ"""
        if self.temp_script_path and os.path.exists(self.temp_script_path):
            try:
                os.remove(self.temp_script_path)
                self.temp_script_path = None
            except Exception as e:
                logger.warning(f"一時ファイル削除警告: {e}")
    
    def get_render_stats(self) -> Dict[str, Any]:
        """レンダリング統計取得"""
        stats = self.stats.copy()
        
        if stats['start_time'] and stats['end_time']:
            stats['total_time'] = stats['end_time'] - stats['start_time']
            if stats['frames_rendered'] > 0:
                stats['time_per_frame'] = stats['total_time'] / stats['frames_rendered']
            else:
                stats['time_per_frame'] = 0
        else:
            stats['total_time'] = 0
            stats['time_per_frame'] = 0
        
        stats['completion_rate'] = (stats['frames_rendered'] / stats['total_frames']) * 100 if stats['total_frames'] > 0 else 0
        
        return stats
    
    def validate_blend_file(self, blend_file: str) -> Dict[str, Any]:
        """Blendファイルの検証"""
        if not os.path.exists(blend_file):
            return {'valid': False, 'error': 'ファイルが存在しません'}
        
        try:
            # Blenderでファイル情報取得
            info_script = '''
import bpy
import json

info = {
    "scene_name": bpy.context.scene.name,
    "render_engine": bpy.context.scene.render.engine,
    "frame_start": bpy.context.scene.frame_start,
    "frame_end": bpy.context.scene.frame_end,
    "resolution_x": bpy.context.scene.render.resolution_x,
    "resolution_y": bpy.context.scene.render.resolution_y,
    "cameras": [obj.name for obj in bpy.data.objects if obj.type == 'CAMERA'],
    "lights": [obj.name for obj in bpy.data.objects if obj.type == 'LIGHT'],
    "meshes": len([obj for obj in bpy.data.objects if obj.type == 'MESH']),
    "materials": len(bpy.data.materials),
    "has_animation": any(obj.animation_data for obj in bpy.data.objects if obj.animation_data)
}

print("BLEND_INFO:" + json.dumps(info, ensure_ascii=False))
'''
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
                f.write(info_script)
                info_script_path = f.name
            
            try:
                cmd = [self.blender_path, '-b', blend_file, '-P', info_script_path]
                result = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=60,
                    encoding='utf-8', errors='replace'
                )
                
                # 出力からファイル情報を抽出
                for line in result.stdout.split('\n'):
                    if line.startswith('BLEND_INFO:'):
                        import json
                        info_data = json.loads(line[11:])
                        info_data['valid'] = True
                        return info_data
                
                return {'valid': False, 'error': 'ファイル情報の取得に失敗'}
                
            finally:
                os.remove(info_script_path)
                
        except subprocess.TimeoutExpired:
            return {'valid': False, 'error': 'ファイル検証タイムアウト'}
        except Exception as e:
            return {'valid': False, 'error': f'検証エラー: {e}'}
    
    def estimate_render_time(self, blend_file: str, settings: Dict[str, Any]) -> Dict[str, float]:
        """レンダリング時間推定"""
        try:
            # 単一フレームでテストレンダリング
            test_settings = settings.copy()
            test_settings.update({
                'frame_start': settings.get('frame_start', 1),
                'frame_end': settings.get('frame_start', 1),  # 1フレームのみ
                'samples': min(settings.get('samples', 128), 32)  # サンプル数制限
            })
            
            # テスト用出力ディレクトリ
            with tempfile.TemporaryDirectory() as temp_dir:
                start_time = time.time()
                
                # テストレンダリング実行
                if self.render(blend_file, temp_dir, test_settings):
                    test_time = time.time() - start_time
                    
                    # 実際の設定での推定時間計算
                    sample_ratio = settings.get('samples', 128) / test_settings['samples']
                    frame_count = settings.get('frame_end', 250) - settings.get('frame_start', 1) + 1
                    
                    estimated_time_per_frame = test_time * sample_ratio
                    estimated_total_time = estimated_time_per_frame * frame_count
                    
                    return {
                        'test_time': test_time,
                        'estimated_time_per_frame': estimated_time_per_frame,
                        'estimated_total_time': estimated_total_time,
                        'estimated_hours': estimated_total_time / 3600
                    }
                else:
                    return {'error': 'テストレンダリング失敗'}
                    
        except Exception as e:
            return {'error': f'時間推定エラー: {e}'}
    
    def __del__(self):
        """デストラクタ"""
        if self.is_running:
            self.cancel_render()
        self._cleanup_temp_files()
