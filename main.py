import os
import subprocess
import threading
import webbrowser
import json
import time
import logging
from glob import glob
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from PIL import Image
import base64
from io import BytesIO
from tkinter import filedialog, Tk

# Blenderパスを固定
BLENDER_PATH = r"C:\Program Files\Blender Foundation\Blender 4.5\blender.exe"

# ファイル選択用のTkinterルートウィンドウ（非表示）
def create_hidden_root():
    root = Tk()
    root.withdraw()  # ウィンドウを非表示にする
    return root

# 既存のBlenderレンダリング関数（blender_pathパラメータを削除し固定値を使用）
def blender_render(blend_file, output_dir, frame_start, frame_end, res_x, res_y, samples, progress_callback=None):
    setpy = os.path.join(output_dir, "_tmp_set_render.py")
    with open(setpy, "w") as f:
        f.write(f"""
import bpy
scene = bpy.context.scene
scene.frame_start = {frame_start}
scene.frame_end = {frame_end}
scene.render.resolution_x = {res_x}
scene.render.resolution_y = {res_y}
scene.cycles.samples = {samples}
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
scene.render.filepath = r'{output_dir}/render_'
""")
    
    cmd = f'"{BLENDER_PATH}" -b "{blend_file}" -P "{setpy}" -a'
    try:
        if progress_callback:
            progress_callback("rendering", 0, "Blenderレンダリング開始...")
        
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # プロセスの進捗を監視
        frame_count = frame_end - frame_start + 1
        current_frame = 0
        
        while process.poll() is None:
            # レンダリングされたファイルをチェック
            rendered_files = glob(os.path.join(output_dir, "render_*.png"))
            new_frame_count = len(rendered_files)
            
            if new_frame_count > current_frame:
                current_frame = new_frame_count
                progress = (current_frame / frame_count) * 100
                if progress_callback:
                    progress_callback("rendering", progress, f"フレーム {current_frame}/{frame_count} レンダリング中...")
            
            time.sleep(1)
        
        if process.returncode == 0:
            if progress_callback:
                progress_callback("rendering", 100, "Blenderレンダリング完了")
        else:
            raise subprocess.CalledProcessError(process.returncode, cmd)
            
    finally:
        if os.path.exists(setpy):
            os.remove(setpy)

def denoise_pngs(input_dir, output_dir, method, oidn_path="C:/oidn/bin/oidnDenoise.exe", 
                fastdvdnet_path="fastdvdnet/fastdvdnet.py", use_cuda=True, progress_callback=None):
    os.makedirs(output_dir, exist_ok=True)
    files = sorted(glob(os.path.join(input_dir, "*.png")))
    total = len(files)
    
    for i, f in enumerate(files, 1):
        out_f = os.path.join(output_dir, os.path.basename(f))
        
        if method == "OIDN":
            im = Image.open(f)
            rgb = im.convert("RGB")
            alpha = im.getchannel("A")
            rgb_path = f + ".rgb.png"
            alpha_path = f + ".a.png"
            rgb.save(rgb_path)
            alpha.save(alpha_path)
            out_rgb_path = f + ".out.rgb.png"
            
            cmd = f'"{oidn_path}" --hdr -i "{rgb_path}" -o "{out_rgb_path}"'
            if use_cuda:
                cmd += " --device cuda"
            
            subprocess.run(cmd, check=True, shell=True)
            out_rgb = Image.open(out_rgb_path)
            result = Image.merge("RGBA", (*out_rgb.split(), alpha))
            result.save(out_f)
            
            # クリーンアップ
            os.remove(rgb_path)
            os.remove(alpha_path)
            os.remove(out_rgb_path)
        else:
            cmd = f'"{fastdvdnet_path}" -i "{f}" -o "{out_f}"'
            subprocess.run(cmd, check=True, shell=True)
        
        progress = (i / total) * 100
        if progress_callback:
            progress_callback("denoising", progress, f"ノイズ除去 {i}/{total}")

