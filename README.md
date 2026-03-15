# Hướng dẫn Combo Đổi Mặt + Đổi Giọng khi Live Stream

Tài liệu hướng dẫn tạo "người ảo" hoàn chỉnh bằng cách kết hợp **đổi mặt real-time** (Deep-Live-Cam / DeepFaceLive) và **đổi giọng real-time** (RVC-WebUI), sau đó phát sóng qua OBS lên TikTok / Facebook.

---

## Tổng quan kiến trúc

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

1. [Yêu cầu phần cứng & phần mềm](#1-yêu-cầu-phần-cứng--phần-mềm)
2. [Bước 1 – Cài đặt & cấu hình Deep-Live-Cam (Đổi mặt)](#2-bước-1--cài-đặt--cấu-hình-deep-live-cam-đổi-mặt)
3. [Bước 2 – Cài đặt & cấu hình RVC-WebUI (Đổi giọng)](#3-bước-2--cài-đặt--cấu-hình-rvc-webui-đổi-giọng)
4. [Bước 3 – Cài đặt Virtual Audio Cable (VB-Audio)](#4-bước-3--cài-đặt-virtual-audio-cable-vb-audio)
5. [Bước 4 – Cấu hình OBS Studio](#5-bước-4--cấu-hình-obs-studio)
6. [Bước 5 – Phát sóng lên TikTok / Facebook](#6-bước-5--phát-sóng-lên-tiktok--facebook)
7. [Xử lý sự cố thường gặp](#7-xử-lý-sự-cố-thường-gặp)
8. [Mẹo tối ưu hiệu suất](#8-mẹo-tối-ưu-hiệu-suất)

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
