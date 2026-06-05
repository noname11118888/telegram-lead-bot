import os
import logging

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

from aiogram.webhook.aiohttp_server import (
    SimpleRequestHandler,
    setup_application
)

from aiohttp import web

# =========================
# CONFIG
# =========================

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is missing")

ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

WEBHOOK_PATH = f"/{TOKEN}"

RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")

WEBHOOK_URL = (
    f"{RENDER_EXTERNAL_URL}{WEBHOOK_PATH}"
    if RENDER_EXTERNAL_URL
    else None
)

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# =========================
# HANDLERS
# =========================

@dp.message(Command("start"))
async def start(message: types.Message):

    contact_button = KeyboardButton(
        text="Đăng ký nhận thông tin bằng SĐT",
        request_contact=True
    )

    reply_kb = ReplyKeyboardMarkup(
        keyboard=[[contact_button]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Tài liệu Telegram Ads",
                    url="https://docs.google.com/presentation/d/1KCLwdUHGvcv_gbLjPKBHklCGi7oT3kXF/edit?usp=sharing"
                )
            ]
        ]
    )

    await message.answer(
        "Chào bạn! Bạn có thể đăng ký nhận thông tin bằng nút bên dưới.",
        reply_markup=reply_kb
    )

    await message.answer(
        "Hoặc nhấn vào đây để xem tài liệu hướng dẫn:",
        reply_markup=inline_kb
    )


@dp.message(F.contact)
async def handle_contact(message: types.Message):

    phone = message.contact.phone_number
    user_name = message.contact.first_name

    try:

        if ADMIN_ID:

            await bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    "🔔 Thông tin khách hàng mới\n\n"
                    f"👤 Tên: {user_name}\n"
                    f"📞 SĐT: {phone}"
                )
            )

        status = "Thông tin đã được gửi tới quản trị viên!"

    except Exception as e:

        logging.exception(e)

        status = "Gửi thông tin thất bại."

    await message.answer(
        f"Cảm ơn! {status}",
        reply_markup=ReplyKeyboardRemove()
    )

    await message.answer(
        f"Bạn đã đăng ký thành công! Cảm ơn {user_name}",
        reply_markup=ReplyKeyboardRemove()
    )

# =========================
# HEALTH CHECK
# =========================

async def health(request):
    return web.Response(text="OK")


# =========================
# WEBHOOK
# =========================

async def on_startup(bot: Bot):

    if WEBHOOK_URL:

        await bot.set_webhook(
            url=WEBHOOK_URL,
            drop_pending_updates=False
        )

        logging.info(f"Webhook set: {WEBHOOK_URL}")

    else:

        logging.warning(
            "RENDER_EXTERNAL_URL not found. Webhook not set."
        )


def create_app():

    app = web.Application()

    app.router.add_get("/health", health)

    webhook_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot
    )

    webhook_handler.register(
        app,
        path=WEBHOOK_PATH
    )

    setup_application(
        app,
        dp,
        bot=bot
    )

    app.on_startup.append(
        lambda app: on_startup(bot)
    )

    return app


def main():

    app = create_app()

    port = int(os.getenv("PORT", "8080"))

    web.run_app(
        app,
        host="0.0.0.0",
        port=port
    )


if __name__ == "__main__":
    main()
