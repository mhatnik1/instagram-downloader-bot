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

ADMIN_ID = 5151695449  # <-- ВСТАВЬ СВОЙ ID

settings = {
    "donate_amount": 10000
}

users = set()

# ===== КНОПКИ =====

platform_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
platform_keyboard.add(
    KeyboardButton("📸 Instagram"),
    KeyboardButton("🎵 TikTok"),
    KeyboardButton("▶️ YouTube")
)
platform_keyboard.add(
    KeyboardButton("⭐ Поддержать"),
    KeyboardButton("📢 Поделиться")
)

# ===== START =====
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    users.add(message.from_user.id)

    await message.answer(
        "🚀 Выбери платформу:\n\n"
        "📸 Instagram\n🎵 TikTok\n▶️ YouTube\n\n"
        "⬇️ Скачивай в максимальном качестве",
        reply_markup=platform_keyboard
    )

# ===== ДОНАТ =====
@dp.message_handler(lambda m: m.text == "⭐ Поддержать")
async def donate(message: types.Message):
    kb = InlineKeyboardMarkup().add(
        InlineKeyboardButton("⭐ Поддержать", callback_data="donate")
    )

    await message.answer(
        "💎 Бот бесплатный\nПоддержка по желанию ❤️",
        reply_markup=kb
    )

@dp.callback_query_handler(lambda c: c.data == "donate")
async def donate_handler(callback_query: types.CallbackQuery):
    await bot.send_invoice(
        chat_id=callback_query.from_user.id,
        title="Поддержка",
        description="Спасибо ❤️",
        payload="donate",
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label="Поддержка", amount=settings["donate_amount"])],
        start_parameter="donate"
    )

# ===== ПОДЕЛИТЬСЯ =====
@dp.message_handler(lambda m: m.text == "📢 Поделиться")
async def share(message: types.Message):
    bot_username = (await bot.get_me()).username

    kb = InlineKeyboardMarkup().add(
        InlineKeyboardButton(
            "📢 Отправить другу",
            url=f"https://t.me/{bot_username}"
        )
    )

    await message.answer("Поделись ботом 🚀", reply_markup=kb)

# ===== ВЫБОР ПЛАТФОРМЫ =====
user_platform = {}

@dp.message_handler(lambda m: m.text in ["📸 Instagram", "🎵 TikTok", "▶️ YouTube"])
async def choose_platform(message: types.Message):
    user_platform[message.from_user.id] = message.text

    await message.answer("📥 Отправь ссылку")

# ===== СКАЧИВАНИЕ =====
def download_video(url):
    ydl_opts = {
        'outtmpl': 'video.%(ext)s',
        'format': 'best'
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    return "video.mp4"

@dp.message_handler(lambda m: "http" in m.text)
async def download_handler(message: types.Message):
    users.add(message.from_user.id)

    await message.answer("⏳ Загружаю...")

    try:
        file_path = download_video(message.text)

        with open(file_path, "rb") as video:
            await message.answer_video(video)

        # КНОПКА ШАРИНГА
        bot_username = (await bot.get_me()).username

        kb = InlineKeyboardMarkup().add(
            InlineKeyboardButton(
                "📢 Поделиться ботом",
                url=f"https://t.me/{bot_username}"
            )
        )

        await message.answer(
            "🔥 Понравилось? Поделись с другом:",
            reply_markup=kb
        )

    except Exception as e:
        await message.answer("❌ Ошибка загрузки")

# ===== ЗАПУСК =====
if __name__ == "__main__":
    while True:
        try:
            executor.start_polling(dp, skip_updates=True)
        except Exception as e:
            print("Ошибка:", e)
