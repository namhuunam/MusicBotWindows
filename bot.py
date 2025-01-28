import os
import re
import discord
import yt_dlp
import aiohttp
import isodate
import asyncio
import shutil
import random
from discord.ext import commands
from discord.ui import Button, View, Select
from dotenv import load_dotenv
import logging
from cachetools import TTLCache
import subprocess

# -----------------------------#
#    Đọc Thông Tin Proxy        #
# -----------------------------#

# Lấy đường dẫn tuyệt đối của thư mục hiện tại
current_dir = os.path.dirname(os.path.abspath(__file__))

# Đường dẫn đến file proxy.txt
proxy_txt_path = os.path.join(current_dir, "proxy.txt")

# Kiểm tra xem proxy.txt có tồn tại không và đọc nội dung proxy
if not os.path.isfile(proxy_txt_path):
    logging.warning(f"Không tìm thấy {proxy_txt_path}. Bot sẽ chạy mà không sử dụng proxy.")
    PROXY_URL = None
else:
    with open(proxy_txt_path, 'r') as proxy_file:
        PROXY_URL = proxy_file.read().strip()

    if not PROXY_URL:
        logging.info("Không sử dụng proxy vì proxy.txt trống.")
        PROXY_URL = None
    else:
        logging.info(f"Đã đọc proxy từ proxy.txt: {PROXY_URL}")

# -----------------------------#
#        Khởi Chạy voice.py     #
# -----------------------------#

# Lấy đường dẫn tuyệt đối của file voice.py
voice_py_path = os.path.join(current_dir, "voice.py")

# Chạy voice.py với Python trên Windows
# Đảm bảo rằng 'python' đã được thêm vào PATH hoặc sử dụng đường dẫn đầy đủ tới python.exe
subprocess.Popen(["python", voice_py_path])

# -----------------------------#
#        Cài Đặt Logging        #
# -----------------------------#

# Thiết lập logging để theo dõi và gỡ lỗi
logging.basicConfig(
    level=logging.INFO,  # Thiết lập mức logging
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Định dạng log
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),  # Ghi log vào file với mã hóa UTF-8
        logging.StreamHandler()  # Ghi log ra console
    ]
)
logger = logging.getLogger(__name__)

# -----------------------------#
#        Cài Đặt Môi Trường     #
# -----------------------------#

# Tải biến môi trường từ file .env
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')          # Token Discord Bot
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')  # API Key YouTube

# Đường dẫn đến ffmpeg và yt-dlp trên Windows
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Thư mục chứa file script
FFMPEG_PATH = os.path.join(BASE_DIR, "ffmpeg", "ffmpeg.exe")
YTDLP_PATH = os.path.join(BASE_DIR, "yt-dlp.exe")

# Kiểm tra sự tồn tại của các file
if not os.path.exists(FFMPEG_PATH):
    raise FileNotFoundError("Không tìm thấy ffmpeg.exe. Vui lòng kiểm tra lại.")
else:
    logger.info(f"Đã tìm thấy ffmpeg.exe tại: {FFMPEG_PATH}")

if not os.path.exists(YTDLP_PATH):
    raise FileNotFoundError("Không tìm thấy yt-dlp.exe. Vui lòng kiểm tra lại.")
else:
    logger.info(f"Đã tìm thấy yt-dlp.exe tại: {YTDLP_PATH}")

# -----------------------------#
#        Định Nghĩa Intents     #
# -----------------------------#

# Định Nghĩa các intents trước khi khởi tạo bot
intents = discord.Intents.default()
intents.message_content = True       # Cho phép bot đọc nội dung tin nhắn
intents.guilds = True                # Cho phép bot nhận sự kiện liên quan đến guilds (máy chủ)
intents.voice_states = True          # Cho phép bot nhận sự kiện liên quan đến trạng thái giọng nói

# -----------------------------#
#        Định Nghĩa Hàm Hỗ Trợ #
# -----------------------------#

