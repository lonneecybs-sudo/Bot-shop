from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove

from config import MAIN_MENU_TEXT, ADMIN_ID
from keyboards import (
    get_reply_main_keyboard,
    get_main_inline_keyboard,
    get_back_keyboard,
    get_tariff_keyboard
)
from states import OrderStates
from database import get_stats, get_user_orders

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    
    stats = get_stats()
    menu_text = MAIN_MENU_TEXT + f"\n\n📊 Статистика:\n└ Заказов: {stats['total_orders']} | Отзывов: {stats['reviews_count']}"
    
    await message.answer(
        "🎨 <b>Загрузка...</b>",
        reply_markup=ReplyKeyboardRemove()
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

@router.message(F.text == "📦 ЗАКАЗАТЬ БОТА")
async def reply_order(message: Message, state: FSMContext):
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

@router.message(F.text == "📋 МОИ ЗАКАЗЫ")
async def reply_my_orders(message: Message):
    user_orders = get_user_orders(message.from_user.id)
    
    if not user_orders:
        await message.answer(
            "📋 <b>У вас пока нет заказов</b>",
            reply_markup=get_back_keyboard(),
            parse_mode="HTML"
        )
        return
    
    text = "📋 <b>ВАШИ ЗАКАЗЫ</b>\n\n"
    for order in sorted(user_orders, key=lambda x: x['created_at'], reverse=True)[:5]:
        status_emoji = {
            'pending': '⏳',
            'waiting_payment': '💰',
            'development': '🛠️',
            'completed': '✅'
        }.get(order['status'], '⏳')
        
        text += f"{status_emoji} <b>Заказ №{order['id']}</b>\n"
        text += f"└ {order['tariff'].value[0]}\n"
        text += f"└ {order['created_at'].strftime('%d.%m.%Y')}\n\n"
    
    await message.answer(text, reply_markup=get_back_keyboard(), parse_mode="HTML")

@router.message(F.text == "📜 ПРАВИЛА")
async def reply_rules(message: Message):
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
    await message.answer(text, reply_markup=get_back_keyboard(), parse_mode="HTML")

@router.message(F.text == "❓ FAQ")
async def reply_faq(message: Message):
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

@router.message(F.text == "💰 ТАРИФЫ")
async def reply_prices(message: Message):
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

@router.message(F.text == "💬 ОТЗЫВЫ")
async def reply_reviews(message: Message):
    from database import get_approved_reviews
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
        stars = "⭐" * review['rating']
        text += f"{stars}\n"
        text += f"<b>@{review['username']}:</b>\n"
        text += f"{review['text']}\n"
        text += f"📅 {review['date'].strftime('%d.%m.%Y')}\n\n"
    
    await message.answer(text, reply_markup=get_back_keyboard(), parse_mode="HTML")

@router.message(F.text == "👑 АДМИН ПАНЕЛЬ")
async def reply_admin(message: Message, state: FSMContext):
    if message.from_user.id == ADMIN_ID:
        await state.set_state(OrderStates.admin_login)
        await message.answer("🔐 <b>ВВЕДИТЕ ПАРОЛЬ ДОСТУПА</b>", parse_mode="HTML")
    else:
        await message.answer("⛔ Доступ запрещен!")

@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer(
        MAIN_MENU_TEXT,
        reply_markup=get_main_inline_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "rules")
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
        "╚══════════════════════════════╝"
    )
    await callback.message.answer(text, reply_markup=get_back_keyboard(), parse_mode="HTML")

@router.callback_query(F.data == "faq")
async def show_faq(callback: CallbackQuery):
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

@router.callback_query(F.data == "prices")
async def show_prices(callback: CallbackQuery):
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
