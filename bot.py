import asyncio
import os
from datetime import date

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

TOKEN = os.getenv("TOKEN")

if not TOKEN:
    raise ValueError("TOKEN not found")

bot = Bot(token=TOKEN)
dp = Dispatcher()

FREE_LIMIT = 3  # 3 расчета в день бесплатно

# user_id -> {
#   step, pro, used_today, last_date, price, cost, commission_percent, ...
# }
users = {}


def ensure_user(user_id: int):
    if user_id not in users:
        users[user_id] = {
            "step": "price",
            "pro": False,
            "used_today": 0,
            "last_date": str(date.today()),
        }
    # сброс счетчика при смене дня
    today = str(date.today())
    if users[user_id]["last_date"] != today:
        users[user_id]["used_today"] = 0
        users[user_id]["last_date"] = today


@dp.message(Command("start"))
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    ensure_user(user_id)
    users[user_id]["step"] = "price"

    await message.answer(
        "📊 WB Калькулятор\n\n"
        f"Бесплатно: {FREE_LIMIT} расчёта в день\n"
        "Введите цену продажи товара (₽):"
    )


@dp.message(Command("pro"))
async def enable_pro(message: types.Message):
    user_id = message.from_user.id
    ensure_user(user_id)

    users[user_id]["pro"] = True
    await message.answer("🔥 PRO режим включён (без лимита)")


@dp.message()
async def calculator(message: types.Message):
    user_id = message.from_user.id
    ensure_user(user_id)

    user = users[user_id]
    step = user["step"]
    is_pro = user["pro"]

    # 1️⃣ Цена
    if step == "price":
        try:
            user["price"] = float(message.text.replace(",", "."))
        except:
            await message.answer("Введите число")
            return

        user["step"] = "cost"
        await message.answer("Введите себестоимость (₽):")
        return

    # 2️⃣ Себестоимость
    if step == "cost":
        try:
            user["cost"] = float(message.text.replace(",", "."))
        except:
            await message.answer("Введите число")
            return

        user["step"] = "commission"
        await message.answer("Введите комиссию WB (%):")
        return

    # 3️⃣ Комиссия
    if step == "commission":
        try:
            user["commission_percent"] = float(message.text.replace(",", "."))
        except:
            await message.answer("Введите число")
            return

        if is_pro:
            user["step"] = "returns"
            await message.answer("Введите % возвратов:")
        else:
            # проверяем лимит
            if user["used_today"] >= FREE_LIMIT:
                await message.answer(
                    "⛔ Лимит бесплатных расчётов исчерпан.\n"
                    "Используйте /pro для режима без ограничений."
                )
                user["step"] = "price"
                return

            user["used_today"] += 1
            await calculate_and_reply(message, user_id)
            user["step"] = "price"
        return

    # 4️⃣ Возвраты (PRO)
    if step == "returns":
        try:
            user["returns_percent"] = float(message.text.replace(",", "."))
        except:
            await message.answer("Введите число")
            return

        user["step"] = "ads"
        await message.answer("Введите ДРР рекламы (%):")
        return

    # 5️⃣ Реклама (PRO)
    if step == "ads":
        try:
            user["ads_percent"] = float(message.text.replace(",", "."))
        except:
            await message.answer("Введите число")
            return

        await calculate_and_reply(message, user_id)
        user["step"] = "price"


async def calculate_and_reply(message: types.Message, user_id: int):
    user = users[user_id]

    price = user["price"]
    cost = user["cost"]
    commission_percent = user["commission_percent"]

    commission = price * commission_percent / 100
    acquiring = price * 0.02
    tax = price * 0.06
    logistics = 150

    returns_loss = 0
    ads_cost = 0

    if user["pro"]:
        returns_percent = user.get("returns_percent", 0)
        ads_percent = user.get("ads_percent", 0)

        returns_loss = price * returns_percent / 100 * 0.5
        ads_cost = price * ads_percent / 100

    total_expenses = (
        commission
        + acquiring
        + tax
        + logistics
        + cost
        + returns_loss
        + ads_cost
    )

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

    if not user["pro"]:
        remaining = FREE_LIMIT - user["used_today"]
        limit_info = f"\nОсталось бесплатных расчётов сегодня: {remaining}"
    else:
        limit_info = "\n🔥 PRO режим — без лимита"

    text = (
        f"📊 Результат\n\n"
        f"💰 Прибыль: {profit:.0f} ₽\n"
        f"📈 Маржа: {margin:.1f}%\n"
        f"🚀 ROI: {roi:.1f}%\n\n"
        f"{verdict}"
        f"{limit_info}\n\n"
        f"Введите новую цену:"
    )

    await message.answer(text)


async def main():
    print("🚀 BOT STARTED")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