def parse_duration(duration_iso8601):
    """
    Phân tích duration từ ISO 8601 sang định dạng HH:MM:SS hoặc MM:SS.
    """
    try:
        duration = isodate.parse_duration(duration_iso8601)
        total_seconds = int(duration.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours > 0:
            return f"{hours}:{minutes:02}:{seconds:02}"
        else:
            return f"{minutes}:{seconds:02}"
    except Exception as e:
        logger.error(f"Lỗi khi phân tích duration: {e}")
        return "Unknown"

def generate_queue_list(music_queue):
    """
    Tạo danh sách các bài hát trong hàng đợi dưới dạng chuỗi.
    """
    if music_queue.empty():
        return "Hàng đợi trống."
    queue_list = ""
    for idx, song in enumerate(music_queue._queue, start=1):
        queue_list += f"{idx}. {song['title']} - {song['duration']}\n"
    return queue_list

def truncate_label(text, max_length):
    """
    Rút gọn văn bản nếu vượt quá độ dài tối đa.
    """
    if len(text) > max_length:
        return text[:max_length-3] + '...'
    return text

# Định Nghĩa Hàm is_url trước khi sử dụng trong lệnh play
URL_REGEX = re.compile(
    r'^(https?://)?(www\.)?(youtube\.com|youtu\.?be)/.+$'
)

def is_url(query):
    """
    Kiểm tra xem chuỗi có phải là URL của YouTube không.
    """
    return re.match(URL_REGEX, query) is not None

# -----------------------------#
#        Định Nghĩa MusicPlayer#
# -----------------------------#

class MusicPlayer:
    """
    Lớp quản lý phát nhạc cho mỗi guild.
    """
    def __init__(self, guild_id, text_channel):
        self.guild_id = guild_id
        self.voice_client = None
        self.voice_channel = None  # Kênh thoại mà bot đang kết nối
        self.current_song = None
        self.is_paused = False
        self.is_looping = False
        self.music_queue = asyncio.Queue()
        self.current_control_message = None
        self.disconnect_task = None
        self.audio_cache = TTLCache(maxsize=100, ttl=7200)  # Bộ nhớ đệm với TTL 2 giờ
        self.text_channel = text_channel  # Kênh TextChannel để gửi thông báo
        self.played_songs = []  # Danh sách các bài hát đã được phát

# -----------------------------#
#        Định Nghĩa YouTubeAPI  #
# -----------------------------#

class YouTubeAPI:
    """
    Lớp quản lý các yêu cầu tới YouTube API.
    """
    def __init__(self, api_key):
        self.api_key = api_key
        self.session = None

    async def init_session(self):
        """
        Khởi tạo session aiohttp.
        """
        self.session = aiohttp.ClientSession()

    async def close(self):
        """
        Đóng session aiohttp.
        """
        if self.session:
            await self.session.close()

    async def search_youtube(self, query, max_results=10):
        """
        Tìm kiếm video trên YouTube dựa trên truy vấn.
        """
        search_url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            'part': 'snippet',
            'q': query,
            'type': 'video',
            'maxResults': max_results,
            'key': self.api_key
        }
        try:
            async with self.session.get(search_url, params=params) as resp:
                if resp.status != 200:
                    logger.error(f"Error in YouTube search: {resp.status}")
                    return None
                data = await resp.json()
                video_ids = [item['id']['videoId'] for item in data.get('items', [])]

            if not video_ids:
                return []

            details_url = "https://www.googleapis.com/youtube/v3/videos"
            details_params = {
                'part': 'contentDetails',
                'id': ','.join(video_ids),
                'key': self.api_key
            }
            async with self.session.get(details_url, params=details_params) as details_resp:
                if details_resp.status != 200:
                    logger.error(f"Error in YouTube video details: {details_resp.status}")
                    return None
                details_data = await details_resp.json()
                id_to_duration = {}
                for item in details_data.get('items', []):
                    video_id = item['id']
                    duration_iso8601 = item['contentDetails']['duration']
                    duration = parse_duration(duration_iso8601)
                    id_to_duration[video_id] = duration

            results = []
            for item in data.get('items', []):
                video_id = item['id']['videoId']
                title = item['snippet']['title']
                thumbnail = item['snippet']['thumbnails']['default']['url']
                url = f"https://www.youtube.com/watch?v={video_id}"
                duration = id_to_duration.get(video_id, "Unknown")
                results.append({
                    'title': title,
                    'url': url,
                    'thumbnail': thumbnail,
                    'duration': duration
                })
            return results
        except Exception as e:
            logger.error(f"Lỗi khi tìm kiếm YouTube: {e}")
            return None

