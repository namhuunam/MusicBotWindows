
# 🎵 Discord Music Bot và Voice Bot 🎙️

Dự án này bao gồm hai bot Discord với các chức năng mạnh mẽ:
1. **Bot nhạc (`bot.py`)**: Cho phép phát nhạc từ YouTube, quản lý hàng đợi nhạc, và hỗ trợ các lệnh điều khiển nhạc dễ dàng.
2. **Bot giọng nói (`voice.py`)**: Chào người dùng khi họ tham gia kênh thoại và hỗ trợ lệnh phát âm thanh từ văn bản.

---

## 🚀 **Chức năng chính**

### **Bot nhạc (`bot.py`)**
- Phát nhạc từ YouTube qua tên bài hát hoặc URL.
- Quản lý hàng đợi nhạc với các tính năng:
  - Tự động phát bài hát tiếp theo.
  - Điều khiển nhạc trực tiếp trên Discord (Tạm dừng, Tiếp tục, Bỏ qua, Lặp lại).
- Tìm kiếm bài hát trên YouTube và hiển thị danh sách kết quả.
- Nếu đã phát hết nhạc thì sẽ tự động phát lại những bài nhạc trước đó 1 giờ đồng hồ.
### **Bot giọng nói (`voice.py`)**
- Chào mừng người dùng khi họ tham gia kênh thoại với giọng nói tiếng Việt.
- Phát âm thanh từ văn bản bằng lệnh `?say`.
- Tự động ngắt kết nối khỏi kênh thoại sau 15 phút không hoạt động.

---

## 📋 **Cài đặt**

### **1. Yêu cầu hệ thống**
- Python 3.10 trở lên [python.org](https://www.python.org/downloads/)
- `ffmpeg` (tải từ [ffmpeg.org](https://github.com/BtbN/FFmpeg-Builds/releases)).
- Chọn ffmpeg bản win64.


### **2. Cài đặt dự án**

1. Clone dự án:
   ```bash
   git clone <repo_url>
   cd <repo_directory>
   ```

2. Tạo môi trường ảo và cài đặt thư viện:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate     # Windows
   pip install -r requirements.txt
   ```

3. Sửa file `.env`:
   ```env
   DISCORD_TOKEN=<Token của bot nhạc>
   DISCORD_TOKEN_2=<Token của bot giọng nói>
   YOUTUBE_API_KEY=<API key YouTube>
   ```

4. Chạy bot:
   - Bot nhạc: `python3 bot.py`
   - Bot giọng nói: `python3 voice.py`

---

## 📚 **Hướng dẫn sử dụng**

### **Bot nhạc (`bot.py`)**
- Tiền tố lệnh: `!`
- Các lệnh chính:
  - `!play <tên bài hát/URL>`: Phát nhạc.
  - `!stop`: Ngừng phát nhạc và ngắt kết nối.
  - `!pause`: Tạm dừng nhạc.
  - `!resume`: Tiếp tục phát nhạc.
  - `!skip`: Bỏ qua bài hát hiện tại.

### **Bot giọng nói (`voice.py`)**
- Tiền tố lệnh: `?`
- Các lệnh chính:
  - `?say <nội dung>`: Phát âm thanh từ nội dung nhập vào.
- Tự động chào người dùng khi họ vào kênh thoại.

---

## 🛠️ **Khắc phục sự cố**
1. **Bot không kết nối được với kênh thoại**:
   - Kiểm tra quyền **Kết nối** và **Phát giọng nói**.
   - Đảm bảo token Discord trong `.env` là chính xác.

2. **Bot không phát nhạc**:
   - Đảm bảo `ffmpeg` đã được cài đặt và thêm vào `PATH`.
   - Kiểm tra kết nối mạng và API key YouTube.

3. **Bot không phản hồi lệnh**:
   - Kiểm tra bot có đang chạy không.
   - Đảm bảo sử dụng đúng tiền tố lệnh (`!` cho nhạc, `?` cho giọng nói).

---

## 📞 **Liên hệ**
Nếu gặp vấn đề, vui lòng liên hệ qua [GitHub Issues](https://github.com/your-repo-url/issues).

---

## 📝 **Tác giả**
Dự án được phát triển để hỗ trợ cộng đồng Discord Việt Nam. Nếu bạn thấy hữu ích, hãy để lại ⭐ trên GitHub của chúng tôi!
