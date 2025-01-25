
# 🎵 Discord Music Bot và Voice Bot 🎙️

Dự án này bao gồm hai bot Discord với các chức năng mạnh mẽ:
1. **Bot nhạc (`bot.py`)**: Cho phép phát nhạc từ YouTube, quản lý hàng đợi nhạc, và hỗ trợ các lệnh điều khiển nhạc dễ dàng.
2. **Bot giọng nói (`voice.py`)**: Chào người dùng khi họ tham gia kênh thoại và hỗ trợ lệnh phát âm thanh từ văn bản.

---

## 🚀 **Chức năng chính**

### **Bot nhạc (`bot.py`)**
- **Phát nhạc từ YouTube**: 
  - Tìm kiếm và phát nhạc từ YouTube bằng tên bài hát hoặc URL.
- **Quản lý hàng đợi nhạc**:
- Phát nhạc từ YouTube qua tên bài hát hoặc URL.
- Quản lý hàng đợi nhạc với các tính năng:
  - Tự động phát bài hát tiếp theo.
  - Hiển thị danh sách hàng đợi.
- **Điều khiển nhạc trên Discord**:
  - Lệnh `!play`: Phát nhạc.
  - Lệnh `!pause`: Tạm dừng nhạc.
  - Lệnh `!resume`: Tiếp tục phát nhạc.
  - Lệnh `!skip`: Bỏ qua bài hát hiện tại.
  - Lệnh `!stop`: Ngắt kết nối và dọn dẹp hàng đợi.
- **Hỗ trợ nút điều khiển trên giao diện**:
  - Tạm dừng, tiếp tục, lặp lại, hoặc bỏ qua bài hát.
  - Điều khiển nhạc trực tiếp trên Discord (Tạm dừng, Tiếp tục, Bỏ qua, Lặp lại).
- Tìm kiếm bài hát trên YouTube và hiển thị danh sách kết quả.
- Nếu đã phát hết nhạc thì sẽ tự động phát lại những bài nhạc trước đó 1 giờ đồng hồ.
### **Bot giọng nói (`voice.py`)**
- **Chào mừng người dùng**:
  - Bot tự động phát âm thanh chào khi người dùng tham gia kênh thoại.
- **Lệnh phát âm thanh từ văn bản**:
  - Lệnh `?say <nội dung>`: Bot phát giọng nói từ nội dung nhập.
- **Tự động ngắt kết nối**:
  - Bot sẽ ngắt kết nối sau 15 phút không hoạt động.
- Chào mừng người dùng khi họ tham gia kênh thoại với giọng nói tiếng Việt.
- Phát âm thanh từ văn bản bằng lệnh `?say`.
- Tự động ngắt kết nối khỏi kênh thoại sau 15 phút không hoạt động.

---

