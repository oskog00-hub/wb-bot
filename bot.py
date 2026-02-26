import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

TOKEN = os.getenv("TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ===== START =====

@dp.message(Command("start"))
async def start(message: types.Message):
await message.answer(
"📊 WB Калькулятор прибыли\n\n"
"Введи цену продажи товара (₽)"
)
dp.user_data[message.from_user.id] = {"step": "price"}

# ===== ОБРАБОТКА =====

@dp.message()
async def calc(message: types.Message):
user = dp.user_data.get(message.from_user.id)

```
if not user:
    await message.answer("Напиши /start")
    return

# шаг цена
if user["step"] == "price":
    try:
        user["price"] = float(message.text.replace(",", "."))
    except:
        await message.answer("Введите число")
        return

    user["step"] = "cost"
    await message.answer("📦 Себестоимость товара?")
    return

# шаг себестоимость
if user["step"] == "cost":
    try:
        user["cost"] = float(message.text.replace(",", "."))
    except:
        await message.answer("Введите число")
        return

    user["step"] = "commission"
    await message.answer("📊 Комиссия WB % ?")
    return

# шаг комиссия
if user["step"] == "commission":
    try:
        commission_percent = float(message.text.replace(",", "."))
    except:
        await message.answer("Введите число")
        return

    price = user["price"]
    cost = user["cost"]

    commission = price * commission_percent / 100
    acquiring = price * 0.02
    tax = price * 0.06
    logistics = 150

    profit = price - commission - acquiring - tax - logistics - cost
    margin = (profit / cost * 100) if cost > 0 else 0

    await message.answer(
        f"💰 Прибыль: {profit:.0f} ₽\n"
        f"📈 Маржа: {margin:.1f}%"
    )

    user["step"] = "price"
    await message.answer("\nВведи новую цену товара")
```

async def main():
print("🚀 BOT START")
await dp.start_polling(bot)

if **name** == "**main**":
asyncio.run(main())
