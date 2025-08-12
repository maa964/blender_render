import os
import subprocess
import threading
from glob import glob
from tkinter import filedialog, Tk, Button, Label, StringVar, IntVar, OptionMenu, Entry, ttk, Canvas
from PIL import Image, ImageTk

# ======= Blenderレンダリング =======
def blender_render(blender_path, blend_file, output_dir, frame_start, frame_end, res_x, res_y, samples):
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
    # blender_pathをクォート
    cmd = f'"{blender_path}" -b "{blend_file}" -P "{setpy}" -a'
    try:
        subprocess.run(cmd, check=True, shell=True)
    finally:
        if os.path.exists(setpy):
            os.remove(setpy)

# ======= ノイズ除去（OIDN/fastdvdnet） =======
def denoise_pngs(
    input_dir,
    output_dir,
    method,
    oidn_path="C:/oidn/bin/oidnDenoise.exe",
    fastdvdnet_path="D:/cursorproject/blender_render/fastdvdnet/fastdvdnet.py",
    use_cuda=True,
    progress_callback=None,
    preview_callback=None
):
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
            os.remove(rgb_path)
            os.remove(alpha_path)
            os.remove(out_rgb_path)
        else:
            cmd = f'"{fastdvdnet_path}" -i "{f}" -o "{out_f}"'
            subprocess.run(cmd, check=True, shell=True)
        if preview_callback:
            preview_callback(out_f)
        if progress_callback:
            progress_callback(i, total)

# ======= アップスケール =======
def upscale_pngs(input_dir, output_dir, realesrgan_path="realesrgan-ncnn-vulkan\realesrgan-ncnn-vulkan.exe", use_cuda=True, scale=2, progress_callback=None, preview_callback=None):
    os.makedirs(output_dir, exist_ok=True)
    files = sorted(glob(os.path.join(input_dir, "*.png")))
    total = len(files)
    for i, f in enumerate(files, 1):
        out_f = os.path.join(output_dir, os.path.basename(f))
        cmd = f'"{realesrgan_path}" -i "{f}" -o "{out_f}" -n realesrgan-x4plus-anime -s {scale}'
        if not use_cuda:
            cmd += " -g 0"
        subprocess.run(cmd, check=True, shell=True)
        if preview_callback:
            preview_callback(out_f)
        if progress_callback:
            progress_callback(i, total)

# ======= フレーム補間 =======
def interpolate_pngs(input_dir, output_dir, rife_path="./rife-ncnn-vulkan", use_cuda=True, status_callback=None):
    os.makedirs(output_dir, exist_ok=True)
    # 入力・出力ディレクトリはダブルクォートで囲む
    cmd = f'"{rife_path}" -i "{input_dir}" -o "{output_dir}"'
    if use_cuda:
        cmd += " -g 0"  # GPU0を明示（または希望するGPU番号）
    if status_callback:
        status_callback("フレーム補間実行中…")
    print("RIFE実行コマンド:", cmd)  # ←デバッグ用
    subprocess.run(cmd, check=True, shell=True)

# ======= 動画化 =======
def pngs_to_video(input_pattern, output_file, framerate=30, codec="prores_ks"):
    if codec == "prores_ks":
        codec_args = ["-c:v", "prores_ks", "-profile:v", "4", "-pix_fmt", "yuva444p10le"]
    elif codec == "qtrle":
        codec_args = ["-c:v", "qtrle", "-pix_fmt", "rgba"]
    else:
        raise ValueError("コーデックは 'prores_ks' または 'qtrle' を指定")
    cmd = [
        "ffmpeg",
        "-y",
        "-framerate", str(framerate),
        "-i", input_pattern,
        *codec_args,
        output_file
    ]
    subprocess.run(cmd, check=True)
    print("✅ 動画化完了:", output_file)

# ======= プレビュー用 =======
def show_preview(image_path, canvas, size=(200, 200)):
    try:
        im = Image.open(image_path).convert("RGBA").resize(size)
        tk_im = ImageTk.PhotoImage(im)
        canvas.img = tk_im
        canvas.create_image(0, 0, anchor="nw", image=tk_im)
    except Exception:
        pass

