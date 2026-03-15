#!/usr/bin/env python3
"""
Swap Tool — Đổi mặt + Đổi giọng trên video có sẵn.

Sử dụng Deep-Live-Cam (face swap) + RVC-WebUI (voice conversion) + ffmpeg (audio/video).

Cách dùng:
    # Chỉ đổi mặt
    python swap_tool.py --source face.jpg --target video.mp4

    # Đổi mặt + đổi giọng
    python swap_tool.py --source face.jpg --target video.mp4 --rvc-model model.pth --pitch 12

    # Đổi mặt + tăng chất lượng
    python swap_tool.py --source face.jpg --target video.mp4 --enhance

    # Xử lý hàng loạt
    python swap_tool.py --source face.jpg --target-dir ./videos/ --output-dir ./output/
"""

import argparse
import glob
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DLC_DIR = SCRIPT_DIR / "Deep-Live-Cam"

SUPPORTED_VIDEO_EXT = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv", ".wmv"}
SUPPORTED_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".bmp"}


def log(msg: str, level: str = "INFO") -> None:
    colors = {
        "INFO": "\033[36m",
        "OK": "\033[32m",
        "WARN": "\033[33m",
        "ERROR": "\033[31m",
        "STEP": "\033[35m",
    }
    reset = "\033[0m"
    color = colors.get(level, "")
    print(f"{color}[{level}]{reset} {msg}")


def check_prerequisites() -> bool:
    ok = True

    if not shutil.which("ffmpeg"):
        log("ffmpeg chưa được cài đặt. Hãy cài ffmpeg trước.", "ERROR")
        ok = False

    if not shutil.which("ffprobe"):
        log("ffprobe chưa được cài đặt. Hãy cài ffmpeg (bao gồm ffprobe).", "ERROR")
        ok = False

    if not DLC_DIR.is_dir():
        log(f"Không tìm thấy Deep-Live-Cam tại {DLC_DIR}", "ERROR")
        log("Hãy chạy: git clone https://github.com/hacksider/Deep-Live-Cam.git", "ERROR")
        ok = False

    run_py = DLC_DIR / "run.py"
    if not run_py.is_file():
        log(f"Không tìm thấy {run_py}", "ERROR")
        ok = False

    return ok


def get_video_duration(video_path: str) -> float:
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path,
    ]
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode().strip()
        return float(output)
    except Exception:
        return 0.0


def has_audio_stream(video_path: str) -> bool:
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "a",
        "-show_entries", "stream=codec_type",
        "-of", "csv=p=0",
        video_path,
    ]
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode().strip()
        return len(output) > 0
    except Exception:
        return False


# ──────────────────────────────────────────────
# BƯỚC 1: Đổi mặt bằng Deep-Live-Cam
# ──────────────────────────────────────────────

def face_swap(
    source_image: str,
    target_video: str,
    output_video: str,
    execution_provider: str = "cpu",
    enhance: bool = False,
    enhance_model: str = "face_enhancer",
    many_faces: bool = False,
    video_quality: int = 18,
    video_encoder: str = "libx264",
    keep_fps: bool = True,
    mouth_mask: bool = False,
    max_memory: int | None = None,
    execution_threads: int | None = None,
) -> bool:
    """Chạy Deep-Live-Cam để swap khuôn mặt trên video."""
    log("Đang đổi mặt bằng Deep-Live-Cam...", "STEP")

    run_py = str(DLC_DIR / "run.py")

    frame_processors = ["face_swapper"]
    if enhance:
        frame_processors.append(enhance_model)

    cmd = [
        sys.executable, run_py,
        "-s", os.path.abspath(source_image),
        "-t", os.path.abspath(target_video),
        "-o", os.path.abspath(output_video),
        "--frame-processor", *frame_processors,
        "--execution-provider", execution_provider,
        "--video-encoder", video_encoder,
        "--video-quality", str(video_quality),
    ]

    if keep_fps:
        cmd.append("--keep-fps")
    if many_faces:
        cmd.append("--many-faces")
    if mouth_mask:
        cmd.append("--mouth-mask")
    if max_memory:
        cmd.extend(["--max-memory", str(max_memory)])
    if execution_threads:
        cmd.extend(["--execution-threads", str(execution_threads)])

    # Không giữ audio gốc vì ta sẽ thay bằng audio đã đổi giọng
    # Deep-Live-Cam mặc định keep-audio=True, ta không cần override
    # vì cuối cùng sẽ dùng ffmpeg ghép lại

    log(f"  Lệnh: {' '.join(cmd)}")

    start = time.time()
    try:
        result = subprocess.run(
            cmd,
            cwd=str(DLC_DIR),
            capture_output=False,
            timeout=7200,  # 2 giờ timeout
        )
        elapsed = time.time() - start

        if result.returncode != 0:
            log(f"Deep-Live-Cam thoát với mã lỗi {result.returncode}", "ERROR")
            return False

        if not os.path.isfile(output_video):
            log(f"File output không tồn tại: {output_video}", "ERROR")
            return False

        log(f"Đổi mặt hoàn tất ({elapsed:.1f}s) → {output_video}", "OK")
        return True

    except subprocess.TimeoutExpired:
        log("Deep-Live-Cam bị timeout (>2 giờ)", "ERROR")
        return False
    except Exception as e:
        log(f"Lỗi khi chạy Deep-Live-Cam: {e}", "ERROR")
        return False


