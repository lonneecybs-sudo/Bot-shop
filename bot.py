import asyncio
import logging
from datetime import datetime
from enum import Enum
from typing import Dict, List

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, LabeledPrice, PreCheckoutQuery
)

# ========== КОНФИГУРАЦИЯ ==========
TOKEN = "8546103501:AAGZv9evkjpQJR92TxX5-6Do7W_7M6XwXbw"
ADMIN_ID = 8259326703
ADMIN_PASSWORD = "17157150Sw!"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== ТАРИФЫ ==========
class Tariff(Enum):
    MIN = ("⭐ Минимальный", 50)
    MID = ("⭐⭐ Средний", 100)
    MAX = ("⭐⭐⭐ Полный", 300)

# ========== ХРАНИЛИЩА ==========
orders = {}
order_counter = 0
reviews = []
review_counter = 0

# ========== РЕАЛИСТИЧНЫЕ ОТЗЫВЫ ==========
import random

def add_sample_reviews():
    global review_counter
    
    # ТВОИ ЮЗЕРНЕЙМЫ (14 штук)
    usernames = [
        "playboyrule", "BLADdrip", "Dragonsz1", "Fusionlol", "xxxxvwl",
        "Mirikjsnsks", "hicoveeer", "jiksop212199", "xxxxvwlu", "FydCortBoy",
        "furyskotikpashot", "xyecocyrodec", "gamagrilaGorilla", "HollikXyeta"
    ]
    
    # Реалистичные отзывы
    reviews_data = [
        # Положительные (8 штук)
        (5, "Сделал бота для магазина, все работает четко! Немного задержал, но предупредил", "playboyrule"),
        (5, "Третий раз заказываю, всегда все нравится", "BLADdrip"),
        (4, "Норм бот, только кнопки немного кривые, сам исправил", "Dragonsz1"),
        (5, "Помог с ботом для конкурса, отработал отлично", "Fusionlol"),
        (4, "Заказывал бота для рассылок, все ок", "xxxxvwl"),
        (5, "Сделал бота для техподдержки, клиенты довольны", "Mirikjsnsks"),
        (5, "Быстро, качественно, не дорого", "hicoveeer"),
        (4, "Есть мелкие недочеты, но в целом доволен", "jiksop212199"),
        
        # Средние (3 штуки)
        (3, "Ну такое... вроде работает, но могло быть и лучше", "xxxxvwlu"),
        (3, "Сделал, но не все функции как хотелось", "FydCortBoy"),
        (4, "Неплохо, но дороговато для такого функционала", "furyskotikpashot"),
        
        # Плохие (3 штуки)
        (2, "Принял заказ, сказал сделает за 2 дня. На 4й день написал что не получается и отказался", "xyecocyrodec"),
        (1, "Не доделал бота, бросил на полпути, пришлось искать другого", "gamagrilaGorilla"),
        (2, "Сделал, но половина функций не работает, на просьбу исправить игнорит", "HollikXyeta"),
    ]
    
    # Добавляем отзывы
    from datetime import datetime, timedelta
    end_date = datetime.now()
    
    for i, (rating, text, username) in enumerate(reviews_data):
        random_days = random.randint(1, 60)
        review_date = end_date - timedelta(days=random_days)
        
        review_counter += 1
        reviews.append({
            'id': review_counter,
            'user_id': 1000000 + i,
            'username': username,
            'rating': rating,
            'text': text,
            'date': review_date,
            'approved': True,
            'order_id': 1000 + i
        })
    
    print(f"✅ Добавлено {len(reviews_data)} реалистичных отзывов")

# ВЫЗОВИ ФУНКЦИЮ ПОСЛЕ СОЗДАНИЯ ХРАНИЛИЩ
import random
add_sample_reviews()

# ========== СОСТОЯНИЯ ==========
class OrderStates(StatesGroup):
    entering_description = State()
    waiting_for_review_rating = State()
    waiting_for_review_text = State()
    admin_login = State()
    admin_in_panel = State()
    waiting_for_message = State()
    waiting_for_token = State()

# ========== КЛАВИАТУРЫ ==========
def get_reply_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📦 ЗАКАЗАТЬ БОТА"), KeyboardButton(text="📋 МОИ ЗАКАЗЫ")],
            [KeyboardButton(text="📜 ПРАВИЛА"), KeyboardButton(text="❓ FAQ")],
            [KeyboardButton(text="💰 ТАРИФЫ"), KeyboardButton(text="💬 ОТЗЫВЫ")],
            [KeyboardButton(text="👑 АДМИН ПАНЕЛЬ")]
        ],
        resize_keyboard=True
    )