def upscale_pngs(input_dir, output_dir, realesrgan_path="realesrgan-ncnn-vulkan/realesrgan-ncnn-vulkan.exe", 
                use_cuda=True, scale=2, progress_callback=None):
    os.makedirs(output_dir, exist_ok=True)
    files = sorted(glob(os.path.join(input_dir, "*.png")))
    total = len(files)
    
    for i, f in enumerate(files, 1):
        out_f = os.path.join(output_dir, os.path.basename(f))
        cmd = f'"{realesrgan_path}" -i "{f}" -o "{out_f}" -n realesrgan-x4plus-anime -s {scale}'
        if not use_cuda:
            cmd += " -g 0"
        
        subprocess.run(cmd, check=True, shell=True)
        
        progress = (i / total) * 100
        if progress_callback:
            progress_callback("upscaling", progress, f"アップスケール {i}/{total}")

def interpolate_pngs(input_dir, output_dir, rife_path="./rife-ncnn-vulkan", use_cuda=True, progress_callback=None):
    os.makedirs(output_dir, exist_ok=True)
    cmd = f'"{rife_path}" -i "{input_dir}" -o "{output_dir}"'
    if use_cuda:
        cmd += " -g 0"
    
    if progress_callback:
        progress_callback("interpolating", 50, "フレーム補間実行中...")
    
    subprocess.run(cmd, check=True, shell=True)
    
    if progress_callback:
        progress_callback("interpolating", 100, "フレーム補間完了")

def pngs_to_video(input_pattern, output_file, framerate=30, codec="prores_ks", progress_callback=None):
    if codec == "prores_ks":
        codec_args = ["-c:v", "prores_ks", "-profile:v", "4", "-pix_fmt", "yuva444p10le"]
    elif codec == "qtrle":
        codec_args = ["-c:v", "qtrle", "-pix_fmt", "rgba"]
    else:
        raise ValueError("コーデックは 'prores_ks' または 'qtrle' を指定")
    
    cmd = [
        "ffmpeg", "-y", "-framerate", str(framerate), "-i", input_pattern,
        *codec_args, output_file
    ]
    
    if progress_callback:
        progress_callback("encoding", 50, "動画エンコード中...")
    
    subprocess.run(cmd, check=True)
    
    if progress_callback:
        progress_callback("encoding", 100, f"動画化完了: {output_file}")

# ======= Webアプリケーション =======
app = Flask(__name__, static_folder=os.path.abspath(os.path.join(os.path.dirname(__file__), 'dist')), static_url_path='')
CORS(app)

# グローバル状態管理
render_status = {
    "step": "idle",
    "progress": 0,
    "message": "準備完了",
    "job_id": None,
    "preview_image": None
}

active_jobs = {}

def progress_callback(step, progress, message):
    """レンダリング進捗のコールバック関数"""
    render_status.update({
        "step": step,
        "progress": progress,
        "message": message
    })

def image_to_base64(image_path):
    """画像をBase64エンコードして返す"""
    try:
        with Image.open(image_path) as img:
            img.thumbnail((400, 400))
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            return f"data:image/png;base64,{img_str}"
    except Exception:
        return None

@app.route('/')
def index():
    """メインページを提供"""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/status')
def get_status():
    """現在のレンダリング状態を返す"""
    return jsonify(render_status)

