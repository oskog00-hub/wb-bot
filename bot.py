import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

TOKEN = os.getenv("TOKEN")

if not TOKEN:
    raise ValueError("TOKEN not found in environment")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Храним временные данные пользователей
users = {}

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    users[message.from_user.id] = {"step": "price"}
    await message.answer(
        "📊 WB Калькулятор прибыли\n\n"
        "Введите цену продажи товара (₽):"
    )

@dp.message()
async def calculator(message: types.Message):
    user_id = message.from_user.id

    if user_id not in users:
        await message.answer("Напишите /start")
        return

    step = users[user_id]["step"]

    # Шаг 1 — цена
    if step == "price":
        try:
            users[user_id]["price"] = float(message.text.replace(",", "."))
        except:
            await message.answer("Введите число")
            return

        users[user_id]["step"] = "cost"
        await message.answer("Введите себестоимость товара (₽):")
        return

    # Шаг 2 — себестоимость
    if step == "cost":
        try:
            users[user_id]["cost"] = float(message.text.replace(",", "."))
        except:
            await message.answer("Введите число")
            return

        users[user_id]["step"] = "commission"
        await message.answer("Введите комиссию WB (%):")
        return

    # Шаг 3 — комиссия
    if step == "commission":
        try:
            commission_percent = float(message.text.replace(",", "."))
        except:
            await message.answer("Введите число")
            return

        price = users[user_id]["price"]
        cost = users[user_id]["cost"]

        commission = price * commission_percent / 100
        acquiring = price * 0.02
        tax = price * 0.06
        logistics = 150

        profit = price - commission - acquiring - tax - logistics - cost
        margin = (profit / cost * 100) if cost > 0 else 0

        await message.answer(
            f"💰 Прибыль: {profit:.0f} ₽\n"
            f"📈 Маржа: {margin:.1f}%\n\n"
            "Введите новую цену для следующего расчёта:"
        )

        users[user_id]["step"] = "price"

async def main():
    print("🚀 BOT STARTED")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