def get_main_inline_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔥 НАЧАТЬ ЗАКАЗ", callback_data="order")],
        [InlineKeyboardButton(text="📋 МОИ ЗАКАЗЫ", callback_data="my_orders")],
        [InlineKeyboardButton(text="💬 ОТЗЫВЫ", callback_data="show_reviews")],
        [
            InlineKeyboardButton(text="📜 ПРАВИЛА", callback_data="rules"),
            InlineKeyboardButton(text="❓ FAQ", callback_data="faq")
        ],
        [InlineKeyboardButton(text="💰 ТАРИФЫ", callback_data="prices")]
    ])

def get_tariff_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ 50⭐ - Минимальный", callback_data="tariff_min")],
        [InlineKeyboardButton(text="⭐⭐ 100⭐ - Средний", callback_data="tariff_mid")],
        [InlineKeyboardButton(text="⭐⭐⭐ 300⭐ - Полный", callback_data="tariff_max")],
        [InlineKeyboardButton(text="◀ НАЗАД", callback_data="back_to_main")]
    ])

def get_client_order_keyboard(order_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 МОИ ЗАКАЗЫ", callback_data="my_orders")],
        [InlineKeyboardButton(text="⭐ ОСТАВИТЬ ОТЗЫВ", callback_data=f"leave_review_{order_id}")],
        [InlineKeyboardButton(text="◀ ГЛАВНОЕ МЕНЮ", callback_data="back_to_main")]
    ])

def get_admin_order_keyboard(order_id: int, is_free: bool = False):
    buttons = []
    if is_free:
        buttons.append([InlineKeyboardButton(text="🆓 ПРИНЯТЬ БЕСПЛАТНО", callback_data=f"accept_free_{order_id}")])
    buttons.append([InlineKeyboardButton(text="✅ ПРИНЯТЬ ЗАКАЗ", callback_data=f"accept_{order_id}")])
    buttons.append([InlineKeyboardButton(text="❌ ОТКАЗАТЬ", callback_data=f"reject_{order_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_development_keyboard(order_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✉️ НАПИСАТЬ КЛИЕНТУ", callback_data=f"write_{order_id}")],
        [InlineKeyboardButton(text="✅ БОТ ГОТОВ", callback_data=f"ready_{order_id}")],
        [InlineKeyboardButton(text="📊 СТАТУС", callback_data=f"status_{order_id}")]
    ])

def get_admin_main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 ВСЕ ЗАКАЗЫ", callback_data="admin_all_orders")],
        [
            InlineKeyboardButton(text="⏳ В ОЖИДАНИИ", callback_data="admin_pending"),
            InlineKeyboardButton(text="🛠️ В РАЗРАБОТКЕ", callback_data="admin_development")
        ],
        [
            InlineKeyboardButton(text="✅ ЗАВЕРШЕННЫЕ", callback_data="admin_completed"),
            InlineKeyboardButton(text="📊 СТАТИСТИКА", callback_data="admin_stats")
        ],
        [InlineKeyboardButton(text="💬 ОТЗЫВЫ (модерация)", callback_data="admin_reviews")],
        [InlineKeyboardButton(text="◀ ВЫЙТИ", callback_data="back_to_main")]
    ])

def get_back_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀ НАЗАД", callback_data="back_to_main")]
    ])

def get_review_rating_keyboard():
    buttons = []
    row = []
    for i in range(1, 6):
        buttons.append([InlineKeyboardButton(text="⭐" * i, callback_data=f"rate_{i}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_admin_reviews_keyboard(review_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ ОДОБРИТЬ", callback_data=f"approve_review_{review_id}"),
            InlineKeyboardButton(text="❌ ОТКЛОНИТЬ", callback_data=f"reject_review_{review_id}")
        ]
    ])

# ========== ФУНКЦИИ БАЗЫ ДАННЫХ ==========
def create_order(user_id: int, username: str, tariff: Tariff, description: str) -> int:
    global order_counter
    order_counter += 1
    orders[order_counter] = {
        'id': order_counter,
        'user_id': user_id,
        'username': username,
        'tariff': tariff,
        'description': description,
        'status': 'pending',
        'created_at': datetime.now(),
        'paid': False,
        'token': None
    }
    return order_counter

