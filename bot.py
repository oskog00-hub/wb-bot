import asyncio
import os
import uuid
import aiosqlite
from datetime import date

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

from yookassa import Configuration, Payment


# ---------------- НАСТРОЙКИ ----------------

TOKEN = os.getenv("TOKEN")
YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID")
YOOKASSA_SECRET = os.getenv("YOOKASSA_SECRET")

if not TOKEN:
    print("TOKEN NOT FOUND")
    exit()

print("BOT STARTED")

Configuration.account_id = YOOKASSA_SHOP_ID
Configuration.secret_key = YOOKASSA_SECRET

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

DB = "bot.db"
FREE_LIMIT = 5  # бесплатных расчетов


# ---------------- БАЗА ----------------

async def init_db():
    async with aiosqlite.connect(DB) as db:

        await db.execute("""
        CREATE TABLE IF NOT EXISTS users(
            user_id INTEGER PRIMARY KEY,
            pro INTEGER DEFAULT 0
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS usage(
            user_id INTEGER,
            calc_date TEXT,
            count INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, calc_date)
        )
        """)

        await db.commit()


# ---------------- FSM ----------------

class Calc(StatesGroup):
    price = State()
    cost = State()
    commission = State()


# ---------------- ПРОВЕРКА ЛИМИТА ----------------

async def check_limit(user_id):

    async with aiosqlite.connect(DB) as db:

        cur = await db.execute("SELECT pro FROM users WHERE user_id=?", (user_id,))
        row = await cur.fetchone()

        if row and row[0] == 1:
            return True

        today = str(date.today())

        cur = await db.execute(
            "SELECT count FROM usage WHERE user_id=? AND calc_date=?",
            (user_id, today)
        )
        row = await cur.fetchone()

        if not row:
            await db.execute(
                "INSERT INTO usage (user_id, calc_date, count) VALUES (?, ?, 1)",
                (user_id, today)
            )
            await db.commit()
            return True

        if row[0] >= FREE_LIMIT:
            return False

        await db.execute(
            "UPDATE usage SET count=count+1 WHERE user_id=? AND calc_date=?",
            (user_id, today)
        )
        await db.commit()
        return True


# ---------------- START ----------------

@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):

    user_id = message.from_user.id

    async with aiosqlite.connect(DB) as db:
        await db.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
        await db.commit()

    await state.clear()
    await state.set_state(Calc.price)

    await message.answer(
        "💰 WB Калькулятор прибыли\n\n"
        "Введи цену продажи товара (₽)"
    )


# ---------------- ЦЕНА ----------------

@dp.message(Calc.price)
async def get_price(message: types.Message, state: FSMContext):
    try:
        price = float(message.text.replace(",", "."))
    except:
        await message.answer("Введите число")
        return

    await state.update_data(price=price)
    await state.set_state(Calc.cost)
    await message.answer("📦 Введите себестоимость товара (₽)")


# ---------------- СЕБЕСТОИМОСТЬ ----------------

@dp.message(Calc.cost)
async def get_cost(message: types.Message, state: FSMContext):
    try:
        cost = float(message.text.replace(",", "."))
    except:
        await message.answer("Введите число")
        return

    await state.update_data(cost=cost)
    await state.set_state(Calc.commission)
    await message.answer("📊 Введите комиссию WB (%)")


# ---------------- РАСЧЕТ ----------------

@dp.message(Calc.commission)
async def calc(message: types.Message, state: FSMContext):

    user_id = message.from_user.id
    allowed = await check_limit(user_id)

    if not allowed:
        await message.answer(
            "⛔ Лимит бесплатных расчетов (5/день) исчерпан\n\n"
            "Хочешь PRO без лимита?\n"
            "Напиши: ХОЧУ PRO"
        )
        await state.clear()
        return

    try:
        commission_percent = float(message.text.replace(",", "."))
    except:
        await message.answer("Введите число")
        return

    data = await state.get_data()
    price = data["price"]
    cost = data["cost"]

    commission = price * (commission_percent / 100)
    acquiring = price * 0.02
    tax = price * 0.06
    logistics = 150

    profit = price - commission - acquiring - tax - logistics - cost
    margin = (profit / cost * 100) if cost > 0 else 0

    total_percent = commission_percent / 100 + 0.08
    break_even = (cost + logistics) / (1 - total_percent) if total_percent < 1 else 0

    await message.answer(
        f"📊 Расчет WB\n\n"
        f"💰 Прибыль: {profit:.0f} ₽\n"
        f"📈 Маржа: {margin:.1f}%\n"
        f"⚖️ Точка 0: {break_even:.0f} ₽"
    )

    await state.clear()


# ---------------- ХОЧУ PRO ----------------

@dp.message(lambda m: m.text and "ХОЧУ PRO" in m.text.upper())
async def want_pro(message: types.Message):
    await message.answer(
        "💎 PRO доступ — 490₽/месяц\n\n"
        "Безлимитные расчеты\n"
        "Точка безубыточности\n\n"
        "Напиши: ОПЛАТА"
    )


# ---------------- ОПЛАТА ----------------

@dp.message(lambda m: m.text and "ОПЛАТА" in m.text.upper())
async def buy_pro(message: types.Message):

    payment = Payment.create({
        "amount": {"value": "490.00", "currency": "RUB"},
        "confirmation": {
            "type": "redirect",
            "return_url": "https://t.me/wbmarging_bot"
        },
        "capture": True,
        "description": "PRO доступ к WB боту"
    }, str(uuid.uuid4()))

    url = payment.confirmation.confirmation_url

    await message.answer(
        f"💳 Оплатить PRO:\n\n{url}\n\n"
        "После оплаты напиши: ОПЛАТИЛ"
    )


# ---------------- АКТИВАЦИЯ PRO ----------------

@dp.message(lambda m: m.text and "ОПЛАТИЛ" in m.text.upper())
async def activate_pro(message: types.Message):

    user_id = message.from_user.id

    async with aiosqlite.connect(DB) as db:
        await db.execute("UPDATE users SET pro=1 WHERE user_id=?", (user_id,))
        await db.commit()

    await message.answer("🔥 PRO активирован! Безлимит включен.")


# ---------------- ЗАПУСК ----------------

async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
