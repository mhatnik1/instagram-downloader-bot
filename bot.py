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
premium_users = set()

BOT_NAME = "iGramDrop"

# ===== QUEUE =====
queue = asyncio.Queue()

async def worker():
    while True:
        user_id, func = await queue.get()
        try:
            await func()
        except Exception as e:
            await bot.send_message(user_id, f"❌ {e}")
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
    user_lang[user_id] = "ru" if "Русский" in message.text else "en"

    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📸 Instagram", "🎵 TikTok", "▶️ YouTube")
    kb.add("💎 Premium", "🔄 Restart")

    photo = InputFile("photo_2026-03-17 17.40.44.jpeg")

    text = f"👋 Я {BOT_NAME}\n\n📥 Отправь ссылку — я скачаю всё 🚀"

    await message.answer_photo(photo, caption=text, reply_markup=kb)

# ===== RESTART =====
@dp.message_handler(lambda m: m.text == "🔄 Restart")
async def restart(message: types.Message):
    await start(message)

# ===== PREMIUM =====
@dp.message_handler(lambda m: m.text == "💎 Premium")
async def premium(message: types.Message):
    await message.answer("💎 Premium = без лимитов\n\nНапиши администратору")

# ===== LINK =====
@dp.message_handler(lambda m: m.text and "http" in m.text)
async def handle_link(message: types.Message):
    user_id = message.from_user.id
    url = message.text

    # лимит
    if user_id not in premium_users:
        count = user_data.get(user_id, {}).get("count", 0)
        if count >= 2:
            await message.answer("💎 Купи Premium для продолжения")
            return

    msg = await message.answer("⏳ Обрабатываю...")

    if "youtube" in url or "youtu.be" in url:
        user_data[user_id] = {"url": url, "loading": False}

        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("🔥 1080p", callback_data="video_1080"),
            InlineKeyboardButton("📺 720p", callback_data="video_720"),
        )
        kb.add(InlineKeyboardButton("🎵 MP3", callback_data="mp3"))

        await msg.delete()
        await message.answer("Выбери качество:", reply_markup=kb)

    else:
        async def task():
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

        await queue.put((user_id, task))

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

                try:
                    ydl_opts = {
                        'format': f'bestvideo[height<={q}]+bestaudio/best',
                        'merge_output_format': 'mp4',
                        'outtmpl': 'video.%(ext)s',
                        'quiet': True,
                        'cookiefile': 'cookies.txt',
                        'http_headers': {
                            'User-Agent': 'Mozilla/5.0'
                        }
                    }

                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([url])

                except:
                    ydl_opts = {
                        'format': 'best[height<=720]',
                        'outtmpl': 'video.%(ext)s',
                        'quiet': True
                    }

                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([url])

                files = glob.glob("video.*")

                if not files:
                    await bot.send_message(user_id, "❌ Ошибка")
                    return

                file = files[0]

                with open(file, "rb") as f:
                    await bot.send_video(user_id, f)

                os.remove(file)

                kb = InlineKeyboardMarkup(row_width=1)
                kb.add(InlineKeyboardButton("🎵 Скачать аудио", callback_data="mp3"))

                await bot.send_message(user_id, "🎧 Доступно аудио:", reply_markup=kb)

            elif data == "mp3":
                ydl_opts = {
                    'format': 'bestaudio',
                    'outtmpl': 'audio.%(ext)s',
                    'quiet': True,
                    'cookiefile': 'cookies.txt'
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

                files = glob.glob("audio.*")

                if files:
                    with open(files[0], "rb") as f:
                        await bot.send_audio(user_id, f)
                    os.remove(files[0])

            # увеличиваем счётчик
            user_data[user_id]["count"] = user_data[user_id].get("count", 0) + 1

        finally:
            user_data[user_id]["loading"] = False

    await queue.put((user_id, task))

# ===== RUN =====
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
