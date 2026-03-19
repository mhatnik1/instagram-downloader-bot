import os
import glob
import yt_dlp
from aiogram import Bot, Dispatcher, types
from aiogram.types import (
    ReplyKeyboardMarkup, InlineKeyboardMarkup,
    InlineKeyboardButton, InputFile, LabeledPrice,
    BotCommand, MenuButtonCommands
)
from aiogram.utils import executor

TOKEN = os.getenv("TOKEN")

bot = Bot(token=TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

BOT_NAME = "iGramDrop"

# ===== STARTUP =====
async def on_startup(dp):
    # команды
    commands = [
        BotCommand("start", "Start bot"),
        BotCommand("donate", "Support bot"),
    ]
    await bot.set_my_commands(commands)

    # кнопка меню слева
    await bot.set_chat_menu_button(
        menu_button=MenuButtonCommands()
    )

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

# ===== DONATE MENU =====
@dp.message_handler(lambda m: m.text == "💎 Donate")
async def donate(message: types.Message):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("❤️ 50 Stars", callback_data="donate_50"),
        InlineKeyboardButton("🔥 100 Stars", callback_data="donate_100"),
        InlineKeyboardButton("👑 250 Stars", callback_data="donate_250"),
    )
    await message.answer("💎 Choose amount:", reply_markup=kb)

# ===== DONATE CALLBACK =====
@dp.callback_query_handler(lambda c: c.data.startswith("donate"))
async def donate_callback(callback: types.CallbackQuery):
    amount = int(callback.data.split("_")[1])

    prices = [LabeledPrice(label="Stars", amount=amount)]

    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title="Support iGramDrop 💎",
        description="Thank you for your support!",
        payload="donate_payload",
        provider_token="",
        currency="XTR",
        prices=prices
    )

    await callback.answer()

# ===== PRE CHECKOUT =====
@dp.pre_checkout_query_handler(lambda query: True)
async def pre_checkout(pre_checkout_q: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_q.id, ok=True)

# ===== SUCCESS PAYMENT =====
@dp.message_handler(content_types=types.ContentType.SUCCESSFUL_PAYMENT)
async def successful_payment(message: types.Message):
    await message.answer("🔥 Payment successful! Thank you ❤️")

# ===== DOWNLOAD =====
@dp.message_handler(lambda m: m.text and "http" in m.text)
async def download(message: types.Message):
    url = message.text
    user_id = message.from_user.id

    msg = await message.answer("⏳ Downloading...")

    try:
        ydl_opts = {
            'outtmpl': 'media.%(ext)s',
            'format': 'best',
            'quiet': True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(url, download=True)

        files = glob.glob("media.*")

        if not files:
            await msg.edit_text("❌ Failed to download")
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

        kb = InlineKeyboardMarkup(row_width=1)
        kb.add(
            InlineKeyboardButton("❤️ 50 Stars", callback_data="donate_50"),
            InlineKeyboardButton("🔥 100 Stars", callback_data="donate_100"),
            InlineKeyboardButton("👑 250 Stars", callback_data="donate_250"),
        )

        await bot.send_message(
            user_id,
            f"🔥 Done!\n\n💎 Support {BOT_NAME}?",
            reply_markup=kb
        )

    except:
        await msg.edit_text("❌ Download error")

# ===== RUN =====
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
