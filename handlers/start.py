from aiogram import types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from config import MAIN_MENU_TEXT, ADMIN_ID
from keyboards import (
    get_reply_main_keyboard, get_main_inline_keyboard,
    get_back_keyboard, get_admin_main_keyboard,
    get_tariff_keyboard, get_review_rating_keyboard
)
from states import OrderStates
from database import get_stats, get_user_orders, get_approved_reviews
import database

async def cmd_start(message: Message, state: FSMContext):
    """Обработчик команды /start"""
    await state.clear()
    
    stats = get_stats()
    menu_text = MAIN_MENU_TEXT + f"\n\n📊 Статистика:\n└ Заказов: {stats['total_orders']} | Отзывов: {stats['reviews_count']}"
    
    await message.answer(
        "🎨 <b>Загрузка...</b>",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await message.answer(
        menu_text,
        reply_markup=get_reply_main_keyboard(),
        parse_mode="HTML"
    )
    await message.answer(
        "✨ <b>Быстрые действия:</b>",
        reply_markup=get_main_inline_keyboard(),
        parse_mode="HTML"
    )

# === ОБРАБОТЧИКИ REPLY KEYBOARD ===
async def reply_order(message: Message, state: FSMContext):
    """Обработка кнопки '📦 ЗАКАЗАТЬ БОТА'"""
    await state.clear()
    await message.answer(
        "📦 <b>ВЫБЕРИТЕ ТАРИФ</b>\n\n"
        "┌─────────────────────────┐\n"
        "│ ⭐ МИНИМАЛЬНЫЙ • 50⭐    │\n"
        "│ Базовые команды         │\n"
        "├─────────────────────────┤\n"
        "│ ⭐⭐ СРЕДНИЙ • 100⭐     │\n"
        "│ Команды + инлайн кнопки │\n"
        "├─────────────────────────┤\n"
        "│ ⭐⭐⭐ ПОЛНЫЙ • 300⭐     │\n"
        "│ Любые функции, кастом   │\n"
        "└─────────────────────────┘\n\n"
        "<i>Выберите подходящий тариф:</i>",
        reply_markup=get_tariff_keyboard(),
        parse_mode="HTML"
    )

async def reply_my_orders(message: Message):
    """Обработка кнопки '📋 МОИ ЗАКАЗЫ'"""
    user_orders = database.get_user_orders(message.from_user.id)
    
    if not user_orders:
        await message.answer(
            "📋 <b>У вас пока нет заказов</b>\n\n"
            "Нажмите «Заказать бота», чтобы оформить заказ.",
            reply_markup=get_back_keyboard(),
            parse_mode="HTML"
        )
        return
    
    text = "📋 <b>ВАШИ ЗАКАЗЫ</b>\n\n"
    for order in sorted(user_orders, key=lambda x: x.created_at, reverse=True)[:5]:
        status_emoji = {
            'pending': '⏳',
            'waiting_payment': '💰',
            'development': '🛠️',
            'completed': '✅'
        }.get(order.status, '⏳')
        
        status_text = {
            'pending': 'Ожидает',
            'waiting_payment': 'Ожидает оплаты',
            'development': 'В разработке',
            'completed': 'Готов'
        }.get(order.status, 'Неизвестно')
        
        text += f"{status_emoji} <b>Заказ №{order.id}</b>\n"
        text += f"└ {order.tariff.value[0]} | {status_text}\n"
        text += f"└ {order.created_at.strftime('%d.%m.%Y')}\n\n"
    
    await message.answer(text, reply_markup=get_back_keyboard(), parse_mode="HTML")

async def reply_rules(message: Message):
    """Обработка кнопки '📜 ПРАВИЛА'"""
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
    await message.answer(text, reply_markup=get_back_keyboard(), parse_mode="HTML")

async def reply_faq(message: Message):
    """Обработка кнопки '❓ FAQ'"""
    text = (
        "💎 <b>ЧАСТО ЗАДАВАЕМЫЕ ВОПРОСЫ</b>\n\n"
        "❓ <b>Как оплатить?</b>\n"
        "➡️ Звездами Telegram прямо в боте\n\n"
        "❓ <b>Как получу бота?</b>\n"
        "➡️ Получу API токен через бота\n\n"
        "❓ <b>Можно вернуть деньги?</b>\n"
        "➡️ <b>НЕТ!</b> Возврат не производится\n\n"
        "❓ <b>Сроки?</b>\n"
        "➡️ 1-5 дней в зависимости от сложности\n\n"
        "❓ <b>Правки?</b>\n"
        "➡️ 3 бесплатные правки в течение 3 дней"
    )
    await message.answer(text, reply_markup=get_back_keyboard(), parse_mode="HTML")

async def reply_prices(message: Message):
    """Обработка кнопки '💰 ТАРИФЫ'"""
    text = (
        "💰 <b>ПРАЙС-ЛИСТ</b>\n\n"
        "┌─────────────────────────┐\n"
        "│ ⭐ МИНИМАЛЬНЫЙ • 50⭐    │\n"
        "│ • Базовые команды       │\n"
        "│ • Срок: 1-2 дня         │\n"
        "├─────────────────────────┤\n"
        "│ ⭐⭐ СРЕДНИЙ • 100⭐     │\n"
        "│ • Команды + кнопки      │\n"
        "│ • Срок: 2-3 дня         │\n"
        "├─────────────────────────┤\n"
        "│ ⭐⭐⭐ ПОЛНЫЙ • 300⭐     │\n"
        "│ • Любые функции         │\n"
        "│ • Срок: 3-5 дней        │\n"
        "└─────────────────────────┘"
    )
    await message.answer(text, reply_markup=get_back_keyboard(), parse_mode="HTML")

async def reply_reviews(message: Message):
    """Обработка кнопки '💬 ОТЗЫВЫ'"""
    approved = get_approved_reviews()
    
    if not approved:
        await message.answer(
            "💬 <b>ОТЗЫВОВ ПОКА НЕТ</b>\n\n"
            "Будьте первым, кто оставит отзыв!",
            reply_markup=get_back_keyboard(),
            parse_mode="HTML"
        )
        return
    
    text = "💬 <b>ОТЗЫВЫ НАШИХ КЛИЕНТОВ</b>\n\n"
    
    for review in approved[-5:]:
        text += f"{'⭐' * review.rating}\n"
        text += f"<b>@{review.username}:</b>\n"
        text += f"{review.text}\n"
        text += f"📅 {review.date.strftime('%d.%m.%Y')}\n\n"
    
    await message.answer(text, reply_markup=get_back_keyboard(), parse_mode="HTML")

async def reply_admin(message: Message, state: FSMContext):
    """Обработка кнопки '👑 АДМИН ПАНЕЛЬ'"""
    if message.from_user.id == ADMIN_ID:
        await state.set_state(OrderStates.admin_login)
        await message.answer(
            "🔐 <b>ВВЕДИТЕ ПАРОЛЬ ДОСТУПА</b>\n\n"
            "Для входа в админ панель требуется авторизация:",
            parse_mode="HTML"
        )
    else:
        await message.answer("⛔ Доступ запрещен! Эта кнопка только для администратора.")

# === INLINE ОБРАБОТЧИКИ ===
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню"""
    await state.clear()
    await callback.message.delete()
    
    stats = get_stats()
    menu_text = MAIN_MENU_TEXT + f"\n\n📊 Статистика:\n└ Заказов: {stats['total_orders']} | Отзывов: {stats['reviews_count']}"
    
    await callback.message.answer(
        menu_text,
        reply_markup=get_main_inline_keyboard(),
        parse_mode="HTML"
    )

async def show_rules(callback: CallbackQuery):
    """Показать правила"""
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
        "╚══════════════════════════════╝"
    )
    await callback.message.answer(text, reply_markup=get_back_keyboard(), parse_mode="HTML")

async def show_faq(callback: CallbackQuery):
    """Показать FAQ"""
    await callback.message.delete()
    text = (
        "💎 <b>ЧАСТО ЗАДАВАЕМЫЕ ВОПРОСЫ</b>\n\n"
        "❓ <b>Как оплатить?</b>\n"
        "➡️ Звездами Telegram прямо в боте\n\n"
        "❓ <b>Как получу бота?</b>\n"
        "➡️ Получу API токен через бота\n\n"
        "❓ <b>Можно вернуть деньги?</b>\n"
        "➡️ <b>НЕТ!</b> Возврат не производится\n\n"
        "❓ <b>Сроки?</b>\n"
        "➡️ 1-5 дней в зависимости от сложности\n\n"
        "❓ <b>Правки?</b>\n"
        "➡️ 3 бесплатные правки в течение 3 дней"
    )
    await callback.message.answer(text, reply_markup=get_back_keyboard(), parse_mode="HTML")

async def show_prices(callback: CallbackQuery):
    """Показать цены"""
    await callback.message.delete()
    text = (
        "💰 <b>ПРАЙС-ЛИСТ</b>\n\n"
        "┌─────────────────────────┐\n"
        "│ ⭐ МИНИМАЛЬНЫЙ • 50⭐    │\n"
        "│ • Базовые команды       │\n"
        "│ • Срок: 1-2 дня         │\n"
        "├─────────────────────────┤\n"
        "│ ⭐⭐ СРЕДНИЙ • 100⭐     │\n"
        "│ • Команды + кнопки      │\n"
        "│ • Срок: 2-3 дня         │\n"
        "├─────────────────────────┤\n"
        "│ ⭐⭐⭐ ПОЛНЫЙ • 300⭐     │\n"
        "│ • Любые функции         │\n"
        "│ • Срок: 3-5 дней        │\n"
        "└─────────────────────────┘"
    )
    await callback.message.answer(text, reply_markup=get_back_keyboard(), parse_mode="HTML")

def register_handlers(dp):
    """Регистрация всех обработчиков"""
    
    # Reply keyboard обработчики (обычные кнопки внизу)
    dp.message.register(cmd_start, CommandStart())
    dp.message.register(reply_order, F.text == "📦 ЗАКАЗАТЬ БОТА")
    dp.message.register(reply_my_orders, F.text == "📋 МОИ ЗАКАЗЫ")
    dp.message.register(reply_rules, F.text == "📜 ПРАВИЛА")
    dp.message.register(reply_faq, F.text == "❓ FAQ")
    dp.message.register(reply_prices, F.text == "💰 ТАРИФЫ")
    dp.message.register(reply_reviews, F.text == "💬 ОТЗЫВЫ")
    dp.message.register(reply_admin, F.text == "👑 АДМИН ПАНЕЛЬ")
    
    # Inline keyboard обработчики
    dp.callback_query.register(back_to_main, F.data == "back_to_main")
    dp.callback_query.register(show_rules, F.data == "rules")
    dp.callback_query.register(show_faq, F.data == "faq")
    dp.callback_query.register(show_prices, F.data == "prices")