# -----------------------------#
#        Định Nghĩa Bot         #
# -----------------------------#

class MyBot(commands.Bot):
    """
    Lớp Bot kế thừa từ commands.Bot để quản lý các chức năng bot.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.youtube_api = YouTubeAPI(YOUTUBE_API_KEY)
        self.music_players = {}  # Dictionary để quản lý MusicPlayer cho từng guild

    async def setup_hook(self):
        """
        Hook để khởi tạo các tài nguyên cần thiết khi bot đã sẵn sàng.
        """
        await self.youtube_api.init_session()

    async def close(self):
        """
        Đóng các tài nguyên khi bot tắt.
        """
        await self.youtube_api.close()
        await super().close()

# Instantiate the bot after defining classes
bot = MyBot(command_prefix='!', intents=intents)

# Helper function to get or create MusicPlayer for a guild
def get_music_player(guild_id, text_channel):
    """
    Lấy hoặc tạo MusicPlayer cho một guild cụ thể.
    """
    if guild_id not in bot.music_players:
        bot.music_players[guild_id] = MusicPlayer(guild_id, text_channel)
    return bot.music_players[guild_id]

# -----------------------------#
#    Định Nghĩa Các Lớp UI      #
# -----------------------------#

class MusicControlView(View):
    """
    Lớp View để quản lý các nút điều khiển nhạc (Pause, Resume, Skip, Loop).
    """
    def __init__(self, music_player):
        super().__init__(timeout=None)
        self.music_player = music_player

    @discord.ui.button(label="Tạm Dừng", style=discord.ButtonStyle.primary, emoji="⏸️")
    async def pause(self, interaction: discord.Interaction, button: Button):
        try:
            if self.music_player.voice_client and self.music_player.voice_client.is_playing():
                self.music_player.voice_client.pause()
                self.music_player.is_paused = True
                await interaction.response.send_message("⏸️ Nhạc đã tạm dừng!", ephemeral=True)
                await send_control_panel(self.music_player)
            else:
                await interaction.response.send_message("❗ Không có nhạc nào đang phát.", ephemeral=True)
        except Exception as e:
            logger.error(f"Lỗi trong nút Tạm Dừng: {e}")
            await interaction.response.send_message("❗ Đã xảy ra lỗi khi tạm dừng nhạc.", ephemeral=True)

    @discord.ui.button(label="Tiếp Tục", style=discord.ButtonStyle.success, emoji="▶️")
    async def resume(self, interaction: discord.Interaction, button: Button):
        try:
            if self.music_player.voice_client and self.music_player.is_paused:
                self.music_player.voice_client.resume()
                self.music_player.is_paused = False
                await interaction.response.send_message("▶️ Nhạc đã tiếp tục!", ephemeral=True)
                await send_control_panel(self.music_player)
            else:
                await interaction.response.send_message("❗ Không có nhạc nào đang tạm dừng.", ephemeral=True)
        except Exception as e:
            logger.error(f"Lỗi trong nút Tiếp Tục: {e}")
            await interaction.response.send_message("❗ Đã xảy ra lỗi khi tiếp tục nhạc.", ephemeral=True)

    @discord.ui.button(label="Bỏ Qua", style=discord.ButtonStyle.danger, emoji="⏭️")
    async def skip(self, interaction: discord.Interaction, button: Button):
        try:
            if self.music_player.voice_client and self.music_player.voice_client.is_playing():
                self.music_player.voice_client.stop()
                await interaction.response.send_message("⏭️ Đã bỏ qua bài hát!", ephemeral=True)
            else:
                await interaction.response.send_message("❗ Không có nhạc nào đang phát.", ephemeral=True)
        except Exception as e:
            logger.error(f"Lỗi trong nút Bỏ Qua: {e}")
            await interaction.response.send_message("❗ Đã xảy ra lỗi khi bỏ qua nhạc.", ephemeral=True)

    @discord.ui.button(label="Lặp Bài Hát", style=discord.ButtonStyle.secondary, emoji="🔁")
    async def loop(self, interaction: discord.Interaction, button: Button):
        try:
            self.music_player.is_looping = not self.music_player.is_looping
            state = "bật" if self.music_player.is_looping else "tắt"
            await interaction.response.send_message(f"🔁 Lặp bài hát đã {state}!", ephemeral=True)
            await send_control_panel(self.music_player)
        except Exception as e:
            logger.error(f"Lỗi trong nút Lặp Bài Hát: {e}")
            await interaction.response.send_message("❗ Đã xảy ra lỗi khi thay đổi chế độ lặp.", ephemeral=True)

class SongSelect(Select):
    """
    Lớp Select để người dùng chọn bài hát từ kết quả tìm kiếm.
    """
    def __init__(self, music_player, songs, user_voice_channel):
        options = [
            discord.SelectOption(
                label=truncate_label(f"{idx + 1}. {song['title']} - {song['duration']}", 100),
                value=str(idx)
            ) for idx, song in enumerate(songs)
        ]
        super().__init__(
            placeholder="Chọn bài hát bạn muốn phát...",
            min_values=1,
            max_values=1,
            options=options
        )
        self.music_player = music_player
        self.songs = songs
        self.user_voice_channel = user_voice_channel

    async def callback(self, interaction: discord.Interaction):
        try:
            selected_index = int(self.values[0])
            selected_song = self.songs[selected_index]
            await interaction.response.defer()
            await interaction.message.delete()
            await process_song_selection_from_selection(self.music_player, selected_song, self.user_voice_channel)
        except Exception as e:
            logger.error(f"Lỗi trong SongSelect callback: {e}")
            await interaction.response.send_message("❗ Đã xảy ra lỗi khi chọn bài hát.", ephemeral=True)

class SongSelectionView(View):
    """
    Lớp View chứa Select để chọn bài hát.
    """
    def __init__(self, music_player, songs, user_voice_channel):
        super().__init__(timeout=60)
        self.music_player = music_player
        self.songs = songs
        self.user_voice_channel = user_voice_channel
        self.add_item(SongSelect(music_player, songs, user_voice_channel))

    async def on_timeout(self):
        try:
            await self.message.edit(content="⏰ Thời gian chọn bài hát đã hết.", view=None)
        except Exception as e:
            logger.error(f"Lỗi khi timeout SongSelectionView: {e}")

    async def send(self, message):
        self.message = await message.edit(view=self)

# -----------------------------#
#      Định Nghĩa Các Hàm       #
# -----------------------------#

async def send_control_panel(music_player):
    """
    Gửi hoặc cập nhật bảng điều khiển nhạc (embed và view).
    """
    channel = music_player.text_channel
    # Xóa bảng điều khiển cũ (nếu có)
    if music_player.current_control_message:
        try:
            await music_player.current_control_message.delete()
        except discord.NotFound:
            pass
        music_player.current_control_message = None

    if music_player.current_song:
        status_message = f"🎶 Đang phát: **{music_player.current_song['title']}** - {music_player.current_song['duration']}"
    else:
        status_message = "🎶 Không có bài hát nào đang được phát."

    embed = discord.Embed(
        title="🎶 Music Player",
        description=status_message,
        color=discord.Color.green()
    )
    embed.add_field(
        name="📀 Trạng thái",
        value="Đang phát" if not music_player.is_paused else "Đã tạm dừng"
    )
    embed.add_field(
        name="🔄 Lặp",
        value="Bật" if music_player.is_looping else "Tắt"
    )
    embed.add_field(
        name="📋 Hàng đợi",
        value=generate_queue_list(music_player.music_queue),
        inline=False
    )
    embed.set_footer(text="Điều khiển nhạc bằng các nút bên dưới!")

    if music_player.current_song and music_player.current_song['thumbnail']:
        embed.set_thumbnail(url=music_player.current_song['thumbnail'])

    view = MusicControlView(music_player)
    music_player.current_control_message = await channel.send(embed=embed, view=view)
    await update_bot_status(music_player)

async def update_bot_status(music_player):
    """
    Cập nhật trạng thái của bot dựa trên trạng thái nhạc hiện tại.
    """
    if music_player.current_song:
        await bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.playing,
                name=f": {music_player.current_song['title']}"
            )
        )
    elif not music_player.music_queue.empty():
        next_song = music_player.music_queue._queue[0]
        await bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.playing,
                name=f"!play {next_song['title']}"
            )
        )
    else:
        await bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name="!play + Tên Bài Hát"
            )
        )

async def get_audio_stream_url(music_player, url):
    """
    Lấy URL luồng âm thanh từ cache hoặc YouTube.
    """
    if url in music_player.audio_cache:
        logger.info(f"Lấy URL âm thanh từ bộ nhớ đệm cho guild {music_player.guild_id}.")
        return music_player.audio_cache[url]

    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'noplaylist': True,
        'default_search': 'auto',
        'nocheckcertificate': True,
        'no_warnings': True,
        'ignoreerrors': True,
        'restrictfilenames': True,
        'skip_download': True,
        'cachedir': False,
        'ffmpeg_location': FFMPEG_PATH,  # Đường dẫn tới ffmpeg.exe
        'youtube_include_dash_manifest': False,  # Không lấy DASH manifest
    }

    if PROXY_URL:
        ydl_opts['proxy'] = PROXY_URL
        logger.info(f"Sử dụng proxy trong ydl_opts: {PROXY_URL}")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Sử dụng asyncio.to_thread để chạy hàm đồng bộ trong một thread
            info = await asyncio.to_thread(ydl.extract_info, url, download=False)
            if info is None:
                logger.error(f"yt_dlp trả về None cho thông tin video tại {url}.")
                return None

            # Lấy luồng âm thanh trực tiếp
            audio_url = info.get('url')
            title = info.get('title', 'URL Provided')
            thumbnail = info.get('thumbnail')
            logger.info(f"URL âm thanh cho guild {music_player.guild_id}: {audio_url}")  # Logging URL âm thanh

            # Lưu trữ vào bộ nhớ đệm dưới dạng dict
            music_player.audio_cache[url] = {
                "url": audio_url,
                "title": title,
                "thumbnail": thumbnail,
                "duration": "Unknown"  # Duration không được biết khi lấy từ URL trực tiếp
            }

        return music_player.audio_cache[url]
    except Exception as e:
        logger.error(f"Lỗi khi lấy audio stream URL tại {url}: {e}")
        return None

async def process_song_selection(ctx, song, user_voice_channel):
    """
    Xử lý bài hát được chọn từ lệnh play.
    """
    music_player = get_music_player(ctx.guild.id, ctx.channel)
    await process_song_selection_from_selection(music_player, song, user_voice_channel)

async def process_song_selection_from_selection(music_player, song, user_voice_channel):
    """
    Xử lý bài hát được chọn từ giao diện chọn bài hát.
    """
    try:
        logger.info(f"Đang xử lý bài hát: {song['title']} cho guild {music_player.guild_id}")

        # Hủy tác vụ ngắt kết nối nếu có
        if music_player.disconnect_task and not music_player.disconnect_task.cancelled():
            music_player.disconnect_task.cancel()
            music_player.disconnect_task = None

        # Kiểm tra và kết nối vào kênh thoại nếu chưa kết nối
        if not music_player.voice_client:
            if not user_voice_channel:
                await music_player.text_channel.send("❗ Bạn cần vào một kênh thoại trước!")
                return
            try:
                music_player.voice_client = await user_voice_channel.connect()
                music_player.voice_channel = user_voice_channel
                logger.info(f"Đã kết nối vào kênh thoại: {user_voice_channel.name}")
            except Exception as e:
                logger.error(f"Lỗi khi kết nối kênh thoại: {e}")
                await music_player.text_channel.send("❗ Không thể kết nối vào kênh thoại.")
                return
        elif music_player.voice_client.channel != user_voice_channel:
            try:
                await music_player.voice_client.move_to(user_voice_channel)
                music_player.voice_channel = user_voice_channel
                logger.info(f"Đã di chuyển vào kênh thoại: {user_voice_channel.name}")
            except Exception as e:
                logger.error(f"Lỗi khi di chuyển kênh thoại: {e}")
                await music_player.text_channel.send("❗ Không thể di chuyển vào kênh thoại.")
                return

        # Lấy URL luồng âm thanh
        audio_data = await get_audio_stream_url(music_player, song['url'])
        if not audio_data:
            await music_player.text_channel.send("❗ Không thể lấy luồng âm thanh của bài hát này.")
            return

        current_song_info = {
            "url": audio_data["url"],
            "title": audio_data["title"],
            "thumbnail": audio_data["thumbnail"],
            "duration": song['duration']
        }

        # Thêm bài hát đã phát vào danh sách đã phát
        music_player.played_songs.append(current_song_info)

        if music_player.voice_client.is_playing() or music_player.voice_client.is_paused():
            await music_player.music_queue.put(current_song_info)
            await send_control_panel(music_player)
            logger.info(f"Đã thêm bài hát vào hàng đợi: {current_song_info['title']}")
        else:
            music_player.current_song = current_song_info
            try:
                logger.info(f"Đang cố gắng phát: {current_song_info['title']} cho guild {music_player.guild_id}")

                before_options = '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
                if PROXY_URL:
                    before_options += f' -http_proxy {PROXY_URL}'

                music_player.voice_client.play(
                    discord.FFmpegOpusAudio(
                        executable=FFMPEG_PATH,
                        source=current_song_info['url'],
                        before_options=before_options,
                        options='-vn -c:a copy -loglevel quiet'  # Stream copy để giảm tải CPU
                    ),
                    after=lambda e: asyncio.run_coroutine_threadsafe(play_next(music_player.guild_id), bot.loop)
                )
                logger.info(f"Đã phát: {current_song_info['title']} cho guild {music_player.guild_id}")
                await send_control_panel(music_player)
            except Exception as e:
                logger.error(f"Lỗi khi phát nhạc: {e}")
                await music_player.text_channel.send("❗ Có lỗi xảy ra khi phát nhạc.")
    except Exception as e:
        logger.error(f"Lỗi trong process_song_selection_from_selection: {e}")
        await music_player.text_channel.send("❗ Đã xảy ra lỗi khi xử lý bài hát.")

async def play_next(guild_id):
    """
    Phát bài hát tiếp theo trong hàng đợi hoặc từ bộ nhớ đệm.
    """
    try:
        music_player = bot.music_players.get(guild_id)
        if not music_player:
            logger.error(f"Không tìm thấy MusicPlayer cho guild {guild_id}.")
            return

        channel = music_player.text_channel
        if not channel:
            logger.error(f"Không tìm thấy kênh text cho MusicPlayer của guild {guild_id}.")
            return

        if music_player.current_control_message:
            try:
                await music_player.current_control_message.delete()
            except discord.NotFound:
                pass
            music_player.current_control_message = None

        if music_player.is_looping and music_player.current_song:
            try:
                logger.info(f"Lặp lại bài hát: {music_player.current_song['title']} cho guild {guild_id}")

                before_options = '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
                if PROXY_URL:
                    before_options += f' -http_proxy {PROXY_URL}'

                music_player.voice_client.play(
                    discord.FFmpegOpusAudio(
                        executable=FFMPEG_PATH,
                        source=music_player.current_song["url"],
                        before_options=before_options,
                        options='-vn -c:a copy -loglevel quiet'  # Stream copy để giảm tải CPU
                    ),
                    after=lambda e: asyncio.run_coroutine_threadsafe(play_next(guild_id), bot.loop)
                )
                logger.info(f"Đã phát lại: {music_player.current_song['title']} cho guild {guild_id}")
                await send_control_panel(music_player)
            except Exception as e:
                logger.error(f"Lỗi khi phát lại bài hát: {e}")
        elif not music_player.music_queue.empty():
            next_song = await music_player.music_queue.get()
            # Đảm bảo next_song là dict
            if isinstance(next_song, tuple):
                logger.error(f"Expected dict but got tuple in music_queue for guild {guild_id}.")
                next_song = {
                    "url": next_song[0],
                    "title": next_song[1],
                    "thumbnail": next_song[2],
                    "duration": "Unknown"
                }
            music_player.current_song = next_song
            try:
                logger.info(f"Đang phát bài tiếp theo: {next_song['title']} cho guild {guild_id}")

                before_options = '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
                if PROXY_URL:
                    before_options += f' -http_proxy {PROXY_URL}'

                music_player.voice_client.play(
                    discord.FFmpegOpusAudio(
                        executable=FFMPEG_PATH,
                        source=next_song["url"],
                        before_options=before_options,
                        options='-vn -c:a copy -loglevel quiet'  # Stream copy để giảm tải CPU
                    ),
                    after=lambda e: asyncio.run_coroutine_threadsafe(play_next(guild_id), bot.loop)
                )
                logger.info(f"Đã phát bài tiếp theo: {next_song['title']} cho guild {guild_id}")
                await send_control_panel(music_player)
            except Exception as e:
                logger.error(f"Lỗi khi phát bài tiếp theo: {e}")
        else:
            # Hàng đợi trống, cố gắng nạp lại từ bộ nhớ đệm một bài hát
            cache_songs = list(music_player.audio_cache.values())
            if cache_songs:
                # Thêm thông báo khi bắt đầu phát lại từ cache
                await channel.send("🔄 Bot sẽ bắt đầu phát lại các bài hát từ bộ nhớ đệm.")
                # Chọn một bài hát ngẫu nhiên từ cache
                song = random.choice(cache_songs)
                await music_player.music_queue.put(song)  # Đảm bảo song là dict
                await play_next(guild_id)  # Gọi lại play_next để bắt đầu phát
            else:
                music_player.current_song = None
                await channel.send("🎵 Hết hàng đợi và bộ nhớ đệm trống. Bot sẽ ngắt kết nối sau 15 phút nếu không có yêu cầu mới.")
                music_player.disconnect_task = asyncio.create_task(disconnect_after_delay(guild_id))
                await update_bot_status(music_player)
    except Exception as e:
        logger.error(f"Lỗi trong play_next cho guild {guild_id}: {e}")

async def disconnect_after_delay(guild_id):
    """
    Ngắt kết nối bot khỏi kênh thoại sau 15 phút không hoạt động.
    """
    try:
        await asyncio.sleep(900)  # 15 phút
        music_player = bot.music_players.get(guild_id)
        if not music_player:
            logger.error(f"Không tìm thấy MusicPlayer cho guild {guild_id} khi ngắt kết nối.")
            return

        channel = music_player.text_channel
        if not channel:
            logger.error(f"Không tìm thấy kênh text cho MusicPlayer của guild {guild_id} khi ngắt kết nối.")
            return

        if (music_player.voice_client and 
            not music_player.voice_client.is_playing() and 
            music_player.music_queue.empty()):
            await channel.send("🕒 15 phút đã trôi qua mà không có yêu cầu mới. Ngắt kết nối.")
            await music_player.voice_client.disconnect()
            music_player.voice_client = None
            music_player.voice_channel = None  # Reset voice_channel sau khi ngắt kết nối
            await update_bot_status(music_player)
    except asyncio.CancelledError:
        logger.info(f"Tác vụ ngắt kết nối đã bị hủy cho guild {guild_id}.")
    except Exception as e:
        logger.error(f"Lỗi khi ngắt kết nối sau thời gian chờ cho guild {guild_id}: {e}")

# -----------------------------#
#        Định Nghĩa Các Lệnh    #
# -----------------------------#

@bot.command(aliases=['p'])
async def play(ctx, *, query: str):
    """
    Lệnh để phát nhạc. Query có thể là tên bài hát hoặc URL YouTube.
    """
    try:
        user_voice = ctx.author.voice
        if not user_voice or not user_voice.channel:
            await ctx.send("❗ Bạn cần vào một kênh thoại trước!")
            return

        music_player = get_music_player(ctx.guild.id, ctx.channel)
        if is_url(query):
            url = query
            audio_data = await get_audio_stream_url(music_player, url)
            if not audio_data:
                await ctx.send("❗ Không thể lấy luồng âm thanh của URL này.")
                return
            await process_song_selection(ctx, {
                'url': url,
                'title': audio_data["title"],
                'thumbnail': audio_data["thumbnail"],
                'duration': "Unknown"
            }, user_voice.channel)
        else:
            await ctx.send(f"🔍 Đang tìm kiếm **{query}** trên YouTube...")
            search_results = await bot.youtube_api.search_youtube(query)

            if not search_results:
                await ctx.send("❌ Không tìm thấy kết quả nào cho tìm kiếm của bạn.")
                return

            embed = discord.Embed(
                title="Kết Quả Tìm Kiếm",
                description=f"Tìm thấy {len(search_results)} kết quả cho **{query}**:",
                color=discord.Color.blue()
            )
            for idx, song in enumerate(search_results, start=1):
                embed.add_field(
                    name=f"{idx}. {song['title']} - {song['duration']}",
                    value="",
                    inline=False
                )

            view = SongSelectionView(music_player, search_results, user_voice.channel)
            message = await ctx.send(embed=embed, view=view)
            await view.send(message)
    except Exception as e:
        logger.error(f"Lỗi trong lệnh play: {e}")
        await ctx.send("❗ Đã xảy ra lỗi khi xử lý lệnh play.")

@bot.command()
async def stop(ctx):
    """
    Lệnh để dừng phát nhạc và ngắt kết nối bot khỏi kênh thoại.
    """
    try:
        music_player = bot.music_players.get(ctx.guild.id)
        if not music_player:
            await ctx.send("❗ Bot không kết nối vào kênh thoại nào.")
            return

        if music_player.disconnect_task and not music_player.disconnect_task.cancelled():
            music_player.disconnect_task.cancel()
            music_player.disconnect_task = None

        # Xóa hàng đợi một cách an toàn
        while not music_player.music_queue.empty():
            try:
                music_player.music_queue.get_nowait()
            except asyncio.QueueEmpty:
                break

        music_player.current_song = None
        if music_player.voice_client.is_playing() or music_player.voice_client.is_paused():
            music_player.voice_client.stop()

        if music_player.current_control_message:
            try:
                await music_player.current_control_message.delete()
            except Exception as e:
                logger.error(f"Lỗi khi xóa control message: {e}")
            music_player.current_control_message = None

        await music_player.voice_client.disconnect()
        music_player.voice_client = None
        music_player.voice_channel = None  # Reset voice_channel sau khi ngắt kết nối
        await ctx.send("🛑 Bot đã ngắt kết nối và xóa hàng đợi.")
        await update_bot_status(music_player)
    except Exception as e:
        logger.error(f"Lỗi trong lệnh stop: {e}")
        await ctx.send("❗ Đã xảy ra lỗi khi ngắt kết nối khỏi kênh thoại.")

# -----------------------------#
#        Định Nghĩa Sự Kiện     #
# -----------------------------#

@bot.event
async def on_ready():
    """
    Sự kiện khi bot đã sẵn sàng và đăng nhập thành công.
    """
    if PROXY_URL:
        logger.info(f"Bot đang sử dụng proxy: {PROXY_URL}")
    else:
        logger.info("Bot không sử dụng proxy.")
    logger.info(f'Bot đã đăng nhập với tên: {bot.user}')

@bot.event
async def on_disconnect():
    """
    Sự kiện khi bot ngắt kết nối khỏi Discord.
    """
    logger.info("Bot đã ngắt kết nối khỏi Discord.")

@bot.event
async def on_error(event, *args, **kwargs):
    """
    Sự kiện xử lý lỗi trong các sự kiện Discord.
    """
    logger.exception(f"Lỗi xảy ra trong event {event}.")

@bot.event
async def on_command_error(ctx, error):
    """
    Handler lỗi toàn cục cho các lệnh Discord.
    """
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❗ Lệnh không tồn tại. Vui lòng kiểm tra lại.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❗ Thiếu đối số cần thiết cho lệnh này.")
    else:
        logger.error(f"Lỗi trong lệnh {ctx.command}: {error}")
        await ctx.send("❗ Đã xảy ra lỗi khi xử lý lệnh của bạn.")

# -----------------------------#
#        Chạy Bot               #
# -----------------------------#

# Đảm bảo đóng session aiohttp khi bot tắt bằng cách sử dụng phương thức close của lớp MyBot
# Không cần tạo task ở đây

bot.run(TOKEN)