# ======= GUI =======
class AllInOneGUI:
    def __init__(self, master):
        self.master = master
        master.title("Blender All-in-One Batch")
        # Blender実行ファイルパス選択欄
        self.blender_exe = StringVar(value="")
        Button(master, text="Blender実行ファイル選択", command=self.select_blender_exe).pack()
        Label(master, textvariable=self.blender_exe).pack()
        # Blender設定
        self.blend_file = StringVar(value="")
        self.frame_start = IntVar(value=1)
        self.frame_end = IntVar(value=250)
        self.res_x = IntVar(value=1280)
        self.res_y = IntVar(value=720)
        self.samples = IntVar(value=16)
        self.output_dir = StringVar(value="")
        # バッチ系設定
        self.method = StringVar(value="OIDN")
        self.codec = StringVar(value="prores_ks")
        self.framerate = IntVar(value=30)
        self.use_cuda = IntVar(value=1)
        self.do_upscale = IntVar(value=0)
        self.do_interpolate = IntVar(value=0)
        self.status = StringVar(value="準備OK")
        self.progress_var = IntVar(value=0)
        self.progress_bar = ttk.Progressbar(master, orient="horizontal", length=350, mode="determinate", variable=self.progress_var)
        self.preview_canvas = Canvas(master, width=200, height=200, bg="gray")
        Button(master, text="Blendファイル選択", command=self.select_blend_file).pack()
        Label(master, textvariable=self.blend_file).pack()
        Label(master, text="フレーム範囲").pack()
        Entry(master, textvariable=self.frame_start, width=6).pack(side="left")
        Entry(master, textvariable=self.frame_end, width=6).pack(side="left")
        Label(master, text="解像度").pack()
        Entry(master, textvariable=self.res_x, width=7).pack(side="left")
        Entry(master, textvariable=self.res_y, width=7).pack(side="left")
        Label(master, text="サンプル数").pack()
        Entry(master, textvariable=self.samples, width=7).pack()
        Button(master, text="レンダー出力フォルダ選択", command=self.select_output_dir).pack()
        Label(master, textvariable=self.output_dir).pack()
        Label(master, text="ノイズ除去方式").pack()
        OptionMenu(master, self.method, "OIDN", "FastDVDnet").pack()
        Label(master, text="CUDA(CPU/CUDA切替)").pack()
        OptionMenu(master, self.use_cuda, 0, 1).pack()
        Label(master, text="アップスケールON(1/0)").pack()
        OptionMenu(master, self.do_upscale, 0, 1).pack()
        Label(master, text="フレーム補間ON(1/0)").pack()
        OptionMenu(master, self.do_interpolate, 0, 1).pack()
        Label(master, text="出力コーデック").pack()
        OptionMenu(master, self.codec, "prores_ks", "qtrle").pack()
        Label(master, text="フレームレート").pack()
        OptionMenu(master, self.framerate, 24, 30, 60).pack()
        Button(master, text="全自動バッチ実行", command=self.run_all).pack()
        self.progress_bar.pack()
        self.preview_canvas.pack()
        Label(master, textvariable=self.status).pack()
        # CLIツールパス（各自パス調整）
        self.oidn_path = "C:/oidn/bin/oidnDenoise.exe"
        self.fastdvdnet_path = "fastdvdnet/fastdvdnet.py"
        self.realesrgan_path = "realesrgan-ncnn-vulkan/realesrgan-ncnn-vulkan.exe"
        self.rife_path = "rife-ncnn-vulkan/rife-ncnn-vulkan.exe"

    def select_blender_exe(self):
        path = filedialog.askopenfilename(filetypes=[("Blender実行ファイル", "*.exe")])
        if path:
            self.blender_exe.set(path)

    def select_blend_file(self):
        path = filedialog.askopenfilename(filetypes=[("Blenderファイル", "*.blend")])
        if path:
            self.blend_file.set(path)

    def select_output_dir(self):
        path = filedialog.askdirectory()
        if path:
            self.output_dir.set(path)

    def preview_img(self, img_path):
        show_preview(img_path, self.preview_canvas)

    def run_all(self):
        threading.Thread(target=self._run_all, daemon=True).start()

    def _run_all(self):
        blender_path = self.blender_exe.get()
        blend = self.blend_file.get()
        outdir = self.output_dir.get()
        start = self.frame_start.get()
        end = self.frame_end.get()
        res_x = self.res_x.get()
        res_y = self.res_y.get()
        samples = self.samples.get()
        method = self.method.get()
        codec = self.codec.get()
        framerate = self.framerate.get()
        use_cuda = bool(self.use_cuda.get())
        do_upscale = bool(self.do_upscale.get())
        do_interpolate = bool(self.do_interpolate.get())

        # 各段階のフォルダ
        denoised_dir = os.path.join(outdir, "denoised")
        upscaled_dir = os.path.join(outdir, "upscaled")
        interpolated_dir = os.path.join(outdir, "interpolated")

        try:
            self.status.set("Blenderレンダリング中…")
            blender_render(blender_path, blend, outdir, start, end, res_x, res_y, samples)
            self.status.set("ノイズ除去中…")
            files = sorted(glob(os.path.join(outdir, "render_*.png")))
            self.progress_bar["maximum"] = len(files)
            def prog_cb(i, total):
                self.progress_var.set(i)
                self.status.set(f"ノイズ除去 {i}/{total}")
                self.master.update_idletasks()
            denoise_pngs(outdir, denoised_dir, method, self.oidn_path, self.fastdvdnet_path, use_cuda, prog_cb, self.preview_img)
            cur_in_dir = denoised_dir
            # アップスケール
            if do_upscale:
                self.status.set("アップスケール中…")
                up_files = sorted(glob(os.path.join(cur_in_dir, "*.png")))
                self.progress_bar["maximum"] = len(up_files)
                upscale_pngs(cur_in_dir, upscaled_dir, self.realesrgan_path, use_cuda, scale=2, progress_callback=prog_cb, preview_callback=self.preview_img)
                cur_in_dir = upscaled_dir
            # フレーム補間
            if do_interpolate:
                self.status.set("フレーム補間中…")
                interpolate_pngs(cur_in_dir, interpolated_dir, self.rife_path, use_cuda)
                cur_in_dir = interpolated_dir
            # 動画化
            self.status.set("動画化中…")
            png_pattern = os.path.join(cur_in_dir, "%08d.png")
            out_movie = os.path.join(outdir, "out.mov")
            pngs_to_video(png_pattern, out_movie, framerate, codec)
            self.status.set(f"完了！{out_movie}")
        except Exception as e:
            self.status.set("エラー:" + str(e))

if __name__ == "__main__":
    root = Tk()
    app = AllInOneGUI(root)
    root.mainloop()
