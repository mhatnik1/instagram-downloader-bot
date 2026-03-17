import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, LabeledPrice
)
from aiogram.utils import executor

TOKEN = os.getenv("8730480600:AAEknl3n3W7Bm9KIz1oZO-aqj5GV6d0uAYs")

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

BOT_USERNAME = "@iGramDrop_Bot"  # ← сюда вставь username без @


# 🔹 Главное меню (нижние кнопки)
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton("📥 Скачать"), KeyboardButton("ℹ️ Помощь")],
    ],
    resize_keyboard=True
)


# 🔹 Кнопки под сообщением
inline_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="⭐ Поддержать", callback_data="donate_menu")],
    [InlineKeyboardButton(
        text="📨 Поделиться ботом",
        url=f"https://t.me/share/url?url=https://t.me/{BOT_USERNAME}&text=🔥 Попробуй этого бота для скачивания Instagram!"
    )]
])


# 🔹 Донат кнопки
donate_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="⭐ 1", callback_data="donate_1"),
        InlineKeyboardButton(text="⭐ 5", callback_data="donate_5")
    ],
    [
        InlineKeyboardButton(text="⭐ 10", callback_data="donate_10"),
        InlineKeyboardButton(text="⭐ 50", callback_data="donate_50")
    ]
])


# 🚀 START
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.answer(
        "👋 Отправь ссылку на Instagram и получи файл\n\n👇 Выбери действие:",
        reply_markup=main_keyboard
    )
    await message.answer("Выбери:", reply_markup=inline_menu)


# 📥 Скачать
@dp.message_handler(lambda message: message.text == "📥 Скачать")
async def download(message: types.Message):
    await message.answer("📩 Отправь ссылку на Instagram")


# ℹ️ Помощь
@dp.message_handler(lambda message: message.text == "ℹ️ Помощь")
async def help_cmd(message: types.Message):
    await message.answer("Просто отправь ссылку Instagram 👍")


# ⭐ Меню доната
@dp.callback_query_handler(lambda c: c.data == "donate_menu")
async def donate_menu(callback: types.CallbackQuery):
    await callback.message.answer(
        "❤️ Поддержи проект:",
        reply_markup=donate_keyboard
    )


# ⭐ Оплата
@dp.callback_query_handler(lambda c: c.data.startswith("donate_"))
async def donate(callback: types.CallbackQuery):
    amount = int(callback.data.split("_")[1])

    prices = [LabeledPrice(label="Support", amount=amount)]

    await bot.send_invoice(
        chat_id=callback.message.chat.id,
        title="Support ❤️",
        description="Спасибо за поддержку!",
        payload="donate",
        provider_token="",
        currency="XTR",
        prices=prices
    )


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
