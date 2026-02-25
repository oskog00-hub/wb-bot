import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

# ===== TOKEN =====
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
async def start_handler(message: types.Message, state: FSMContext):
    await state.clear()
    await state.set_state(Calc.price)
    await message.answer("💰 Введите цену продажи товара (₽)")

# ===== Получаем цену =====
@dp.message(Calc.price)
async def get_price(message: types.Message, state: FSMContext):
    try:
        price = float(message.text.replace(",", "."))
    except:
        await message.answer("Введите корректное число, например: 1990")
        return

    await state.update_data(price=price)
    await state.set_state(Calc.cost)
    await message.answer("📦 Введите себестоимость товара (₽)")

# ===== Получаем себестоимость =====
@dp.message(Calc.cost)
async def get_cost(message: types.Message, state: FSMContext):
    try:
        cost = float(message.text.replace(",", "."))
    except:
        await message.answer("Введите корректное число, например: 800")
        return

    await state.update_data(cost=cost)
    await state.set_state(Calc.commission)
    await message.answer("📊 Введите комиссию WB (%) для вашей категории\nНапример: 18")

# ===== Получаем комиссию и считаем =====
@dp.message(Calc.commission)
async def get_commission(message: types.Message, state: FSMContext):
    try:
        commission_percent = float(message.text.replace(",", "."))
    except:
        await message.answer("Введите корректное число, например: 18")
        return

    data = await state.get_data()
    price = data["price"]
    cost = data["cost"]

    # ===== Расчёт =====
    commission = price * (commission_percent / 100)
    acquiring = price * 0.02
    tax = price * 0.06
    logistics = 150

    profit = price - commission - acquiring - tax - logistics - cost
    margin = (profit / cost * 100) if cost > 0 else 0

    # ===== Точка безубыточности =====
    total_percent = commission_percent / 100 + 0.08  # комиссия + 8% (эквайринг + налог)

    if total_percent < 1:
        break_even = (cost + logistics) / (1 - total_percent)
    else:
        break_even = 0

    # ===== Ответ =====
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
        f"📈 Маржа: {margin:.1f}%\n\n"
        f"⚖️ Точка безубыточности: {break_even:.0f} ₽"
    )

    await state.clear()

# ===== Запуск =====
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
