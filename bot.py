import glob
import os
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
user_actions = {}
user_platform = {}
user_lang = {}

DONATE_AMOUNT = 10000

# ===== ПЕРЕВОДЫ =====
TEXTS = {
    "ru": {
        "start": "🚀 MULTI DOWNLOADER\n\n📥 Выбери платформу\n👥 Уже 1000+ пользователей",
        "choose_lang": "🌍 Выбери язык",
        "send_link": "📥 Отправь ссылку",
        "processing": "⏳ Обрабатываю...",
        "error": "❌ Ошибка",
        "choose_quality": "📥 Выбери качество:",
        "done": "🔥 Готово!\n\n❤️ Бот бесплатный — поддержка по желанию",
        "donate": "⭐ Поддержать",
        "share": "📢 Поделиться",
        "support_text": "💎 Бот бесплатный\nПоддержка по желанию ❤️"
    },
    "en": {
        "start": "🚀 MULTI DOWNLOADER\n\n📥 Choose platform\n👥 1000+ users",
        "choose_lang": "🌍 Choose language",
        "send_link": "📥 Send link",
        "processing": "⏳ Processing...",
        "error": "❌ Error",
        "choose_quality": "📥 Choose quality:",
        "done": "🔥 Done!\n\n❤️ Bot is free — support optional",
        "donate": "⭐ Support",
        "share": "📢 Share",
        "support_text": "💎 Bot is free\nSupport if you want ❤️"
    }
}

def t(user_id, key):
    lang = user_lang.get(user_id, "ru")
    return TEXTS[lang][key]

# ===== ЯЗЫК =====
lang_kb = ReplyKeyboardMarkup(resize_keyboard=True)
lang_kb.add("🇷🇺 Русский", "🇬🇧 English")

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("🌍 Choose language / Выбери язык", reply_markup=lang_kb)

@dp.message_handler(lambda m: m.text in ["🇷🇺 Русский", "🇬🇧 English"])
async def set_lang(message: types.Message):
    user_id = message.from_user.id

    if "Русский" in message.text:
        user_lang[user_id] = "ru"
    else:
        user_lang[user_id] = "en"

    users.add(user_id)

    kb = get_main_kb(user_id)

    await message.answer(t(user_id, "start"), reply_markup=kb)

# ===== КНОПКИ =====
def get_main_kb(user_id):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(
        KeyboardButton("📸 Instagram"),
        KeyboardButton("🎵 TikTok"),
        KeyboardButton("▶️ YouTube")
    )
    kb.add(
        KeyboardButton(t(user_id, "donate")),
        KeyboardButton(t(user_id, "share"))
    )
    return kb

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
        InlineKeyboardButton(
            t(message.from_user.id, "share"),
            url=f"https://t.me/{bot_username}"
        )
    )
    await message.answer("🚀", reply_markup=kb)

# ===== ССЫЛКА =====
@dp.message_handler(lambda m: "http" in m.text)
async def handle_link(message: types.Message):
    user_id = message.from_user.id
    users.add(user_id)

    platform = user_platform.get(user_id)

    if not platform:
        await message.answer("❌")
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

            video_file = glob.glob("video.*")[0]

with open(video_file, "rb") as f:
                await message.answer_video(f)

            await after_download(user_id)

    except:
        await message.answer(t(user_id, "error"))

# ===== CALLBACK =====
@dp.callback_query_handler(lambda c: True)
async def callbacks(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = callback.data

    if user_id not in user_data:
        return

    url = user_data[user_id]["url"]

    try:
        if data.startswith("video_"):
    q = data.split("_")[1]

    ydl_opts = {
        'format': f'bestvideo[height<={q}]+bestaudio/best',
        'outtmpl': 'video.%(ext)s',
        'merge_output_format': 'mp4'
    }
            q = data.split("_")[1]
            ydl_opts = {
                'format': f'bestvideo[height<={q}]+bestaudio/best',
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
            thumb = user_data[user_id]["info"].get("thumbnail")
            if thumb:
                await bot.send_photo(user_id, thumb)
            return

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        with open(filename, "rb") as f:
            if data == "mp3":
                await bot.send_audio(user_id, f)
            else:
                await bot.send_video(user_id, f)

        await after_download(user_id)

    except:
        await bot.send_message(user_id, t(user_id, "error"))

# ===== ПОСЛЕ СКАЧИВАНИЯ =====
async def after_download(user_id):
    bot_username = (await bot.get_me()).username

    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton(t(user_id, "donate"), callback_data="donate"),
        InlineKeyboardButton(t(user_id, "share"), url=f"https://t.me/{bot_username}")
    )

    await bot.send_message(
        user_id,
        f"{t(user_id, 'done')}\n\n👥 {len(users)} users",
        reply_markup=kb
    )

# ===== ЗАПУСК =====
if __name__ == "__main__":
    while True:
        try:
            executor.start_polling(dp, skip_updates=True)
        except Exception as e:
            print("Ошибка:", e)
