import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import asyncio
from gtts import gTTS
from collections import deque  # Hàng đợi để xử lý tuần tự

# Tải biến môi trường từ file .env
load_dotenv()

# Lấy token từ file .env
TOKEN = os.getenv("DISCORD_TOKEN_2")  # Sử dụng DISCORD_TOKEN_2

# Thiết lập bot với prefix "?"
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.voice_states = True
bot = commands.Bot(command_prefix="?", intents=intents)

# Đảm bảo thư mục temp tồn tại với đường dẫn tuyệt đối
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Thư mục chứa file script
TEMP_DIR = os.path.join(BASE_DIR, "temp")
os.makedirs(TEMP_DIR, exist_ok=True)

# Đường dẫn đến ffmpeg.exe
FFMPEG_PATH = os.path.join(BASE_DIR, "ffmpeg", "ffmpeg.exe")

# Kiểm tra sự tồn tại của ffmpeg.exe
if not os.path.exists(FFMPEG_PATH):
    raise FileNotFoundError("Không tìm thấy ffmpeg.exe. Vui lòng kiểm tra lại đường dẫn.")


# Hàng đợi chào người dùng
greeting_queue = deque()  # Danh sách hàng đợi người dùng cần chào
is_greeting = False  # Trạng thái: bot có đang chào ai không
current_guild_vc = {}  # Theo dõi voice client hiện tại theo từng guild


# Sự kiện khởi động bot
@bot.event
async def on_ready():
    print(f"Bot đã sẵn sàng! Đăng nhập với tên {bot.user}")
    # Dọn dẹp thư mục temp
    for file in os.listdir(TEMP_DIR):
        file_path = os.path.join(TEMP_DIR, file)
        try:
            os.remove(file_path)
        except Exception as e:
            print(f"Lỗi khi xóa file tạm cũ: {file_path}, {e}")



# Hủy kết nối voice sau 15 phút không hoạt động
async def disconnect_after_timeout(vc):
    await asyncio.sleep(15 * 60)  # Đợi 15 phút
    if vc.is_connected() and not vc.is_playing() and len(vc.channel.members) == 1:
        await vc.disconnect()
        print("Bot đã tự động ngắt kết nối vì không còn ai trong kênh.")


# Xử lý chào người dùng trong hàng đợi
async def handle_greetings(vc):
    global is_greeting
    is_greeting = True

    while greeting_queue:  # Xử lý từng người trong hàng đợi
        member = greeting_queue.popleft()  # Lấy người đầu tiên trong hàng đợi
        nickname = member.display_name
        greeting_text = f"Địt mẹ mày thằng {nickname}!"

        # Đợi 1 giây trước khi chào
        await asyncio.sleep(1)

        # Tạo file âm thanh
        temp_file = os.path.join(TEMP_DIR, f"welcome_{member.id}.mp3")
        tts = gTTS(greeting_text, lang="vi")
        tts.save(temp_file)

        # Phát file âm thanh
        vc.play(
            discord.FFmpegPCMAudio(temp_file, executable=FFMPEG_PATH, options="-loglevel panic"),
            after=lambda e: print(f"Đã phát xong: {e}")
        )
        while vc.is_playing():
            await asyncio.sleep(1)

        # Xóa file âm thanh tạm thời
        try:
            os.remove(temp_file)
        except FileNotFoundError:
            print(f"Không tìm thấy file tạm: {temp_file}")
        except Exception as e:
            print(f"Lỗi khi xóa file tạm: {temp_file}, {e}")

    is_greeting = False  # Đặt lại trạng thái


# Khi có người tham gia hoặc chuyển phòng voice
@bot.event
async def on_voice_state_update(member, before, after):
    # Bỏ qua nếu thành viên là chính bot
    if member == bot.user:
        return

    # Kiểm tra nếu người dùng tham gia voice channel mới
    if after.channel is not None:
        voice_channel = after.channel
        guild = voice_channel.guild
        vc = None  # Khởi tạo mặc định cho vc

        # Ngắt kết nối khỏi kênh hiện tại nếu bot đã kết nối
        if guild.voice_client:
            current_vc = guild.voice_client
            if current_vc.channel != voice_channel:  # Nếu bot không cùng kênh với người dùng mới
                await current_vc.disconnect()  # Ngắt kết nối khỏi kênh cũ
                vc = await voice_channel.connect()  # Kết nối kênh mới
                current_guild_vc[guild.id] = vc  # Cập nhật voice client hiện tại
            else:  # Nếu bot đã ở cùng kênh
                vc = current_vc
        else:  # Nếu bot chưa ở kênh voice nào
            vc = await voice_channel.connect()
            current_guild_vc[guild.id] = vc

        # Đảm bảo vc luôn được khởi tạo trước khi gọi disconnect_after_timeout
        if vc:
            # Đặt hẹn giờ tự ngắt kết nối sau 15 phút
            bot.loop.create_task(disconnect_after_timeout(vc))

        # Thêm người dùng vào hàng đợi chào
        greeting_queue.append(member)

        # Nếu bot chưa bận chào ai, bắt đầu xử lý hàng đợi
        if not is_greeting:
            await handle_greetings(vc)


# Lệnh ?say: Phát âm thanh từ văn bản
@bot.command()
async def say(ctx, *, text: str):
    if not ctx.author.voice:
        await ctx.send("Bạn cần tham gia một phòng voice trước!")
        return

    # Kiểm tra bot đã ở trong phòng voice chưa
    voice_channel = ctx.author.voice.channel
    if ctx.guild.voice_client:  # Nếu bot đã kết nối
        vc = ctx.guild.voice_client
        if vc.channel != voice_channel:
            await vc.move_to(voice_channel)
    else:
        vc = await voice_channel.connect()

    # Tạo file âm thanh tạm thời từ văn bản
    temp_file = os.path.join(TEMP_DIR, "say.mp3")
    tts = gTTS(text, lang="vi")
    tts.save(temp_file)

    # Phát file âm thanh
    vc.play(
        discord.FFmpegPCMAudio(temp_file, executable=FFMPEG_PATH, options="-loglevel panic"),
        after=lambda e: print(f"Đã phát xong: {e}")
    )
    while vc.is_playing():
        await asyncio.sleep(1)

    # Xóa file âm thanh tạm thời
    try:
        os.remove(temp_file)
    except FileNotFoundError:
        print(f"Không tìm thấy file tạm: {temp_file}")
    except Exception as e:
        print(f"Lỗi khi xóa file tạm: {temp_file}, {e}")

    # Xóa tin nhắn chứa lệnh ?say
    try:
        await ctx.message.delete()
    except discord.Forbidden:
        print("Không thể xóa tin nhắn do thiếu quyền.")

# Chạy bot với token DISCORD_TOKEN_2
bot.run(TOKEN)