# ──────────────────────────────────────────────
# BƯỚC 2: Tách audio từ video
# ──────────────────────────────────────────────

def extract_audio(video_path: str, audio_output: str, sample_rate: int = 44100) -> bool:
    """Tách audio từ video thành file WAV."""
    log("Đang tách audio từ video gốc...", "STEP")

    if not has_audio_stream(video_path):
        log("Video không có audio stream.", "WARN")
        return False

    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", video_path,
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", str(sample_rate),
        "-ac", "1",
        audio_output,
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True)
        if os.path.isfile(audio_output):
            log(f"Tách audio hoàn tất → {audio_output}", "OK")
            return True
        else:
            log("Không tạo được file audio.", "ERROR")
            return False
    except subprocess.CalledProcessError as e:
        log(f"Lỗi ffmpeg khi tách audio: {e.stderr.decode()}", "ERROR")
        return False


# ──────────────────────────────────────────────
# BƯỚC 3: Đổi giọng bằng RVC
# ──────────────────────────────────────────────

def find_rvc_dir() -> Path | None:
    """Tìm thư mục RVC-WebUI trong workspace."""
    candidates = [
        SCRIPT_DIR / "Retrieval-based-Voice-Conversion-WebUI",
        SCRIPT_DIR / "RVC-WebUI",
        SCRIPT_DIR / "rvc",
        Path.home() / "Retrieval-based-Voice-Conversion-WebUI",
    ]
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    return None


def voice_convert_rvc(
    audio_input: str,
    audio_output: str,
    rvc_model: str,
    pitch: int = 0,
    index_path: str | None = None,
    index_rate: float = 0.66,
    f0_method: str = "harvest",
    rvc_dir: str | None = None,
) -> bool:
    """Đổi giọng bằng RVC-WebUI CLI."""
    log("Đang đổi giọng bằng RVC...", "STEP")

    rvc_path = Path(rvc_dir) if rvc_dir else find_rvc_dir()
    if not rvc_path or not rvc_path.is_dir():
        log("Không tìm thấy RVC-WebUI. Bỏ qua bước đổi giọng.", "WARN")
        log("Để sử dụng, hãy clone RVC-WebUI:", "WARN")
        log("  git clone https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI.git", "WARN")
        return False

    cli_script = rvc_path / "tools" / "infer_cli.py"
    if not cli_script.is_file():
        log(f"Không tìm thấy RVC CLI script: {cli_script}", "ERROR")
        return False

    cmd = [
        sys.executable, str(cli_script),
        "--f0up_key", str(pitch),
        "--input_path", os.path.abspath(audio_input),
        "--opt_path", os.path.abspath(audio_output),
        "--model_name", rvc_model,
        "--index_rate", str(index_rate),
        "--f0method", f0_method,
        "--device", "cuda:0",
    ]

    if index_path:
        cmd.extend(["--index_path", index_path])

    log(f"  Model: {rvc_model}, Pitch: {pitch:+d}, F0: {f0_method}")

    try:
        result = subprocess.run(
            cmd,
            cwd=str(rvc_path),
            capture_output=False,
            timeout=3600,
        )

        if result.returncode != 0:
            log(f"RVC thoát với mã lỗi {result.returncode}", "ERROR")
            return False

        if os.path.isfile(audio_output):
            log(f"Đổi giọng hoàn tất → {audio_output}", "OK")
            return True
        else:
            log("File audio output không tồn tại.", "ERROR")
            return False

    except subprocess.TimeoutExpired:
        log("RVC bị timeout (>1 giờ)", "ERROR")
        return False
    except Exception as e:
        log(f"Lỗi khi chạy RVC: {e}", "ERROR")
        return False


