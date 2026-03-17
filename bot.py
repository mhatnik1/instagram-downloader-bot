import os
import glob
import asyncio
import yt_dlp
from aiogram import Bot, Dispatcher, types
from aiogram.types import (
    ReplyKeyboardMarkup, InlineKeyboardMarkup,
    InlineKeyboardButton, InputFile
)
from aiogram.utils import executor

TOKEN = os.getenv("TOKEN")

bot = Bot(token=TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

user_data = {}
user_lang = {}

BOT_NAME = "iGramDrop"

# ===== QUEUE =====
queue = asyncio.Queue()

async def worker():
    while True:
        user_id, func = await queue.get()
        try:
            await func()
        except:
            await bot.send_message(user_id, "⚠️ Ошибка, попробуй позже")
        queue.task_done()

# ===== STARTUP =====
async def on_startup(dp):
    await bot.delete_webhook(drop_pending_updates=True)
    asyncio.create_task(worker())

# ===== START =====
lang_kb = ReplyKeyboardMarkup(resize_keyboard=True)
lang_kb.add("🇷🇺 Русский", "🇬🇧 English")

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("🌍 Choose language / Выбери язык", reply_markup=lang_kb)

@dp.message_handler(lambda m: m.text in ["🇷🇺 Русский", "🇬🇧 English"])
async def set_lang(message: types.Message):
    user_id = message.from_user.id
    user_lang[user_id] = "ru"

    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📸 Instagram", "🎵 TikTok")
    kb.row("▶️ YouTube", "💎 Premium")
    kb.row("🔄 Restart")

    photo = InputFile("photo_2026-03-17 17.40.44.jpeg")

    text = (
        "👋 <b>Добро пожаловать в iGramDrop</b>\n\n"
        "📥 Скачивай контент:\n"
        "• Instagram\n"
        "• TikTok\n"
        "• YouTube\n\n"
        "🎬 HD качество\n"
        "🎧 MP3 без потерь\n\n"
        "🚀 Просто отправь ссылку"
    )

    await message.answer_photo(photo, caption=text, reply_markup=kb)

# ===== RESTART =====
@dp.message_handler(lambda m: m.text == "🔄 Restart")
async def restart(message: types.Message):
    await start(message)

# ===== PREMIUM =====
@dp.message_handler(lambda m: m.text == "💎 Premium")
async def premium(message: types.Message):
    await message.answer(
        "💎 <b>Premium</b>\n\n"
        "⚡ Быстрее загрузка\n"
        "🎬 Лучшее качество\n\n"
        "🚀 Просто пользуйся ботом"
    )

# ===== LINK =====
@dp.message_handler(lambda m: m.text and "http" in m.text)
async def handle_link(message: types.Message):
    user_id = message.from_user.id
    url = message.text

    msg = await message.answer("⏳ Обрабатываю...")

    if "youtube" in url or "youtu.be" in url:
        user_data[user_id] = {"url": url, "loading": False}

        kb = InlineKeyboardMarkup(row_width=2)
        kb.row(
            InlineKeyboardButton("🔥 1080p", callback_data="video_1080"),
            InlineKeyboardButton("📺 720p", callback_data="video_720"),
        )
        kb.row(
            InlineKeyboardButton("🎵 MP3", callback_data="mp3")
        )

        await msg.delete()
        await message.answer("Выбери качество:", reply_markup=kb)

    else:
        async def task():
            try:
                ydl_opts = {
                    'format': 'best',
                    'outtmpl': 'media.%(ext)s',
                    'quiet': True
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

                files = glob.glob("media.*")

                for file in files:
                    with open(file, "rb") as f:
                        await bot.send_document(user_id, f)
                    os.remove(file)

            except:
                await bot.send_message(user_id, "⚠️ Не удалось скачать")

        await queue.put((user_id, task))

# ===== VIDEO DOWNLOAD =====
async def download_video(url, quality):
    formats = [
        f'bestvideo[height<={quality}]+bestaudio/best',
        'best[height<=720]',
        'best'
    ]

    for fmt in formats:
        try:
            ydl_opts = {
                'format': fmt,
                'merge_output_format': 'mp4',
                'outtmpl': 'video.%(ext)s',
                'quiet': True,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0'
                }
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            files = glob.glob("video.*")
            if files:
                return files[0]

        except:
            continue

    return None

# ===== CALLBACK =====
@dp.callback_query_handler(lambda c: True)
async def callbacks(callback: types.CallbackQuery):
    await callback.answer()

    user_id = callback.from_user.id
    data = callback.data
    url = user_data.get(user_id, {}).get("url")

    if not url:
        return

    if user_data.get(user_id, {}).get("loading"):
        return

    user_data[user_id]["loading"] = True

    async def task():
        try:
            if data.startswith("video_"):
                q = data.split("_")[1]

                file = await download_video(url, q)

                if not file:
                    await bot.send_message(user_id, "⚠️ Видео недоступно")
                    return

                with open(file, "rb") as f:
                    await bot.send_video(user_id, f)

                os.remove(file)

                kb = InlineKeyboardMarkup()
                kb.add(InlineKeyboardButton("🎵 Скачать аудио", callback_data="mp3"))

                await bot.send_message(user_id, "🎧 Аудио:", reply_markup=kb)

            elif data == "mp3":
                try:
                    ydl_opts = {
                        'format': 'bestaudio',
                        'outtmpl': 'audio.%(ext)s',
                        'quiet': True
                    }

                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([url])

                    files = glob.glob("audio.*")

                    if files:
                        with open(files[0], "rb") as f:
                            await bot.send_audio(user_id, f)
                        os.remove(files[0])

                except:
                    await bot.send_message(user_id, "⚠️ Ошибка аудио")

        finally:
            user_data[user_id]["loading"] = False

    await queue.put((user_id, task))

# ===== RUN =====
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
