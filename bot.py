import asyncio
import os
import aiosqlite
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# ===== ТОКЕН =====

TOKEN = os.environ.get("TOKEN")

if not TOKEN:
print("TOKEN НЕ НАЙДЕН В RAILWAY")
exit()

print("TOKEN OK")

bot = Bot(token=TOKEN)
dp = Dispatcher()

DB = "users.db"

# ===== БАЗА =====

async def init_db():
async with aiosqlite.connect(DB) as db:
await db.execute("""
CREATE TABLE IF NOT EXISTS users(
user_id INTEGER
)
""")
await db.commit()

# ===== СТАРТ =====

@dp.message(Command("start"))
async def start(message: types.Message):
await message.answer("WB бот работает 24/7 🚀")

# ===== ТЕСТ =====

@dp.message()
async def echo(message: types.Message):
await message.answer("Работаю.")

# ===== ЗАПУСК =====

async def main():
print("БОТ ЗАПУСКАЕТСЯ...")
await init_db()
await dp.start_polling(bot)

if **name** == "**main**":
asyncio.run(main())





