import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

TOKEN = os.getenv("TOKEN")

if not TOKEN:
    print("TOKEN NOT FOUND")
    exit()

print("TOKEN OK")
print("BOT STARTING...")

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# ===== Состояния =====
class Calc(StatesGroup):
    price = State()
    cost = State()
    commission = State()


# ===== START =====
@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    await state.set_state(Calc.price)
    await message.answer("💰 Введите цену продажи товара (₽)")


# ===== Цена =====
@dp.message(Calc.price)
async def get_price(message: types.Message, state: FSMContext):
    try:
        price = float(message.text.replace(",", "."))
    except:
        await message.answer("Введите число, например 1990")
        return

    await state.update_data(price=price)
    await state.set_state(Calc.cost)
    await message.answer("📦 Введите себестоимость товара (₽)")


# ===== Себестоимость =====
@dp.message(Calc.cost)
async def get_cost(message: types.Message, state: FSMContext):
    try:
        cost = float(message.text.replace(",", "."))
    except:
        await message.answer("Введите число, например 800")
        return

    await state.update_data(cost=cost)
    await state.set_state(Calc.commission)
    await message.answer("📊 Введите комиссию WB (%) для вашей категории\nНапример: 18")


# ===== Комиссия =====
@dp.message(Calc.commission)
async def get_commission(message: types.Message, state: FSMContext):
    try:
        commission_percent = float(message.text.replace(",", "."))
    except:
        await message.answer("Введите число, например 18")
        return

    data = await state.get_data()
    price = data["price"]
    cost = data["cost"]

    # ===== Реальный расчет =====
    commission = price * (commission_percent / 100)
    acquiring = price * 0.02
    tax = price * 0.06
    logistics = 150

    profit = price - commission - acquiring - tax - logistics - cost
    margin = (profit / cost * 100) if cost > 0 else 0

    await message.answer(
        f"📊 Расчет прибыли WB\n\n"
        f"💰 Цена: {price:.0f} ₽\n"
        f"📦 Себестоимость: {cost:.0f} ₽\n"
        f"📈 Комиссия категории: {commission_percent:.1f}%\n\n"
        f"Комиссия WB: {commission:.0f} ₽\n"
        f"Эквайринг: {acquiring:.0f} ₽\n"
        f"Налог: {tax:.0f} ₽\n"
        f"Логистика: {logistics:.0f} ₽\n\n"
        f"🔥 Чистая прибыль: {profit:.0f} ₽\n"
        f"📈 Маржа: {margin:.1f}%"
    )

    await state.clear()


# ===== Запуск =====
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
