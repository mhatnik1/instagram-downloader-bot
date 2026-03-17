import os
import yt_dlp
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor

TOKEN = os.getenv("TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

user_data = {}

# ===== START =====
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer(
        "🚀 YouTube Downloader PRO\n\n"
        "📥 Отправь ссылку на видео\n"
        "🎯 Получи выбор качества + MP3"
    )

# ===== ПОЛУЧЕНИЕ ССЫЛКИ =====
@dp.message_handler(lambda m: "youtube.com" in m.text or "youtu.be" in m.text)
async def handle_link(message: types.Message):
    url = message.text

    await message.answer("⏳ Получаю информацию...")

    ydl_opts = {'quiet': True}

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        user_data[message.from_user.id] = {
            "url": url,
            "info": info
        }

        title = info.get("title", "Видео")
        thumbnail = info.get("thumbnail")
        duration = info.get("duration", 0)

        formats = info.get("formats", [])

        # Фильтр качеств
        qualities = {}
        for f in formats:
            if f.get("height") and f.get("filesize"):
                h = f.get("height")
                size = f.get("filesize") // (1024 * 1024)
                qualities[h] = size

        text = f"🎬 {title}\n\n📥 Доступные качества:\n\n"

        kb = InlineKeyboardMarkup(row_width=2)

        for q in sorted(qualities.keys()):
            text += f"✅ {q}p ~ {qualities[q]}MB\n"
            kb.insert(
                InlineKeyboardButton(
                    f"📹 {q}p",
                    callback_data=f"video_{q}"
                )
            )

        kb.add(
            InlineKeyboardButton("🎧 MP3", callback_data="mp3"),
            InlineKeyboardButton("🖼 Превью", callback_data="preview")
        )

        if thumbnail:
            await message.answer_photo(thumbnail, caption=text, reply_markup=kb)
        else:
            await message.answer(text, reply_markup=kb)

    except:
        await message.answer("❌ Ошибка при получении данных")

# ===== CALLBACK =====
@dp.callback_query_handler(lambda c: True)
async def callbacks(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = callback.data

    if user_id not in user_data:
        await callback.message.answer("❌ Сначала отправь ссылку")
        return

    url = user_data[user_id]["url"]
    info = user_data[user_id]["info"]

    await callback.message.answer("⏳ Скачиваю...")

    try:
        if data.startswith("video_"):
            quality = data.split("_")[1]

            ydl_opts = {
                'format': f'bestvideo[height<={quality}]+bestaudio/best',
                'outtmpl': 'video.%(ext)s',
                'merge_output_format': 'mp4'
            }

            filename = "video.mp4"

        elif data == "mp3":
            ydl_opts = {
                'format': 'bestaudio',
                'outtmpl': 'audio.%(ext)s',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                }]
            }

            filename = "audio.mp3"

        elif data == "preview":
            thumbnail = info.get("thumbnail")
            if thumbnail:
                await bot.send_photo(user_id, thumbnail)
            return

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        with open(filename, "rb") as f:
            if data == "mp3":
                await bot.send_audio(user_id, f)
            else:
                await bot.send_video(user_id, f)

        # 🔥 ШАРИНГ
        bot_username = (await bot.get_me()).username

        kb = InlineKeyboardMarkup().add(
            InlineKeyboardButton(
                "📢 Поделиться ботом",
                url=f"https://t.me/{bot_username}"
            )
        )

        await bot.send_message(
            user_id,
            "🔥 Понравилось? Поделись с другом:",
            reply_markup=kb
        )

    except Exception as e:
        await bot.send_message(user_id, "❌ Ошибка скачивания")

# ===== ЗАПУСК =====
if __name__ == "__main__":
    while True:
        try:
            executor.start_polling(dp, skip_updates=True)
        except Exception as e:
            print("Ошибка:", e)