def get_order(order_id: int):
    return orders.get(order_id)

def mark_order_paid(order_id: int):
    if order_id in orders:
        orders[order_id]['paid'] = True
        orders[order_id]['status'] = 'development'

def get_user_orders(user_id: int) -> list:
    return [o for o in orders.values() if o['user_id'] == user_id]

def create_review(user_id: int, username: str, rating: int, text: str, order_id: int = None) -> int:
    global review_counter
    review_counter += 1
    reviews.append({
        'id': review_counter,
        'user_id': user_id,
        'username': username,
        'rating': rating,
        'text': text,
        'date': datetime.now(),
        'approved': False,
        'order_id': order_id
    })
    return review_counter

def get_approved_reviews() -> list:
    return [r for r in reviews if r.get('approved', False)]

def get_pending_reviews() -> list:
    return [r for r in reviews if not r.get('approved', False)]

def approve_review(review_id: int) -> bool:
    for review in reviews:
        if review['id'] == review_id:
            review['approved'] = True
            return True
    return False

def reject_review(review_id: int):
    global reviews
    reviews = [r for r in reviews if r['id'] != review_id]

def get_stats():
    total_orders = len(orders)
    completed = len([o for o in orders.values() if o['status'] == 'completed'])
    paid = len([o for o in orders.values() if o.get('paid', False)])
    total_stars = sum([o['tariff'].value[1] for o in orders.values() if o.get('paid', False)])
    return {
        'total_orders': total_orders,
        'completed': completed,
        'paid': paid,
        'total_stars': total_stars,
        'reviews_count': len(get_approved_reviews())
    }

# ========== ТЕКСТЫ ==========
MAIN_MENU_TEXT = (
    "✨ <b>Добро пожаловать в премиум студию разработки ботов!</b>\n\n"
    "🔥 <b>Тарифы:</b>\n"
    "┌─────────────────────────┐\n"
    "│ ⭐ МИНИМАЛЬНЫЙ • 50⭐    │\n"
    "│ Базовые команды          │\n"
    "├─────────────────────────┤\n"
    "│ ⭐⭐ СРЕДНИЙ • 100⭐     │\n"
    "│ Команды + инлайн кнопки  │\n"
    "├─────────────────────────┤\n"
    "│ ⭐⭐⭐ ПОЛНЫЙ • 300⭐     │\n"
    "│ Любые функции, кастом    │\n"
    "└─────────────────────────┘"
)

# ========== ЗАПУСК ==========
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# ========== START ==========
@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    stats = get_stats()
    await message.answer(
        MAIN_MENU_TEXT + f"\n\n📊 Статистика:\n└ Заказов: {stats['total_orders']} | Отзывов: {stats['reviews_count']}",
        reply_markup=get_reply_main_keyboard(),
        parse_mode="HTML"
    )
    await message.answer("✨ <b>Быстрые действия:</b>", reply_markup=get_main_inline_keyboard(), parse_mode="HTML")

