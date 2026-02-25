import asyncio
from aiogram import Bot, Dispatcher, types
import aiosqlite
import datetime

import os
TOKEN = os.getenv("TOKEN")
DB = "users.db"

bot = Bot(token=TOKEN)
dp = Dispatcher()

async def init_db():
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            requests INTEGER DEFAULT 0,
            last_reset TEXT,
            sub INTEGER DEFAULT 0
        )
        """)
        await db.commit()

async def get_user(user_id):
    async with aiosqlite.connect(DB) as db:
        async with db.execute("SELECT * FROM users WHERE user_id=?", (user_id,)) as cur:
            return await cur.fetchone()

async def add_user(user_id):
    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, last_reset) VALUES (?, ?)",
            (user_id, datetime.date.today().isoformat())
        )
        await db.commit()

async def update_requests(user_id):
    async with aiosqlite.connect(DB) as db:
        await db.execute("UPDATE users SET requests = requests + 1 WHERE user_id=?", (user_id,))
        await db.commit()

@dp.message(lambda m: m.text == "/start")
async def start(message: types.Message):
    await add_user(message.from_user.id)
    await message.answer(
        "💰 Калькулятор прибыли WB\n\n"
        "Введите: цена себестоимость\n"
        "Пример: 1990 600\n\n"
        "Лимит: 5 расчетов в день"
    )

@dp.message()
async def calc(message: types.Message):
    user_id = message.from_user.id
    await add_user(user_id)
    user = await get_user(user_id)

    today = datetime.date.today().isoformat()

    # сброс лимита каждый день
    if user[2] != today:
        async with aiosqlite.connect(DB) as db:
            await db.execute(
                "UPDATE users SET requests=0, last_reset=? WHERE user_id=?",
                (today, user_id)
            )
            await db.commit()
        user = await get_user(user_id)

    # проверка лимита
    if user[1] >= 5 and user[3] == 0:
        await message.answer(
            "🔒 Лимит исчерпан\n"
            "PRO доступ 490₽/мес\n"
            "Напишите: ОПЛАТА"
        )
        return

    try:
        price, cost = map(float, message.text.split())

        commission = price * 0.20
        logistics = 120
        profit = price - cost - commission - logistics
        margin = (profit / price) * 100

        await update_requests(user_id)

        await message.answer(
            f"Цена: {price}₽\n"
            f"Себестоимость: {cost}₽\n"
            f"Комиссия WB: {commission:.0f}₽\n"
            f"Логистика: {logistics}₽\n\n"
            f"Чистая прибыль: {profit:.0f}₽\n"
            f"Маржа: {margin:.1f}%"
        )

    except:
        await message.answer("Введите в формате: цена себестоимость\nПример: 1990 600")

async def main():
    await init_db()
    await dp.start_polling(bot)


asyncio.run(main())