# ──────────────────────────────────────────────
# BƯỚC 4: Ghép video + audio
# ──────────────────────────────────────────────

def merge_video_audio(
    video_path: str,
    audio_path: str,
    output_path: str,
    audio_bitrate: str = "192k",
) -> bool:
    """Ghép video đã swap mặt với audio đã đổi giọng."""
    log("Đang ghép video + audio...", "STEP")

    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", audio_bitrate,
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        "-movflags", "+faststart",
        output_path,
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True)
        if os.path.isfile(output_path):
            log(f"Ghép hoàn tất → {output_path}", "OK")
            return True
        else:
            log("File output không tồn tại.", "ERROR")
            return False
    except subprocess.CalledProcessError as e:
        log(f"Lỗi ffmpeg khi ghép: {e.stderr.decode()}", "ERROR")
        return False


def strip_audio(video_path: str, output_path: str) -> bool:
    """Xóa audio khỏi video."""
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", video_path,
        "-an", "-c:v", "copy",
        output_path,
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        return os.path.isfile(output_path)
    except Exception:
        return False


# ──────────────────────────────────────────────
# PIPELINE CHÍNH
# ──────────────────────────────────────────────

def process_single_video(args: argparse.Namespace, target_video: str, output_path: str) -> bool:
    """Xử lý một video: đổi mặt → tách audio → đổi giọng → ghép."""
    total_start = time.time()
    basename = Path(target_video).stem
    work_dir = Path(args.work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)

    log(f"{'='*60}", "INFO")
    log(f"Xử lý: {target_video}", "INFO")
    log(f"Output: {output_path}", "INFO")
    log(f"{'='*60}", "INFO")

    # ── Bước 1: Đổi mặt ──
    swapped_video = str(work_dir / f"{basename}_swapped.mp4")

    enhance_model = "face_enhancer"
    if args.enhance_model:
        enhance_model = args.enhance_model

    ok = face_swap(
        source_image=args.source,
        target_video=target_video,
        output_video=swapped_video,
        execution_provider=args.execution_provider,
        enhance=args.enhance,
        enhance_model=enhance_model,
        many_faces=args.many_faces,
        video_quality=args.video_quality,
        video_encoder=args.video_encoder,
        keep_fps=args.keep_fps,
        mouth_mask=args.mouth_mask,
        max_memory=args.max_memory,
        execution_threads=args.execution_threads,
    )

    if not ok:
        log("Đổi mặt thất bại. Dừng xử lý.", "ERROR")
        return False

    # Nếu không cần đổi giọng → output là video đã swap (giữ audio gốc)
    if not args.rvc_model:
        if swapped_video != output_path:
            shutil.move(swapped_video, output_path)
        total_elapsed = time.time() - total_start
        log(f"HOÀN THÀNH (chỉ đổi mặt) — {total_elapsed:.1f}s → {output_path}", "OK")
        return True

    # ── Bước 2: Tách audio từ video gốc ──
    audio_original = str(work_dir / f"{basename}_audio_original.wav")
    has_audio = extract_audio(target_video, audio_original)

    if not has_audio:
        log("Video không có audio, bỏ qua đổi giọng.", "WARN")
        if swapped_video != output_path:
            shutil.move(swapped_video, output_path)
        total_elapsed = time.time() - total_start
        log(f"HOÀN THÀNH (chỉ đổi mặt, video gốc không có audio) — {total_elapsed:.1f}s", "OK")
        return True

    # ── Bước 3: Đổi giọng ──
    audio_converted = str(work_dir / f"{basename}_audio_converted.wav")
    voice_ok = voice_convert_rvc(
        audio_input=audio_original,
        audio_output=audio_converted,
        rvc_model=args.rvc_model,
        pitch=args.pitch,
        index_path=args.rvc_index,
        index_rate=args.index_rate,
        f0_method=args.f0_method,
        rvc_dir=args.rvc_dir,
    )

    if not voice_ok:
        log("Đổi giọng thất bại. Giữ nguyên audio gốc.", "WARN")
        if swapped_video != output_path:
            shutil.move(swapped_video, output_path)
        total_elapsed = time.time() - total_start
        log(f"HOÀN THÀNH (chỉ đổi mặt, đổi giọng thất bại) — {total_elapsed:.1f}s", "OK")
        return True

    # ── Bước 4: Ghép video (đã swap) + audio (đã đổi giọng) ──
    video_no_audio = str(work_dir / f"{basename}_noaudio.mp4")
    strip_audio(swapped_video, video_no_audio)

    ok = merge_video_audio(video_no_audio, audio_converted, output_path)

    # Dọn dẹp file trung gian
    if not args.keep_temp:
        for f in [swapped_video, audio_original, audio_converted, video_no_audio]:
            if os.path.isfile(f) and f != output_path:
                os.remove(f)

    total_elapsed = time.time() - total_start
    if ok:
        log(f"HOÀN THÀNH (đổi mặt + đổi giọng) — {total_elapsed:.1f}s → {output_path}", "OK")
    else:
        log(f"Ghép video thất bại sau {total_elapsed:.1f}s", "ERROR")

    return ok


