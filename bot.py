import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

TOKEN = os.getenv("TOKEN")

if not TOKEN:
    raise ValueError("TOKEN not found")

bot = Bot(token=TOKEN)
dp = Dispatcher()

users = {}

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    users[message.from_user.id] = {
        "step": "price",
        "pro": False
    }
    await message.answer(
        "📊 WB Калькулятор\n\n"
        "Введите цену продажи товара (₽):"
    )

@dp.message(Command("pro"))
async def enable_pro(message: types.Message):
    if message.from_user.id not in users:
        users[message.from_user.id] = {"step": "price", "pro": False}

    users[message.from_user.id]["pro"] = True
    await message.answer("🔥 PRO режим включён")

@dp.message()
async def calculator(message: types.Message):
    user_id = message.from_user.id

    if user_id not in users:
        await message.answer("Напишите /start")
        return

    step = users[user_id]["step"]
    is_pro = users[user_id]["pro"]

    # Цена
    if step == "price":
        try:
            users[user_id]["price"] = float(message.text.replace(",", "."))
        except:
            await message.answer("Введите число")
            return

        users[user_id]["step"] = "cost"
        await message.answer("Введите себестоимость (₽):")
        return

    # Себестоимость
    if step == "cost":
        try:
            users[user_id]["cost"] = float(message.text.replace(",", "."))
        except:
            await message.answer("Введите число")
            return

        users[user_id]["step"] = "commission"
        await message.answer("Введите комиссию WB (%):")
        return

    # Комиссия
    if step == "commission":
        try:
            users[user_id]["commission_percent"] = float(message.text.replace(",", "."))
        except:
            await message.answer("Введите число")
            return

        if is_pro:
            users[user_id]["step"] = "returns"
            await message.answer("Введите % возвратов:")
        else:
            await calculate_and_reply(message, user_id)
            users[user_id]["step"] = "price"
        return

    # Возвраты (PRO)
    if step == "returns":
        try:
            users[user_id]["returns_percent"] = float(message.text.replace(",", "."))
        except:
            await message.answer("Введите число")
            return

        users[user_id]["step"] = "ads"
        await message.answer("Введите ДРР рекламы (%):")
        return

    # Реклама (PRO)
    if step == "ads":
        try:
            users[user_id]["ads_percent"] = float(message.text.replace(",", "."))
        except:
            await message.answer("Введите число")
            return

        await calculate_and_reply(message, user_id)
        users[user_id]["step"] = "price"


async def calculate_and_reply(message, user_id):
    data = users[user_id]

    price = data["price"]
    cost = data["cost"]
    commission_percent = data["commission_percent"]

    commission = price * commission_percent / 100
    acquiring = price * 0.02
    tax = price * 0.06
    logistics = 150

    returns_loss = 0
    ads_cost = 0

    if data["pro"]:
        returns_percent = data.get("returns_percent", 0)
        ads_percent = data.get("ads_percent", 0)

        returns_loss = price * returns_percent / 100 * 0.5
        ads_cost = price * ads_percent / 100

    total_expenses = commission + acquiring + tax + logistics + cost + returns_loss + ads_cost
    profit = price - total_expenses
    margin = (profit / price * 100) if price > 0 else 0
    investments = cost + logistics
    roi = (profit / investments * 100) if investments > 0 else 0

    if profit <= 0:
        verdict = "❌ Убыточно"
    elif roi < 20:
        verdict = "⚠️ Слабый ROI"
    else:
        verdict = "✅ Можно заходить"

    text = (
        f"📊 Результат\n\n"
        f"💰 Прибыль: {profit:.0f} ₽\n"
        f"📈 Маржа: {margin:.1f}%\n"
        f"🚀 ROI: {roi:.1f}%\n\n"
        f"{verdict}\n\n"
        f"Введите новую цену:"
    )

    await message.answer(text)


async def main():
    print("🚀 BOT STARTED")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
