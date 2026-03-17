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

bot = Bot(token=TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

BOT_NAME = "iGramDrop"

# ===== START =====
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📸 Instagram", "🎵 TikTok")
    kb.row("🔄 Restart", "💎 Donate")

    photo = InputFile("photo_2026-03-17 17.40.44.jpeg")

    text = (
        f"👋 <b>{BOT_NAME}</b>\n\n"
        "📥 Instagram • TikTok\n"
        "🎬 Фото • Видео • Карусели\n\n"
        "⚡ Отправь ссылку и я всё скачаю"
    )

    await message.answer_photo(photo, caption=text, reply_markup=kb)

# ===== RESTART =====
@dp.message_handler(lambda m: m.text == "🔄 Restart")
async def restart(message: types.Message):
    await start(message)

# ===== DONATE =====
@dp.message_handler(lambda m: m.text == "💎 Donate")
async def donate(message: types.Message):
    kb = InlineKeyboardMarkup(row_width=3)
    kb.add(
        InlineKeyboardButton("❤️ 50⭐", callback_data="donate_50"),
        InlineKeyboardButton("🔥 100⭐", callback_data="donate_100"),
        InlineKeyboardButton("👑 250⭐", callback_data="donate_250"),
    )
    await message.answer("💎 Поддержать проект", reply_markup=kb)

# ===== LINK =====
@dp.message_handler(lambda m: m.text and "http" in m.text)
async def download(message: types.Message):
    url = message.text
    user_id = message.from_user.id

    msg = await message.answer("⏳ Скачиваю...")

    try:
        ydl_opts = {
            'outtmpl': 'media.%(ext)s',
            'format': 'best',
            'quiet': True,
            'noplaylist': False
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        files = glob.glob("media.*")

        if not files:
            await msg.edit_text("❌ Не удалось скачать")
            return

        for file in files:
            size = os.path.getsize(file)

            with open(file, "rb") as f:
                if size > 49 * 1024 * 1024:
                    await bot.send_document(user_id, f)
                else:
                    await bot.send_video(user_id, f)

            os.remove(file)

        await msg.delete()

        # ===== AFTER DOWNLOAD =====
        kb = InlineKeyboardMarkup(row_width=3)
        kb.add(
            InlineKeyboardButton("❤️ 50⭐", callback_data="donate_50"),
            InlineKeyboardButton("🔥 100⭐", callback_data="donate_100"),
            InlineKeyboardButton("👑 250⭐", callback_data="donate_250"),
        )

        kb.add(
            InlineKeyboardButton("📢 Share", url=f"https://t.me/{(await bot.get_me()).username}")
        )

        await bot.send_message(
            user_id,
            f"🔥 Готово!\n\n🙏 Поддержать {BOT_NAME}?",
            reply_markup=kb
        )

    except Exception as e:
        await msg.edit_text("❌ Ошибка скачивания")

# ===== CALLBACK =====
@dp.callback_query_handler(lambda c: c.data.startswith("donate"))
async def donate_callback(callback: types.CallbackQuery):
    await callback.answer("Спасибо ❤️")

# ===== RUN =====
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
