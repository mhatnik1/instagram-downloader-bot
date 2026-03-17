import os
import glob
import yt_dlp
from aiogram import Bot, Dispatcher, types
from aiogram.types import (
    ReplyKeyboardMarkup, InlineKeyboardMarkup,
    InlineKeyboardButton, InputFile
)
from aiogram.utils import executor

TOKEN = os.getenv("TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

user_data = {}
user_lang = {}

BOT_NAME = "iGramDrop"

# ===== STARTUP =====
async def on_startup(dp):
    await bot.delete_webhook(drop_pending_updates=True)

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
    kb.add("💎 Donate", "🔄 Restart")

    photo = InputFile("photo_2026-03-17 17.40.44.jpeg" if user_lang[user_id]=="ru"
                      else "photo_2026-03-17 17.40.42.jpeg")

    text = (
        f"👋 Привет! Я {BOT_NAME}\n\n📥 Отправь ссылку"
        if user_lang[user_id]=="ru"
        else f"👋 Hey! I'm {BOT_NAME}\n\n📥 Send link"
    )

    await message.answer_photo(photo, caption=text, reply_markup=kb)

# ===== RESTART =====
@dp.message_handler(lambda m: m.text == "🔄 Restart")
async def restart(message: types.Message):
    await start(message)

# ===== LINK =====
@dp.message_handler(lambda m: m.text and "http" in m.text)
async def handle_link(message: types.Message):
    user_id = message.from_user.id
    url = message.text

    await message.answer("⏳ Обрабатываю...")

    try:
        if "youtube" in url or "youtu.be" in url:
            user_data[user_id] = {"url": url}

            kb = InlineKeyboardMarkup(row_width=2)
            kb.add(
                InlineKeyboardButton("🔥 1080p", callback_data="video_1080"),
                InlineKeyboardButton("📺 720p", callback_data="video_720"),
            )
            kb.add(InlineKeyboardButton("🎵 MP3", callback_data="mp3"))

            await message.answer("Выбери качество:", reply_markup=kb)

        else:
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
                    await message.answer_document(f)
                os.remove(file)

    except Exception as e:
        await message.answer(f"❌ {e}")

# ===== CALLBACK =====
@dp.callback_query_handler(lambda c: True)
async def callbacks(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = callback.data
    url = user_data.get(user_id, {}).get("url")

    try:
        if data.startswith("video_"):
            q = data.split("_")[1]

            try:
                ydl_opts = {
                    'format': f'bestvideo[height<={q}]+bestaudio/best',
                    'merge_output_format': 'mp4',
                    'outtmpl': 'video.%(ext)s',
                    'quiet': True,

                    # 🔥 cookies
                    'cookiefile': 'cookies.txt',

                    # 🔥 анти-бот
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

            file = glob.glob("video.*")[0]

            with open(file, "rb") as f:
                await bot.send_video(user_id, f)

            os.remove(file)

            kb = InlineKeyboardMarkup(row_width=1)
            kb.add(InlineKeyboardButton("🎵 Скачать аудио", callback_data="mp3"))

            await bot.send_message(user_id, " ", reply_markup=kb)

        elif data == "mp3":
            ydl_opts = {
                'format': 'bestaudio',
                'outtmpl': 'audio.%(ext)s',
                'quiet': True,
                'cookiefile': 'cookies.txt'
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            file = glob.glob("audio.*")[0]

            with open(file, "rb") as f:
                await bot.send_audio(user_id, f)

            os.remove(file)

    except Exception as e:
        await bot.send_message(user_id, f"❌ {e}")

# ===== RUN =====
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