# ========== REPLY КНОПКИ ==========
@dp.message(F.text == "📦 ЗАКАЗАТЬ БОТА")
async def reply_order(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("📦 <b>ВЫБЕРИТЕ ТАРИФ</b>", reply_markup=get_tariff_keyboard(), parse_mode="HTML")

@dp.message(F.text == "📋 МОИ ЗАКАЗЫ")
async def reply_my_orders(message: Message):
    user_orders = get_user_orders(message.from_user.id)
    if not user_orders:
        await message.answer("📋 <b>У вас пока нет заказов</b>", reply_markup=get_back_keyboard(), parse_mode="HTML")
        return
    text = "📋 <b>ВАШИ ЗАКАЗЫ</b>\n\n"
    for order in sorted(user_orders, key=lambda x: x['created_at'], reverse=True)[:5]:
        status_emoji = {'pending': '⏳', 'waiting_payment': '💰', 'development': '🛠️', 'completed': '✅'}.get(order['status'], '⏳')
        text += f"{status_emoji} <b>Заказ №{order['id']}</b>\n└ {order['tariff'].value[0]}\n"
    await message.answer(text, reply_markup=get_back_keyboard(), parse_mode="HTML")

@dp.message(F.text == "📜 ПРАВИЛА")
async def reply_rules(message: Message):
    text = "╔══════════════════════════════╗\n║         📜 ПРАВИЛА           ║\n╠══════════════════════════════╣\n║ ❌ <b>НЕ РАЗРАБАТЫВАЕМ:</b>     ║\n║ • 18+ контент                 ║\n║ • Пробив/базы данных          ║\n║ • Спам/рассылки               ║\n║ • Противозаконное             ║\n╠══════════════════════════════╣\n║ ⚠️ <b>УСЛОВИЯ:</b>               ║\n║ • Возврат НЕ производится     ║\n║ • Связь только через бота     ║\n║ • Сроки: 1-5 дней             ║\n╚══════════════════════════════╝"
    await message.answer(text, reply_markup=get_back_keyboard(), parse_mode="HTML")

@dp.message(F.text == "❓ FAQ")
async def reply_faq(message: Message):
    text = "💎 <b>FAQ</b>\n\n❓ Как оплатить?\n➡️ Звездами Telegram\n\n❓ Сроки?\n➡️ 1-5 дней"
    await message.answer(text, reply_markup=get_back_keyboard(), parse_mode="HTML")

@dp.message(F.text == "💰 ТАРИФЫ")
async def reply_prices(message: Message):
    text = "💰 <b>ТАРИФЫ</b>\n\n⭐ Минимальный - 50⭐\n⭐⭐ Средний - 100⭐\n⭐⭐⭐ Полный - 300⭐"
    await message.answer(text, reply_markup=get_back_keyboard(), parse_mode="HTML")

@dp.message(F.text == "💬 ОТЗЫВЫ")
async def reply_reviews(message: Message):
    approved = get_approved_reviews()
    if not approved:
        await message.answer("💬 <b>ОТЗЫВОВ ПОКА НЕТ</b>", reply_markup=get_back_keyboard(), parse_mode="HTML")
        return
    text = "💬 <b>ОТЗЫВЫ</b>\n\n"
    for r in approved[-5:]:
        text += f"{'⭐'*r['rating']} @{r['username']}: {r['text']}\n"
    await message.answer(text, reply_markup=get_back_keyboard(), parse_mode="HTML")

@dp.message(F.text == "👑 АДМИН ПАНЕЛЬ")
async def reply_admin(message: Message, state: FSMContext):
    if message.from_user.id == ADMIN_ID:
        await state.set_state(OrderStates.admin_login)
        await message.answer("🔐 <b>Пароль:</b>", parse_mode="HTML")
    else:
        await message.answer("⛔ Доступ запрещен!")

# ========== ЗАКАЗЫ ==========
@dp.callback_query(F.data == "order")
async def order_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer("📦 <b>ВЫБЕРИТЕ ТАРИФ</b>", reply_markup=get_tariff_keyboard(), parse_mode="HTML")

@dp.callback_query(F.data.startswith("tariff_"))
async def tariff_chosen(callback: CallbackQuery, state: FSMContext):
    tariff_map = {"tariff_min": Tariff.MIN, "tariff_mid": Tariff.MID, "tariff_max": Tariff.MAX}
    await state.update_data(tariff=tariff_map[callback.data])
    await state.set_state(OrderStates.entering_description)
    await callback.message.delete()
    await callback.message.answer("📝 <b>ОПИШИТЕ ЗАДАЧУ</b>", parse_mode="HTML")

@dp.message(OrderStates.entering_description)
async def description_received(message: Message, state: FSMContext):
    data = await state.get_data()
    order_id = create_order(message.from_user.id, message.from_user.username or "user", data['tariff'], message.text)
    await state.clear()
    await message.answer(f"✅ <b>ЗАКАЗ №{order_id} ОФОРМЛЕН!</b>", reply_markup=get_client_order_keyboard(order_id), parse_mode="HTML")
    await bot.send_message(ADMIN_ID, f"🔔 Новый заказ #{order_id}", reply_markup=get_admin_order_keyboard(order_id, True))

@dp.callback_query(F.data == "my_orders")
async def my_orders(callback: CallbackQuery):
    user_orders = get_user_orders(callback.from_user.id)
    await callback.message.delete()
    if not user_orders:
        await callback.message.answer("📋 Нет заказов", reply_markup=get_back_keyboard())
        return
    text = "📋 <b>ВАШИ ЗАКАЗЫ</b>\n\n"
    for o in user_orders[-5:]:
        text += f"{'⏳'} Заказ №{o['id']} - {o['tariff'].value[0]}\n"
    await callback.message.answer(text, reply_markup=get_back_keyboard(), parse_mode="HTML")

# ========== АДМИНКА ==========
@dp.message(OrderStates.admin_login)
async def check_admin_password(message: Message, state: FSMContext):
    if message.text == ADMIN_PASSWORD:
        await state.set_state(OrderStates.admin_in_panel)
        await message.answer("👑 <b>АДМИН ПАНЕЛЬ</b>", reply_markup=get_admin_main_keyboard(), parse_mode="HTML")
    else:
        await message.answer("❌ Неверный пароль!")
        await state.clear()

@dp.callback_query(F.data == "admin_all_orders", OrderStates.admin_in_panel)
async def admin_all_orders(callback: CallbackQuery):
    text = "📋 <b>ВСЕ ЗАКАЗЫ</b>\n\n"
    for oid, o in list(orders.items())[-10:]:
        text += f"#{oid} @{o['username']} - {o['tariff'].value[0]}\n"
    await callback.message.edit_text(text, reply_markup=get_admin_main_keyboard(), parse_mode="HTML")

@dp.callback_query(F.data == "admin_stats", OrderStates.admin_in_panel)
async def admin_stats(callback: CallbackQuery):
    s = get_stats()
    text = f"📊 <b>СТАТИСТИКА</b>\n\nЗаказов: {s['total_orders']}\nЗавершено: {s['completed']}\nЗаработано: {s['total_stars']}⭐"
    await callback.message.edit_text(text, reply_markup=get_admin_main_keyboard(), parse_mode="HTML")

@dp.callback_query(F.data == "admin_reviews", OrderStates.admin_in_panel)
async def admin_reviews(callback: CallbackQuery):
    pending = get_pending_reviews()
    if not pending:
        await callback.message.edit_text("📋 Нет отзывов", reply_markup=get_admin_main_keyboard())
        return
    await callback.message.delete()
    for r in pending[:5]:
        await callback.message.answer(f"💬 Отзыв #{r['id']}\n@{r['username']}: {r['text']}", reply_markup=get_admin_reviews_keyboard(r['id']))

# ========== ПЛАТЕЖИ ==========
@dp.callback_query(F.data.startswith("accept_"))
async def accept_order(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    parts = callback.data.split("_")
    order_id = int(parts[1] if len(parts) == 2 else parts[2])
    order = get_order(order_id)
    if not order:
        await callback.answer("❌ Не найден", show_alert=True)
        return
    if "free" in callback.data:
        mark_order_paid(order_id)
        order['status'] = 'development'
        await bot.send_message(order['user_id'], f"🆓 Заказ #{order_id} принят бесплатно!", reply_markup=get_client_order_keyboard(order_id))
        await callback.message.edit_text(f"✅ Заказ #{order_id} принят бесплатно")
    else:
        order['status'] = 'waiting_payment'
        await bot.send_invoice(order['user_id'], f"Оплата #{order_id}", f"Тариф: {order['tariff'].value[0]}", f"order_{order_id}", "", "XTR", [LabeledPrice("Оплата", order['tariff'].value[1])])
        await callback.message.edit_text(f"✅ Счет отправлен")

@dp.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@dp.message(F.successful_payment)
async def successful_payment_handler(message: Message):
    order_id = int(message.successful_payment.invoice_payload.split("_")[1])
    mark_order_paid(order_id)
    order = get_order(order_id)
    await message.answer(f"✅ Оплачено! Заказ #{order_id} в работе", reply_markup=get_client_order_keyboard(order_id))
    await bot.send_message(ADMIN_ID, f"💰 Заказ #{order_id} оплачен", reply_markup=get_development_keyboard(order_id))

# ========== РАЗРАБОТКА ==========
@dp.callback_query(F.data.startswith("write_"))
async def write_to_client(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    order_id = int(callback.data.split("_")[1])
    await state.update_data(write_order_id=order_id)
    await state.set_state(OrderStates.waiting_for_message)
    await callback.message.delete()
    await callback.message.answer("✉️ Введите сообщение:")

@dp.message(OrderStates.waiting_for_message)
async def send_message_to_client(message: Message, state: FSMContext):
    data = await state.get_data()
    order = get_order(data['write_order_id'])
    await bot.send_message(order['user_id'], f"📩 <b>От разработчика</b>\n\n{message.text}", parse_mode="HTML")
    await state.clear()
    await message.answer("✅ Отправлено", reply_markup=get_development_keyboard(order['id']))

@dp.callback_query(F.data.startswith("ready_"))
async def bot_ready(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    order_id = int(callback.data.split("_")[1])
    await state.update_data(ready_order_id=order_id)
    await state.set_state(OrderStates.waiting_for_token)
    await callback.message.delete()
    await callback.message.answer("✅ Введите API токен:")

@dp.message(OrderStates.waiting_for_token)
async def send_token_to_client(message: Message, state: FSMContext):
    data = await state.get_data()
    order = get_order(data['ready_order_id'])
    order['status'] = 'completed'
    order['token'] = message.text
    await bot.send_message(order['user_id'], f"🎉 <b>БОТ ГОТОВ!</b>\n\n<code>{message.text}</code>", parse_mode="HTML")
    await state.clear()
    await message.answer("✅ Токен отправлен", reply_markup=get_development_keyboard(order['id']))

@dp.callback_query(F.data.startswith("status_"))
async def check_status(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    order_id = int(callback.data.split("_")[1])
    order = get_order(order_id)
    status = {'pending': '⏳', 'waiting_payment': '💰', 'development': '🛠️', 'completed': '✅'}.get(order['status'], '❓')
    await callback.message.edit_text(f"📊 Статус #{order_id}: {status}", reply_markup=get_development_keyboard(order_id))

# ========== ОТЗЫВЫ ==========
@dp.callback_query(F.data == "show_reviews")
async def show_reviews(callback: CallbackQuery):
    approved = get_approved_reviews()
    await callback.message.delete()
    if not approved:
        await callback.message.answer("💬 Нет отзывов", reply_markup=get_back_keyboard())
        return
    text = "💬 <b>ОТЗЫВЫ</b>\n\n"
    for r in approved[-10:]:
        text += f"{'⭐'*r['rating']} @{r['username']}: {r['text']}\n"
    await callback.message.answer(text, reply_markup=get_back_keyboard(), parse_mode="HTML")

@dp.callback_query(F.data.startswith("leave_review_"))
async def leave_review_start(callback: CallbackQuery, state: FSMContext):
    order_id = int(callback.data.split("_")[2])
    order = get_order(order_id)
    if not order or order['user_id'] != callback.from_user.id or order['status'] != 'completed':
        await callback.answer("❌ Нельзя оставить отзыв", show_alert=True)
        return
    await state.update_data(review_order_id=order_id)
    await state.set_state(OrderStates.waiting_for_review_rating)
    await callback.message.delete()
    await callback.message.answer("⭐ <b>ОЦЕНКА</b>", reply_markup=get_review_rating_keyboard(), parse_mode="HTML")

@dp.callback_query(F.data.startswith("rate_"), OrderStates.waiting_for_review_rating)
async def review_rating_chosen(callback: CallbackQuery, state: FSMContext):
    rating = int(callback.data.split("_")[1])
    await state.update_data(review_rating=rating)
    await state.set_state(OrderStates.waiting_for_review_text)
    await callback.message.delete()
    await callback.message.answer(f"📝 <b>НАПИШИТЕ ОТЗЫВ</b> (оценка: {'⭐'*rating})", parse_mode="HTML")

@dp.message(OrderStates.waiting_for_review_text)
async def review_text_received(message: Message, state: FSMContext):
    data = await state.get_data()
    review_id = create_review(message.from_user.id, message.from_user.username or "user", data['review_rating'], message.text, data['review_order_id'])
    await state.clear()
    await message.answer("✅ <b>СПАСИБО!</b> Отзыв отправлен на модерацию", reply_markup=get_back_keyboard(), parse_mode="HTML")
    await bot.send_message(ADMIN_ID, f"📝 Новый отзыв #{review_id}", reply_markup=get_admin_reviews_keyboard(review_id))

@dp.callback_query(F.data.startswith("approve_review_"))
async def approve_review_handler(callback: CallbackQuery):
    review_id = int(callback.data.split("_")[2])
    if approve_review(review_id):
        await callback.message.edit_text("✅ Одобрено")
    else:
        await callback.answer("❌ Ошибка", show_alert=True)

@dp.callback_query(F.data.startswith("reject_review_"))
async def reject_review_handler(callback: CallbackQuery):
    review_id = int(callback.data.split("_")[2])
    reject_review(review_id)
    await callback.message.edit_text("❌ Отклонено")

# ========== ОБЩЕЕ ==========
@dp.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer(MAIN_MENU_TEXT, reply_markup=get_main_inline_keyboard(), parse_mode="HTML")

# ========== ЗАПУСК ==========
async def main():
    logger.info("🚀 БОТ ЗАПУЩЕН!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
