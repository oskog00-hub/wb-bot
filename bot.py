import asyncio
import os
import uuid
import aiosqlite
from datetime import date

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

from yookassa import Configuration, Payment

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

# ================= TOKENS =================

TOKEN = os.getenv("TOKEN")
YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID")
YOOKASSA_SECRET = os.getenv("YOOKASSA_SECRET")

if not TOKEN:
print("❌ TOKEN NOT FOUND")
exit()

print("✅ TOKEN OK")

Configuration.account_id = YOOKASSA_SHOP_ID
Configuration.secret_key = YOOKASSA_SECRET

# ================= BOT =================

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())
app = FastAPI()

DB = "bot.db"
FREE_LIMIT = 5

# ================= DATABASE =================

async def init_db():
async with aiosqlite.connect(DB) as db:
await db.execute("""
CREATE TABLE IF NOT EXISTS users(
user_id INTEGER PRIMARY KEY,
pro INTEGER DEFAULT 0
)
""")
await db.execute("""
CREATE TABLE IF NOT EXISTS usage(
user_id INTEGER,
calc_date TEXT,
count INTEGER DEFAULT 0,
PRIMARY KEY(user_id, calc_date)
)
""")
await db.commit()

# ================= FSM =================

class Calc(StatesGroup):
price = State()
cost = State()
commission = State()

# ================= LIMIT =================

async def check_limit(user_id):
async with aiosqlite.connect(DB) as db:
cur = await db.execute("SELECT pro FROM users WHERE user_id=?", (user_id,))
row = await cur.fetchone()

```
    if row and row[0] == 1:
        return True

    today = str(date.today())
    cur = await db.execute(
        "SELECT count FROM usage WHERE user_id=? AND calc_date=?",
        (user_id, today)
    )
    row = await cur.fetchone()

    if not row:
        await db.execute(
            "INSERT INTO usage(user_id, calc_date, count) VALUES(?,?,1)",
            (user_id, today)
        )
        await db.commit()
        return True

    if row[0] >= FREE_LIMIT:
        return False

    await db.execute(
        "UPDATE usage SET count=count+1 WHERE user_id=? AND calc_date=?",
        (user_id, today)
    )
    await db.commit()
    return True
```

# ================= START =================

@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
user_id = message.from_user.id

```
async with aiosqlite.connect(DB) as db:
    await db.execute("INSERT OR IGNORE INTO users(user_id) VALUES(?)", (user_id,))
    await db.commit()

await state.clear()
await state.set_state(Calc.price)

await message.answer(
    "💰 WB Калькулятор прибыли\n\n"
    "Введи цену продажи товара (₽)"
)
```

# ================= PRICE =================

@dp.message(Calc.price)
async def get_price(message: types.Message, state: FSMContext):
try:
price = float(message.text.replace(",", "."))
except:
await message.answer("Введите число")
return

```
await state.update_data(price=price)
await state.set_state(Calc.cost)
await message.answer("📦 Введи себестоимость товара (₽)")
```

# ================= COST =================

@dp.message(Calc.cost)
async def get_cost(message: types.Message, state: FSMContext):
try:
cost = float(message.text.replace(",", "."))
except:
await message.answer("Введите число")
return

```
await state.update_data(cost=cost)
await state.set_state(Calc.commission)
await message.answer("📊 Введи комиссию WB (%)")
```

# ================= CALC =================

@dp.message(Calc.commission)
async def get_commission(message: types.Message, state: FSMContext):
user_id = message.from_user.id

```
allowed = await check_limit(user_id)

if not allowed:
    await message.answer(
        "⛔ Лимит бесплатных расчетов (5/день) исчерпан\n\n"
        "Хочешь PRO без лимита?\nНапиши: ХОЧУ PRO"
    )
    await state.clear()
    return

try:
    commission_percent = float(message.text.replace(",", "."))
except:
    await message.answer("Введите число")
    return

data = await state.get_data()
price = data["price"]
cost = data["cost"]

commission = price * (commission_percent / 100)
acquiring = price * 0.02
tax = price * 0.06
logistics = 150

profit = price - commission - acquiring - tax - logistics - cost
margin = (profit / cost * 100) if cost > 0 else 0

total_percent = commission_percent/100 + 0.08
break_even = (cost + logistics) / (1 - total_percent) if total_percent < 1 else 0

await message.answer(
    f"📊 Расчет WB\n\n"
    f"🔥 Прибыль: {profit:.0f} ₽\n"
    f"📈 Маржа: {margin:.1f}%\n"
    f"⚖️ Точка 0: {break_even:.0f} ₽"
)

await state.clear()
```

# ================= WANT PRO =================

@dp.message(lambda m: "хочу" in m.text.lower())
async def want_pro(message: types.Message):
await message.answer(
"💎 PRO доступ — 490₽/месяц\n\n"
"Безлимитные расчеты\n"
"Точка безубыточности\n\n"
"Напиши: ОПЛАТА"
)

# ================= PAYMENT =================

@dp.message(lambda m: "оплата" in m.text.lower())
async def buy_pro(message: types.Message):

```
payment = Payment.create({
    "amount": {
        "value": "490.00",
        "currency": "RUB"
    },
    "confirmation": {
        "type": "redirect",
        "return_url": "https://t.me"
    },
    "capture": True,
    "description": "PRO доступ к WB боту",
    "metadata": {
        "user_id": str(message.from_user.id)
    }
}, str(uuid.uuid4()))

url = payment.confirmation.confirmation_url

await message.answer(
    f"💳 Оплатить PRO:\n{url}\n\nПосле оплаты доступ включится автоматически"
)
```

# ================= YOOKASSA WEBHOOK =================

@app.post("/yookassa")
async def yookassa_webhook(request: Request):
data = await request.json()

```
if data.get("event") == "payment.succeeded":
    payment = data.get("object", {})
    user_id = payment.get("metadata", {}).get("user_id")

    if user_id:
        async with aiosqlite.connect(DB) as db:
            await db.execute(
                "UPDATE users SET pro=1 WHERE user_id=?",
                (int(user_id),)
            )
            await db.commit()

return JSONResponse({"ok": True})
```

# ================= RUN =================

async def start_bot():
await init_db()
print("🚀 BOT STARTED")
await dp.start_polling(bot)

if **name** == "**main**":
loop = asyncio.get_event_loop()
loop.create_task(start_bot())
uvicorn.run(app, host="0.0.0.0", port=8000)
