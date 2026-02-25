import asyncio
import os
import datetime
import aiosqlite

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# ===== ПОЛУЧАЕМ ТОКЕН ИЗ RAILWAY =====

TOKEN = os.environ.get("TOKEN")

if not TOKEN:
print("❌ ОШИБКА: TOKEN не найден в Railway!")
exit()

print("✅ TOKEN загружен")

DB = "users.db"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ===== СОЗДАНИЕ БД =====

async def init_db():
async with aiosqlite.connect(DB) as db:
await db.execute("""
CREATE TABLE IF NOT EXISTS users (
user_id INTEGER,
date TEXT
)
""")
await db.commit()

# ===== /start =====

@dp.message(Command("start"))
async def start(message: types.Message):
await message.answer("🚀 WB Калькулятор прибыли запущен!")

# ===== ПРОСТОЙ ТЕСТ =====

@dp.message()
async def test(message: types.Message):
await message.answer("Бот работает 24/7 🚀")

# ===== ЗАПУСК =====

async def main():
print("🚀 Бот запускается...")
await init_db()
await dp.start_polling(bot)

if **name** == "**main**":
asyncio.run(main())



asyncio.run(main())




