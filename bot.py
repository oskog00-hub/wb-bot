import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

TOKEN = os.getenv("TOKEN")

if not TOKEN:
    raise ValueError("TOKEN not found")

bot = Bot(token=TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Бот работает ✅")


async def main():
    print("BOT STARTED")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
