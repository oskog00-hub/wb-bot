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


# ===== FSM =====
class CalcState(StatesGroup):
    waiting_price = State()
    waiting_cost = State()


# ===== /start =====
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "Введите цену продажи товара (₽):"
    )
    await dp.fsm.set_state(message.from_user.id, CalcState.waiting_price)


# ===== Получаем цену =====
@dp.message(CalcState.waiting_price)
async def get_price(message: types.Message, state: FSMContext):
    try:
        price = float(message.text.replace(",", "."))
    except:
        await message.answer("Введите число.")
        return

    await state.update_data(price=price)
    await message.answer("Введите себестоимость товара (₽):")
    await state.set_state(CalcState.waiting_cost)


# ===== Получаем себестоимость =====
@dp.message(CalcState.waiting_cost)
async def get_cost(message: types.Message, state: FSMContext):
    try:
        cost = float(message.text.replace(",", "."))
    except:
        await message.answer("Введите число.")
        return

    data = await state.get_data()
    price = data["price"]

    # --- расчёт ---
    commission = price * 0.15
    acquiring = price * 0.02
    logistics = 120

    profit = price - commission - acquiring - logistics - cost

    if cost > 0:
        margin = (profit / cost) * 100
    else:
        margin = 0

    await message.answer(
        f"📊 Результат:\n\n"
        f"Цена: {price:.2f} ₽\n"
        f"Себестоимость: {cost:.2f} ₽\n\n"
        f"Комиссия WB: {commission:.2f} ₽\n"
        f"Эквайринг: {acquiring:.2f} ₽\n"
        f"Логистика: {logistics:.2f} ₽\n\n"
        f"💰 Чистая прибыль: {profit:.2f} ₽\n"
        f"📈 Маржинальность: {margin:.2f} %"
    )

    await state.clear()


# ===== Запуск =====
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
