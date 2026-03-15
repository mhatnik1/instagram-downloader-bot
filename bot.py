import asyncio
import instaloader
import requests
import os

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8730480600:AAHh_ZI7_hzQDAtktFLH-xlmF6MS0cXRxNM"
BOT_USERNAME = "@iGramDrop_Bot"

bot = Bot(token=TOKEN)
dp = Dispatcher()

L = instaloader.Instaloader()

users = set()
mode = {}

# Главное меню
start_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="📷 Скачать фото", callback_data="photo")],
        [InlineKeyboardButton(text="🎬 Скачать видео / Reels", callback_data="video")],
        [InlineKeyboardButton(text="1⭐ Поддержать", callback_data="donate")],
        [InlineKeyboardButton(text="🔗 Поделиться ботом", url=f"https://t.me/{BOT_USERNAME}")]
    ]
)

# Кнопки под файлом
share_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="1⭐ Поддержать", callback_data="donate")],
        [InlineKeyboardButton(text="🔗 Поделиться ботом", url=f"https://t.me/{BOT_USERNAME}")]
    ]
)


@dp.message(Command("start"))
async def start(message: types.Message):

    users.add(message.from_user.id)

    await message.answer(
        "👋 Добро пожаловать в *iGramDrop*\n\n"
        "📥 Скачивайте фото и видео из Instagram\n"
        "⚡ Просто отправьте ссылку\n\n"
        f"👥 Пользователей: {len(users)}",
        reply_markup=start_keyboard,
        parse_mode="Markdown"
    )


@dp.callback_query(lambda c: c.data == "photo")
async def choose_photo(callback: types.CallbackQuery):

    mode[callback.from_user.id] = "photo"

    await callback.message.answer(
        "📷 Отправьте ссылку на фото из Instagram"
    )

    await callback.answer()


@dp.callback_query(lambda c: c.data == "video")
async def choose_video(callback: types.CallbackQuery):

    mode[callback.from_user.id] = "video"

    await callback.message.answer(
        "🎬 Отправьте ссылку на видео или Reels"
    )

    await callback.answer()


# Донат Telegram Stars
@dp.callback_query(lambda c: c.data == "donate")
async def donate(callback: types.CallbackQuery):

    prices = [types.LabeledPrice(label="Support", amount=1)]

    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title="Поддержать бота ⭐",
        description="Отправьте 1 Telegram Star чтобы поддержать развитие бота",
        payload="donate-stars",
        provider_token="",
        currency="XTR",
        prices=prices
    )

    await callback.answer()


# Обязательная часть для оплаты
@dp.pre_checkout_query()
async def pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery):

    await bot.answer_pre_checkout_query(
        pre_checkout_query.id,
        ok=True
    )


# Подтверждение оплаты
@dp.message(lambda message: message.successful_payment)
async def successful_payment(message: types.Message):

    await message.answer(
        "⭐ Спасибо за поддержку!\n\n"
        "Вы отправили 1 Telegram Star ❤️"
    )


# Скачивание Instagram
@dp.message()
async def download(message: types.Message):

    if message.from_user.id not in mode:
        await message.answer("Нажмите /start чтобы начать")
        return

    url = message.text

    if "instagram.com" not in url:
        await message.answer("❌ Отправьте правильную ссылку Instagram")
        return

    try:

        shortcode = url.split("/")[-2]

        post = instaloader.Post.from_shortcode(L.context, shortcode)

        if post.is_video:
            media_url = post.video_url
            filename = "video.mp4"
        else:
            media_url = post.url
            filename = "photo.jpg"

        r = requests.get(media_url)

        with open(filename, "wb") as f:
            f.write(r.content)

        if post.is_video:

            await message.answer_video(
                types.FSInputFile(filename),
                reply_markup=share_keyboard
            )

        else:

            await message.answer_photo(
                types.FSInputFile(filename),
                reply_markup=share_keyboard
            )

        os.remove(filename)

    except Exception as e:
        print(e)

        await message.answer("❌ Ошибка скачивания")


async def main():

    print("Бот запущен 🚀")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())