# 新しいAPIエンドポイントを追加
@app.route('/api/select-blend-file', methods=['POST'])
def select_blend_file():
    """Blendファイル選択ダイアログを表示"""
    try:
        logging.info("Blendファイル選択ダイアログを開始")
        root = create_hidden_root()
        if not root:
            return jsonify({"success": False, "error": "Tkinterの初期化に失敗しました"}), 500
        
        try:
            file_path = filedialog.askopenfilename(
                parent=root,
                title="Blendファイルを選択",
                filetypes=[("Blender Files", "*.blend"), ("All Files", "*.*")],
                initialdir=os.path.expanduser("~")
            )
        finally:
            root.destroy()
        
        if file_path:
            logging.info(f"選択されたBlendファイル: {file_path}")
            return jsonify({"success": True, "path": file_path})
        else:
            logging.info("Blendファイルの選択がキャンセルされました")
            return jsonify({"success": False, "message": "ファイルが選択されませんでした"})
    except Exception as e:
        logging.error(f"Blendファイル選択エラー: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/select-output-folder', methods=['POST'])
def select_output_folder():
    """出力フォルダ選択ダイアログを表示"""
    try:
        logging.info("出力フォルダ選択ダイアログを開始")
        root = create_hidden_root()
        if not root:
            return jsonify({"success": False, "error": "Tkinterの初期化に失敗しました"}), 500
        
        try:
            folder_path = filedialog.askdirectory(
                parent=root,
                title="出力フォルダを選択",
                initialdir=os.path.expanduser("~")
            )
        finally:
            root.destroy()
        
        if folder_path:
            logging.info(f"選択された出力フォルダ: {folder_path}")
            return jsonify({"success": True, "path": folder_path})
        else:
            logging.info("出力フォルダの選択がキャンセルされました")
            return jsonify({"success": False, "message": "フォルダが選択されませんでした"})
    except Exception as e:
        logging.error(f"出力フォルダ選択エラー: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# run_render_pipeline関数を更新（blender_pathパラメータを削除）
def run_render_pipeline(settings, job_id):
    """レンダリングパイプラインを実行"""
    try:
        # パラメータの取得（blenderPathを削除）
        blend_file = settings['blendFile']
        output_dir = settings['outputDir']
        frame_start = settings.get('frameStart', 1)
        frame_end = settings.get('frameEnd', 250)
        res_x = settings.get('resolutionX', 1920)
        res_y = settings.get('resolutionY', 1080)
        samples = settings.get('samples', 128)
        denoise_method = settings.get('denoiseMethod', 'OIDN')
        use_cuda = settings.get('useCuda', True)
        enable_upscale = settings.get('enableUpscale', False)
        enable_interpolation = settings.get('enableInterpolation', False)
        codec = settings.get('codec', 'prores_ks')
        framerate = settings.get('framerate', 30)
        
        # 各段階のフォルダ
        denoised_dir = os.path.join(output_dir, "denoised")
        upscaled_dir = os.path.join(output_dir, "upscaled")
        interpolated_dir = os.path.join(output_dir, "interpolated")
        
        # 1. Blenderレンダリング（固定パスを使用）
        blender_render(blend_file, output_dir, frame_start, frame_end, 
                      res_x, res_y, samples, progress_callback)
        
        # 2. ノイズ除去
        files = sorted(glob(os.path.join(output_dir, "render_*.png")))
        if files:
            denoise_pngs(output_dir, denoised_dir, denoise_method, 
                        use_cuda=use_cuda, progress_callback=progress_callback)
            current_dir = denoised_dir
            
            # プレビュー画像を設定
            if files:
                render_status["preview_image"] = image_to_base64(os.path.join(denoised_dir, os.path.basename(files[0])))
        else:
            current_dir = output_dir
        
        # 3. アップスケール（オプション）
        if enable_upscale:
            upscale_pngs(current_dir, upscaled_dir, use_cuda=use_cuda, 
                        progress_callback=progress_callback)
            current_dir = upscaled_dir
        
        # 4. フレーム補間（オプション）
        if enable_interpolation:
            interpolate_pngs(current_dir, interpolated_dir, use_cuda=use_cuda, 
                           progress_callback=progress_callback)
            current_dir = interpolated_dir
        
        # 5. 動画化
        png_pattern = os.path.join(current_dir, "render_%08d.png")
        output_video = os.path.join(output_dir, "output.mov")
        pngs_to_video(png_pattern, output_video, framerate, codec, progress_callback)
        
        # 完了状態を設定
        render_status.update({
            "step": "complete",
            "progress": 100,
            "message": f"レンダリング完了: {output_video}"
        })
        
    except Exception as e:
        render_status.update({
            "step": "error",
            "progress": 0,
            "message": f"エラー: {str(e)}"
        })

@app.route('/api/start-render', methods=['POST'])
def start_render():
    """レンダリングを開始"""
    try:
        data = request.json
        settings = data.get('settings', {})
        
        # 必須パラメータのチェック（blenderPathを削除）
        required_fields = ['blendFile', 'outputDir']
        for field in required_fields:
            if not settings.get(field):
                return jsonify({"error": f"{field} is required"}), 400
        
        # Blenderの存在確認
        if not os.path.exists(BLENDER_PATH):
            return jsonify({"error": f"Blender not found at: {BLENDER_PATH}"}), 400
        
        # レンダリングジョブを別スレッドで実行
        job_id = f"job_{int(time.time())}"
        render_status["job_id"] = job_id
        
        thread = threading.Thread(
            target=run_render_pipeline,
            args=(settings, job_id),
            daemon=True
        )
        thread.start()
        
        return jsonify({"job_id": job_id, "status": "started"})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/cancel-render', methods=['POST'])
def cancel_render():
    """レンダリングをキャンセル"""
    render_status.update({
        "step": "idle",
        "progress": 0,
        "message": "キャンセルされました"
    })
    return jsonify({"status": "cancelled"})

@app.route('/api/system-info')
def get_system_info():
    """システム情報を返す"""
    import platform
    import psutil
    
    try:
        # CUDA の確認
        cuda_available = False
        try:
            result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
            cuda_available = result.returncode == 0
        except:
            pass
        
        blender_exists = os.path.exists(BLENDER_PATH)
        info = {
            "platform": platform.system(),
            "cpu_count": psutil.cpu_count(),
            "memory_gb": round(psutil.virtual_memory().total / (1024**3), 1),
            "cuda_available": cuda_available,
            "blender_exists": blender_exists
        }
        return jsonify(info)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def create_static_files():
    """静的ファイル（HTML、CSS、JS）を作成"""
    os.makedirs('dist', exist_ok=True)
    
    # React.createElement を使った完全修正版
    html_content = '''<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Blender Render Pipeline</title>
    <script crossorigin src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
    <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif; margin: 0; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; color: #333; }
        .container { max-width: 1200px; margin: 0 auto; }
        .card { background: white; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { text-align: center; color: white; margin-bottom: 30px; }
        .input-group { margin-bottom: 15px; }
        .input-group label { display: block; margin-bottom: 5px; font-weight: bold; }
        .file-select { display: flex; gap: 10px; align-items: center; }
        .file-select input { flex: 1; padding: 8px; border: 1px solid #ddd; border-radius: 4px; background: #f9f9f9; }
        .file-select button { padding: 8px 16px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
        .file-select button:hover { background: #0056b3; }
        .file-select button:disabled { background: #ccc; cursor: not-allowed; }
        input, select { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
        .progress-bar { width: 100%; height: 20px; background: #f0f0f0; border-radius: 10px; overflow: hidden; margin: 10px 0; }
        .progress-fill { height: 100%; background: #007bff; transition: width 0.3s ease; }
        .btn-primary { background: #007bff; color: white; border: none; padding: 12px 24px; border-radius: 4px; cursor: pointer; font-size: 16px; width: 100%; margin-bottom: 10px; }
        .btn-primary:hover { background: #0056b3; }
        .btn-primary:disabled { background: #ccc; cursor: not-allowed; }
        .btn-danger { background: #dc3545; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; width: 100%; }
        .btn-danger:hover { background: #c82333; }
        .status-info { background: #f8f9fa; padding: 15px; border-radius: 4px; margin: 10px 0; }
        .preview-area { width: 100%; height: 200px; background: #f0f0f0; border: 2px dashed #ccc; display: flex; align-items: center; justify-content: center; border-radius: 4px; }
        .system-info { font-size: 12px; color: rgba(255,255,255,0.8); margin-top: 10px; }
    </style>
</head>
<body>
    <div id="root"></div>
    
    <script>
        function App() {
            console.log("App component is rendering!"); // Debug log
            const [settings, setSettings] = React.useState({
                blendFile: '',
                outputDir: '',
                frameStart: 1,
                frameEnd: 250,
                resolutionX: 1920,
                resolutionY: 1080,
                samples: 128,
            });
            
            const [status, setStatus] = React.useState({ step: 'idle', progress: 0, message: '準備完了' });
            const [isRendering, setIsRendering] = React.useState(false);
            const [systemInfo, setSystemInfo] = React.useState(null);
            
            React.useEffect(() => {
                fetch('/api/system-info').then(r => r.json()).then(setSystemInfo).catch(console.error);
                const interval = setInterval(() => {
                    fetch('/api/status').then(r => r.json()).then(data => {
                        setStatus(data);
                        setIsRendering(data.step !== 'idle' && data.step !== 'complete' && data.step !== 'error');
                    }).catch(console.error);
                }, 1000);
                return () => clearInterval(interval);
            }, []);
            
            const selectBlendFile = async () => {
                try {
                    const response = await fetch('/api/select-blend-file', { method: 'POST', headers: { 'Content-Type': 'application/json' } });
                    const data = await response.json();
                    if (data.success && data.path) setSettings({...settings, blendFile: data.path});
                    else alert('ファイル選択エラー: ' + (data.message || data.error));
                } catch (error) { alert('ファイル選択エラー: ' + error.message); }
            };
            
            const selectOutputFolder = async () => {
                try {
                    const response = await fetch('/api/select-output-folder', { method: 'POST', headers: { 'Content-Type': 'application/json' } });
                    const data = await response.json();
                    if (data.success && data.path) setSettings({...settings, outputDir: data.path});
                    else alert('フォルダ選択エラー: ' + (data.message || data.error));
                } catch (error) { alert('フォルダ選択エラー: ' + error.message); }
            };
            
            const startRender = async () => {
                if (!settings.blendFile || !settings.outputDir) { alert('Blendファイルと出力フォルダを選択してください'); return; }
                try {
                    const response = await fetch('/api/start-render', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ settings }) });
                    if (!response.ok) { const error = await response.json(); alert('エラー: ' + error.error); }
                } catch (error) { alert('レンダリング開始エラー: ' + error.message); }
            };
            
            const getStepName = (step) => ({ 'idle': '待機中', 'rendering': 'レンダリング', 'denoising': 'ノイズ除去', 'upscaling': 'アップスケール', 'interpolating': 'フレーム補間', 'encoding': '動画化', 'complete': '完了', 'error': 'エラー' }[step] || step);
            
            return React.createElement('div', { className: 'container' },
                React.createElement('div', { className: 'header' },
                    React.createElement('h1', null, 'Blender Render Pipeline'),
                    React.createElement('p', null, 'プロフェッショナル3Dレンダリング'),
                    systemInfo && React.createElement('div', { className: 'system-info' }, systemInfo.platform + ' | CPU: ' + systemInfo.cpu_count + 'コア | RAM: ' + systemInfo.memory_gb + 'GB | CUDA: ' + (systemInfo.cuda_available ? '利用可能' : '利用不可') + ' | Blender: ' + (systemInfo.blender_exists ? '検出' : '未検出'))
                ),
                React.createElement('div', { className: 'card' },
                    React.createElement('h2', null, 'ファイル選択'),
                    React.createElement('div', { className: 'input-group' }, React.createElement('label', null, 'Blendファイル'), React.createElement('div', { className: 'file-select' }, React.createElement('input', { type: 'text', value: settings.blendFile, readOnly: true, placeholder: 'Blendファイルを選択' }), React.createElement('button', { onClick: selectBlendFile, disabled: isRendering }, '選択'))),
                    React.createElement('div', { className: 'input-group' }, React.createElement('label', null, '出力フォルダ'), React.createElement('div', { className: 'file-select' }, React.createElement('input', { type: 'text', value: settings.outputDir, readOnly: true, placeholder: '出力フォルダを選択' }), React.createElement('button', { onClick: selectOutputFolder, disabled: isRendering }, '選択')))
                ),
                React.createElement('div', { className: 'card' },
                    React.createElement('h2', null, 'レンダリング設定'),
                    React.createElement('div', { className: 'grid' },
                        React.createElement('div', { className: 'input-group' }, React.createElement('label', null, '開始フレーム'), React.createElement('input', { type: 'number', value: settings.frameStart, onChange: e => setSettings({...settings, frameStart: parseInt(e.target.value) || 1}), disabled: isRendering })),
                        React.createElement('div', { className: 'input-group' }, React.createElement('label', null, '終了フレーム'), React.createElement('input', { type: 'number', value: settings.frameEnd, onChange: e => setSettings({...settings, frameEnd: parseInt(e.target.value) || 250}), disabled: isRendering }))
                    ),
                    React.createElement('div', { className: 'grid' },
                        React.createElement('div', { className: 'input-group' }, React.createElement('label', null, '幅'), React.createElement('input', { type: 'number', value: settings.resolutionX, onChange: e => setSettings({...settings, resolutionX: parseInt(e.target.value) || 1920}), disabled: isRendering })),
                        React.createElement('div', { className: 'input-group' }, React.createElement('label', null, '高さ'), React.createElement('input', { type: 'number', value: settings.resolutionY, onChange: e => setSettings({...settings, resolutionY: parseInt(e.target.value) || 1080}), disabled: isRendering }))
                    ),
                    React.createElement('div', { className: 'input-group' }, React.createElement('label', null, 'サンプル数'), React.createElement('input', { type: 'number', value: settings.samples, onChange: e => setSettings({...settings, samples: parseInt(e.target.value) || 128}), disabled: isRendering }))
                ),
                React.createElement('div', { className: 'card' },
                    React.createElement('h2', null, 'レンダリング実行'),
                    React.createElement('div', { className: 'status-info' }, 'ステップ: ' + getStepName(status.step) + ' | 進捗: ' + Math.round(status.progress) + '% | 状況: ' + status.message),
                    React.createElement('div', { className: 'progress-bar' }, React.createElement('div', { className: 'progress-fill', style: { width: status.progress + '%' } })),
                    React.createElement('button', { className: 'btn-primary', onClick: startRender, disabled: isRendering || !settings.blendFile || !settings.outputDir }, isRendering ? 'レンダリング中...' : 'レンダリング開始'),
                    isRendering && React.createElement('button', { className: 'btn-danger', onClick: () => fetch('/api/cancel-render', { method: 'POST' }) }, 'キャンセル'),
                    React.createElement('div', { className: 'preview-area' }, status.preview_image ? React.createElement('img', { src: status.preview_image, alt: 'Preview', style: { maxWidth: '100%', maxHeight: '100%' } }) : React.createElement('div', null, 'プレビューはここに表示されます'))
                )
            );
        }
        
        ReactDOM.createRoot(document.getElementById('root')).render(React.createElement(App));
    </script>
</body>
</html>'''
    

def main():
    """メイン関数: Webサーバーを起動してブラウザを開く"""
    print("🚀 Blender Render Pipeline を起動中...")
    
    # 静的ファイルを作成
    create_static_files()
    
    # Webサーバーを別スレッドで起動
    server_thread = threading.Thread(
        target=lambda: app.run(host='127.0.0.1', port=5000, debug=True, use_reloader=False),
        daemon=True
    )
    server_thread.start()
    
    # サーバーの起動を待つ
    time.sleep(2)
    
    # ブラウザでWebアプリを開く
    url = "http://127.0.0.1:5000"
    print(f"🌐 Webアプリケーションを開いています: {url}")
    webbrowser.open(url)
    
    print("✅ アプリケーションが起動しました！")
    print("📝 ブラウザでWebインターフェースを使用してください")
    print("🛑 終了するには Ctrl+C を押してください")
    
    try:
        # メインスレッドを維持
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 アプリケーションを終了します...")

if __name__ == "__main__":
    main()
