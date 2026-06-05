import os
import logging

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    BotCommand,
    WebAppInfo
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
WEBHOOK_URL = f"{RENDER_EXTERNAL_URL}{WEBHOOK_PATH}" if RENDER_EXTERNAL_URL else None

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# =========================
# MENU & COMMANDS
# =========================

# async def set_main_menu(bot: Bot):
#     commands = [
#         BotCommand(command="start", description="Khởi động bot"),
#         BotCommand(command="webapp", description="Mở ứng dụng Mini App")
#     ]
#     await bot.set_my_commands(commands)

# =========================
# HANDLERS
# =========================

@dp.message(Command("start"))
async def start(message: types.Message):
    # Nút bấm luôn hiện (one_time_keyboard=False)
    contact_button = KeyboardButton(text="Đăng ký nhận thông tin bằng SĐT", request_contact=True)
    docs_button = KeyboardButton(text="Tài liệu Telegram Ads")
    
    reply_kb = ReplyKeyboardMarkup(
        keyboard=[[contact_button], [docs_button]],
        resize_keyboard=True,
        one_time_keyboard=False 
    )

    await message.answer(
        "Chào bạn! Vui lòng chọn tính năng bên dưới:",
        reply_markup=reply_kb
    )

@dp.message(F.text == "Tài liệu Telegram Ads")
async def send_docs(message: types.Message):
    await message.answer(
        "Bạn có thể xem tài liệu tại đây:\n"
        "https://docs.google.com/presentation/d/1KCLwdUHGvcv_gbLjPKBHklCGi7oT3kXF/edit?usp=sharing"
    )

@dp.message(Command("webapp"))
async def open_webapp(message: types.Message):
    # Thay URL bên dưới bằng địa chỉ Mini App của bạn
    web_app_url = "https://docs.google.com/presentation/d/1KCLwdUHGvcv_gbLjPKBHklCGi7oT3kXF/edit?usp=sharing"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Mở Mini App", web_app=WebAppInfo(url=web_app_url))]
    ])
    await message.answer("Nhấn nút dưới để mở ứng dụng:", reply_markup=kb)

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

    await message.answer(f"Cảm ơn {user_name}! {status}")

# =========================
# WEBHOOK & STARTUP
# =========================

async def on_startup(bot: Bot):
    await set_main_menu(bot) # Cài đặt menu khi khởi động
    if WEBHOOK_URL:
        await bot.set_webhook(url=WEBHOOK_URL, drop_pending_updates=False)
        logging.info(f"Webhook set: {WEBHOOK_URL}")

# ... (Giữ nguyên phần health check và create_app như code cũ của bạn)

def create_app():
    app = web.Application()
    app.router.add_get("/health", lambda r: web.Response(text="OK"))
    webhook_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_handler.register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)
    app.on_startup.append(lambda app: on_startup(bot))
    return app

if __name__ == "__main__":
    app = create_app()
    port = int(os.getenv("PORT", "8080"))
    web.run_app(app, host="0.0.0.0", port=port)
