# Swap Tool — Đổi Mặt + Đổi Giọng

Tool tự động đổi mặt và đổi giọng trên video, sử dụng **Deep-Live-Cam** + **RVC-WebUI** + **ffmpeg**.

## Cài đặt nhanh

```bash
# 1. Clone repo
git clone <repo-url> && cd <repo>

# 2. Chạy setup (CPU)
bash setup.sh

# 2b. Hoặc setup với GPU NVIDIA
bash setup.sh --gpu
```

## Sử dụng nhanh

```bash
# Chỉ đổi mặt
python3 swap_tool.py -s anh_mat.jpg -t video.mp4

# Đổi mặt + GPU NVIDIA
python3 swap_tool.py -s anh_mat.jpg -t video.mp4 --gpu cuda

# Đổi mặt + tăng chất lượng
python3 swap_tool.py -s anh_mat.jpg -t video.mp4 --enhance --gpu cuda

# Đổi mặt + đổi giọng (nam → nữ)
python3 swap_tool.py -s anh_mat.jpg -t video.mp4 --rvc-model model.pth --pitch 12

# Đổi mặt + đổi giọng (nữ → nam)
python3 swap_tool.py -s anh_mat.jpg -t video.mp4 --rvc-model model.pth --pitch -12

# Xử lý hàng loạt
python3 swap_tool.py -s anh_mat.jpg --target-dir ./videos/ --output-dir ./output/

# Đổi tất cả khuôn mặt trong video
python3 swap_tool.py -s anh_mat.jpg -t video.mp4 --many-faces --gpu cuda
```

## Tham số đầy đủ

| Tham số | Mô tả | Mặc định |
|---|---|---|
| `-s`, `--source` | **Bắt buộc.** Ảnh khuôn mặt nguồn (JPG/PNG) | — |
| `-t`, `--target` | File video đầu vào | — |
| `--target-dir` | Thư mục video (xử lý hàng loạt) | — |
| `-o`, `--output` | File video đầu ra | `<tên>_output.mp4` |
| `--output-dir` | Thư mục đầu ra (hàng loạt) | `./output` |
| `--gpu` | Execution provider: `cpu`, `cuda`, `coreml`, `rocm` | `cpu` |
| `--enhance` | Bật face enhancer (GFPGAN) | tắt |
| `--enhance-model` | Model enhancer: `face_enhancer`, `face_enhancer_gpen256`, `face_enhancer_gpen512` | `face_enhancer` |
| `--many-faces` | Swap tất cả khuôn mặt | tắt |
| `--mouth-mask` | Giữ nguyên khẩu hình miệng | tắt |
| `--video-quality` | Chất lượng video (CRF 0-51, thấp = tốt hơn) | `18` |
| `--video-encoder` | Codec: `libx264`, `libx265`, `libvpx-vp9` | `libx264` |
| `--rvc-model` | Model RVC (.pth) — bỏ trống = không đổi giọng | — |
| `--pitch` | Dịch cao độ: `+12` nam→nữ, `-12` nữ→nam | `0` |
| `--f0-method` | Phương pháp F0: `pm`, `harvest`, `crepe`, `rmvpe` | `harvest` |
| `--keep-temp` | Giữ file trung gian | tắt |

## Cấu trúc dự án

```
.
├── swap_tool.py          # Tool chính — CLI
├── setup.sh              # Script cài đặt tự động
├── requirements.txt      # Python dependencies
├── Deep-Live-Cam/        # Engine đổi mặt (auto-clone khi setup)
│   ├── models/           # ONNX models (auto-download)
│   └── ...
└── README.md             # Tài liệu này
```

---

## Hướng dẫn chi tiết

Tài liệu hướng dẫn tạo "người ảo" hoàn chỉnh bằng cách kết hợp **đổi mặt** (Deep-Live-Cam / DeepFaceLive) và **đổi giọng** (RVC-WebUI):

- **Phần A:** Xử lý video có sẵn (offline / hậu kỳ)
- **Phần B:** Phát sóng trực tiếp (live stream) qua OBS lên TikTok / Facebook

---

## Tổng quan kiến trúc

### Chế độ Offline (Video có sẵn)

```
                    Video gốc (.mp4)
                         │
          ┌──────────────┴──────────────┐
          v                             v
  ┌───────────────┐            ┌───────────────┐
  │  Deep-Live-Cam│            │ ffmpeg (tách) │
  │  / roop       │            │      +        │
  │  (Đổi mặt)   │            │  RVC-WebUI    │
  │               │            │  (Đổi giọng)  │
  └───────┬───────┘            └───────┬───────┘
          │                            │
          │    ┌───────────────┐       │
          └───>│ ffmpeg (ghép) │<──────┘
               │               │
               │  final.mp4    │
               └───────────────┘
```