def main():
    parser = argparse.ArgumentParser(
        description="Swap Tool — Đổi mặt + Đổi giọng trên video có sẵn",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ:
  # Chỉ đổi mặt
  python swap_tool.py -s face.jpg -t video.mp4

  # Đổi mặt + tăng chất lượng khuôn mặt
  python swap_tool.py -s face.jpg -t video.mp4 --enhance

  # Đổi mặt + đổi giọng (nam → nữ)
  python swap_tool.py -s face.jpg -t video.mp4 --rvc-model model.pth --pitch 12

  # Xử lý hàng loạt tất cả video trong thư mục
  python swap_tool.py -s face.jpg --target-dir ./videos/ --output-dir ./results/

  # Dùng GPU NVIDIA
  python swap_tool.py -s face.jpg -t video.mp4 --gpu cuda

  # Đổi tất cả khuôn mặt trong video
  python swap_tool.py -s face.jpg -t video.mp4 --many-faces
        """,
    )

    # ── Bắt buộc ──
    parser.add_argument(
        "-s", "--source",
        required=True,
        help="Ảnh khuôn mặt nguồn (JPG/PNG, rõ nét, chính diện)",
    )

    target_group = parser.add_mutually_exclusive_group(required=True)
    target_group.add_argument(
        "-t", "--target",
        help="File video đầu vào",
    )
    target_group.add_argument(
        "--target-dir",
        help="Thư mục chứa nhiều video để xử lý hàng loạt",
    )

    # ── Output ──
    parser.add_argument(
        "-o", "--output",
        help="File video đầu ra (mặc định: <tên_gốc>_swapped.mp4)",
    )
    parser.add_argument(
        "--output-dir",
        help="Thư mục đầu ra cho xử lý hàng loạt (mặc định: ./output/)",
        default="./output",
    )

    # ── Face Swap ──
    swap_group = parser.add_argument_group("Face Swap (Deep-Live-Cam)")
    swap_group.add_argument(
        "--gpu", "--execution-provider",
        dest="execution_provider",
        default="cpu",
        choices=["cpu", "cuda", "coreml", "rocm", "directml", "openvino"],
        help="Execution provider (mặc định: cpu, dùng cuda cho GPU NVIDIA)",
    )
    swap_group.add_argument(
        "--enhance",
        action="store_true",
        default=False,
        help="Bật face enhancer để tăng chất lượng khuôn mặt",
    )
    swap_group.add_argument(
        "--enhance-model",
        choices=["face_enhancer", "face_enhancer_gpen256", "face_enhancer_gpen512"],
        default=None,
        help="Chọn model face enhancer (mặc định: face_enhancer / GFPGAN)",
    )
    swap_group.add_argument(
        "--many-faces",
        action="store_true",
        default=False,
        help="Swap tất cả khuôn mặt trong video",
    )
    swap_group.add_argument(
        "--mouth-mask",
        action="store_true",
        default=False,
        help="Giữ nguyên vùng miệng gốc (khớp khẩu hình)",
    )
    swap_group.add_argument(
        "--video-quality",
        type=int,
        default=18,
        choices=range(0, 52),
        metavar="[0-51]",
        help="Chất lượng video output (CRF, 0=tốt nhất, mặc định: 18)",
    )
    swap_group.add_argument(
        "--video-encoder",
        default="libx264",
        choices=["libx264", "libx265", "libvpx-vp9"],
        help="Codec video (mặc định: libx264)",
    )
    swap_group.add_argument(
        "--keep-fps",
        action="store_true",
        default=True,
        help="Giữ nguyên FPS gốc (mặc định: bật)",
    )
    swap_group.add_argument(
        "--max-memory",
        type=int,
        default=None,
        help="Giới hạn RAM tối đa (GB)",
    )
    swap_group.add_argument(
        "--execution-threads",
        type=int,
        default=None,
        help="Số thread xử lý",
    )

    # ── Voice Conversion ──
    voice_group = parser.add_argument_group("Voice Conversion (RVC)")
    voice_group.add_argument(
        "--rvc-model",
        default=None,
        help="Tên model RVC (file .pth). Bỏ trống = không đổi giọng",
    )
    voice_group.add_argument(
        "--pitch",
        type=int,
        default=0,
        help="Dịch cao độ giọng: +12 (nam→nữ), -12 (nữ→nam), 0 (giữ nguyên)",
    )
    voice_group.add_argument(
        "--rvc-index",
        default=None,
        help="File .index của model RVC (tùy chọn)",
    )
    voice_group.add_argument(
        "--index-rate",
        type=float,
        default=0.66,
        help="Index rate (0.0-1.0, mặc định: 0.66)",
    )
    voice_group.add_argument(
        "--f0-method",
        dest="f0_method",
        default="harvest",
        choices=["pm", "harvest", "crepe", "rmvpe"],
        help="Phương pháp F0 (mặc định: harvest)",
    )
    voice_group.add_argument(
        "--rvc-dir",
        default=None,
        help="Đường dẫn tới thư mục RVC-WebUI (tự tìm nếu bỏ trống)",
    )

    # ── Khác ──
    other_group = parser.add_argument_group("Tùy chọn khác")
    other_group.add_argument(
        "--work-dir",
        default="./swap_temp",
        help="Thư mục chứa file trung gian (mặc định: ./swap_temp)",
    )
    other_group.add_argument(
        "--keep-temp",
        action="store_true",
        default=False,
        help="Giữ lại file trung gian sau khi xong",
    )

    args = parser.parse_args()

    # ── Kiểm tra điều kiện tiên quyết ──
    print()
    log("Swap Tool — Đổi mặt + Đổi giọng trên video")
    log("=" * 50)
    print()

    if not check_prerequisites():
        sys.exit(1)

    if not os.path.isfile(args.source):
        log(f"Không tìm thấy ảnh nguồn: {args.source}", "ERROR")
        sys.exit(1)

    ext = Path(args.source).suffix.lower()
    if ext not in SUPPORTED_IMAGE_EXT:
        log(f"Ảnh nguồn phải là: {', '.join(SUPPORTED_IMAGE_EXT)}", "ERROR")
        sys.exit(1)

    # ── Xử lý một video ──
    if args.target:
        if not os.path.isfile(args.target):
            log(f"Không tìm thấy video: {args.target}", "ERROR")
            sys.exit(1)

        if not args.output:
            stem = Path(args.target).stem
            parent = Path(args.target).parent
            args.output = str(parent / f"{stem}_output.mp4")

        success = process_single_video(args, args.target, args.output)
        sys.exit(0 if success else 1)

    # ── Xử lý hàng loạt ──
    if args.target_dir:
        target_dir = Path(args.target_dir)
        if not target_dir.is_dir():
            log(f"Không tìm thấy thư mục: {args.target_dir}", "ERROR")
            sys.exit(1)

        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        videos = []
        for ext_pattern in SUPPORTED_VIDEO_EXT:
            videos.extend(target_dir.glob(f"*{ext_pattern}"))
        videos.sort()

        if not videos:
            log(f"Không tìm thấy video nào trong {args.target_dir}", "WARN")
            sys.exit(0)

        log(f"Tìm thấy {len(videos)} video để xử lý", "INFO")
        print()

        results = []
        for i, video in enumerate(videos, 1):
            log(f"[{i}/{len(videos)}] {video.name}", "INFO")
            out = output_dir / f"{video.stem}_output.mp4"
            ok = process_single_video(args, str(video), str(out))
            results.append((video.name, ok))
            print()

        # Tóm tắt
        print()
        log("=" * 50)
        log("TÓM TẮT KẾT QUẢ", "STEP")
        log("=" * 50)
        success_count = sum(1 for _, ok in results if ok)
        for name, ok in results:
            status = "OK" if ok else "ERROR"
            log(f"  {name}: {'Thành công' if ok else 'Thất bại'}", status)
        log(f"Tổng: {success_count}/{len(results)} thành công", "INFO")

        sys.exit(0 if success_count == len(results) else 1)


if __name__ == "__main__":
    main()
