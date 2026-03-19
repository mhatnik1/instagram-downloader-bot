import logging
import os
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
    LabeledPrice, BotCommand, MenuButtonCommands
)
import yt_dlp

API_TOKEN = "8730480600:AAFItJ_0cxbOLbVsCjmpGljoEUsns4jG1V8"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# ====== КНОПКИ ======
main_kb = ReplyKeyboardMarkup(resize_keyboard=True)
main_kb.add(
    KeyboardButton("📸 Instagram"),
    KeyboardButton("🎵 TikTok")
)
main_kb.add(
    KeyboardButton("🔄 Restart"),
    KeyboardButton("💎 Donate")
)

# ====== СТАРТ ======
@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    await message.answer_photo(
        photo=open("start.jpg", "rb"),  # твоя картинка
        caption="👋 Welcome!\n\n📥 Send me Instagram or TikTok link\n⚡ Fast download",
        reply_markup=main_kb
    )

# ====== DONATE ======
@dp.message_handler(lambda message: message.text == "💎 Donate")
async def donate(message: types.Message):
    prices = [LabeledPrice(label="Support bot", amount=100)]  # 100 stars

    await bot.send_invoice(
        chat_id=message.chat.id,
        title="Support the bot 💎",
        description="Donate to support development",
        payload="donate_payload",
        provider_token="",  # для Stars пусто
        currency="XTR",
        prices=prices
    )

# ====== ОБРАБОТКА ПЛАТЕЖА ======
@dp.pre_checkout_query_handler(lambda query: True)
async def pre_checkout(pre_checkout_q: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_q.id, ok=True)

@dp.message_handler(content_types=types.ContentType.SUCCESSFUL_PAYMENT)
async def successful_payment(message: types.Message):
    await message.answer("✅ Спасибо за донат!")

# ====== RESTART ======
@dp.message_handler(lambda message: message.text == "🔄 Restart")
async def restart(message: types.Message):
    await start_cmd(message)

# ====== СКАЧИВАНИЕ ======
def download_video(url):
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'noplaylist': True,
        'quiet': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        return filename

# ====== ЛОВИМ ССЫЛКИ ======
@dp.message_handler()
async def handle_message(message: types.Message):
    text = message.text

    if "instagram.com" in text or "tiktok.com" in text:
        await message.answer("⏳ Downloading...")

        try:
            file_path = download_video(text)

            with open(file_path, "rb") as video:
                await message.answer_video(video)

            os.remove(file_path)

        except Exception as e:
            print(e)
            await message.answer("❌ Download error, try again later")

    else:
        await message.answer("❗ Send Instagram or TikTok link")

# ====== МЕНЮ СЛЕВА ======
async def on_startup(dp):
    await bot.set_my_commands([
        BotCommand("start", "Start bot"),
        BotCommand("donate", "Support bot")
    ])

    await bot.set_chat_menu_button(
        menu_button=MenuButtonCommands()
    )

# ====== ЗАПУСК ======
if __name__ == '__main__':
    if not os.path.exists("downloads"):
        os.makedirs("downloads")

    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
