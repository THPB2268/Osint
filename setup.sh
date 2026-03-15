#!/bin/bash
# ============================================================
#  Setup Script — Cài đặt môi trường cho Swap Tool
#  Sử dụng: bash setup.sh [--gpu]
# ============================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log()  { echo -e "${CYAN}[INFO]${NC} $1"; }
ok()   { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
err()  { echo -e "${RED}[ERROR]${NC} $1"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DLC_DIR="$SCRIPT_DIR/Deep-Live-Cam"
USE_GPU=false

if [[ "$1" == "--gpu" ]] || [[ "$1" == "--cuda" ]]; then
    USE_GPU=true
fi

echo ""
echo "=========================================="
echo " Swap Tool — Setup"
echo "=========================================="
echo ""

# ── 1. Kiểm tra Python ──
log "Kiểm tra Python..."
if ! command -v python3 &>/dev/null; then
    err "Python 3 chưa được cài. Hãy cài Python 3.10+ trước."
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
log "Python version: $PYTHON_VERSION"

# ── 2. Kiểm tra ffmpeg ──
log "Kiểm tra ffmpeg..."
if command -v ffmpeg &>/dev/null; then
    ok "ffmpeg đã cài"
else
    warn "ffmpeg chưa cài. Đang cài đặt..."
    if command -v apt-get &>/dev/null; then
        sudo apt-get update -qq && sudo apt-get install -y -qq ffmpeg
    elif command -v brew &>/dev/null; then
        brew install ffmpeg
    elif command -v pacman &>/dev/null; then
        sudo pacman -S --noconfirm ffmpeg
    else
        err "Không thể tự cài ffmpeg. Hãy cài thủ công."
        exit 1
    fi
    ok "ffmpeg đã cài xong"
fi

# ── 3. Clone Deep-Live-Cam ──
log "Kiểm tra Deep-Live-Cam..."
if [ -d "$DLC_DIR" ]; then
    ok "Deep-Live-Cam đã tồn tại tại $DLC_DIR"
else
    log "Đang clone Deep-Live-Cam..."
    git clone https://github.com/hacksider/Deep-Live-Cam.git "$DLC_DIR"
    ok "Clone hoàn tất"
fi

# ── 4. Cài đặt dependencies ──
log "Cài đặt Python dependencies..."

pip install --upgrade pip -q

if [ "$USE_GPU" = true ]; then
    log "Chế độ GPU (CUDA) — cài onnxruntime-gpu"
    pip install -q \
        "numpy>=1.23.5,<2" \
        "opencv-python==4.10.0.84" \
        "onnx==1.18.0" \
        "insightface==0.7.3" \
        "psutil==5.9.8" \
        "pillow>=10.0.0" \
        "onnxruntime-gpu==1.24.2" \
        "tqdm" \
        "protobuf==4.25.1"
else
    log "Chế độ CPU"
    pip install -q \
        "numpy>=1.23.5,<2" \
        "opencv-python==4.10.0.84" \
        "onnx==1.18.0" \
        "insightface==0.7.3" \
        "psutil==5.9.8" \
        "pillow>=10.0.0" \
        "onnxruntime>=1.16.0" \
        "tqdm" \
        "protobuf==4.25.1"
fi

ok "Dependencies đã cài xong"

# ── 5. Tải model ──
MODELS_DIR="$DLC_DIR/models"
mkdir -p "$MODELS_DIR"

MODEL_FILE="$MODELS_DIR/inswapper_128_fp16.onnx"
if [ -f "$MODEL_FILE" ]; then
    ok "Model inswapper đã tồn tại"
else
    log "Đang tải model inswapper_128_fp16.onnx từ HuggingFace..."
    if command -v wget &>/dev/null; then
        wget -q --show-progress -O "$MODEL_FILE" \
            "https://huggingface.co/hacksider/deep-live-cam/resolve/main/inswapper_128_fp16.onnx"
    elif command -v curl &>/dev/null; then
        curl -L --progress-bar -o "$MODEL_FILE" \
            "https://huggingface.co/hacksider/deep-live-cam/resolve/main/inswapper_128_fp16.onnx"
    else
        err "Cần wget hoặc curl để tải model."
        exit 1
    fi
    ok "Model đã tải xong"
fi

# ── 6. Kiểm tra GPU ──
if [ "$USE_GPU" = true ]; then
    log "Kiểm tra GPU NVIDIA..."
    if command -v nvidia-smi &>/dev/null; then
        nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null || true
        ok "GPU NVIDIA sẵn sàng"
    else
        warn "nvidia-smi không tìm thấy. GPU có thể không hoạt động."
    fi
fi

# ── Hoàn tất ──
echo ""
echo "=========================================="
echo -e " ${GREEN}SETUP HOÀN TẤT${NC}"
echo "=========================================="
echo ""
echo "Cách sử dụng:"
echo ""
echo "  # Chỉ đổi mặt"
echo "  python3 swap_tool.py -s anh_mat.jpg -t video.mp4"
echo ""
echo "  # Đổi mặt + GPU"
echo "  python3 swap_tool.py -s anh_mat.jpg -t video.mp4 --gpu cuda"
echo ""
echo "  # Đổi mặt + tăng chất lượng"
echo "  python3 swap_tool.py -s anh_mat.jpg -t video.mp4 --enhance --gpu cuda"
echo ""
echo "  # Đổi mặt + đổi giọng"
echo "  python3 swap_tool.py -s anh_mat.jpg -t video.mp4 --rvc-model model.pth --pitch 12"
echo ""
echo "  # Xử lý hàng loạt"
echo "  python3 swap_tool.py -s anh_mat.jpg --target-dir ./videos/ --output-dir ./output/"
echo ""
