import asyncio
import os
import aiosqlite
from datetime import date

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message

TOKEN = os.getenv("TOKEN")

if not TOKEN:
    raise ValueError("TOKEN NOT FOUND")

bot = Bot(token=TOKEN)
dp = Dispatcher()

DB = "users.db"
FREE_LIMIT = 3

# твой Telegram ID
ADMIN_ID = 804249688


async def init_db():
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users(
            user_id INTEGER PRIMARY KEY,
            used_today INTEGER DEFAULT 0,
            last_reset TEXT
        )
        """)
        await db.commit()


async def check_limit(user_id):

    if user_id == ADMIN_ID:
        return True

    today = date.today().isoformat()

    async with aiosqlite.connect(DB) as db:

        cur = await db.execute(
            "SELECT used_today,last_reset FROM users WHERE user_id=?",
            (user_id,)
        )

        user = await cur.fetchone()

        if not user:

            await db.execute(
                "INSERT INTO users(user_id,used_today,last_reset) VALUES(?,?,?)",
                (user_id, 0, today)
            )

            await db.commit()
            return True

        used, last = user

        if last != today:

            await db.execute(
                "UPDATE users SET used_today=0,last_reset=? WHERE user_id=?",
                (today, user_id)
            )

            await db.commit()

            used = 0

        if used >= FREE_LIMIT:
            return False

        await db.execute(
            "UPDATE users SET used_today=used_today+1 WHERE user_id=?",
            (user_id,)
        )

        await db.commit()

        return True


@dp.message(CommandStart())
async def start(message: Message):

    text = (
        "📊 WB Калькулятор прибыли\n\n"
        "Введите:\n"
        "Цена Себестоимость Комиссия%\n\n"
        "Пример:\n"
        "2000 800 15"
    )

    await message.answer(text)


@dp.message()
async def calculator(message: Message):

    user_id = message.from_user.id

    allowed = await check_limit(user_id)

    if not allowed:

        await message.answer(
            "🚫 Лимит 3 расчёта в день\n\n"
            "Купите PRO чтобы снять лимит."
        )

        return

    try:

        price, cost, commission = map(float, message.text.split())

    except:

        await message.answer(
            "Введите данные так:\n\n"
            "2000 800 15"
        )

        return

    commission_value = price * commission / 100

    profit = price - cost - commission_value
    margin = profit / price * 100
    roi = profit / cost * 100

    result = (
        f"📊 Результат\n\n"
        f"💰 Прибыль: {profit:.0f} ₽\n"
        f"📈 Маржа: {margin:.1f}%\n"
        f"🚀 ROI: {roi:.1f}%"
    )

    await message.answer(result)


async def main():

    await init_db()

    print("🚀 BOT STARTED")

    await dp.start_polling(bot)


if __name__ == "__main__":

    asyncio.run(main())
