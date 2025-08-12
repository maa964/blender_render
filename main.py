import os
import subprocess
import threading
import webbrowser
import json
import time
from glob import glob
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from PIL import Image
import base64
from io import BytesIO

# ======= 既存のBlenderレンダリング関数 =======
def blender_render(blender_path, blend_file, output_dir, frame_start, frame_end, res_x, res_y, samples, progress_callback=None):
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
    
    cmd = f'"{blender_path}" -b "{blend_file}" -P "{setpy}" -a'
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
app = Flask(__name__, static_folder='dist', static_url_path='')
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

@app.route('/api/start-render', methods=['POST'])
def start_render():
    """レンダリングを開始"""
    try:
        data = request.json
        settings = data.get('settings', {})
        
        # 必須パラメータのチェック
        required_fields = ['blenderPath', 'blendFile', 'outputDir']
        for field in required_fields:
            if not settings.get(field):
                return jsonify({"error": f"{field} is required"}), 400
        
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

def run_render_pipeline(settings, job_id):
    """レンダリングパイプラインを実行"""
    try:
        # パラメータの取得
        blender_path = settings['blenderPath']
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
        
        # 1. Blenderレンダリング
        blender_render(blender_path, blend_file, output_dir, frame_start, frame_end, 
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
        
        info = {
            "platform": platform.system(),
            "cpu_count": psutil.cpu_count(),
            "memory_gb": round(psutil.virtual_memory().total / (1024**3), 1),
            "cuda_available": cuda_available
        }
        return jsonify(info)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def create_static_files():
    """静的ファイル（HTML、CSS、JS）を作成"""
    os.makedirs('dist', exist_ok=True)
    
    # 簡単なHTMLファイルを作成
    html_content = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Blender Render Pipeline</title>
    <script src="https://unpkg.com/react@18/umd/react.development.js"></script>
    <script src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <style>
        .gradient-bg {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        .card {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }
    </style>
</head>
<body class="gradient-bg min-h-screen">
    <div id="root"></div>
    
    <script type="text/babel">
        const { useState, useEffect } = React;
        
        function App() {
            const [settings, setSettings] = useState({
                blenderPath: '',
                blendFile: '',
                outputDir: '',
                frameStart: 1,
                frameEnd: 250,
                resolutionX: 1920,
                resolutionY: 1080,
                samples: 128,
                denoiseMethod: 'OIDN',
                useCuda: true,
                enableUpscale: false,
                enableInterpolation: false,
                codec: 'prores_ks',
                framerate: 30
            });
            
            const [status, setStatus] = useState({
                step: 'idle',
                progress: 0,
                message: '準備完了'
            });
            
            const [isRendering, setIsRendering] = useState(false);
            
            // ステータスを定期的に更新
            useEffect(() => {
                const interval = setInterval(async () => {
                    try {
                        const response = await fetch('/api/status');
                        const data = await response.json();
                        setStatus(data);
                        setIsRendering(data.step !== 'idle' && data.step !== 'complete' && data.step !== 'error');
                    } catch (error) {
                        console.error('Status update failed:', error);
                    }
                }, 1000);
                
                return () => clearInterval(interval);
            }, []);
            
            const handleStartRender = async () => {
                try {
                    const response = await fetch('/api/start-render', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ settings })
                    });
                    
                    if (!response.ok) {
                        const error = await response.json();
                        alert('エラー: ' + error.error);
                    }
                } catch (error) {
                    alert('レンダリング開始に失敗しました: ' + error.message);
                }
            };
            
            const getStepName = (step) => {
                const steps = {
                    'idle': '待機中',
                    'rendering': 'レンダリング',
                    'denoising': 'ノイズ除去',
                    'upscaling': 'アップスケール',
                    'interpolating': 'フレーム補間',
                    'encoding': '動画化',
                    'complete': '完了',
                    'error': 'エラー'
                };
                return steps[step] || step;
            };
            
            return (
                <div className="container mx-auto p-6 max-w-6xl">
                    <div className="text-center mb-8">
                        <h1 className="text-4xl font-bold text-white mb-2">
                            Blender Render Pipeline
                        </h1>
                        <p className="text-white opacity-80">
                            プロフェッショナル3Dレンダリング with AI強化
                        </p>
                    </div>
                    
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        {/* 設定パネル */}
                        <div className="lg:col-span-2">
                            <div className="card p-6 mb-6">
                                <h2 className="text-xl font-bold mb-4">基本設定</h2>
                                
                                <div className="space-y-4">
                                    <div>
                                        <label className="block text-sm font-medium mb-1">Blender実行ファイル</label>
                                        <input
                                            type="text"
                                            className="w-full p-2 border rounded-lg"
                                            placeholder="C:/Program Files/Blender Foundation/Blender 4.0/blender.exe"
                                            value={settings.blenderPath}
                                            onChange={(e) => setSettings({...settings, blenderPath: e.target.value})}
                                        />
                                    </div>
                                    
                                    <div>
                                        <label className="block text-sm font-medium mb-1">Blendファイル</label>
                                        <input
                                            type="text"
                                            className="w-full p-2 border rounded-lg"
                                            placeholder="レンダリングするBlendファイルのパス"
                                            value={settings.blendFile}
                                            onChange={(e) => setSettings({...settings, blendFile: e.target.value})}
                                        />
                                    </div>
                                    
                                    <div>
                                        <label className="block text-sm font-medium mb-1">出力ディレクトリ</label>
                                        <input
                                            type="text"
                                            className="w-full p-2 border rounded-lg"
                                            placeholder="レンダリング結果の保存先"
                                            value={settings.outputDir}
                                            onChange={(e) => setSettings({...settings, outputDir: e.target.value})}
                                        />
                                    </div>
                                    
                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <label className="block text-sm font-medium mb-1">開始フレーム</label>
                                            <input
                                                type="number"
                                                className="w-full p-2 border rounded-lg"
                                                value={settings.frameStart}
                                                onChange={(e) => setSettings({...settings, frameStart: parseInt(e.target.value)})}
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium mb-1">終了フレーム</label>
                                            <input
                                                type="number"
                                                className="w-full p-2 border rounded-lg"
                                                value={settings.frameEnd}
                                                onChange={(e) => setSettings({...settings, frameEnd: parseInt(e.target.value)})}
                                            />
                                        </div>
                                    </div>
                                    
                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <label className="block text-sm font-medium mb-1">幅</label>
                                            <input
                                                type="number"
                                                className="w-full p-2 border rounded-lg"
                                                value={settings.resolutionX}
                                                onChange={(e) => setSettings({...settings, resolutionX: parseInt(e.target.value)})}
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium mb-1">高さ</label>
                                            <input
                                                type="number"
                                                className="w-full p-2 border rounded-lg"
                                                value={settings.resolutionY}
                                                onChange={(e) => setSettings({...settings, resolutionY: parseInt(e.target.value)})}
                                            />
                                        </div>
                                    </div>
                                    
                                    <div>
                                        <label className="block text-sm font-medium mb-1">サンプル数</label>
                                        <input
                                            type="number"
                                            className="w-full p-2 border rounded-lg"
                                            value={settings.samples}
                                            onChange={(e) => setSettings({...settings, samples: parseInt(e.target.value)})}
                                        />
                                    </div>
                                </div>
                            </div>
                            
                            <div className="card p-6">
                                <h2 className="text-xl font-bold mb-4">AI強化設定</h2>
                                
                                <div className="space-y-4">
                                    <div>
                                        <label className="block text-sm font-medium mb-1">ノイズ除去方式</label>
                                        <select
                                            className="w-full p-2 border rounded-lg"
                                            value={settings.denoiseMethod}
                                            onChange={(e) => setSettings({...settings, denoiseMethod: e.target.value})}
                                        >
                                            <option value="OIDN">Intel Open Image Denoise</option>
                                            <option value="FastDVDnet">FastDVDnet</option>
                                        </select>
                                    </div>
                                    
                                    <div className="flex items-center space-x-2">
                                        <input
                                            type="checkbox"
                                            id="cuda"
                                            checked={settings.useCuda}
                                            onChange={(e) => setSettings({...settings, useCuda: e.target.checked})}
                                        />
                                        <label htmlFor="cuda" className="text-sm font-medium">CUDA加速を使用</label>
                                    </div>
                                    
                                    <div className="flex items-center space-x-2">
                                        <input
                                            type="checkbox"
                                            id="upscale"
                                            checked={settings.enableUpscale}
                                            onChange={(e) => setSettings({...settings, enableUpscale: e.target.checked})}
                                        />
                                        <label htmlFor="upscale" className="text-sm font-medium">AIアップスケール</label>
                                    </div>
                                    
                                    <div className="flex items-center space-x-2">
                                        <input
                                            type="checkbox"
                                            id="interpolation"
                                            checked={settings.enableInterpolation}
                                            onChange={(e) => setSettings({...settings, enableInterpolation: e.target.checked})}
                                        />
                                        <label htmlFor="interpolation" className="text-sm font-medium">フレーム補間</label>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        {/* ステータスパネル */}
                        <div className="space-y-6">
                            <div className="card p-6">
                                <h2 className="text-xl font-bold mb-4">レンダリング状態</h2>
                                
                                <div className="space-y-4">
                                    <div>
                                        <div className="flex justify-between text-sm mb-1">
                                            <span>現在のステップ:</span>
                                            <span className="font-medium">{getStepName(status.step)}</span>
                                        </div>
                                        
                                        <div className="flex justify-between text-sm mb-2">
                                            <span>進捗:</span>
                                            <span>{Math.round(status.progress)}%</span>
                                        </div>
                                        
                                        <div className="w-full bg-gray-200 rounded-full h-2">
                                            <div 
                                                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                                                style={{width: `${status.progress}%`}}
                                            ></div>
                                        </div>
                                    </div>
                                    
                                    <div className="text-sm text-gray-600">
                                        {status.message}
                                    </div>
                                    
                                    <button
                                        onClick={handleStartRender}
                                        disabled={isRendering}
                                        className={`w-full py-3 px-4 rounded-lg font-medium ${
                                            isRendering 
                                                ? 'bg-gray-400 cursor-not-allowed' 
                                                : 'bg-blue-600 hover:bg-blue-700 text-white'
                                        }`}
                                    >
                                        {isRendering ? 'レンダリング中...' : 'レンダリング開始'}
                                    </button>
                                </div>
                            </div>
                            
                            <div className="card p-6">
                                <h2 className="text-xl font-bold mb-4">プレビュー</h2>
                                <div className="aspect-video bg-gray-100 rounded-lg flex items-center justify-center">
                                    {status.preview_image ? (
                                        <img 
                                            src={status.preview_image || "/placeholder.svg"} 
                                            alt="Preview" 
                                            className="max-w-full max-h-full rounded-lg"
                                        />
                                    ) : (
                                        <div className="text-gray-500 text-center">
                                            <div className="text-4xl mb-2">🎬</div>
                                            <p>プレビューはここに表示されます</p>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            );
        }
        
        ReactDOM.render(<App />, document.getElementById('root'));
    </script>
</body>
</html>
    """
    
    with open('dist/index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)

def main():
    """メイン関数：Webサーバーを起動してブラウザを開く"""
    print("🚀 Blender Render Pipeline を起動中...")
    
    # 静的ファイルを作成
    create_static_files()
    
    # Webサーバーを別スレッドで起動
    server_thread = threading.Thread(
        target=lambda: app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False),
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
