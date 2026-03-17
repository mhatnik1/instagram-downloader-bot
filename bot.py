import os
import glob
import yt_dlp
from aiogram import Bot, Dispatcher, types
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice
)
from aiogram.utils import executor

TOKEN = os.getenv("TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# ===== ХРАНЕНИЕ =====
users = set()
user_data = {}
user_platform = {}
user_lang = {}
user_actions = {}

DONATE_AMOUNT = 10000

# ===== ПЕРЕВОДЫ =====
TEXTS = {
    "ru": {
        "start": "🚀 MULTI DOWNLOADER\n\n📥 Выбери платформу",
        "choose_lang": "🌍 Выбери язык",
        "send_link": "📥 Отправь ссылку",
        "processing": "⏳ Обрабатываю...",
        "error": "❌ Ошибка",
        "choose_quality": "📥 Выбери качество:",
        "done": "🔥 Готово!\n\n❤️ Бот бесплатный",
        "donate": "⭐ Поддержать",
        "share": "📢 Поделиться",
        "support_text": "💎 Поддержка по желанию ❤️"
    },
    "en": {
        "start": "🚀 MULTI DOWNLOADER\n\n📥 Choose platform",
        "choose_lang": "🌍 Choose language",
        "send_link": "📥 Send link",
        "processing": "⏳ Processing...",
        "error": "❌ Error",
        "choose_quality": "📥 Choose quality:",
        "done": "🔥 Done!\n\n❤️ Free bot",
        "donate": "⭐ Support",
        "share": "📢 Share",
        "support_text": "💎 Support if you want ❤️"
    }
}

def t(user_id, key):
    return TEXTS.get(user_lang.get(user_id, "ru"))[key]

# ===== ЯЗЫК =====
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
    kb.add(t(user_id, "donate"), t(user_id, "share"))

    await message.answer(t(user_id, "start"), reply_markup=kb)

# ===== ПЛАТФОРМА =====
@dp.message_handler(lambda m: m.text in ["📸 Instagram", "🎵 TikTok", "▶️ YouTube"])
async def choose_platform(message: types.Message):
    user_platform[message.from_user.id] = message.text
    await message.answer(t(message.from_user.id, "send_link"))

# ===== ДОНАТ =====
@dp.message_handler(lambda m: m.text in ["⭐ Поддержать", "⭐ Support"])
async def donate(message: types.Message):
    kb = InlineKeyboardMarkup().add(
        InlineKeyboardButton(t(message.from_user.id, "donate"), callback_data="donate")
    )
    await message.answer(t(message.from_user.id, "support_text"), reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == "donate")
async def donate_callback(callback: types.CallbackQuery):
    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title="Support",
        description="❤️",
        payload="donate",
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label="Support", amount=DONATE_AMOUNT)],
        start_parameter="donate"
    )

# ===== ПОДЕЛИТЬСЯ =====
@dp.message_handler(lambda m: m.text in ["📢 Поделиться", "📢 Share"])
async def share(message: types.Message):
    bot_username = (await bot.get_me()).username
    kb = InlineKeyboardMarkup().add(
        InlineKeyboardButton("📢 Share", url=f"https://t.me/{bot_username}")
    )
    await message.answer("🚀", reply_markup=kb)

# ===== ССЫЛКА =====
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
        # ===== YOUTUBE =====
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

        # ===== INSTAGRAM / TIKTOK =====
        else:
            ydl_opts = {'format': 'best', 'outtmpl': 'video.%(ext)s'}

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([message.text])

            video_file = glob.glob("video.*")[0]

            with open(video_file, "rb") as f:
                await message.answer_video(f)

            await after_download(user_id)

    except Exception as e:
        await message.answer(f"❌ {e}")

# ===== CALLBACK =====
@dp.callback_query_handler(lambda c: True)
async def callbacks(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = callback.data

    if user_id not in user_data:
        return

    url = user_data[user_id]["url"]

    await bot.send_message(user_id, "⏳ Downloading...")

    try:
        if data.startswith("video_"):
            q = data.split("_")[1]

            ydl_opts = {
                'format': f'best[height<={q}]'
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            files = glob.glob("video.*")

if not files:
    await bot.send_message(user_id, "❌ Ошибка загрузки видео")
    return

video_file = files[0]

            with open(video_file, "rb") as f:
                await bot.send_video(user_id, f)

        elif data == "mp3":
            ydl_opts = {
                'format': 'bestaudio',
                'outtmpl': 'audio.%(ext)s',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                }]
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            files = glob.glob("audio.*")

if not files:
    await bot.send_message(user_id, "❌ Ошибка загрузки аудио")
    return

audio_file = files[0]

            with open(audio_file, "rb") as f:
                await bot.send_audio(user_id, f)

        elif data == "preview":
            thumb = user_data[user_id]["info"].get("thumbnail")
            if thumb:
                await bot.send_photo(user_id, thumb)
            return

        await after_download(user_id)

    except Exception as e:
        await bot.send_message(user_id, f"❌ {e}")

# ===== ПОСЛЕ СКАЧИВАНИЯ =====
async def after_download(user_id):
    bot_username = (await bot.get_me()).username

    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("⭐ Support", callback_data="donate"),
        InlineKeyboardButton("📢 Share", url=f"https://t.me/{bot_username}")
    )

    await bot.send_message(
        user_id,
        f"🔥 Done!\n👥 {len(users)} users",
        reply_markup=kb
    )

# ===== ЗАПУСК =====
if __name__ == "__main__":
    while True:
        try:
            executor.start_polling(dp, skip_updates=True)
        except Exception as e:
            print("Ошибка:", e)