## 📋 **Hướng dẫn lấy API Key YouTube**
### **1. Truy cập Google Cloud Console**
1. Mở [Google Cloud Console](https://console.cloud.google.com/).
2. Đăng nhập bằng tài khoản Google của bạn.
### **2. Tạo một dự án mới**
1. Nhấn vào **Select a project** (Chọn dự án) ở góc trên bên trái.
2. Nhấn **New Project** (Dự án mới).
3. Nhập tên dự án (ví dụ: `Discord Music Bot`) và nhấn **Create** (Tạo).
### **3. Kích hoạt YouTube Data API**
1. Trong thanh tìm kiếm, nhập **YouTube Data API v3** và chọn kết quả.
2. Nhấn **Enable** (Bật).
## 📋 **Cài đặt**

### **4. Tạo API Key**
1. Vào **APIs & Services** > **Credentials** (Thông tin xác thực).
2. Nhấn **Create Credentials** (Tạo thông tin xác thực) và chọn **API Key**.
3. API Key sẽ được tạo. Sao chép và lưu lại API Key này.
### **1. Yêu cầu hệ thống**
- Python 3.10 trở lên.
- `ffmpeg` .

### **5. Hạn chế quyền API Key (khuyến nghị)**
1. Nhấn vào API Key vừa tạo.
2. Trong phần **Application restrictions** (Hạn chế ứng dụng):
   - Chọn **HTTP referrers (web sites)**.
   - Thêm các tên miền hoặc IP được phép sử dụng API Key.
3. Trong phần **API restrictions** (Hạn chế API):
   - Chọn **Restrict key** (Hạn chế key).
   - Chọn **YouTube Data API v3**.
   - Lưu thay đổi.
### **2. Cài đặt dự án**

---
## 📋 **Hướng dẫn tạo bot discord, cần tạo 2 con bot discord**
1. Mở [Discord Developer Portal](https://discord.com/developers/applications).
2. Bấm nút `New Application`
3. Nhập tên bot mà bạn muốn (sau đó tải ảnh avt tùy theo ý muốn của bạn)
4. Bấm vào biểu tượng Bot ở cột bên phải sau đó bấm nút `Reset Token` rồi Copy token và nhập vào file .env
5. Tương tự tạo tiếp một Bot nữa như các bước trên rồi nhập vào `DISCORD_TOKEN_2` trong file `.env` để làm bot chuyển text sang giọng đọc
## **Hướng dẫn cài đặt trên Linux (Ubuntu)**
### **1. Cập nhật hệ thống**
```bash
sudo apt update && sudo apt upgrade -y
```
### **2. Cài đặt Python 3.10 trở lên và các công cụ cần thiết**
```bash
sudo apt install python3 python3-pip python3-venv ffmpeg git -y
```
### **3. Clone dự án**
```bash
git clone https://github.com/namhuunam/MusicBot.git
cd MusicBot
```
### **4. Tạo môi trường ảo và cài đặt thư viện**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
### **5. Cấu hình file `.env`**
1. Sửa file `.env` trong thư mục dự án:
2. Thêm nội dung:
   ```env
   DISCORD_TOKEN=<Token Discord của bot nhạc>
   DISCORD_TOKEN_2=<Token Discord của bot giọng nói>
   YOUTUBE_API_KEY=<API Key của YouTube>
   ```
3. Lưu file và thoát (`Ctrl+O`, `Enter`, `Ctrl+X`).
### **6. Sửa proxy trong file `bot.py` dùng proxy v4 hay v6 đều được, khuyên dùng v6 cho rẻ đâu đó khoảng tầm 4000vnđ/tháng :D**
1. Tìm từ khóa `proxy` trong file `bot.py` nằm ở dòng `468`, `565`, `608`, `635` .
2. Thay thế thành proxy của bạn theo dạng `http://user:pass@ip:port` ví dụ `http://user123:pass123@192.168.1.1:8080` .
**Vì sao phải sử dụng proxy ? Vì một số vps bị youtube block ip lên phải sử dụng proxy để lấy url âm thanh của youtube**
**Còn nếu ip vps của bạn không bị block thì bạn có thể xóa bỏ proxy đi cũng được**
**Lưu ý là phải thay proxy không là bot sẽ không phát nhạc được**
### **6. Chạy bot thủ công, chỉ cần chạy một file bot.py**
- Chạy bot nhạc:
  ```bash
  python3 bot.py
  ```
  
### **7. Thiết lập tự động chạy bằng `systemd`**
1. Tạo file dịch vụ:
2. Tạo môi trường ảo và cài đặt thư viện:
   ```bash
   sudo nano /etc/systemd/system/discord-bot.service
   ```
2. Thêm nội dung:
   ```ini
   [Unit]
   Description=Discord Bot
   After=network.target
   [Service]
   Type=simple
   User=<username>  # Thay <username> bằng tên người dùng của bạn ví dụ: root
   WorkingDirectory=/path/to/your/project  # Thay bằng đường dẫn đến thư mục chứa bot.py ví dụ: /root/bot
   ExecStart=/path/to/your/project/venv/bin/python3 bot.py #ví dụ: /root/bot/venv/bin/python3 bot.py
   Restart=always
   RestartSec=3
   Environment="PYTHONUNBUFFERED=1"
   [Install]
   WantedBy=multi-user.target
   ```

3. Lưu file và tải lại cấu hình:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable discord-bot.service
   sudo systemctl start discord-bot.service
   ```

4. Kiểm tra trạng thái:
   ```bash
   sudo systemctl status discord-bot.service
   ```

---

## **📚 Lệnh sử dụng**
## 📚 **Hướng dẫn sử dụng**

### **Bot nhạc**
- `!play <tên bài hát>`: Tìm kiếm nhạc trên youtube.
- `!play <URL Youtube>`: Phát nhạc từ url youtube.
- `!pause`: Tạm dừng nhạc.
- `!resume`: Tiếp tục phát nhạc.
- `!skip`: Bỏ qua bài hát.
- `!stop`: Dừng phát và ngắt kết nối.

### **Bot giọng nói**
- `?say <nội dung>`: Bot phát âm thanh từ văn bản.
- Tự động chào người dùng khi họ vào kênh thoại.

---

## 🛠️ **Khắc phục sự cố**
- **Kiểm tra log dịch vụ**:
  ```bash
  journalctl -u discord-bot.service -f
  ```
- **Lỗi thiếu thư viện**:
  ```bash
  pip install -r requirements.txt
  ```
- **Kiểm tra `ffmpeg`**:
  ```bash
  ffmpeg -version
  ```
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



## **📝 Tác giả**
Dự án được phát triển để hỗ trợ cộng đồng Discord. Nếu bạn thấy hữu ích, hãy để lại ⭐ trên GitHub của chúng tôi!
