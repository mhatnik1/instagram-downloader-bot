import os
import glob
import yt_dlp
from aiogram import Bot, Dispatcher, types
from aiogram.types import (
    ReplyKeyboardMarkup, InlineKeyboardMarkup,
    InlineKeyboardButton, LabeledPrice, InputFile
)
from aiogram.utils import executor

TOKEN = os.getenv("TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

users = set()
user_data = {}
user_platform = {}
user_lang = {}

# ===== УБИРАЕМ WEBHOOK =====
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
    users.add(user_id)

    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📸 Instagram", "🎵 TikTok", "▶️ YouTube")

    # ===== ПЕРСОНАЖ =====
    if user_lang[user_id] == "ru":

        text = (
            "👋 Привет! Я Dropix\n\n"
            "🤖 Твой личный помощник для скачивания контента\n\n"
            "📥 Я помогу тебе скачать:\n"
            "📸 Instagram • 🎵 TikTok • ▶️ YouTube\n\n"
            "⚡ Просто отправь ссылку — и я всё сделаю за тебя\n\n"
            "🔥 Быстро. Просто. Без лишнего."
        )

        photo = InputFile("/mnt/data/0C31C239-D120-45A6-9A5D-580525088A1A.jpeg")

    else:

        text = (
            "👋 Hey! I'm Dropix\n\n"
            "🤖 Your personal download assistant\n\n"
            "📥 I can download from:\n"
            "📸 Instagram • 🎵 TikTok • ▶️ YouTube\n\n"
            "⚡ Just send me a link — I’ll handle everything\n\n"
            "🔥 Fast. Simple. No hassle."
        )

        photo = InputFile("/mnt/data/973C20F9-1D64-449E-9D1C-B596684A9432.jpeg")

    await message.answer_photo(photo, caption=text, reply_markup=kb)

# ===== PLATFORM =====
@dp.message_handler(lambda m: m.text in ["📸 Instagram", "🎵 TikTok", "▶️ YouTube"])
async def choose_platform(message: types.Message):
    user_platform[message.from_user.id] = message.text
    await message.answer("📥 Send link" if user_lang.get(message.from_user.id) == "en" else "📥 Отправь ссылку")

# ===== LINK =====
@dp.message_handler(lambda m: "http" in m.text)
async def handle_link(message: types.Message):
    user_id = message.from_user.id

    platform = user_platform.get(user_id)

    if not platform:
        await message.answer("❌ Choose platform first")
        return

    await message.answer("⏳ Processing..." if user_lang.get(user_id) == "en" else "⏳ Обрабатываю...")

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

            await message.answer("Choose quality:" if user_lang.get(user_id) == "en" else "Выбери качество:", reply_markup=kb)

        else:
            ydl_opts = {'format': 'best', 'outtmpl': 'video.%(ext)s'}

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([message.text])

            file = glob.glob("video.*")[0]

            with open(file, "rb") as f:
                await message.answer_video(f)

            os.remove(file)
            await after_download(user_id)

    except Exception as e:
        await message.answer(f"❌ {e}")

# ===== CALLBACK =====
@dp.callback_query_handler(lambda c: True)
async def callbacks(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = callback.data

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

            file = glob.glob("video.*")[0]

            with open(file, "rb") as f:
                await bot.send_video(user_id, f)

            os.remove(file)

        elif data == "mp3":
            ydl_opts = {
                'format': 'bestaudio',
                'outtmpl': 'audio.%(ext)s'
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            file = glob.glob("audio.*")[0]

            with open(file, "rb") as f:
                await bot.send_audio(user_id, f)

            os.remove(file)

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
        text = "🔥 Готово!\n\n🙏 Хочешь поддержать Dropix?"

        kb.add(
            InlineKeyboardButton("❤️ 50⭐", callback_data="donate_50"),
            InlineKeyboardButton("🔥 100⭐", callback_data="donate_100"),
            InlineKeyboardButton("👑 250⭐", callback_data="donate_250"),
        )

    else:
        text = "🔥 Done!\n\n🙏 Want to support Dropix?"

        kb.add(
            InlineKeyboardButton("❤️ $0.5", callback_data="donate_50"),
            InlineKeyboardButton("🔥 $1", callback_data="donate_100"),
            InlineKeyboardButton("👑 $2.5", callback_data="donate_250"),
        )

    kb.add(
        InlineKeyboardButton("📢 Share bot", url=f"https://t.me/{bot_username}")
    )

    await bot.send_message(user_id, text, reply_markup=kb)

# ===== RUN =====
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
    @dp.message_handler(content_types=['photo'])
async def get_file_id(message: types.Message):
    file_id = message.photo[-1].file_id
    await message.answer(f"FILE_ID:\n{file_id}")
