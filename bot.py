import os
import glob
import yt_dlp
from aiogram import Bot, Dispatcher, types
from aiogram.types import (
    ReplyKeyboardMarkup, InlineKeyboardMarkup,
    InlineKeyboardButton, LabeledPrice
)
from aiogram.utils import executor

TOKEN = os.getenv("TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

users = set()
user_data = {}
user_platform = {}
user_lang = {}

TEXTS = {
    "ru": {
        "start": "🚀 Бесплатный загрузчик\n\n📥 Выбери платформу",
        "send_link": "📥 Отправь ссылку",
        "processing": "⏳ Обрабатываю...",
        "choose_quality": "📥 Выбери качество:",
    },
    "en": {
        "start": "🚀 Free downloader\n\n📥 Choose platform",
        "send_link": "📥 Send link",
        "processing": "⏳ Processing...",
        "choose_quality": "📥 Choose quality:",
    }
}

def t(user_id, key):
    return TEXTS.get(user_lang.get(user_id, "ru"))[key]

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
    users.add(user_id)

    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📸 Instagram", "🎵 TikTok", "▶️ YouTube")

    if user_lang[user_id] == "ru":
        text = (
            "🔥 Добро пожаловать!\n\n"
            "🚀 Это быстрый и бесплатный загрузчик\n\n"
            "📥 Скачивай видео и музыку из:\n"
            "📸 Instagram • 🎵 TikTok • ▶️ YouTube\n\n"
            "⚡ Просто отправь ссылку и получи результат за секунды"
        )

        with open("welcome_ru.jpg", "rb") as photo:
            await message.answer_photo(photo, caption=text, reply_markup=kb)

    else:
        text = (
            "🔥 Welcome!\n\n"
            "🚀 This is a fast and free downloader\n\n"
            "📥 Download videos & music from:\n"
            "📸 Instagram • 🎵 TikTok • ▶️ YouTube\n\n"
            "⚡ Just send a link and get your file in seconds"
        )

        with open("welcome_en.jpg", "rb") as photo:
            await message.answer_photo(photo, caption=text, reply_markup=kb)

# ===== PLATFORM =====
@dp.message_handler(lambda m: m.text in ["📸 Instagram", "🎵 TikTok", "▶️ YouTube"])
async def choose_platform(message: types.Message):
    user_platform[message.from_user.id] = message.text
    await message.answer(t(message.from_user.id, "send_link"))

# ===== LINK =====
@dp.message_handler(lambda m: "http" in m.text)
async def handle_link(message: types.Message):
    user_id = message.from_user.id
    users.add(user_id)

    platform = user_platform.get(user_id)

    if not platform:
        await message.answer("❌ Choose platform first")
        return

    await message.answer(t(user_id, "processing"))

    try:
        if platform == "▶️ YouTube":
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(message.text, download=False)

            user_data[user_id] = {"url": message.text, "info": info}

            kb = InlineKeyboardMarkup(row_width=2)
            for q in [144, 360, 720]:
                kb.insert(InlineKeyboardButton(f"{q}p", callback_data=f"video_{q}"))

            kb.add(
                InlineKeyboardButton("MP3", callback_data="mp3"),
                InlineKeyboardButton("Preview", callback_data="preview")
            )

            await message.answer(t(user_id, "choose_quality"), reply_markup=kb)

        else:
            ydl_opts = {'format': 'best', 'outtmpl': 'video.%(ext)s'}

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([message.text])

            files = glob.glob("video.*")
            if not files:
                await message.answer("❌ Ошибка загрузки")
                return

            video_file = files[0]

            with open(video_file, "rb") as f:
                await message.answer_video(f)

            os.remove(video_file)
            await after_download(user_id)

    except Exception as e:
        await message.answer(f"❌ {e}")

# ===== CALLBACK =====
@dp.callback_query_handler(lambda c: True)
async def callbacks(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = callback.data

    # ===== ДОНАТ =====
    if data.startswith("donate_"):
        amount = int(data.split("_")[1])

        await bot.send_invoice(
            chat_id=user_id,
            title="Support ❤️",
            description="Thanks for support ❤️",
            payload=f"donate_{amount}",
            provider_token="",
            currency="XTR",
            prices=[LabeledPrice(label="Support", amount=amount)],
            start_parameter="donate"
        )
        return

    if user_id not in user_data:
        return

    url = user_data[user_id]["url"]

    try:
        if data.startswith("video_"):
            q = data.split("_")[1]

            ydl_opts = {
                'format': f'best[height<={q}]',
                'outtmpl': 'video.%(ext)s'
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            files = glob.glob("video.*")
            if not files:
                await bot.send_message(user_id, "❌ Ошибка")
                return

            video_file = files[0]

            with open(video_file, "rb") as f:
                await bot.send_video(user_id, f)

            os.remove(video_file)

        elif data == "mp3":
            ydl_opts = {
                'format': 'bestaudio',
                'outtmpl': 'audio.%(ext)s'
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            files = glob.glob("audio.*")
            if not files:
                await bot.send_message(user_id, "❌ Ошибка")
                return

            audio_file = files[0]

            with open(audio_file, "rb") as f:
                await bot.send_audio(user_id, f)

            os.remove(audio_file)

        elif data == "preview":
            thumb = user_data[user_id]["info"].get("thumbnail")
            if thumb:
                await bot.send_photo(user_id, thumb)
            return

        await after_download(user_id)

    except Exception as e:
        await bot.send_message(user_id, f"❌ {e}")

# ===== МОНЕТИЗАЦИЯ =====
async def after_download(user_id):
    bot_username = (await bot.get_me()).username
    lang = user_lang.get(user_id, "ru")

    kb = InlineKeyboardMarkup(row_width=1)

    if lang == "ru":
        text = (
            "🔥 Готово!\n\n"
            "❤️ Бот бесплатный и работает благодаря пользователям\n\n"
            "🙏 Если тебе помогло — можешь отблагодарить\n"
            "Даже небольшой донат помогает поддерживать сервис"
        )

        kb.add(
            InlineKeyboardButton("❤️ 50⭐", callback_data="donate_50"),
            InlineKeyboardButton("🔥 100⭐ (лучший)", callback_data="donate_100"),
            InlineKeyboardButton("👑 250⭐", callback_data="donate_250"),
        )

        kb.add(
            InlineKeyboardButton("📢 Поделиться ботом", url=f"https://t.me/{bot_username}")
        )

    else:
        text = (
            "🔥 Done!\n\n"
            "❤️ This bot is free and supported by users\n\n"
            "🙏 If it helped you — you can support\n"
            "Even a small tip makes a difference"
        )

        kb.add(
            InlineKeyboardButton("❤️ $0.5", callback_data="donate_50"),
            InlineKeyboardButton("🔥 $1 (most popular)", callback_data="donate_100"),
            InlineKeyboardButton("👑 $2.5", callback_data="donate_250"),
        )

        kb.add(
            InlineKeyboardButton("📢 Share bot", url=f"https://t.me/{bot_username}")
        )

    await bot.send_message(user_id, text, reply_markup=kb)

# ===== RUN =====
if __name__ == "__main__":
    while True:
        try:
            executor.start_polling(dp, skip_updates=True)
        except Exception as e:
            print("Ошибка:", e)
