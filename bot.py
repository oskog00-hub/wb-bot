import asyncio
import os
import uuid
from datetime import date

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from yookassa import Payment, Configuration

# ================= ENV =================

TOKEN = os.getenv("TOKEN")
SHOP_ID = os.getenv("YOOKASSA_SHOP_ID")
SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY")

if not TOKEN:
    raise ValueError("TOKEN NOT FOUND")

if not SHOP_ID or not SECRET_KEY:
    raise ValueError("YOOKASSA CREDENTIALS NOT FOUND")

Configuration.account_id = SHOP_ID
Configuration.secret_key = SECRET_KEY

bot = Bot(token=TOKEN)
dp = Dispatcher()

FREE_LIMIT = 3
PRO_PRICE = 490

users = {}

# ================= HELPERS =================

def ensure_user(user_id):
    if user_id not in users:
        users[user_id] = {
            "pro": False,
            "used_today": 0,
            "last_date": str(date.today()),
            "payment_id": None
        }

    today = str(date.today())
    if users[user_id]["last_date"] != today:
        users[user_id]["used_today"] = 0
        users[user_id]["last_date"] = today


def pro_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="💳 Купить PRO", callback_data="buy_pro")
    return kb.as_markup()

# ================= START =================

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    ensure_user(user_id)

    await message.answer(
        "📊 WB Калькулятор\n\n"
        "3 расчёта в день бесплатно\n"
        "PRO — без ограничений",
        reply_markup=pro_keyboard()
    )

# ================= BUY PRO =================

@dp.callback_query(lambda c: c.data == "buy_pro")
async def buy_pro(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    ensure_user(user_id)

    payment = Payment.create({
        "amount": {
            "value": str(PRO_PRICE),
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": "https://t.me/"
        },
        "capture": True,
        "description": f"PRO доступ {user_id}"
    }, uuid.uuid4())

    users[user_id]["payment_id"] = payment.id

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Оплатить", url=payment.confirmation.confirmation_url)],
        [InlineKeyboardButton(text="✅ Я оплатил", callback_data="check_payment")]
    ])

    await callback.message.answer(
        f"🔥 PRO — {PRO_PRICE} ₽\n\n"
        "После оплаты нажмите «Я оплатил»",
        reply_markup=keyboard
    )

    await callback.answer()

# ================= CHECK PAYMENT =================

@dp.callback_query(lambda c: c.data == "check_payment")
async def check_payment(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    ensure_user(user_id)

    payment_id = users[user_id]["payment_id"]

    if not payment_id:
        await callback.answer("Платёж не найден", show_alert=True)
        return

    payment = Payment.find_one(payment_id)

    if payment.status == "succeeded":
        users[user_id]["pro"] = True
        await callback.message.answer("🔥 PRO активирован!")
    else:
        await callback.message.answer("❌ Платёж ещё не подтверждён")

    await callback.answer()

# ================= CALCULATOR =================

@dp.message()
async def calculator(message: types.Message):
    user_id = message.from_user.id
    ensure_user(user_id)

    user = users[user_id]

    try:
        price = float(message.text.replace(",", "."))
    except:
        await message.answer("Введите цену числом")
        return

    if not user["pro"]:
        if user["used_today"] >= FREE_LIMIT:
            await message.answer(
                "⛔ Лимит бесплатных расчётов исчерпан.\n"
                "Оформите PRO."
            )
            return
        user["used_today"] += 1

    # Простейшая модель расчёта
    cost = price * 0.7
    profit = price - cost
    margin = (profit / price) * 100

    if user["pro"]:
        status_text = "🔥 PRO режим"
    else:
        remaining = FREE_LIMIT - user["used_today"]
        status_text = f"Осталось: {remaining}"

    await message.answer(
        f"💰 Прибыль: {profit:.0f} ₽\n"
        f"📈 Маржа: {margin:.1f}%\n\n"
        f"{status_text}"
    )

# ================= MAIN =================

async def main():
    print("🚀 BOT STARTED")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
