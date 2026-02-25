import asyncio
import os
import aiosqlite
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

TOKEN = os.environ.get("TOKEN")

if TOKEN is None:
    print("TOKEN NOT FOUND")
    raise SystemExit(1)

print("TOKEN OK")

bot = Bot(token=TOKEN)
dp = Dispatcher()

DB = "users.db"


async def init_db():
    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "CREATE TABLE IF NOT EXISTS users (user_id INTEGER)"
        )
        await db.commit()


@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("WB бот работает 24/7 🚀")


@dp.message()
async def echo(message: types.Message):
    await message.answer("Работаю.")


async def main():
    print("BOT STARTING...")
    await init_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
