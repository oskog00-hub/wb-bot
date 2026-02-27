import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

TOKEN = os.getenv("TOKEN")

if not TOKEN:
    raise ValueError("TOKEN not found in environment")

bot = Bot(token=TOKEN)
dp = Dispatcher()

users = {}

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    users[message.from_user.id] = {"step": "price"}
    await message.answer(
        "📊 WB PRO Калькулятор\n\n"
        "Введите цену продажи товара (₽):"
    )

@dp.message()
async def calculator(message: types.Message):
    user_id = message.from_user.id

    if user_id not in users:
        await message.answer("Напишите /start")
        return

    step = users[user_id]["step"]

    # ШАГ 1 — ЦЕНА
    if step == "price":
        try:
            users[user_id]["price"] = float(message.text.replace(",", "."))
        except:
            await message.answer("Введите число")
            return

        users[user_id]["step"] = "cost"
        await message.answer("Введите себестоимость товара (₽):")
        return

    # ШАГ 2 — СЕБЕСТОИМОСТЬ
    if step == "cost":
        try:
            users[user_id]["cost"] = float(message.text.replace(",", "."))
        except:
            await message.answer("Введите число")
            return

        users[user_id]["step"] = "commission"
        await message.answer("Введите комиссию WB (%):")
        return

    # ШАГ 3 — КОМИССИЯ
    if step == "commission":
        try:
            commission_percent = float(message.text.replace(",", "."))
        except:
            await message.answer("Введите число")
            return

        price = users[user_id]["price"]
        cost = users[user_id]["cost"]

        # ===== РАСЧЁТЫ =====
        commission = price * commission_percent / 100
        acquiring = price * 0.02
        tax = price * 0.06
        logistics = 150

        total_expenses = commission + acquiring + tax + logistics + cost
        profit = price - total_expenses
        margin = (profit / price * 100) if price > 0 else 0

        investments = cost + logistics
        roi = (profit / investments * 100) if investments > 0 else 0

        # Точка безубыточности
        fixed_costs = cost + logistics
        percent_costs = commission_percent / 100 + 0.02 + 0.06
        breakeven_price = fixed_costs / (1 - percent_costs)

        # ===== ОЦЕНКА =====
        if profit <= 0:
            verdict = "❌ Проект убыточен"
        elif roi < 20:
            verdict = "⚠️ Низкий ROI — риск"
        else:
            verdict = "✅ Можно заходить"

        await message.answer(
            f"📊 WB PRO расчёт\n\n"
            f"💰 Прибыль: {profit:.0f} ₽\n"
            f"📈 Маржа: {margin:.1f}%\n"
            f"🚀 ROI: {roi:.1f}%\n"
            f"🎯 Точка 0: {breakeven_price:.0f} ₽\n\n"
            f"{verdict}\n\n"
            f"Введите новую цену для следующего расчёта:"
        )

        users[user_id]["step"] = "price"

async def main():
    print("🚀 BOT STARTED")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
