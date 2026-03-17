import logging
import asyncio
from datetime import datetime
from typing import Dict, Optional
from enum import Enum

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton,
    CallbackQuery, Message, FSInputFile
)

# ТВОИ ДАННЫЕ
TOKEN = "8546103501:AAGZv9evkjpQJR92TxX5-6Do7W_7M6XwXbw"
ADMIN_ID = 8259326703  # твой ID
ADMIN_PASSWORD = "17157150Sw!"  # пароль для админ панели

# Логирование
logging.basicConfig(level=logging.INFO)

# Инициализация
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Хранилище заказов
orders = {}
order_counter = 0

# Классы состояний
class OrderStates(StatesGroup):
    choosing_tariff = State()
    entering_description = State()
    waiting_for_payment = State()
    in_development = State()
    waiting_for_token = State()
    admin_login = State()
    admin_waiting_message = State()

class Tariff(Enum):
    MIN = ("⭐ Минимальный", 50)
    MID = ("⭐⭐ Средний", 100)
    MAX = ("⭐⭐⭐ Полный", 300)

# === REPLY KEYBOARD (Обычные кнопки внизу) ===
def get_reply_main_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📦 Заказать бота"), KeyboardButton(text="📋 Мои заказы")],
            [KeyboardButton(text="📜 Правила"), KeyboardButton(text="❓ FAQ")],
            [KeyboardButton(text="👑 Админ панель")]
        ],
        resize_keyboard=True,  # Автоматический размер
        input_field_placeholder="Выберите действие..."
    )
    return keyboard

# === INLINE КНОПКИ ===
def get_main_inline_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 ЗАКАЗАТЬ БОТА", callback_data="order")],
        [InlineKeyboardButton(text="📋 МОИ ЗАКАЗЫ", callback_data="my_orders")],
        [InlineKeyboardButton(text="📜 ПРАВИЛА И FAQ", callback_data="rules")]
    ])

def get_tariff_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ 50 ⭐ - Минимальный", callback_data="tariff_min")],
        [InlineKeyboardButton(text="⭐⭐ 100 ⭐ - Средний", callback_data="tariff_mid")],
        [InlineKeyboardButton(text="⭐⭐⭐ 300 ⭐ - Полный", callback_data="tariff_max")],
        [InlineKeyboardButton(text="◀ НАЗАД", callback_data="back_to_main")]
    ])

def get_payment_keyboard(order_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Я ОПЛАТИЛ", callback_data=f"paid_{order_id}")],
        [InlineKeyboardButton(text="◀ ОТМЕНА", callback_data="back_to_main")]
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
        [InlineKeyboardButton(text="📊 СТАТУС ЗАКАЗА", callback_data=f"status_{order_id}")]
    ])

def get_client_order_keyboard(order_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 МОИ ЗАКАЗЫ", callback_data="my_orders")],
        [InlineKeyboardButton(text="◀ ГЛАВНОЕ МЕНЮ", callback_data="back_to_main")]
    ])

def get_back_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀ НАЗАД", callback_data="back_to_main")]
    ])

def get_admin_main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 ВСЕ ЗАКАЗЫ", callback_data="admin_all_orders")],
        [InlineKeyboardButton(text="⏳ В ОЖИДАНИИ", callback_data="admin_pending")],
        [InlineKeyboardButton(text="🛠️ В РАЗРАБОТКЕ", callback_data="admin_development")],
        [InlineKeyboardButton(text="✅ ЗАВЕРШЕННЫЕ", callback_data="admin_completed")],
        [InlineKeyboardButton(text="📊 СТАТИСТИКА", callback_data="admin_stats")],
        [InlineKeyboardButton(text="◀ ВЫЙТИ", callback_data="back_to_main")]
    ])

