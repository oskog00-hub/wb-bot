import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import aiosqlite

TOKEN = os.getenv("TOKEN")

if not TOKEN:
    print("TOKEN NOT FOUND")
    exit()

print("TOKEN OK")
print("BOT STARTING...")

bot = Bot(token=TOKEN)
dp = Dispatcher()

DB = "users.db"

# создаём базу
async def init_db():
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER
        )
        """)
        await db.commit()

# ответ только на /start
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("WB бот работает 24/7 🚀")

async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
