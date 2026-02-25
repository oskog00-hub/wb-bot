import asyncio
import os
import aiosqlite
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# ===== ПОЛУЧАЕМ TOKEN ИЗ RAILWAY =====

TOKEN = os.environ.get("TOKEN")

if TOKEN is None:
print("❌ TOKEN не найден в Railway")
exit()

print("✅ TOKEN найден")

bot = Bot(token=TOKEN)
dp = Dispatcher()

DB = "users.db"

# ===== СОЗДАНИЕ БАЗЫ =====

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
await message.answer("🚀 WB бот работает 24/7")

# ===== ПРОСТОЙ ОТВЕТ =====

@dp.message()
async def echo(message: types.Message):
await message.answer("Бот онлайн и работает.")

# ===== ЗАПУСК =====

async def main():
print("🚀 Бот запускается...")
await init_db()
await dp.start_polling(bot)

if **name** == "**main**":
asyncio.run(main())