# === СТАРТ ===
@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    
    text = (
        "✨ <b>Добро пожаловать в студию разработки ботов!</b>\n\n"
        "Создаю ботов любой сложности под ваши задачи.\n\n"
        "<b>🔥 Тарифы:</b>\n"
        "⭐ Минимальный (50 ⭐) - базовые команды\n"
        "⭐⭐ Средний (100 ⭐) - инлайн кнопки + команды\n"
        "⭐⭐⭐ Полный фарш (300 ⭐) - всё что угодно!\n\n"
        "<i>Используйте кнопки внизу для навигации 👇</i>"
    )
    
    await message.answer(
        text, 
        reply_markup=get_reply_main_keyboard(),  # Reply keyboard внизу
        parse_mode="HTML"
    )
    
    # Отправляем отдельно inline клавиатуру для красоты
    await message.answer(
        "📌 <b>Быстрые действия:</b>",
        reply_markup=get_main_inline_keyboard(),
        parse_mode="HTML"
    )

# === ОБРАБОТКА REPLY КНОПОК ===
@dp.message(F.text == "📦 Заказать бота")
async def reply_order(message: Message, state: FSMContext):
    await order_start(message, state)

@dp.message(F.text == "📋 Мои заказы")
async def reply_my_orders(message: Message):
    await show_my_orders(message)

@dp.message(F.text == "📜 Правила")
async def reply_rules(message: Message):
    await show_rules(message)

@dp.message(F.text == "❓ FAQ")
async def reply_faq(message: Message):
    await show_faq(message)

@dp.message(F.text == "👑 Админ панель")
async def reply_admin(message: Message, state: FSMContext):
    if message.from_user.id == ADMIN_ID:
        await state.set_state(OrderStates.admin_login)
        await message.answer(
            "🔐 <b>Введите пароль для доступа к админ панели:</b>",
            parse_mode="HTML"
        )
    else:
        await message.answer("⛔ Доступ запрещен!")

# === ПРОВЕРКА ПАРОЛЯ ===
@dp.message(OrderStates.admin_login)
async def check_admin_password(message: Message, state: FSMContext):
    if message.text == ADMIN_PASSWORD:
        await state.clear()
        await message.answer(
            "👑 <b>ДОБРО ПОЖАЛОВАТЬ В АДМИН ПАНЕЛЬ</b>\n\n"
            "Выберите раздел:",
            reply_markup=get_admin_main_keyboard(),
            parse_mode="HTML"
        )
    else:
        await message.answer("❌ Неверный пароль! Доступ запрещен.")
        await state.clear()