### Chế độ Live Stream (Real-time)

```
┌──────────┐    ┌─────────────────────┐    ┌──────────────────────┐
│  Webcam  │───>│  Deep-Live-Cam /    │───>│  OBS Virtual Camera  │──┐
│          │    │  DeepFaceLive       │    │  (nguồn Hình ảnh)    │  │
└──────────┘    └─────────────────────┘    └──────────────────────┘  │
                                                                     │
┌──────────┐    ┌─────────────────────┐    ┌──────────────────────┐  │  ┌───────────┐    ┌──────────────┐
│   Micro  │───>│  RVC-WebUI          │───>│  Virtual Audio Cable │──┼─>│    OBS    │───>│ TikTok /     │
│          │    │  (Voice Changer)    │    │  (VB-Audio Cable)    │  │  │  Studio   │    │ Facebook     │
└──────────┘    └─────────────────────┘    └──────────────────────┘  │  └───────────┘    └──────────────┘
                                                                     │
                                                                     └── Hội tụ tại OBS
```

---

## Mục lục

### Phần A — Xử lý Video có sẵn (Offline)

- [A1. Tổng quan quy trình offline](#a1-tổng-quan-quy-trình-offline)
- [A2. Đổi mặt trên video có sẵn](#a2-đổi-mặt-trên-video-có-sẵn)
- [A3. Đổi giọng trên video có sẵn](#a3-đổi-giọng-trên-video-có-sẵn)
- [A4. Ghép hình + tiếng thành video hoàn chỉnh](#a4-ghép-hình--tiếng-thành-video-hoàn-chỉnh)
- [A5. Script tự động hóa toàn bộ quy trình](#a5-script-tự-động-hóa-toàn-bộ-quy-trình)

### Phần B — Live Stream (Real-time)

1. [Yêu cầu phần cứng & phần mềm](#1-yêu-cầu-phần-cứng--phần-mềm)
2. [Bước 1 – Cài đặt & cấu hình Deep-Live-Cam (Đổi mặt)](#2-bước-1--cài-đặt--cấu-hình-deep-live-cam-đổi-mặt)
3. [Bước 2 – Cài đặt & cấu hình RVC-WebUI (Đổi giọng)](#3-bước-2--cài-đặt--cấu-hình-rvc-webui-đổi-giọng)
4. [Bước 3 – Cài đặt Virtual Audio Cable (VB-Audio)](#4-bước-3--cài-đặt-virtual-audio-cable-vb-audio)
5. [Bước 4 – Cấu hình OBS Studio](#5-bước-4--cấu-hình-obs-studio)
6. [Bước 5 – Phát sóng lên TikTok / Facebook](#6-bước-5--phát-sóng-lên-tiktok--facebook)
7. [Xử lý sự cố thường gặp](#7-xử-lý-sự-cố-thường-gặp)
8. [Mẹo tối ưu hiệu suất](#8-mẹo-tối-ưu-hiệu-suất)

---

# Phần A — Xử lý Video có sẵn (Offline)

## A1. Tổng quan quy trình offline

Hoàn toàn có thể đổi mặt + đổi giọng trên một video đã quay sẵn. Quy trình gồm 3 bước chính:

```
                         Video gốc (input.mp4)
                                │
               ┌────────────────┼────────────────┐
               │                                 │
               v                                 v
     ┌──────────────────┐              ┌──────────────────┐
     │  BƯỚC 1: ĐỔI MẶT │              │  BƯỚC 2: ĐỔI GIỌNG│
     │                    │              │                    │
     │  Deep-Live-Cam     │              │  ffmpeg (tách audio)│
     │  hoặc roop         │              │       +             │
     │                    │              │  RVC-WebUI          │
     │  input.mp4         │              │                    │
     │  + ảnh khuôn mặt   │              │  audio gốc → audio │
     │  → swapped.mp4     │              │  đã đổi giọng      │
     └────────┬───────────┘              └────────┬───────────┘
              │                                   │
              │        ┌──────────────────┐       │
              └───────>│  BƯỚC 3: GHÉP    │<──────┘
                       │                  │
                       │  ffmpeg          │
                       │  video (đã swap) │
                       │  + audio (đã đổi)│
                       │  → final.mp4     │
                       └──────────────────┘
```

**So sánh với Live Stream:**

| | Offline (Video có sẵn) | Live Stream |
|---|---|---|
| Chất lượng | Cao hơn (xử lý từng frame) | Phụ thuộc tốc độ real-time |
| Thời gian | Lâu hơn (phải render) | Tức thời |
| Yêu cầu GPU | Vẫn cần GPU mạnh | Cần GPU mạnh + ổn định |
| Không cần | VB-Audio, OBS, Virtual Camera | — |
| Cần thêm | ffmpeg (tách/ghép audio) | OBS, VB-Audio |

---

## A2. Đổi mặt trên video có sẵn

### Cách 1: Dùng Deep-Live-Cam (đơn giản nhất)

Deep-Live-Cam hỗ trợ xử lý file video trực tiếp, không chỉ webcam.

```bash
git clone https://github.com/hacksider/Deep-Live-Cam.git
cd Deep-Live-Cam
pip install -r requirements.txt
```

**Chạy bằng giao diện (GUI):**

1. Chạy `python run.py`
2. **Source image:** Chọn ảnh khuôn mặt muốn hoán đổi sang.
3. **Target:** Chọn **file video** (thay vì webcam) — ví dụ `input.mp4`.
4. Chọn thư mục output.
5. Nhấn **Start** và chờ xử lý.

**Chạy bằng dòng lệnh (CLI) — nhanh hơn cho batch processing:**

```bash
python run.py \
  --source "anh_khuon_mat.jpg" \
  --target "input.mp4" \
  --output "swapped_video.mp4" \
  --execution-provider cuda \
  --frame-processor face_swapper
```

Các tham số quan trọng:

| Tham số | Mô tả |
|---|---|
| `--source` | Ảnh khuôn mặt nguồn (ảnh rõ nét, chính diện) |
| `--target` | File video đầu vào |
| `--output` | File video đầu ra |
| `--execution-provider cuda` | Dùng GPU NVIDIA (nhanh hơn nhiều so với CPU) |
| `--frame-processor face_swapper` | Chỉ swap khuôn mặt |
| `--frame-processor face_swapper face_enhancer` | Swap + tăng chất lượng mặt |
| `--keep-fps` | Giữ nguyên FPS gốc |
| `--keep-audio` | Giữ nguyên audio gốc (chưa đổi giọng) |
| `--many-faces` | Swap tất cả khuôn mặt trong video (nếu có nhiều người) |

### Cách 2: Dùng roop (công cụ gốc)

```bash
git clone https://github.com/s0md3v/roop.git
cd roop
pip install -r requirements.txt
```

```bash
python run.py \
  --source "anh_khuon_mat.jpg" \
  --target "input.mp4" \
  --output "swapped_video.mp4" \
  --execution-provider cuda
```

### Cách 3: Dùng DeepFaceLab (chất lượng cao nhất, phức tạp hơn)

DeepFaceLab cho kết quả tốt nhất nhưng cần train model riêng (mất vài giờ đến vài ngày). Phù hợp khi cần chất lượng cao nhất hoặc xử lý video dài.

1. Tải từ: https://github.com/iperov/DeepFaceLab
2. Quy trình: Extract faces → Train model → Merge vào video.
3. Tham khảo hướng dẫn chi tiết trên kênh YouTube của dự án.

### So sánh các công cụ đổi mặt cho video offline

| Công cụ | Dễ dùng | Chất lượng | Tốc độ | Phù hợp cho |
|---|---|---|---|---|
| **Deep-Live-Cam** | Rất dễ | Tốt | Nhanh | Video ngắn, dùng nhanh |
| **roop** | Dễ | Tốt | Nhanh | Video ngắn, CLI |
| **DeepFaceLab** | Khó | Rất tốt | Chậm (cần train) | Video chuyên nghiệp |

---

## A3. Đổi giọng trên video có sẵn

### Bước 3.1: Tách audio ra khỏi video

Dùng **ffmpeg** để tách phần âm thanh:

```bash
# Tách audio thành file WAV (chất lượng cao, không nén)
ffmpeg -i input.mp4 -vn -acodec pcm_s16le -ar 44100 -ac 1 audio_goc.wav

# Hoặc nếu đã swap mặt ở bước trước, tách audio từ video gốc
ffmpeg -i input.mp4 -vn -acodec pcm_s16le -ar 44100 -ac 1 audio_goc.wav
```

Giải thích tham số:

| Tham số | Mô tả |
|---|---|
| `-vn` | Bỏ phần video, chỉ lấy audio |
| `-acodec pcm_s16le` | Codec WAV không nén |
| `-ar 44100` | Sample rate 44100 Hz |
| `-ac 1` | Mono (1 kênh — RVC hoạt động tốt nhất với mono) |

### Bước 3.2: Đổi giọng bằng RVC-WebUI (chế độ file)

1. Chạy RVC-WebUI:

```bash
cd Retrieval-based-Voice-Conversion-WebUI
python infer-web.py
```

2. Truy cập `http://localhost:7865`
3. Chuyển sang tab **Inference** (không phải tab Real-time).
4. Cấu hình:
   - **Model:** Chọn model giọng nói đã tải (file `.pth`).
   - **Input audio:** Chọn file `audio_goc.wav` vừa tách.
   - **Transpose (Pitch):** +12 (nam→nữ), -12 (nữ→nam), 0 (giữ cao độ).
   - **Index file:** Chọn file `.index` tương ứng với model (nếu có).
   - **Index Rate:** 0.5 – 0.8
   - **Feature retrieval method:** pm hoặc harvest (harvest chậm hơn nhưng chính xác hơn).
5. Nhấn **Convert** / **Chuyển đổi**.
6. Tải file audio đã đổi giọng về — ví dụ: `audio_da_doi.wav`.

### Bước 3.2 (thay thế): Dùng RVC CLI

Nếu muốn tự động hóa bằng dòng lệnh:

```bash
python tools/infer_cli.py \
  --f0up_key 12 \
  --input_path "audio_goc.wav" \
  --index_path "logs/model_name/added_index.index" \
  --f0method harvest \
  --opt_path "audio_da_doi.wav" \
  --model_name "model_name.pth" \
  --index_rate 0.66 \
  --device "cuda:0"
```

### Bước 3.2 (thay thế 2): Dùng so-vits-svc

Một lựa chọn khác cho đổi giọng offline với chất lượng cao:

```bash
git clone https://github.com/svc-develop-team/so-vits-svc.git
cd so-vits-svc
pip install -r requirements.txt
```

```bash
python inference_main.py \
  -m "logs/model/G_xxx.pth" \
  -c "configs/config.json" \
  -n "audio_goc.wav" \
  -t 0 \
  -s "speaker_name"
```

---

## A4. Ghép hình + tiếng thành video hoàn chỉnh

Sau khi có **video đã đổi mặt** (`swapped_video.mp4`) và **audio đã đổi giọng** (`audio_da_doi.wav`), ghép lại bằng ffmpeg:

### Cách 1: Thay thế audio (đơn giản)

```bash
ffmpeg -i swapped_video.mp4 -i audio_da_doi.wav \
  -c:v copy -c:a aac -b:a 192k \
  -map 0:v:0 -map 1:a:0 \
  -shortest \
  final_output.mp4
```

Giải thích:

| Tham số | Mô tả |
|---|---|
| `-c:v copy` | Giữ nguyên codec video (không re-encode, nhanh) |
| `-c:a aac -b:a 192k` | Encode audio thành AAC 192kbps |
| `-map 0:v:0` | Lấy video stream từ file thứ nhất (swapped_video) |
| `-map 1:a:0` | Lấy audio stream từ file thứ hai (audio_da_doi) |
| `-shortest` | Cắt theo file ngắn hơn (phòng trường hợp lệch độ dài) |

### Cách 2: Nếu video đã swap vẫn còn audio cũ, cần xóa audio cũ trước

```bash
# Xóa audio cũ khỏi video đã swap
ffmpeg -i swapped_video.mp4 -an -c:v copy swapped_no_audio.mp4

# Ghép audio mới
ffmpeg -i swapped_no_audio.mp4 -i audio_da_doi.wav \
  -c:v copy -c:a aac -b:a 192k \
  -map 0:v:0 -map 1:a:0 \
  -shortest \
  final_output.mp4
```

### Cách 3: Nếu cần đồng bộ (audio bị lệch thời gian)

```bash
# Thêm delay cho audio (ví dụ: trễ 0.5 giây)
ffmpeg -i swapped_video.mp4 -i audio_da_doi.wav \
  -c:v copy -c:a aac -b:a 192k \
  -map 0:v:0 -map 1:a:0 \
  -af "adelay=500|500" \
  -shortest \
  final_output.mp4
```

### Kiểm tra kết quả

```bash
# Xem thông tin file output
ffmpeg -i final_output.mp4

# Phát thử (nếu có ffplay)
ffplay final_output.mp4
```

---

## A5. Script tự động hóa toàn bộ quy trình

Dưới đây là script Bash tổng hợp toàn bộ quy trình xử lý video offline:

```bash
#!/bin/bash
# ============================================================
#  Script: swap_face_voice.sh
#  Đổi mặt + Đổi giọng cho video có sẵn
#  Sử dụng: bash swap_face_voice.sh <video_goc> <anh_mat> <rvc_model>
# ============================================================

VIDEO_INPUT="$1"        # Video gốc (ví dụ: input.mp4)
FACE_IMAGE="$2"         # Ảnh khuôn mặt (ví dụ: face.jpg)
RVC_MODEL="$3"          # Tên model RVC (ví dụ: model_name.pth)
PITCH="${4:-0}"          # Pitch shift, mặc định 0 (tùy chọn)

# Tên file trung gian
BASENAME=$(basename "$VIDEO_INPUT" .mp4)
SWAPPED_VIDEO="${BASENAME}_swapped.mp4"
AUDIO_ORIGINAL="${BASENAME}_audio_goc.wav"
AUDIO_CONVERTED="${BASENAME}_audio_doi.wav"
FINAL_OUTPUT="${BASENAME}_final.mp4"

echo "=== BƯỚC 1: Đổi mặt trên video ==="
cd Deep-Live-Cam
python run.py \
  --source "../$FACE_IMAGE" \
  --target "../$VIDEO_INPUT" \
  --output "../$SWAPPED_VIDEO" \
  --execution-provider cuda \
  --frame-processor face_swapper face_enhancer \
  --keep-fps
cd ..

echo "=== BƯỚC 2: Tách audio từ video gốc ==="
ffmpeg -y -i "$VIDEO_INPUT" -vn -acodec pcm_s16le -ar 44100 -ac 1 "$AUDIO_ORIGINAL"

echo "=== BƯỚC 3: Đổi giọng bằng RVC ==="
cd Retrieval-based-Voice-Conversion-WebUI
python tools/infer_cli.py \
  --f0up_key "$PITCH" \
  --input_path "../$AUDIO_ORIGINAL" \
  --opt_path "../$AUDIO_CONVERTED" \
  --model_name "$RVC_MODEL" \
  --index_rate 0.66 \
  --device "cuda:0" \
  --f0method harvest
cd ..

echo "=== BƯỚC 4: Ghép video đã swap + audio đã đổi giọng ==="
ffmpeg -y -i "$SWAPPED_VIDEO" -i "$AUDIO_CONVERTED" \
  -c:v copy -c:a aac -b:a 192k \
  -map 0:v:0 -map 1:a:0 \
  -shortest \
  "$FINAL_OUTPUT"

echo "=== HOÀN THÀNH ==="
echo "File output: $FINAL_OUTPUT"

# Dọn file trung gian (tùy chọn)
# rm -f "$SWAPPED_VIDEO" "$AUDIO_ORIGINAL" "$AUDIO_CONVERTED"
```

**Cách sử dụng:**

```bash
chmod +x swap_face_voice.sh

# Cơ bản (giữ nguyên cao độ giọng)
bash swap_face_voice.sh video_goc.mp4 anh_khuon_mat.jpg model_giong.pth

# Nam chuyển nữ (pitch +12)
bash swap_face_voice.sh video_goc.mp4 anh_khuon_mat.jpg model_giong.pth 12

# Nữ chuyển nam (pitch -12)
bash swap_face_voice.sh video_goc.mp4 anh_khuon_mat.jpg model_giong.pth -12
```

### Xử lý hàng loạt (batch) nhiều video

```bash
#!/bin/bash
# Xử lý tất cả file .mp4 trong thư mục hiện tại
for video in *.mp4; do
  echo "Đang xử lý: $video"
  bash swap_face_voice.sh "$video" face.jpg model.pth 0
done
```

---

# Phần B — Live Stream (Real-time)

> Phần dưới đây hướng dẫn đổi mặt + đổi giọng **trực tiếp** (real-time) khi live stream.
> Nếu bạn chỉ cần xử lý video có sẵn, hãy xem [Phần A](#phần-a--xử-lý-video-có-sẵn-offline) ở trên.

---

## 1. Yêu cầu phần cứng & phần mềm

### Phần cứng tối thiểu

| Thành phần | Yêu cầu tối thiểu | Khuyến nghị |
|---|---|---|
| GPU | NVIDIA GTX 1060 (6 GB VRAM) | NVIDIA RTX 3060 trở lên (12 GB VRAM) |
| CPU | Intel i5 thế hệ 8 / AMD Ryzen 5 3600 | Intel i7 / AMD Ryzen 7 trở lên |
| RAM | 16 GB | 32 GB |
| Webcam | 720p | 1080p, 30 fps trở lên |
| Micro | Micro tích hợp hoặc tai nghe | Micro condenser USB (ví dụ: Blue Yeti, HyperX) |

### Phần mềm cần cài

| Phần mềm | Mục đích | Link tải |
|---|---|---|
| **Deep-Live-Cam** | Đổi mặt real-time | https://github.com/hacksider/Deep-Live-Cam |
| **DeepFaceLive** (thay thế) | Đổi mặt real-time | https://github.com/iperov/DeepFaceLive |
| **RVC-WebUI** | Đổi giọng real-time | https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI |
| **VB-Audio Virtual Cable** | Cáp âm thanh ảo | https://vb-audio.com/Cable/ |
| **OBS Studio** | Phát sóng & quản lý nguồn | https://obsproject.com/ |
| **Python 3.10** | Môi trường chạy AI | https://www.python.org/downloads/ |
| **CUDA Toolkit** | Tăng tốc GPU cho NVIDIA | https://developer.nvidia.com/cuda-toolkit |
| **ffmpeg** | Xử lý media | https://ffmpeg.org/download.html |

---

## 2. Bước 1 – Cài đặt & cấu hình Deep-Live-Cam (Đổi mặt)

### 2.1. Cài đặt Deep-Live-Cam

```bash
git clone https://github.com/hacksider/Deep-Live-Cam.git
cd Deep-Live-Cam
pip install -r requirements.txt
```

> **Lưu ý:** Cần cài thêm các model ONNX. Tham khảo README của dự án để tải model phù hợp (ví dụ: `inswapper_128.onnx`). Đặt model vào thư mục `models/`.

### 2.2. Chạy Deep-Live-Cam

```bash
python run.py
```

### 2.3. Cấu hình trong giao diện

1. **Source (Khuôn mặt nguồn):** Tải lên ảnh khuôn mặt bạn muốn hoán đổi (ảnh rõ nét, chính diện, ánh sáng tốt).
2. **Webcam:** Chọn webcam của bạn làm đầu vào camera.
3. **Output:** Chọn chế độ **Virtual Camera** (camera ảo) — đây là bước quan trọng nhất, vì OBS sẽ lấy nguồn hình từ camera ảo này.
4. Nhấn **Start** để bắt đầu xử lý.

### 2.4. Thay thế: DeepFaceLive

Nếu dùng DeepFaceLive thay cho Deep-Live-Cam:

```bash
git clone https://github.com/iperov/DeepFaceLive.git
cd DeepFaceLive
```

- Tải bản build sẵn cho Windows từ trang release.
- Chạy `DeepFaceLive.exe`.
- Chọn webcam đầu vào, chọn model khuôn mặt, bật **Virtual Camera output**.

### 2.5. Kiểm tra camera ảo

Mở một ứng dụng bất kỳ hỗ trợ camera (Zoom, Google Meet...) và chọn **OBS Virtual Camera** hoặc **DeepFaceLive Virtual Camera** để xác nhận khuôn mặt đã được hoán đổi thành công.

---

## 3. Bước 2 – Cài đặt & cấu hình RVC-WebUI (Đổi giọng)

### 3.1. Cài đặt RVC-WebUI

```bash
git clone https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI.git
cd Retrieval-based-Voice-Conversion-WebUI
pip install -r requirements.txt
```

### 3.2. Tải model giọng nói

- Tải các model giọng nói pre-trained (file `.pth`) từ cộng đồng hoặc tự train.
- Đặt file model vào thư mục `weights/`.
- Một số nguồn model phổ biến: [weights.gg](https://weights.gg/), [Hugging Face](https://huggingface.co/).

### 3.3. Chạy RVC-WebUI

```bash
python infer-web.py
```

Truy cập giao diện web tại `http://localhost:7865`.

### 3.4. Cấu hình đổi giọng real-time

1. Chuyển sang tab **Real-time Voice Conversion** (hoặc **实时变声**).
2. **Input Device:** Chọn **Microphone** của bạn (micro vật lý).
3. **Output Device:** Chọn **CABLE Input (VB-Audio Virtual Cable)** — đây là bước quan trọng, giọng nói sau khi biến đổi sẽ được đẩy vào cáp âm thanh ảo.
4. **Model:** Chọn model giọng nói đã tải ở bước trên.
5. Điều chỉnh các thông số:
   - **Pitch (Cao độ):** Thường +12 nếu nam chuyển nữ, -12 nếu nữ chuyển nam.
   - **Index Rate:** 0.5 – 0.8 (độ giống giọng gốc của model).
   - **Block Size / Extra Length:** Giảm để giảm độ trễ (nhưng tăng tải CPU/GPU).
6. Nhấn **Start** để bắt đầu đổi giọng real-time.

---

## 4. Bước 3 – Cài đặt Virtual Audio Cable (VB-Audio)

### 4.1. Tải và cài đặt

1. Truy cập https://vb-audio.com/Cable/
2. Tải **VB-CABLE Driver** (miễn phí).
3. Giải nén và chạy `VBCABLE_Setup_x64.exe` (Run as Administrator).
4. Khởi động lại máy tính sau khi cài đặt.

### 4.2. Xác nhận cài đặt

Sau khi cài xong, vào **Windows Sound Settings** (chuột phải vào biểu tượng loa > Sound Settings):

- Trong mục **Playback devices:** sẽ thấy **CABLE Input (VB-Audio Virtual Cable)**.
- Trong mục **Recording devices:** sẽ thấy **CABLE Output (VB-Audio Virtual Cable)**.

### 4.3. Luồng âm thanh

```
Micro vật lý ──> RVC-WebUI (đổi giọng) ──> CABLE Input ──> CABLE Output ──> OBS (nguồn Audio)
```

> **Lưu ý:** Không đặt CABLE Input làm thiết bị phát mặc định của Windows, nếu không bạn sẽ không nghe được âm thanh hệ thống.

---

## 5. Bước 4 – Cấu hình OBS Studio

### 5.1. Thêm nguồn Hình ảnh (Video)

1. Mở **OBS Studio**.
2. Trong phần **Sources**, nhấn **+** > **Video Capture Device**.
3. Đặt tên (ví dụ: "Face Swap Cam").
4. Trong mục **Device**, chọn **OBS Virtual Camera** (hoặc **DeepFaceLive Virtual Camera**) — đây là camera ảo đầu ra từ phần mềm đổi mặt.
5. Nhấn **OK**.

### 5.2. Thêm nguồn Âm thanh (Audio)

1. Trong phần **Sources**, nhấn **+** > **Audio Input Capture**.
2. Đặt tên (ví dụ: "Voice Changer").
3. Trong mục **Device**, chọn **CABLE Output (VB-Audio Virtual Cable)** — đây là đầu ra âm thanh từ RVC sau khi đã đổi giọng.
4. Nhấn **OK**.

### 5.3. Tắt micro gốc trong OBS

Rất quan trọng: Tắt micro gốc để tránh phát giọng thật.

1. Vào **Settings** > **Audio**.
2. Đặt **Mic/Auxiliary Audio** thành **Disabled** (hoặc chọn CABLE Output nếu muốn).
3. Hoặc trong **Audio Mixer**, nhấn biểu tượng loa bên cạnh "Mic/Aux" để tắt tiếng.

### 5.4. Kiểm tra trước khi phát sóng

1. Nhấn **Start Recording** để quay thử.
2. Xem lại video vừa quay:
   - Kiểm tra khuôn mặt đã hoán đổi đúng chưa.
   - Kiểm tra giọng nói đã thay đổi chưa.
   - Kiểm tra độ trễ giữa hình và tiếng.
3. Nếu hình và tiếng lệch nhau, vào **Advanced Audio Properties** (chuột phải vào nguồn audio trong Audio Mixer) và điều chỉnh **Sync Offset** (đơn vị: ms).

---

## 6. Bước 5 – Phát sóng lên TikTok / Facebook

### 6.1. Phát sóng lên Facebook Live

1. Vào **Facebook** > **Live Video** (Video trực tiếp).
2. Chọn **Use Stream Key** (Phần mềm phát trực tiếp).
3. Sao chép **Stream Key**.
4. Trong OBS, vào **Settings** > **Stream**:
   - **Service:** Facebook Live
   - **Server:** Để mặc định
   - **Stream Key:** Dán stream key vừa sao chép
5. Nhấn **OK**, sau đó nhấn **Start Streaming** trong OBS.
6. Quay lại Facebook và nhấn **Go Live** (Phát trực tiếp).

### 6.2. Phát sóng lên TikTok Live

1. Yêu cầu: Tài khoản TikTok phải đủ điều kiện live (thường ≥ 1000 followers).
2. Vào **TikTok Live Studio** hoặc sử dụng **TikTok Live** trên web.
3. Chọn chế độ **PC/Software** (OBS) và sao chép **Stream Key** + **Server URL**.
4. Trong OBS, vào **Settings** > **Stream**:
   - **Service:** Custom
   - **Server:** Dán Server URL từ TikTok
   - **Stream Key:** Dán stream key từ TikTok
5. Nhấn **Start Streaming**.

### 6.3. Cài đặt Stream khuyến nghị

| Thông số | Giá trị khuyến nghị |
|---|---|
| Output Resolution | 1280×720 (720p) |
| FPS | 30 |
| Video Bitrate | 2500 – 4000 kbps |
| Audio Bitrate | 128 kbps |
| Encoder | NVENC (nếu có GPU NVIDIA) hoặc x264 |
| Rate Control | CBR |

---

## 7. Xử lý sự cố thường gặp

### Không thấy Virtual Camera trong OBS

- Đảm bảo Deep-Live-Cam / DeepFaceLive đang chạy và đã bật chế độ Virtual Camera.
- Cài plugin **OBS-VirtualCam** nếu dùng OBS phiên bản cũ (OBS 26+ đã tích hợp sẵn).
- Thử khởi động lại OBS.

### Không có âm thanh từ CABLE Output

- Kiểm tra RVC-WebUI đã chọn đúng output là **CABLE Input**.
- Mở **Windows Sound Settings** > **Recording** > **CABLE Output** > kiểm tra thanh âm lượng có nhảy khi nói không.
- Đảm bảo VB-Audio Cable đã cài đúng cách (Run as Administrator).

### Khuôn mặt swap bị giật/lag

- Giảm độ phân giải webcam (từ 1080p xuống 720p).
- Đóng các ứng dụng nặng khác.
- Kiểm tra GPU có đang được sử dụng (Task Manager > GPU).
- Cập nhật driver NVIDIA mới nhất.

### Giọng nói bị trễ (delay)

- Trong RVC-WebUI, giảm **Block Size** (thử 128 hoặc 256).
- Giảm **Extra Length**.
- Sử dụng ASIO driver nếu có thể.
- Trong OBS, điều chỉnh **Sync Offset** của nguồn audio.

### Giọng nói bị rè/noise

- Bật **Noise Suppression** trong RVC-WebUI (nếu có).
- Trong OBS, thêm **Filter** > **Noise Suppression** vào nguồn audio.
- Sử dụng micro chất lượng tốt hơn và đặt gần miệng.

### OBS báo lỗi khi stream

- Kiểm tra lại Stream Key (có thể đã hết hạn, cần lấy lại).
- Kiểm tra kết nối internet (khuyến nghị upload ≥ 5 Mbps).
- Thử giảm bitrate.

---

## 8. Mẹo tối ưu hiệu suất

### Giảm tải GPU

- Chỉ chạy **một** phần mềm đổi mặt (Deep-Live-Cam HOẶC DeepFaceLive, không cả hai).
- Đóng trình duyệt web và ứng dụng không cần thiết.
- Sử dụng **NVENC** encoder trong OBS thay vì x264 để giảm tải CPU.

### Tối ưu chất lượng

- Sử dụng ảnh khuôn mặt nguồn chất lượng cao, chính diện, ánh sáng đều.
- Giữ ánh sáng phòng stream ổn định, tránh ngược sáng.
- Train model giọng nói riêng với RVC để đạt chất lượng tốt nhất (cần ~10-20 phút audio sạch).

### Giảm độ trễ tổng thể

- Ưu tiên sử dụng GPU cho cả face swap và voice conversion.
- Giữ webcam ở 30 fps (không cần 60 fps nếu GPU yếu).
- Sử dụng kết nối có dây (Ethernet) thay vì Wi-Fi khi stream.

### Checklist trước khi Live

- [ ] Deep-Live-Cam / DeepFaceLive đã chạy và bật Virtual Camera
- [ ] Kiểm tra face swap hoạt động đúng
- [ ] RVC-WebUI đã chạy và output ra CABLE Input
- [ ] Kiểm tra giọng nói đã đổi đúng
- [ ] OBS đã thêm nguồn Video (Virtual Camera) và Audio (CABLE Output)
- [ ] Micro gốc đã bị tắt trong OBS
- [ ] Quay thử 30 giây, xem lại kiểm tra hình + tiếng
- [ ] Stream Key đã nhập đúng
- [ ] Kết nối internet ổn định

---

## Sơ đồ tóm tắt toàn bộ quy trình

```
╔══════════════════════════════════════════════════════════════════════╗
║                    QUY TRÌNH "NGƯỜI ẢO" LIVE STREAM                ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║  ┌─────────────┐         ┌──────────────────┐                        ║
║  │   WEBCAM    │────────>│  Deep-Live-Cam   │                        ║
║  │  (1080p)    │         │  hoặc            │                        ║
║  └─────────────┘         │  DeepFaceLive    │                        ║
║                          └────────┬─────────┘                        ║
║                                   │                                  ║
║                                   v                                  ║
║                          ┌──────────────────┐                        ║
║                          │  Virtual Camera  │                        ║
║                          │  (OBS-VCam)      │                        ║
║                          └────────┬─────────┘                        ║
║                                   │                                  ║
║                                   v                                  ║
║                          ┌──────────────────┐      ┌──────────────┐  ║
║                          │                  │      │   TikTok     │  ║
║                          │   OBS Studio     │─────>│   Facebook   │  ║
║                          │                  │      │   YouTube    │  ║
║                          └──────────────────┘      └──────────────┘  ║
║                                   ^                                  ║
║                                   │                                  ║
║                          ┌──────────────────┐                        ║
║                          │  CABLE Output    │                        ║
║                          │  (VB-Audio)      │                        ║
║                          └────────┬─────────┘                        ║
║                                   ^                                  ║
║                                   │                                  ║
║                          ┌──────────────────┐                        ║
║  ┌─────────────┐         │   RVC-WebUI      │                        ║
║  │   MICRO     │────────>│   (Voice         │                        ║
║  │             │         │    Changer)       │                        ║
║  └─────────────┘         └──────────────────┘                        ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
```

---

> **Cảnh báo pháp lý:** Việc sử dụng công nghệ deepfake để mạo danh người khác, lừa đảo, hoặc tạo nội dung vi phạm pháp luật là bất hợp pháp. Chỉ sử dụng cho mục đích giải trí hợp pháp và luôn tuân thủ quy định của nền tảng phát sóng.