# === АДМИН ПАНЕЛЬ (INLINE) ===
@dp.callback_query(F.data == "admin_all_orders")
async def admin_all_orders(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Доступ запрещен", show_alert=True)
        return
    
    if not orders:
        await callback.message.edit_text(
            "📋 <b>Нет заказов</b>",
            reply_markup=get_back_keyboard(),
            parse_mode="HTML"
        )
        return
    
    text = "📋 <b>ВСЕ ЗАКАЗЫ:</b>\n\n"
    for order_id, order in orders.items():
        status_emoji = {
            'pending': '⏳',
            'waiting_payment': '💰',
            'development': '🛠️',
            'completed': '✅'
        }.get(order['status'], '⏳')
        
        text += f"{status_emoji} <b>#{order_id}</b> @{order['username']} - {order['tariff'].value[0]}\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_admin_main_keyboard(),
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "admin_pending")
async def admin_pending(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Доступ запрещен", show_alert=True)
        return
    
    pending = {k: v for k, v in orders.items() if v['status'] in ['pending', 'waiting_payment']}
    
    if not pending:
        await callback.message.edit_text(
            "📋 <b>Нет заказов в ожидании</b>",
            reply_markup=get_admin_main_keyboard(),
            parse_mode="HTML"
        )
        return
    
    text = "⏳ <b>ЗАКАЗЫ В ОЖИДАНИИ:</b>\n\n"
    for order_id, order in pending.items():
        text += f"• <b>#{order_id}</b> @{order['username']} - {order['tariff'].value[0]} ({order['status']})\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_admin_main_keyboard(),
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "admin_development")
async def admin_development(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Доступ запрещен", show_alert=True)
        return
    
    dev = {k: v for k, v in orders.items() if v['status'] == 'development'}
    
    if not dev:
        await callback.message.edit_text(
            "📋 <b>Нет заказов в разработке</b>",
            reply_markup=get_admin_main_keyboard(),
            parse_mode="HTML"
        )
        return
    
    text = "🛠️ <b>ЗАКАЗЫ В РАЗРАБОТКЕ:</b>\n\n"
    for order_id, order in dev.items():
        text += f"• <b>#{order_id}</b> @{order['username']} - {order['tariff'].value[0]}\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_admin_main_keyboard(),
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "admin_completed")
async def admin_completed(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Доступ запрещен", show_alert=True)
        return
    
    completed = {k: v for k, v in orders.items() if v['status'] == 'completed'}
    
    if not completed:
        await callback.message.edit_text(
            "📋 <b>Нет завершенных заказов</b>",
            reply_markup=get_admin_main_keyboard(),
            parse_mode="HTML"
        )
        return
    
    text = "✅ <b>ЗАВЕРШЕННЫЕ ЗАКАЗЫ:</b>\n\n"
    for order_id, order in completed.items():
        text += f"• <b>#{order_id}</b> @{order['username']} - {order['tariff'].value[0]}\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_admin_main_keyboard(),
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Доступ запрещен", show_alert=True)
        return
    
    total = len(orders)
    pending = len([o for o in orders.values() if o['status'] in ['pending', 'waiting_payment']])
    development = len([o for o in orders.values() if o['status'] == 'development'])
    completed = len([o for o in orders.values() if o['status'] == 'completed'])
    
    total_stars = sum([o['tariff'].value[1] for o in orders.values() if o.get('paid', False)])
    
    text = (
        "📊 <b>СТАТИСТИКА</b>\n\n"
        f"📋 Всего заказов: {total}\n"
        f"⏳ В ожидании: {pending}\n"
        f"🛠️ В разработке: {development}\n"
        f"✅ Завершено: {completed}\n"
        f"💰 Заработано звезд: {total_stars}⭐\n"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_admin_main_keyboard(),
        parse_mode="HTML"
    )

# === INLINE ОБРАБОТЧИКИ ===
@dp.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer(
        "✨ <b>Главное меню</b>",
        reply_markup=get_main_inline_keyboard(),
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "order")
async def order_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer(
        "📦 <b>ВЫБЕРИТЕ ТАРИФ</b>\n\n"
        "⭐ <b>Минимальный (50⭐)</b> - только команды\n"
        "⭐⭐ <b>Средний (100⭐)</b> - команды + инлайн кнопки\n"
        "⭐⭐⭐ <b>Полный (300⭐)</b> - полный кастом, любые функции\n\n"
        "<i>Выберите подходящий тариф:</i>",
        reply_markup=get_tariff_keyboard(),
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "rules")
async def show_rules(callback: CallbackQuery):
    await callback.message.delete()
    text = (
        "╔══════════════════════════════╗\n"
        "║         📜 ПРАВИЛА           ║\n"
        "╠══════════════════════════════╣\n"
        "║ ❌ <b>НЕ РАЗРАБАТЫВАЕМ:</b>     ║\n"
        "║ • 18+ контент                 ║\n"
        "║ • Пробив/базы данных          ║\n"
        "║ • Спам/рассылки               ║\n"
        "║ • Противозаконное             ║\n"
        "╠══════════════════════════════╣\n"
        "║ ⚠️ <b>УСЛОВИЯ:</b>               ║\n"
        "║ • Возврат НЕ производится     ║\n"
        "║ • Связь только через бота     ║\n"
        "║ • Сроки: 1-5 дней             ║\n"
        "║ • Передается API токен        ║\n"
        "╚══════════════════════════════╝"
    )
    await callback.message.answer(text, reply_markup=get_back_keyboard(), parse_mode="HTML")

@dp.callback_query(F.data == "faq")
async def show_faq(callback: CallbackQuery):
    await callback.message.delete()
    text = (
        "💎 <b>ЧАСТО ЗАДАВАЕМЫЕ ВОПРОСЫ</b>\n\n"
        "❓ <b>Как я получу бота?</b>\n"
        "➡️ После завершения разработки \n"
        "   я передам вам API токен и полную \n"
        "   инструкцию через бота\n\n"
        "❓ <b>Можно вернуть деньги?</b>\n"
        "➡️ <b>НЕТ!</b> Возврат не производится, \n"
        "   но вы получаете гарантированно \n"
        "   рабочего бота\n\n"
        "❓ <b>Сколько ждать?</b>\n"
        "➡️ 1-5 дней в зависимости от сложности\n\n"
        "❓ <b>Как связаться с вами?</b>\n"
        "➡️ Только через этого бота. \n"
        "   После оплаты я смогу писать вам"
    )
    await callback.message.answer(text, reply_markup=get_back_keyboard(), parse_mode="HTML")

# === ВЫБОР ТАРИФА ===
@dp.callback_query(F.data.startswith("tariff_"))
async def tariff_chosen(callback: CallbackQuery, state: FSMContext):
    tariff_map = {
        "tariff_min": Tariff.MIN,
        "tariff_mid": Tariff.MID,
        "tariff_max": Tariff.MAX
    }
    
    tariff = tariff_map[callback.data]
    await state.update_data(tariff=tariff)
    await state.set_state(OrderStates.entering_description)
    
    await callback.message.delete()
    await callback.message.answer(
        f"📝 <b>ОПИШИТЕ ЗАДАЧУ</b>\n\n"
        f"Выбран тариф: {tariff.value[0]} ({tariff.value[1]}⭐)\n\n"
        f"Подробно опишите, какого бота вам нужно:\n"
        f"• Основные функции\n"
        f"• Желаемый функционал\n"
        f"• Дополнительные пожелания\n\n"
        f"<i>Отправьте описание одним сообщением:</i>",
        parse_mode="HTML"
    )

# === ПРИЕМ ОПИСАНИЯ ===
@dp.message(OrderStates.entering_description)
async def description_received(message: Message, state: FSMContext):
    global order_counter
    order_counter += 1
    order_id = order_counter
    
    data = await state.get_data()
    tariff = data['tariff']
    
    # Сохраняем заказ
    orders[order_id] = {
        'id': order_id,
        'user_id': message.from_user.id,
        'username': message.from_user.username or "нет username",
        'tariff': tariff,
        'description': message.text,
        'status': 'pending',
        'created_at': datetime.now(),
        'paid': False
    }
    
    await state.clear()
    
    # Подтверждение клиенту
    await message.answer(
        f"✅ <b>ЗАКАЗ №{order_id} ОФОРМЛЕН!</b>\n\n"
        f"Тариф: {tariff.value[0]} ({tariff.value[1]}⭐)\n"
        f"Описание: {message.text[:100]}...\n\n"
        f"⏳ Ожидайте подтверждения от разработчика.\n"
        f"Статус заказа можно отслеживать в меню <b>«Мои заказы»</b>",
        reply_markup=get_client_order_keyboard(order_id),
        parse_mode="HTML"
    )
    
    # Уведомление админу
    admin_text = (
        f"🔔 <b>НОВЫЙ ЗАКАЗ #{order_id}</b>\n\n"
        f"От: @{orders[order_id]['username']} (ID: {message.from_user.id})\n"
        f"Тариф: {tariff.value[0]} ({tariff.value[1]}⭐)\n\n"
        f"<b>Описание:</b>\n{message.text}\n\n"
        f"<i>Выберите действие:</i>"
    )
    
    await bot.send_message(
        ADMIN_ID,
        admin_text,
        reply_markup=get_admin_order_keyboard(order_id, is_free=True),
        parse_mode="HTML"
    )

# === ПРИНЯТЬ ЗАКАЗ ===
@dp.callback_query(F.data.startswith("accept_"))
async def accept_order(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Ты не админ!", show_alert=True)
        return
    
    parts = callback.data.split("_")
    if len(parts) == 2:  # accept_123
        order_id = int(parts[1])
        is_free = False
    else:  # accept_free_123
        order_id = int(parts[2])
        is_free = True
    
    if order_id not in orders:
        await callback.answer("Заказ не найден!", show_alert=True)
        return
    
    order = orders[order_id]
    
    if is_free:
        order['paid'] = True
        order['status'] = 'development'
        
        # Клиенту
        await bot.send_message(
            order['user_id'],
            f"🆓 <b>ЗАКАЗ №{order_id} ПРИНЯТ БЕСПЛАТНО!</b>\n\n"
            f"Разработчик начал работу над вашим ботом.\n"
            f"Статус можно отслеживать в меню.",
            reply_markup=get_client_order_keyboard(order_id),
            parse_mode="HTML"
        )
        
        await callback.message.edit_text(
            f"✅ Заказ #{order_id} принят БЕСПЛАТНО!",
            reply_markup=None
        )
    else:
        order['status'] = 'waiting_payment'
        
        # Клиенту
        await bot.send_message(
            order['user_id'],
            f"✅ <b>ЗАКАЗ №{order_id} ПРИНЯТ!</b>\n\n"
            f"Тариф: {order['tariff'].value[0]} ({order['tariff'].value[1]}⭐)\n"
            f"Сумма к оплате: {order['tariff'].value[1]} ⭐\n\n"
            f"После оплаты нажмите кнопку ниже:",
            reply_markup=get_payment_keyboard(order_id),
            parse_mode="HTML"
        )
        
        await callback.message.edit_text(
            f"✅ Заказ #{order_id} принят, ожидаем оплату",
            reply_markup=None
        )

# === ПОДТВЕРЖДЕНИЕ ОПЛАТЫ ===
@dp.callback_query(F.data.startswith("paid_"))
async def payment_confirmed(callback: CallbackQuery):
    order_id = int(callback.data.split("_")[1])
    
    if order_id not in orders:
        await callback.answer("Заказ не найден!", show_alert=True)
        return
    
    order = orders[order_id]
    order['paid'] = True
    order['status'] = 'development'
    
    await callback.message.delete()
    await callback.message.answer(
        f"✅ <b>ОПЛАТА ПОДТВЕРЖДЕНА!</b>\n\n"
        f"Заказ №{order_id}\n"
        f"Статус: <b>В разработке</b> 🛠️\n\n"
        f"Разработчик скоро приступит к работе.",
        reply_markup=get_client_order_keyboard(order_id),
        parse_mode="HTML"
    )
    
    # Уведомление админу
    await bot.send_message(
        ADMIN_ID,
        f"💰 <b>ЗАКАЗ #{order_id} ОПЛАЧЕН!</b>\n\n"
        f"Клиент: @{order['username']}\n"
        f"Сумма: {order['tariff'].value[1]}⭐\n\n"
        f"Можете начинать разработку.\n\n"
        f"<b>Кнопка связи с клиентом доступна в меню заказа</b>",
        reply_markup=get_development_keyboard(order_id),
        parse_mode="HTML"
    )

# === НАПИСАТЬ КЛИЕНТУ ===
@dp.callback_query(F.data.startswith("write_"))
async def write_to_client(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Доступ запрещен", show_alert=True)
        return
    
    order_id = int(callback.data.split("_")[1])
    await state.update_data(write_order_id=order_id)
    await state.set_state(OrderStates.admin_waiting_message)
    
    await callback.message.delete()
    await callback.message.answer(
        f"✉️ <b>НАПИСАТЬ КЛИЕНТУ</b>\n\n"
        f"Заказ №{order_id}\n"
        f"Клиент: @{orders[order_id]['username']}\n\n"
        f"Введите сообщение для клиента:",
        parse_mode="HTML"
    )

@dp.message(OrderStates.admin_waiting_message)
async def send_message_to_client(message: Message, state: FSMContext):
    data = await state.get_data()
    order_id = data['write_order_id']
    order = orders[order_id]
    
    await bot.send_message(
        order['user_id'],
        f"📩 <b>СООБЩЕНИЕ ОТ РАЗРАБОТЧИКА</b>\n\n"
        f"По заказу №{order_id}\n\n"
        f"{message.text}",
        reply_markup=get_client_order_keyboard(order_id),
        parse_mode="HTML"
    )
    
    await state.clear()
    await message.answer(
        f"✅ Сообщение отправлено клиенту @{order['username']}",
        reply_markup=get_development_keyboard(order_id)
    )

# === БОТ ГОТОВ ===
@dp.callback_query(F.data.startswith("ready_"))
async def bot_ready(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Доступ запрещен", show_alert=True)
        return
    
    order_id = int(callback.data.split("_")[1])
    await state.update_data(ready_order_id=order_id)
    await state.set_state(OrderStates.waiting_for_token)
    
    await callback.message.delete()
    await callback.message.answer(
        f"✅ <b>БОТ ГОТОВ!</b>\n\n"
        f"Заказ №{order_id}\n"
        f"Клиент: @{orders[order_id]['username']}\n\n"
        f"Введите API токен готового бота:",
        parse_mode="HTML"
    )

@dp.message(OrderStates.waiting_for_token)
async def send_token_to_client(message: Message, state: FSMContext):
    data = await state.get_data()
    order_id = data['ready_order_id']
    order = orders[order_id]
    
    token = message.text
    order['status'] = 'completed'
    
    await bot.send_message(
        order['user_id'],
        f"🎉 <b>ТВОЙ БОТ ГОТОВ!</b>\n\n"
        f"<b>🤖 API Токен:</b>\n<code>{token}</code>\n\n"
        f"<b>📋 Инструкция:</b>\n"
        f"1. Перейди в @BotFather\n"
        f"2. Вставь этот токен\n"
        f"3. Готово! Бот твой\n\n"
        f"┌─────────────────────────────┐\n"
        f"│  ✅ ПОДТВЕРДИТЬ ПОЛУЧЕНИЕ   │\n"
        f"└─────────────────────────────┘",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ ПОДТВЕРДИТЬ ПОЛУЧЕНИЕ", callback_data=f"confirm_{order_id}")]
        ]),
        parse_mode="HTML"
    )
    
    await state.clear()
    await message.answer(
        f"✅ Токен отправлен клиенту @{order['username']}",
        reply_markup=get_development_keyboard(order_id)
    )

# === ПОДТВЕРЖДЕНИЕ ПОЛУЧЕНИЯ ===
@dp.callback_query(F.data.startswith("confirm_"))
async def confirm_receipt(callback: CallbackQuery):
    order_id = int(callback.data.split("_")[1])
    
    await callback.message.edit_text(
        f"✅ <b>ЗАКАЗ №{order_id} ЗАВЕРШЕН!</b>\n\n"
        f"Спасибо за заказ! Обращайтесь еще!",
        reply_markup=get_back_keyboard(),
        parse_mode="HTML"
    )
    
    await bot.send_message(
        ADMIN_ID,
        f"✅ <b>КЛИЕНТ ПОДТВЕРДИЛ ПОЛУЧЕНИЕ</b>\n\n"
        f"Заказ №{order_id}\n"
        f"Клиент: @{orders[order_id]['username']}\n\n"
        f"Заказ успешно завершен!",
        parse_mode="HTML"
    )

# === СТАТУС ЗАКАЗА ===
@dp.callback_query(F.data.startswith("status_"))
async def check_status(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Доступ запрещен", show_alert=True)
        return
    
    order_id = int(callback.data.split("_")[1])
    order = orders[order_id]
    
    status_text = {
        'pending': '⏳ Ожидает подтверждения',
        'waiting_payment': '💰 Ожидает оплаты',
        'development': '🛠️ В разработке',
        'completed': '✅ Завершен'
    }.get(order['status'], 'Неизвестно')
    
    await callback.message.edit_text(
        f"📊 <b>СТАТУС ЗАКАЗА #{order_id}</b>\n\n"
        f"Клиент: @{order['username']}\n"
        f"Тариф: {order['tariff'].value[0]} ({order['tariff'].value[1]}⭐)\n"
        f"Статус: {status_text}\n"
        f"Оплачен: {'✅' if order.get('paid', False) else '❌'}\n"
        f"Дата: {order['created_at'].strftime('%d.%m.%Y %H:%M')}\n\n"
        f"<b>Описание:</b>\n{order['description']}",
        reply_markup=get_development_keyboard(order_id),
        parse_mode="HTML"
    )

# === МОИ ЗАКАЗЫ (INLINE) ===
@dp.callback_query(F.data == "my_orders")
async def my_orders_inline(callback: CallbackQuery):
    await show_my_orders(callback.message)

async def show_my_orders(message: types.Message):
    user_orders = [o for o in orders.values() if o['user_id'] == message.from_user.id]
    
    if not user_orders:
        await message.answer(
            "📋 <b>У вас пока нет заказов</b>\n\n"
            "Нажмите «Заказать бота», чтобы оформить заказ.",
            reply_markup=get_back_keyboard(),
            parse_mode="HTML"
        )
        return
    
    text = "📋 <b>ВАШИ ЗАКАЗЫ:</b>\n\n"
    for order in user_orders[-5:]:  # последние 5
        status_emoji = {
            'pending': '⏳',
            'waiting_payment': '💰',
            'development': '🛠️',
            'completed': '✅'
        }.get(order['status'], '⏳')
        
        status_text = {
            'pending': 'Ожидает',
            'waiting_payment': 'Ожидает оплаты',
            'development': 'В разработке',
            'completed': 'Готов'
        }.get(order['status'], 'Неизвестно')
        
        text += f"{status_emoji} <b>Заказ №{order['id']}</b>\n"
        text += f"Тариф: {order['tariff'].value[0]}\n"
        text += f"Статус: {status_text}\n"
        text += f"Дата: {order['created_at'].strftime('%d.%m.%Y')}\n\n"
    
    text += "<i>Статусы обновляются автоматически</i>"
    
    await message.answer(text, reply_markup=get_back_keyboard(), parse_mode="HTML")

# === ОТКАЗ ОТ ЗАКАЗА ===
@dp.callback_query(F.data.startswith("reject_"))
async def reject_order(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Доступ запрещен", show_alert=True)
        return
    
    order_id = int(callback.data.split("_")[1])
    
    if order_id in orders:
        await bot.send_message(
            orders[order_id]['user_id'],
            f"❌ <b>ЗАКАЗ №{order_id} ОТКЛОНЕН</b>\n\n"
            f"К сожалению, разработчик не может принять этот заказ.\n"
            f"Попробуйте оформить заказ с другим описанием.",
            reply_markup=get_main_inline_keyboard(),
            parse_mode="HTML"
        )
        
        del orders[order_id]
    
    await callback.message.edit_text(
        f"❌ Заказ #{order_id} отклонен",
        reply_markup=None
    )

# === ЗАПУСК ===
async def main():
    print("🚀 Бот запущен и готов к работе!")
    print(f"👤 Админ ID: {ADMIN_ID}")
    print(f"🔐 Пароль админ панели: {ADMIN_PASSWORD}")
    print("📱 Проверьте бота: @KRIchiboBot")
    print("✅ Reply keyboard добавлена!")
    print("✅ Админ панель с паролем работает!")
    print("✅ Кнопка связи с клиентом есть в разработке!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
